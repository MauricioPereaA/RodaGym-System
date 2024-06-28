from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.
class ConfiguracionesAcesso(models.Model):
    miembro_nuevo = models.BooleanField(default=False)
    mensaje_global = models.BooleanField(default=False)
    mensaje_global_str = models.TextField(blank=True)

class RegistroVisitas(models.Model):
    miembro = models.IntegerField()
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
