from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Producto
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q

@method_decorator(login_required, name='dispatch')
class ProductoListView(ListView):
    model = Producto
    context_object_name = 'productos'
    paginate_by = 20  # Ajusta este número según tus necesidades
    template_name = 'inventario/lista_inventario.html'  # Ajusta la ruta del template según tu estructura
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')  # Obtiene el parámetro de búsqueda 'q' de la URL, el valor por defecto es una cadena vacía
        if query:
            return Producto.objects.filter(
                Q(codigo_barras__icontains=query) | 
                Q(nombre__icontains=query)
            )
        return Producto.objects.all()

@login_required
def agregar_producto(request):
    return render(request, 'inventario/agregar_producto.html')


@csrf_exempt
def crear_producto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        print(nombre)
        codigo_barras = request.POST.get('codigo_barras')
        print(codigo_barras)
        precio = request.POST.get('precio')
        print(precio)
        total_bodega = request.POST.get('total_bodega')
        print(total_bodega)
        tipo = request.POST.get('tipo')
        print(tipo)
        
        # Crear y guardar el nuevo producto
        nuevo_producto = Producto(
            nombre=nombre,
            codigo_barras=codigo_barras,
            precio=precio,
            total_bodega=total_bodega,
            tipo=tipo,
        )
        nuevo_producto.save()
        
        # Retornar una respuesta para AJAX
        return JsonResponse({'success': True, 'mensaje': 'Producto guardado exitosamente'})

    # En caso de que no sea una petición POST, redirigir a la lista de inventario
    return redirect('lista_inventario')

@method_decorator(login_required, name='dispatch')
class ProductoUpdateView(UpdateView):
    model = Producto
    fields = ['nombre', 'codigo_barras', 'precio', 'total_bodega', 'tipo']
    template_name = 'inventario/editar_producto.html'
    pk_url_kwarg = 'producto_id'
    success_url = reverse_lazy('inventario:lista_inventario')

@csrf_exempt
def actualizar_producto(request, producto_id):
    if request.method == 'POST':
        # Obtén el miembro a actualizar
        producto = get_object_or_404(Producto, pk=producto_id)

        # Actualiza los campos del miembro
        producto.nombre = request.POST.get('nombre')
        producto.codigo_barras = request.POST.get('codigo_barras')
        producto.total_bodega = request.POST.get('total_bodega')
        producto.precio = request.POST.get('precio')
        producto.tipo = request.POST.get('tipo')
        producto.save()

        # Devuelve una respuesta
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False}, status=405)