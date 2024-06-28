from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.views import View
from inventario.models import Producto
from finanzas.models import Caja, Transaccion, Ticket, ItemTicket
from miembros.models import Miembro
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from escpos import *
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from finanzas.models import Caja

@method_decorator(login_required, name='dispatch')
class AperturaCajaView(TemplateView):
    template_name = 'ventas/apertura_caja.html'

    def post(self, request, *args, **kwargs):
        total_en_caja = request.POST.get('total_en_caja', 0)
        descripcion = request.POST.get('descripcion', '')
        caja = Caja.objects.create(total_en_caja=total_en_caja, descripcion=descripcion)
        miembro = get_object_or_404(Miembro, nombres='Ventas General')
        transaccion = Transaccion.objects.create(
            caja=caja,
            miembro=miembro,
            fecha=timezone.localtime(timezone.now()),
            tipo='Pago',
            cantidad=float(total_en_caja),
            descripcion='Fondo de apertura de Caja nueva',
            metodo_pago='Efectivo',
            usuario=request.user,  # Asumiendo que tienes un campo de usuario en tu modelo de Transacción
            venta_general=True,
        )
        return redirect('ventas:punto_venta')

@method_decorator(login_required, name='dispatch')
class CorteCajaView(TemplateView):
    template_name = 'ventas/corte_caja.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            caja = Caja.objects.filter(abierta=True).latest('fecha_apertura')
        except Caja.DoesNotExist:
            messages.error(self.request, "Es necesario abrir una caja antes de realizar el corte.")
            return context
        
        total_efectivo = sum(transaccion.cantidad for transaccion in caja.transacciones.filter(metodo_pago='Efectivo'))
        total_tarjeta = sum(transaccion.cantidad for transaccion in caja.transacciones.filter(metodo_pago='Tarjeta'))
        total_transferencia = sum(transaccion.cantidad for transaccion in caja.transacciones.filter(metodo_pago='Transferencia'))
        transacciones = caja.transacciones.all()
        context['total_efectivo'] = total_efectivo
        context['total_tarjeta'] = total_tarjeta
        context['total_transferencia'] = total_transferencia
        context['transacciones'] = transacciones
        context['caja'] = caja
        return context

    def post(self, request, *args, **kwargs):
        try:
            caja = Caja.objects.filter(abierta=True).latest('fecha_apertura')
        except Caja.DoesNotExist:
            messages.error(request, "Es necesario abrir una caja antes de realizar el corte.")
            return redirect('ventas:punto_venta')
        
        caja.descripcion = f'Corte de caja realizado el {timezone.now().strftime("%Y-%m-%d %H:%M")}'
        caja.abierta = False
        caja.save()
        return redirect('ventas:punto_venta')

# Create your views here.
@method_decorator(login_required, name='dispatch')
class PuntoVentaView(TemplateView):
    template_name = 'ventas/punto_venta.html'

@login_required
def buscar_producto(request):
    #nombre = request.GET.get('nombre')
    codigo = request.GET.get('codigo')
    producto = None

    if codigo:
        producto = Producto.objects.filter(codigo_barras=codigo).first()

    if producto:
        response = {
            'precio': producto.precio,
            'nombre': producto.nombre,
            'total_bodega': producto.total_bodega,
            # Agrega otros datos necesarios
        }
        return JsonResponse(response)
    else:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@login_required
@csrf_exempt
def procesar_pago_venta(request):
    if request.method == "POST":
        datos_carrito = request.POST.get("carrito")  # Obtenemos los datos del carrito enviados desde el frontend
        metodo_pago = request.POST.get("metodoPago")
        descuento = request.POST.get("descuento", 0)  # Asumir 0 si no se provee
        costo = request.POST.get("costo")  # Total de la compra
        recibido = request.POST.get("cantidadRecibida")
        cambio = request.POST.get("cambio")
        miembro = get_object_or_404(Miembro, nombres='Ventas General')
        
        # Convertir los datos del carrito de JSON a Python dict
        import json
        carrito = json.loads(datos_carrito)

        # Asumiendo que ya tienes una instancia de Caja abierta para hoy
        caja = Caja.objects.filter(abierta=True).latest('fecha_apertura')

        # Crear Ticket y ItemTicket para cada producto vendido
        ticket = Ticket.objects.create(
            cajero=request.user,
            fecha=timezone.localtime(timezone.now()),
            miembro=miembro,
            total=float(costo),
            metodo_pago=metodo_pago,
            recibido=float(recibido),
            cambio=float(cambio),
        )

        # Crear Transacción
        descripcion = f"Venta general Punto de venta con ticketid:{ticket.id} con total de venta de {costo} con descuento aplicado del {descuento}%"

        transaccion = Transaccion.objects.create(
            caja=caja,
            miembro=miembro,
            fecha=timezone.localtime(timezone.now()),
            tipo='Pago',
            cantidad=float(costo) - (float(costo) * float(descuento) / 100),
            descripcion=descripcion,
            metodo_pago=metodo_pago,
            usuario=request.user,  # Asumiendo que tienes un campo de usuario en tu modelo de Transacción
            venta_general=True,
        )


        for item in carrito:
            producto = Producto.objects.get(codigo_barras=item['codigo'])
            producto.total_bodega -= item['cantidad']  # Restar del inventario
            producto.save()

            itemticket = ItemTicket.objects.create(
                ticket=ticket,
                cantidad=int(item['cantidad']),
                descripcion=item['descripcion'],
                importe=float(item['precio']) * float(item['cantidad'])
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
        thermal_printer.textln(f'MIEMBROID:{ticket.miembro.nombres}')
        thermal_printer.textln('================================')
        thermal_printer.set(align='center')
        thermal_printer.set(bold=True)
        thermal_printer.textln('CANT   DESCRIPCION       IMPORTE')
        thermal_printer.textln('================================')
        thermal_printer.set(bold=False)
        for item in carrito:
            itemCantidad = str(item['cantidad'])
            itemDescripcion = item['descripcion']
            itemDescripcion = itemDescripcion[:19]
            itemImporte = str(float(item['precio']) * float(item['cantidad']))
            thermal_printer.textln(f'{itemCantidad:<4}{itemDescripcion:<19} ${itemImporte:>7}')
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

        return JsonResponse({'success': True})
    else:
        return JsonResponse({"error": "Método no permitido"}, status=405)

@login_required
def reimprimir_ticket(request):
    ticket_id = request.session.get('ultimo_ticket_id')
    ticket = Ticket.objects.get(id=ticket_id)
    items_ticket = ticket.items.all()

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
    thermal_printer.textln(f'MIEMBROID:{ticket.miembro.nombres}')
    thermal_printer.textln('================================')
    thermal_printer.set(align='center')
    thermal_printer.set(bold=True)
    thermal_printer.textln('CANT   DESCRIPCION       IMPORTE')
    thermal_printer.textln('================================')
    thermal_printer.set(bold=False)
    for item in items_ticket:
        itemCantidad = str(item.cantidad)
        itemDescripcion = item.descripcion
        itemDescripcion = itemDescripcion[:19]
        itemImporte = str(item.importe)
        thermal_printer.textln(f'{itemCantidad:<4}{itemDescripcion:<19} ${itemImporte:>7}')
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

def hay_caja_abierta():
    try:
        caja_abierta = Caja.objects.filter(abierta=True).latest('fecha_apertura')
        return True
    except Caja.DoesNotExist:
        return False
    
def check_caja_abierta(request):
    data = {'caja_abierta': hay_caja_abierta()}
    return JsonResponse(data)