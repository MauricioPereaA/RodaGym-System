from django.urls import path
from .views import PuntoVentaView, buscar_producto, procesar_pago_venta, reimprimir_ticket, \
                AperturaCajaView, CorteCajaView, check_caja_abierta

app_name = 'ventas'

urlpatterns = [
    path('', PuntoVentaView.as_view(), name='punto_venta'),
    path('buscar_producto/', buscar_producto, name='buscar_producto'),
    path('procesar_pago_venta/', procesar_pago_venta, name='procesar_pago_venta'),
    path('reimprimir_ticket/', reimprimir_ticket, name='reimprimir_ticket'),
    path('apertura_caja/', AperturaCajaView.as_view(), name='apertura_caja'),
    path('corte_caja/', CorteCajaView.as_view(), name='corte_caja'),
    path('check_caja_abierta/', check_caja_abierta, name='check_caja_abierta'),
]
