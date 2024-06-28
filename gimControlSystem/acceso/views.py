from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import ConfiguracionesAcesso
from django.utils.safestring import mark_safe
import markdown
import emoji

# Create your views here.
@method_decorator(login_required, name='dispatch')
class AccesoLiveView(TemplateView):
    template_name = 'acceso/acceso.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        configuracion = ConfiguracionesAcesso.objects.first()
        if configuracion and configuracion.mensaje_global:
            #mensaje_procesado = markdown.markdown(configuracion.mensaje_global_str)
            context['mensaje_global'] = emoji.emojize(configuracion.mensaje_global_str, language='alias')
        else:
            context['mensaje_global'] = ''
        return context


class AccesoFitLiveView(TemplateView):
    template_name = 'acceso/acceso_fit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        configuracion = ConfiguracionesAcesso.objects.first()
        if configuracion and configuracion.mensaje_global:
            #mensaje_procesado = markdown.markdown(configuracion.mensaje_global_str)
            context['mensaje_global'] = emoji.emojize(configuracion.mensaje_global_str, language='alias')
        else:
            context['mensaje_global'] = ''
        return context