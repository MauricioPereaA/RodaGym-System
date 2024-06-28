import base64, os
from django.views.generic import ListView, TemplateView, View
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import CreateView
from .models import Miembro, DuracionActividad, Actividad, Configuracion
from finanzas.models import Transaccion, Caja, Ticket, ItemTicket
from .forms import MiembroForm
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .utils.fingerprint import FingerprintScanner
from time import sleep
from datetime import timedelta, datetime
from django.contrib import messages
from .tasks import verificar_y_actualizar_estatus_membresias
from acceso.models import ConfiguracionesAcesso
from escpos import *
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
class MiembroListView(ListView):
    model = Miembro
    context_object_name = 'miembros'
    paginate_by = 20
    template_name = 'miembros/lista_miembros.html'
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')  # Obtiene el parámetro de búsqueda 'q' de la URL, el valor por defecto es una cadena vacía
        if query:
            return Miembro.objects.filter(
                Q(nombres__icontains=query) | 
                Q(apellidos__icontains=query) | 
                Q(id__icontains=query)
            ).order_by('apellidos', 'nombres')
        return Miembro.objects.all().order_by('apellidos', 'nombres')
    
@method_decorator(login_required, name='dispatch')
class AgregarMiembroView(CreateView):
    model = Miembro
    form_class = MiembroForm
    template_name = 'miembros/agregar_miembro.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Pasar el request al formulario
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)

        # Obtén la imagen en formato Base64 desde el formulario
        image_data = self.request.POST.get('image_data')
        fingerprint_data = self.request.POST.get('fingerprint_data')
        if image_data:
            # Separa el prefijo de la cadena Base64 y decodifica la imagen
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]

            try:
                # Crea un nombre de archivo único
                filename = f"miembro_{slugify(self.object.nombres)}_{timezone.localtime(timezone.now()).strftime('%Y%m%d-%H%M%S')}.{ext.lower()}"
                # Decodifica la imagen y guarda el archivo
                image_data = base64.b64decode(imgstr)
                filepath = os.path.join(settings.MEDIA_ROOT, 'fotos_miembros', filename)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                # Asigna la ruta relativa del archivo al campo 'foto'
                self.object.foto = os.path.join('fotos_miembros', filename)
                self.object.huella_dactilar = fingerprint_data
            except Exception as e:
                print(e)

        duracion = self.request.POST.get('duracion_actividad')
        fecha_inicio = self.object.fecha_inicio_membresia

        # Luego realizas el cálculo de la fecha de fin basado en la duración seleccionada
        fecha_fin = self.calcular_fecha_fin_membresia(fecha_inicio, duracion)
        self.object.fecha_fin_membresia = fecha_fin

        self.object.save()
        form.save_m2m()  # Guarda las relaciones ManyToMany

        # Guardar el ID del miembro en la sesión y mas datos para la sesion
        actividad_id = self.request.POST.get('actividades')
        self.request.session['actividad_id'] = actividad_id
        self.request.session['duracion_actividad'] = duracion
        self.request.session['miembro_id'] = self.object.id

        #actualizar DB templates en miembros
        nuevo_miembro = ConfiguracionesAcesso.objects.first()
        nuevo_miembro.miembro_nuevo = True
        nuevo_miembro.save()

        # Redireccionar a la vista de pago con el ID del miembro
        return HttpResponseRedirect(reverse('miembros:miembro_pago', kwargs={'miembro_id': self.object.id}))
    
    @staticmethod
    def calcular_fecha_fin_membresia(fecha_inicio, duracion):
        if duracion == 'Anual':
            return fecha_inicio + timedelta(days=365)
        elif duracion == 'Semestral':
            return fecha_inicio + timedelta(days=182)
        elif duracion == 'Mensual':
            return fecha_inicio + timedelta(days=30)
        elif duracion == 'Quincenal':
            return fecha_inicio + timedelta(days=15)
        elif duracion == 'Semanal':
            return fecha_inicio + timedelta(days=7)
        elif duracion == 'Diario':
            return fecha_inicio  # Asumimos que Visita no agrega tiempo
        return fecha_inicio 

