from celery import shared_task
from django.utils import timezone
from .models import Miembro

@shared_task
def verificar_y_actualizar_estatus_membresias():
    miembros = Miembro.objects.all()
    fecha_actual = timezone.localtime(timezone.now()).date()
    print(f"Fecha actual: {fecha_actual}")
    
    for miembro in miembros:
        print(f"Procesando miembro: {miembro.id} - Fecha fin membresía: {miembro.fecha_fin_membresia}")
        if miembro.fecha_fin_membresia and miembro.estatus_membresia != "":
            if fecha_actual > miembro.fecha_fin_membresia:
                print(f"Actualizando estatus a Inactiva - Miembro: {miembro.id}")
                miembro.estatus_membresia = 'Inactiva'
            else:
                print(f"Miembro: {miembro.id} sigue Activo")
                miembro.estatus_membresia = 'Activa'
            miembro.save()

    print("Estatus de membresías actualizado.")
