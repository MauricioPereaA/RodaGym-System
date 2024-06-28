from django.urls import path
from .views import ConfiguracionesView, AltaUsuarioView, ReportesView, reimpresion_ticket_view
app_name = 'configuraciones'

urlpatterns = [
    path('', ConfiguracionesView.as_view(), name='configuraciones'),
    path('alta_usuario/', AltaUsuarioView.as_view(), name='alta_usuario'),
    path('reportes/', ReportesView.as_view(), name='reportes'),
    path('reimprimir_ticket/', reimpresion_ticket_view, name='reimprimir_ticket'),
]