@require_POST
@csrf_exempt
def iniciar_captura_huella(request):
    print("Sesión init:", request.session.items())
    if request.POST.get('reset') == 'true':
        print(request.POST.get('control_flag'))
        print("Sesión reset:", request.session.items())
        fingerprint_scanner = FingerprintScanner()
        sleep(1)
        fingerprint_scanner.zkfp2.CloseDevice()
        request.session.clear()
        request.session.modified = True
        request.session['reset_flag'] = True
        request.session.modified = True
        print("Sesión actual:", request.session.items())

        # Puedes responder con un JSON indicando el éxito del reseteo
        return JsonResponse({'success': True})
    
    # Asegurarse de que la sesión está iniciada
    if not request.session.exists(request.session.session_key):
        request.session.create()
    print("Sesión actual:", request.session.items())

    fingerprint_scanner = FingerprintScanner()

    # Obtener la lista de templates de huellas dactilares de la sesión o iniciar una lista vacía
    templates = request.session.get('fingerprints', [])

    # Iniciar el proceso de captura
    capture = None
    while capture is None:
        if request.session.get('reset_flag'):
            fingerprint_scanner.zkfp2.CloseDevice()
            del request.session['reset_flag']  # Limpia el flag para futuras operaciones
            request.session.modified = True
            print("Sesión ciclo no controlado:", request.session.items())
            return JsonResponse({'success': False, 'message': 'Captura interrumpida por reinicio'})
        capture = fingerprint_scanner.zkfp2.AcquireFingerprint()
        sleep(0.1)
    template, img = capture
    if template:
        # Añadir el nuevo template a la lista en la sesión
        template_bytes = bytes(template)
        template_base64 = base64.b64encode(template_bytes).decode('utf-8')
        templates.append(template_base64)
        print("Sesión template1:", request.session.items())
        request.session['fingerprints'] = templates
        request.session.modified = True  # Indicar a Django que la sesión ha sido modificada
        print("Sesión template2:", request.session.items())
        # Revisar si se han capturado las 4 huellas dactilares
        #request.session.flush()
        if len(templates) == 3:
            # Si es la cuarta huella, combinar los templates y guardar en un lugar más permanente o en la sesión para uso futuro
            templates_temp = []
            for template_base64 in templates:
                templates_temp.append(base64.b64decode(template_base64))
            final_template, regTempLen = fingerprint_scanner.zkfp2.DBMerge(*templates_temp)
            final_template_bytes = bytes(final_template)
            final_template_base64 = base64.b64encode(final_template_bytes).decode('utf-8')
            #request.session['final_fingerprint_template'] = final_template_base64
            # Limpia la lista temporal de templates después de combinarlos
            fingerprint_scanner.zkfp2.CloseDevice()
            del request.session['fingerprints']
            request.session.modified = True
            print("Sesión final:", request.session.items())
            # Indicar éxito y que se han registrado las 4 huellas dactilares
            return JsonResponse({'success': True, 'registeredCount': 3, 'final_template': final_template_base64})
        else:
            #fingerprint_scanner.zkfp2.Terminate()
            #sleep(1)
            # Indicar éxito y la cantidad de huellas registradas hasta ahora
            return JsonResponse({'success': True, 'registeredCount': len(templates)})
    else:
        # Si la captura falló, enviar una respuesta indicando el fallo
        return JsonResponse({'success': False, 'registeredCount': len(templates)})

