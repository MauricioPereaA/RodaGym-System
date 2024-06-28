from django.contrib import admin
from .models import ConfiguracionesAcesso
from finanzas.models import Transaccion

@admin.register(ConfiguracionesAcesso)
class ConfiguracionesAcesso(admin.ModelAdmin):
    list_display = ('miembro_nuevo', )
    