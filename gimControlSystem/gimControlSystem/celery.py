import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gimControlSystem.settings')

app = Celery('gimControlSystem')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'verificar_y_actualizar_estatus_membresias_diariamente': {
        'task': 'miembros.tasks.verificar_y_actualizar_estatus_membresias',
        'schedule': crontab(hour=4, minute=35),  # Ejecuta diariamente a medianoche
    },
}