@method_decorator(login_required, name='dispatch')
class MiembroPagoView(TemplateView):
    template_name = 'miembros/miembro_pago.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        miembro_id = self.kwargs.get('miembro_id')
        actividad_id = self.request.session.get('actividad_id')
        duracion_actividad = self.request.session.get('duracion_actividad')
        miembro_fin_old = self.request.session.get('miembro_fin_old')

        miembro = get_object_or_404(Miembro, pk=miembro_id)
        actividad = get_object_or_404(Actividad, pk=actividad_id)
        duracion_actividad_obj = get_object_or_404(DuracionActividad, actividad=actividad, duracion=duracion_actividad)

        costo_actividad = duracion_actividad_obj.precio

        # Obtener la cuota de inscripción desde la configuración
        try:
            configuracion = Configuracion.objects.first()
            cuota_inscripcion = configuracion.costo_inscripcion if configuracion else 500.00
        except Configuracion.DoesNotExist:
            cuota_inscripcion = 500.00  # Valor por defecto si no hay configuración

        hoy = timezone.localtime(timezone.now()).date()
        if miembro.estatus_membresia == "Inactiva" or miembro.estatus_membresia == '':
            if miembro_fin_old == None:
                miembro_fin_old = str(hoy.isoformat())
            if ((hoy - datetime.strptime(miembro_fin_old, '%Y-%m-%d').date()).days <= 90) and miembro.estatus_membresia == "Inactiva":
                context['inscripcion'] = False
                context['miembro'] = miembro
                context['imagen_url'] = miembro.foto.url if miembro.foto else None
                context['actividad'] = actividad.nombre
                context['costo_actividad'] = costo_actividad
                context['costo_inscripcion'] = 0 
                context['costo_total'] = costo_actividad
                context['duracion'] = duracion_actividad
            else:
                context['inscripcion'] = True
                context['miembro'] = miembro
                context['imagen_url'] = miembro.foto.url if miembro.foto else None
                context['actividad'] = actividad.nombre
                context['costo_actividad'] = costo_actividad
                context['costo_inscripcion'] = cuota_inscripcion 
                context['costo_total'] = costo_actividad + cuota_inscripcion
                context['duracion'] = duracion_actividad
        else:
            context['inscripcion'] = False
            context['miembro'] = miembro
            context['imagen_url'] = miembro.foto.url if miembro.foto else None
            context['actividad'] = actividad.nombre
            context['costo_actividad'] = costo_actividad
            context['costo_total'] = costo_actividad
            context['duracion'] = duracion_actividad

        return context
    
@login_required
@csrf_exempt
def procesar_pago(request, miembro_id):
    if request.method == "POST":
        miembro = Miembro.objects.get(id=miembro_id)
        costo = request.POST.get("costo")
        print(f'Costo {costo} \n')
        cambio = request.POST.get("cambio")
        metodo_pago = request.POST.get("metodoPago")  # Asegúrate de obtener el valor correcto desde el frontend
        descuento = request.POST.get("descuento")
        duracion_actividad = request.POST.get("duracion")
        actividad = miembro.actividades.first()  # Ejemplo simplificado para obtener la actividad
        
        descripcion = f"Pago de {actividad} {duracion_actividad} del miembro {miembro.nombres} {miembro.apellidos} con descuento aplicado de: {descuento}%"
        caja = Caja.objects.filter(abierta=True).latest('fecha_apertura')
        # Crear la transacción
        Transaccion.objects.create(
            caja=caja,
            miembro=miembro,
            fecha=timezone.localtime(timezone.now()),
            tipo='Pago',
            cantidad=float(costo),
            descripcion=descripcion,
            metodo_pago=metodo_pago,
            usuario=request.user,  # Asumiendo que tienes un campo de usuario en tu modelo de Transacción
            venta_general=False,
        )

        miembro = get_object_or_404(Miembro, pk=miembro_id)
        miembro.estatus_membresia = "Activa"

        miembro.save()

        #actualizar DB templates en miembros
        nuevo_miembro = ConfiguracionesAcesso.objects.first()
        nuevo_miembro.miembro_nuevo = True
        nuevo_miembro.save()

        #actualizar membresias
        verificar_y_actualizar_estatus_membresias.apply()

        # Redirigir a otra vista o retornar una respuesta
        return JsonResponse({'success': True})
    else:
        # Manejar el caso para GET o mostrar un error
        return JsonResponse({"error": "Método no permitido"}, status=405)

