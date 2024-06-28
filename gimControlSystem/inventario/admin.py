from django.contrib import admin
from .models import Producto
# Register your models here.

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_barras', 'nombre', 'total_bodega', 'precio', 'tipo')  # Atributos que quieres mostrar en la lista
    search_fields = ('codigo_barras', 'nombre')  # Campos por los cuales quieres permitir la búsqueda
    list_filter = ('tipo',) 

admin.site.register(Producto, ProductoAdmin)