from django.urls import path
from .views import AccesoLiveView, AccesoFitLiveView

app_name = 'acceso'

urlpatterns = [
    path('', AccesoLiveView.as_view(), name='acceso_live'),
    path('fit/', AccesoFitLiveView.as_view(), name='acceso_live_fit'),
]