@login_required
def imprimir_ticket(request):
    if request.method == "POST":
        miembro_id = request.POST.get("miembroId")
        miembro = Miembro.objects.get(id=miembro_id)
        costo = request.POST.get("costo")
        recibido = request.POST.get("cantidadRecibida")
        cambio = request.POST.get("cambio")
        metodo_pago = request.POST.get("metodoPago")  # Asegúrate de obtener el valor correcto desde el frontend
        duracion_actividad = request.POST.get("duracion")
        actividad = miembro.actividades.first()  # Ejemplo simplificado para obtener la actividad

         # Crear el Ticket
        ticket = Ticket.objects.create(
            cajero=request.user,
            fecha=timezone.localtime(timezone.now()),
            miembro=miembro,
            total=float(costo),
            metodo_pago=metodo_pago,
            recibido=float(recibido),
            cambio=float(cambio),
        )

        # Crear los ItemTicket
        
        itemticket = ItemTicket.objects.create(
            ticket=ticket,
            cantidad=1,
            descripcion=f'{duracion_actividad} {actividad}',
            importe=float(costo),
        )


        ruta_imagen = os.path.join(settings.BASE_DIR, 'static', 'images', 'spacefit', 'logo_impresion.png')
        thermal_printer = printer.Win32Raw('POS58 Printer')
        thermal_printer.set_with_default()
        thermal_printer.set(align='center')
        thermal_printer.image(ruta_imagen)
        thermal_printer.textln('Avenida Elias Zamora, Los Mangos')
        thermal_printer.textln('28869-Manzanillo, Colima')
        thermal_printer.textln('================================')
        thermal_printer.set(align='left')
        thermal_printer.textln(f'FOLIO:{ticket.id}')
        ticket_fecha_str = ticket.fecha.strftime('%Y-%m-%d %H:%M')
        thermal_printer.textln(f'FECHA:{ticket_fecha_str}')
        thermal_printer.textln(f'CAJERO:{ticket.cajero}')
        thermal_printer.textln(f'MIEMBRO:{ticket.miembro.nombres}')
        thermal_printer.textln(f'MIEMBROID:{ticket.miembro.id}')
        thermal_printer.textln('================================')
        thermal_printer.set(align='center')
        thermal_printer.set(bold=True)
        thermal_printer.textln('CANT   DESCRIPCION       IMPORTE')
        thermal_printer.textln('================================')
        thermal_printer.set(bold=False)
        thermal_printer.textln(f'{itemticket.cantidad:^4}{itemticket.descripcion:.19} ${itemticket.importe:^7}')
        thermal_printer.textln('________________________________')
        thermal_printer.textln(f'                 TOTAL: ${ticket.total:>7}')
        thermal_printer.textln('================================')
        thermal_printer.set(align='right')
        thermal_printer.textln(f'RECIBIDO: ${ticket.recibido:>7}')
        thermal_printer.textln(f'CAMBIO: ${ticket.cambio:>7}')
        thermal_printer.textln(f'FORMA PAGO:{ticket.metodo_pago}')
        thermal_printer.textln('================================')
        thermal_printer.ln(2)
        thermal_printer.cashdraw(2)
        thermal_printer.close()

        # Guardar ticket id en sesion para reimpresion
        request.session['ultimo_ticket_id'] = ticket.id

        # Redirigir a otra vista o retornar una respuesta
        return JsonResponse({'success': True})
    else:
        # Manejar el caso para GET o mostrar un error
        return JsonResponse({"error": "Método no permitido"}, status=405)

