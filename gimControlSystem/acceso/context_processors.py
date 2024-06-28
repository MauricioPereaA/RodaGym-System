# acceso/context_processors.py
from datetime import date
from django.utils import timezone
from .models import RegistroVisitas

def visitas_hoy(request):
    hoy = timezone.localtime(timezone.now()).date()
    visitas_hoy = RegistroVisitas.objects.filter(fecha=hoy).count()
    return {
        'visitas_hoy': visitas_hoy
    }