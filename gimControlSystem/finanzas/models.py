from django.db import models
from django.conf import settings
from miembros.models import Miembro


class Caja(models.Model):
    fecha_apertura = models.DateField(auto_now_add=True)
    total_en_caja = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    descripcion = models.TextField(blank=True, null=True)
    abierta = models.BooleanField(default=True)

    def __str__(self):
        return f"Caja {self.id} - Apertura: {self.fecha_apertura}"
    
class Transaccion(models.Model):
    TIPO_TRANSACCION = [
        ('Pago', 'Pago'),
        ('Corte', 'Corte de Caja'),
        # Añade más tipos de transacción según sea necesario
    ]
    METODO_PAGOS = [
        ('Efectivo', 'Efectivo'),
        ('Tarjeta', 'Tarjeta'),
        ('Transferencia', 'Transferencia')
    ]

    caja = models.ForeignKey('Caja', on_delete=models.CASCADE, related_name='transacciones')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transacciones_realizadas')
    miembro = models.ForeignKey(Miembro, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos')
    fecha = models.DateField(auto_now_add=False)
    tipo = models.CharField(max_length=50, choices=TIPO_TRANSACCION)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    metodo_pago = models.CharField(max_length=50, choices=METODO_PAGOS)
    venta_general = models.BooleanField(default=False)

    def __str__(self):
        descripcion_transaccion = f"{self.tipo} - {self.cantidad}"
        if self.miembro:
            descripcion_transaccion += f" - {self.miembro.nombres} {self.miembro.apellidos}"
        return descripcion_transaccion
    
class Ticket(models.Model):
    id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=False)
    cajero = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    miembro = models.ForeignKey(Miembro, on_delete=models.SET_NULL, null=True)
    metodo_pago = models.CharField(max_length=255)
    recibido = models.DecimalField(max_digits=10, decimal_places=2)
    cambio = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Ticket {self.id} - Fecha: {self.fecha.strftime('%Y-%m-%d %H:%M')} - Total: ${self.total}"

class ItemTicket(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='items', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    descripcion = models.CharField(max_length=255)
    importe = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"Item {self.id} de Ticket {self.ticket.id}: {self.cantidad}x {self.descripcion} - ${self.importe}"