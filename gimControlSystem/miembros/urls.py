from django.urls import path
from .views import MiembroListView, AgregarMiembroView, \
                    iniciar_captura_huella, MiembroPagoView, procesar_pago, EditarMiembroView, SaveMemberImageView, \
                    SaveMemberFingerPrintView, actualizar_miembro, RenovarActividadView, guardar_actividad_sesion, \
                    imprimir_ticket, reimprimir_ticket
app_name = 'miembros'

urlpatterns = [
    path('', MiembroListView.as_view(), name='lista_miembros'),
    path('agregar/', AgregarMiembroView.as_view(), name='agregar_miembro'),
    path('registro-huella/', iniciar_captura_huella, name='iniciar_captura_huella'),
    path('miembro_pago/<int:miembro_id>/', MiembroPagoView.as_view(), name='miembro_pago'),
    path('procesar_pago/<int:miembro_id>/', procesar_pago, name='procesar_pago'),
    path('imprimir_ticket/', imprimir_ticket, name='imprimir_ticket'),
    path('reimprimir_ticket/', reimprimir_ticket, name='reimprimir_ticket'),
    path('editar/<int:miembro_id>/', EditarMiembroView.as_view(), name='editar_miembro'),
    path('actualizar_imagen/', SaveMemberImageView.as_view(), name='actualizar_imagen'),
    path('actualizar_fingerprint/', SaveMemberFingerPrintView.as_view(), name='actualizar_fingerprint'),
    path('actualizar/<int:miembro_id>/', actualizar_miembro, name='actualizar_miembro'),
    path('renovar_actividad/<int:miembro_id>/', RenovarActividadView.as_view(), name='renovar_actividad'),
    path('actualizar_membresia/', guardar_actividad_sesion, name='actualizar_membresia'),


]
