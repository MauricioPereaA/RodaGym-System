from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Hidden, HTML, Field
from crispy_forms.bootstrap import StrictButton, InlineRadios
from crispy_bootstrap5.bootstrap5 import FloatingField
from .models import Miembro, Actividad, DuracionActividad
from django.utils import timezone

DURACION_OPCIONES = (
    ('Anual', 'Anual'),
    ('Semestral', 'Semestral'),
    ('Mensual', 'Mensual'),
    ('Quincenal', 'Quincenal'),
    ('Semanal', 'Semanal'),
    ('Diario', 'Diario'),
)

class MiembroForm(forms.ModelForm):
    image_data = forms.CharField(widget=forms.HiddenInput(), required=True)
    fingerprint_data = forms.CharField(widget=forms.HiddenInput(), required=True)
    duracion_actividad = forms.ChoiceField(choices=DURACION_OPCIONES, widget=forms.RadioSelect, initial='Mensual')
    class Meta:
        model = Miembro
        fields = '__all__'  # Asegúrate de incluir todos los campos o especifica los que necesitas
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'fecha_inicio_membresia': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin_membresia': forms.DateInput(attrs={'type': 'date'}),
            'duracion_actividad': forms.RadioSelect()
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(MiembroForm, self).__init__(*args, **kwargs)
        self.fields['actividades'].queryset = Actividad.objects.all()
        self.fields['fecha_inicio_membresia'].initial = timezone.localtime(timezone.now()).date()

        if self.fields['actividades'].queryset.exists():
            # Preseleccionar la primera actividad en la lista
            self.fields['actividades'].initial = [self.fields['actividades'].queryset.first().id]

        if self.request and not self.request.user.is_staff:
            self.fields['fecha_inicio_membresia'].disabled = True

        if self.is_bound and 'actividades' in self.data:
            # Filtrar las duraciones de actividad basadas en la actividad seleccionada.
            actividad_id = self.data.get('actividades')
            self.fields['duracion_actividad'].queryset = DuracionActividad.objects.filter(actividad_id=actividad_id)
        else:
            # Opción por defecto si aún no se ha seleccionado ninguna actividad.
            self.fields['duracion_actividad'].queryset = DuracionActividad.objects.none()

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column(FloatingField('nombres'), css_class='form-group col-md-6 mb-0'),
                Column(FloatingField('apellidos'), css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column(FloatingField('fecha_nacimiento'), css_class='form-group col-auto mb-0'),
                Column(FloatingField('sexo'), css_class='form-group col-auto mb-0'),
            ),
            Row(
                Column(FloatingField('telefono'), css_class='form-group col-md-6 mb-0'),
                Column(FloatingField('email'), css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column(FloatingField('contacto_emergencia'), css_class='form-group col-md-6 mb-0'),
                Column(FloatingField('telefono_emergencia'), css_class='form-group col-md-6 mb-0'),
            ),
            Row(
                Column(FloatingField('tipo_sangre'), css_class='form-group col-auto mb-0'),
            ),
            FloatingField('condiciones_medicas', style='height: 200px'),
            Hidden(FloatingField('foto'), ''),
            Hidden(FloatingField('huella_dactilar'), ''),
            HTML("""
                <hr style="background-color: black; height: 3px;">
                <h4 class="title">Agregar Actividad Miembro</h2>
                &nbsp
            """
            ),
            Row(
                Column(FloatingField('actividades'), css_class='form-group col-auto mb-0'),
            ),
            Row(
                Column(InlineRadios('duracion_actividad'), css_class='form-group col-auto mb-0'),
            ),
            Row(
                Column(FloatingField('fecha_inicio_membresia'), css_class='form-group col-md-6 mb-0', style='width: 200px'),
                Hidden('fecha_fin_membresia', '')
            ),
            Hidden('estatus_membresia', ''),
            Hidden('image_data', ''),
            Hidden('fingerprint_data', ''),
        )

    def clean(self):
        cleaned_data = super().clean()
        nombres = cleaned_data.get('nombres')
        apellidos = cleaned_data.get('apellidos')

        if Miembro.objects.filter(nombres=nombres, apellidos=apellidos).exists():
            raise forms.ValidationError('Ya existe un miembro con los mismos nombres y apellidos.')

        return cleaned_data
