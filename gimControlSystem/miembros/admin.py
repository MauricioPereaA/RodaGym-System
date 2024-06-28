from django.contrib import admin
from .models import Miembro, Actividad, DuracionActividad, Configuracion
from finanzas.models import Transaccion

class TransaccionInline(admin.TabularInline):
    model = Transaccion
    extra = 1  # Número de formularios para pagos nuevos a mostrar

@admin.register(Miembro)
class MiembroAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'telefono', 'email', 'fecha_inicio_membresia', 'estatus_membresia')
    search_fields = ('nombres', 'apellidos', 'email')
    inlines = [TransaccionInline]
    filter_horizontal = ('actividades',)

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(DuracionActividad)
class DuracionActividadAdmin(admin.ModelAdmin):
    list_display = ('actividad', 'duracion', 'precio')
    search_fields = ('actividad', 'duracion')

@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ['costo_inscripcion']
    fields = ['costo_inscripcion']