from django.db import models
from django.conf import settings

class Actividad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

class DuracionActividad(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='duracion_actividades')
    duracion = models.CharField(max_length=10, choices=[
        ('Anual', 'Anual'),
        ('Semestral', 'Semestral'),
        ('Mensual', 'Mensual'),
        ('Quincenal', 'Quincenal'),
        ('Semanal', 'Semanal'),
        ('Diario', 'Diario'),
    ])
    precio = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.actividad.nombre} - {self.duracion} - ${self.precio}"

    

class Miembro(models.Model):
    class Meta:
        ordering = ['apellidos', 'nombres']
        
    SEXO_OPCIONES = [
        ('H', 'Hombre'),
        ('M', 'Mujer'),
        ('N', 'No especificar'),
    ]
    TIPO_SANGRE_OPCIONES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    ESTATUS_MEMBRESIA_OPCIONES = [
        ('Activa', 'Activa'),
        ('Inactiva', 'Inactiva'),
    ]
    
    id = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_OPCIONES)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    tipo_sangre = models.CharField(max_length=3, choices=TIPO_SANGRE_OPCIONES)
    contacto_emergencia = models.CharField(max_length=100)
    telefono_emergencia = models.CharField(max_length=20)
    condiciones_medicas = models.TextField(blank=True)  # Permitimos que este campo sea opcional
    foto = models.ImageField(upload_to='fotos_miembros/', blank=True, null=True)
    huella_dactilar = models.TextField(blank=True)
    actividades = models.ManyToManyField(Actividad, related_name='miembros', default=None)
    fecha_inicio_membresia = models.DateField()
    estatus_membresia = models.CharField(max_length=10, choices=ESTATUS_MEMBRESIA_OPCIONES, blank=True, default='Inactiva')
    fecha_fin_membresia = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    
class Configuracion(models.Model):
    costo_inscripcion = models.DecimalField(max_digits=6, decimal_places=2, default=100.00, help_text="Costo de la inscripción para nuevos miembros o miembros inactivos.")

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuraciones"

    def __str__(self):
        return f"Configuración {self.pk}"