@login_required
def reimprimir_ticket(request):
    ticket_id = request.session.get('ultimo_ticket_id')
    ticket = Ticket.objects.get(id=ticket_id)
    itemticket = ticket.items.first()

    #reimpresion ticket
    ruta_imagen = os.path.join(settings.BASE_DIR, 'static', 'images', 'spacefit', 'logo_impresion.png')
    thermal_printer = printer.Win32Raw('POS58 Printer')
    thermal_printer.set_with_default()
    thermal_printer.set(align='center')
    thermal_printer.image(ruta_imagen)
    thermal_printer.textln('Avenida Elias Zamora, Los Mangos')
    thermal_printer.textln('28869-Manzanillo, Colima')
    thermal_printer.textln('================================')
    thermal_printer.set(align='left')
    thermal_printer.textln(f'FOLIO:{ticket.id}')
    ticket_fecha_str = ticket.fecha.strftime('%Y-%m-%d %H:%M')
    thermal_printer.textln(f'FECHA:{ticket_fecha_str}')
    thermal_printer.textln(f'CAJERO:{ticket.cajero}')
    thermal_printer.textln(f'MIEMBRO:{ticket.miembro.nombres}')
    thermal_printer.textln(f'MIEMBROID:{ticket.miembro.id}')
    thermal_printer.textln('================================')
    thermal_printer.set(align='center')
    thermal_printer.set(bold=True)
    thermal_printer.textln('CANT   DESCRIPCION       IMPORTE')
    thermal_printer.textln('================================')
    thermal_printer.set(bold=False)
    thermal_printer.textln(f'{itemticket.cantidad:^4}{itemticket.descripcion:.19} ${itemticket.importe:^7}')
    thermal_printer.textln('________________________________')
    thermal_printer.textln(f'                 TOTAL: ${ticket.total:>7}')
    thermal_printer.textln('================================')
    thermal_printer.set(align='right')
    thermal_printer.textln(f'RECIBIDO: ${ticket.recibido:>7}')
    thermal_printer.textln(f'CAMBIO: ${ticket.cambio:>7}')
    thermal_printer.textln(f'FORMA PAGO:{ticket.metodo_pago}')
    thermal_printer.textln('================================')
    thermal_printer.ln(2)
    thermal_printer.cashdraw(2)
    thermal_printer.close()

    # Redirigir a otra vista o retornar una respuesta
    return JsonResponse({'success': True})

@method_decorator(login_required, name='dispatch')
class EditarMiembroView(UpdateView):
    model = Miembro
    form_class = MiembroForm
    template_name = 'miembros/editar_miembro.html'
    pk_url_kwarg = 'miembro_id'
    success_url = reverse_lazy('miembros:lista_miembros') 
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, "La información se ha actualizado correctamente.")
        return HttpResponseRedirect(self.get_success_url())

@method_decorator(login_required, name='dispatch')
class SaveMemberImageView(View):
    def post(self, request, *args, **kwargs):
        image_data = request.POST.get('image_data')
        miembro_id =  request.POST.get('miembro_id')
        miembro = Miembro.objects.get(id=miembro_id)
        if image_data:
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]

            try:             
                filename = f"miembro_{slugify(miembro.nombres)}_{timezone.localtime(timezone.now()).strftime('%Y%m%d-%H%M%S')}.{ext.lower()}"
                image_data = base64.b64decode(imgstr)
                filepath = os.path.join(settings.MEDIA_ROOT, 'fotos_miembros', filename)
                with open(filepath, 'wb') as f:
                    f.write(image_data)

                # Devuelve la URL de la imagen guardada
                miembro.foto = os.path.join('fotos_miembros', filename)
                new_image_url = os.path.join(settings.MEDIA_URL, 'fotos_miembros', filename)
                miembro.save()
                print(new_image_url)
                return JsonResponse({'success': True, 'new_image_url': request.build_absolute_uri(new_image_url)})
            except Exception as e:
                print(e)
                return JsonResponse({'success': False})

        return JsonResponse({'success': False})

@method_decorator(login_required, name='dispatch')
class SaveMemberFingerPrintView(View):
    def post(self, request, *args, **kwargs):
        fingerprint_data = request.POST.get('fingerprint_data')
        miembro_id =  request.POST.get('miembro_id')
        miembro = Miembro.objects.get(id=miembro_id)
        if fingerprint_data:
            try:             
                miembro.huella_dactilar = fingerprint_data
                miembro.save()
                return JsonResponse({'success': True, })
            except Exception as e:
                print(e)
                return JsonResponse({'success': False})

        return JsonResponse({'success': False})
    
