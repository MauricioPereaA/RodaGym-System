from django.db import models

# Opciones para el campo de tipo de producto
TIPO_OPCIONES = [
    ('Venta', 'Producto a la venta'),
    ('Insumo', 'Insumo del gimnasio'),
]

class Producto(models.Model):
    codigo_barras = models.CharField(max_length=100, unique=True, blank=False)
    nombre = models.CharField(max_length=255, blank=False)
    total_bodega = models.IntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_OPCIONES, default='Venta')

    def __str__(self):
        return self.nombre
