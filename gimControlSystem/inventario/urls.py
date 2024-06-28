from django.urls import path
from .views import ProductoListView, agregar_producto, crear_producto, ProductoUpdateView, actualizar_producto

app_name = 'inventario'

urlpatterns = [
    path('', ProductoListView.as_view(), name='lista_inventario'),
    path('agregar_producto/', agregar_producto, name='agregar_producto'),
    path('crear_producto/', crear_producto, name='crear_producto'),
    path('editar_producto/<int:producto_id>/', ProductoUpdateView.as_view(), name='editar_producto'),
    path('actualizar_producto/<int:producto_id>/', actualizar_producto, name='actualizar_producto'),
]