@csrf_exempt
def actualizar_miembro(request, miembro_id):
    if request.method == 'POST':
        # Obtén el miembro a actualizar
        miembro = get_object_or_404(Miembro, pk=miembro_id)

        # Actualiza los campos del miembro
        miembro.nombres = request.POST.get('nombre')
        miembro.apellidos = request.POST.get('apellidos')
        miembro.fecha_nacimiento = request.POST.get('fechaNacimiento')
        miembro.telefono = request.POST.get('telefono')
        miembro.sexo = request.POST.get('sexo')
        miembro.email = request.POST.get('email')
        miembro.tipo_sangre = request.POST.get('sangre')
        miembro.contacto_emergencia = request.POST.get('contactoEmergencia')
        miembro.telefono_emergencia = request.POST.get('telEmergencia')
        miembro.condiciones_medicas = request.POST.get('condiciones')

        miembro.save()

        #actualizar DB templates en miembros
        nuevo_miembro = ConfiguracionesAcesso.objects.first()
        nuevo_miembro.miembro_nuevo = True
        nuevo_miembro.save()

        #actualizar membresias
        verificar_y_actualizar_estatus_membresias.apply()

        # Devuelve una respuesta
        return JsonResponse({"success": True, "message": "Información actualizada correctamente."})
    else:
        return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

@method_decorator(login_required, name='dispatch')
class RenovarActividadView(TemplateView):
    template_name = 'miembros/miembro_renovar_actividad.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Aquí asumimos que 'miembro_id' es pasado a la vista como parte de la URL
        miembro_id = self.kwargs.get('miembro_id')
        miembro = Miembro.objects.get(id=miembro_id)
        actividades = Actividad.objects.all()
        fecha_hoy = timezone.localtime(timezone.now()).date().isoformat()
        miembro_fin_old_str = str(miembro.fecha_fin_membresia.isoformat())
        context['miembro'] = miembro
        context['actividades'] = actividades
        context['fecha_hoy'] = fecha_hoy
        context['fecha_fin_old'] = miembro_fin_old_str
        return context

def calcular_fecha_fin_membresia(fecha_inicio, duracion):
    if duracion == 'Anual':
        return fecha_inicio + timedelta(days=365)
    elif duracion == 'Semestral':
        return fecha_inicio + timedelta(days=182)
    elif duracion == 'Mensual':
        return fecha_inicio + timedelta(days=30)
    elif duracion == 'Quincenal':
        return fecha_inicio + timedelta(days=15)
    elif duracion == 'Semanal':
        return fecha_inicio + timedelta(days=7)
    elif duracion == 'Diario':
        return fecha_inicio  # Asumimos que Visita no agrega tiempo
    return fecha_inicio 

@csrf_exempt 
@require_POST
def guardar_actividad_sesion(request):
    if request.method == "POST":
        miembro_id = request.POST.get("miembroId")
        miembro = Miembro.objects.get(id=miembro_id)
        actividad = request.POST.get("actividad")
        duracion = request.POST.get("duracion")
        fechaInicio = request.POST.get("fechaInicio")
        miembro_fin_old = request.POST.get("miembro_fin_old")
        fechaInicio = datetime.strptime(fechaInicio, "%Y-%m-%d").date()

        miembro.actividades.set(actividad)
        miembro.fecha_inicio_membresia = fechaInicio
        miembro.fecha_fin_membresia = calcular_fecha_fin_membresia(fechaInicio, duracion)
        miembro.save()
        
        # Guarda los datos en la sesión
        print("Sesión inicial:", request.session.items())
        try:
            if request.session['actividad_id']:
                del request.session['actividad_id'] 
                print("Sesión 1:", request.session.items())
        except Exception as e:
            pass
        try:
            if request.session['duracion_actividad']:
                del request.session['duracion_actividad']
                print("Sesión 2:", request.session.items())
        except Exception as e:
            pass
        try:
            if request.session['miembro_id']:
                del request.session['miembro_id']
                print("Sesión 3:", request.session.items())
        except Exception as e:
            pass
        request.session['actividad_id'] = actividad
        request.session['duracion_actividad'] = duracion
        request.session['miembro_id'] = miembro_id
        request.session['miembro_fin_old'] = miembro_fin_old
        print("Sesión actual:", request.session.items())
        
        return JsonResponse({'success': True})
