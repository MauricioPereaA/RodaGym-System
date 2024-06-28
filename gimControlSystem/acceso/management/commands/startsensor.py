# comando_personalizado.py o cualquier nombre que elijas
from django.core.management.base import BaseCommand
from django.db import DatabaseError
from miembros.models import Miembro
from acceso.models import ConfiguracionesAcesso
from acceso.utils.zk9500 import LectorHuellasZK9500
from acceso.utils.arduino_controller import ArduinoController
import time, base64
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from acceso.models import RegistroVisitas

class Command(BaseCommand):
    help = 'Monitoreo continuo del sensor de huellas dactilares y actualización de la base de datos local.'

    def handle(self, *args, **kwargs):
        lector_huellas = LectorHuellasZK9500()
        lector_huellas.initialize_sensor()
        lector_huellas.initialize_DB()
        # Cargar inicialmente todas las huellas registradas
        for miembro in Miembro.objects.all():
            if len(miembro.huella_dactilar) > 1000:
                lector_huellas.add_member_DB(miembro.id, base64.b64decode(miembro.huella_dactilar))
        
        self.stdout.write(self.style.SUCCESS('Inicialización completada. Comenzando monitoreo...'))

        while True:
            try:
                flag = ConfiguracionesAcesso.objects.get(id=1)
                if flag.miembro_nuevo:
                    self.stdout.write(self.style.SUCCESS('Detectado nuevo miembro. Actualizando base de datos de huellas...'))
                    lector_huellas.zkfp2.DBClear()
                    for miembro in Miembro.objects.all():
                        if len(miembro.huella_dactilar) > 1000:
                            lector_huellas.add_member_DB(miembro.id, base64.b64decode(miembro.huella_dactilar))
                    flag.miembro_nuevo = False
                    flag.save()
                    self.stdout.write(self.style.SUCCESS('Base de datos de huellas actualizada.'))
                
                capture = lector_huellas.zkfp2.AcquireFingerprint()
                if capture:
                    tmp, img = capture
                    fid = lector_huellas.identify_member_DB(tmp)
                    if fid:
                        miembro_identificado = Miembro.objects.get(id=fid)
                        RegistroVisitas.objects.create(
                            miembro=miembro_identificado.id,
                            nombres=miembro_identificado.nombres,
                            apellidos=miembro_identificado.apellidos
                        )
                        self.stdout.write(self.style.SUCCESS(f'Miembro identificado: {miembro_identificado.nombres} {miembro_identificado.apellidos} con ID {fid}'))
                        # enviar meimbro ID para actualizacion interfaz
                        channel_layer = get_channel_layer()
                        print(channel_layer)
                        if channel_layer is None:
                            self.stdout.write(self.style.ERROR('Channel layer no encontrado. ¿Está Channels correctamente configurado?'))
                            return
                        async_to_sync(channel_layer.group_send)(
                            "acceso_group",  # Define un nombre para tu grupo de WebSocket
                            {
                                "type": "enviar_datos_miembro",
                                "miembro_id": miembro_identificado.id,
                                "miembro_nombres": miembro_identificado.nombres,
                                "miembro_apellidos": miembro_identificado.apellidos,
                                "miembro_foto_url": miembro_identificado.foto.url if miembro_identificado.foto else None,
                                "actividad": str(miembro_identificado.actividades.first()),
                                "vigencia": str(miembro_identificado.fecha_fin_membresia),
                                "estatus_membresia": miembro_identificado.estatus_membresia,
                            }
                        )
                        if miembro_identificado.estatus_membresia == 'Activa':
                            #agregar el COM a settings de la DB y jalarlo
                            with ArduinoController('COM4') as arduino_controller:
                                arduino_controller.output(7)
                                self.stdout.write(self.style.SUCCESS(f'Activacion de Torniquete Entrada Completada'))

                            # Eliminar explícitamente la referencia a la instancia
                            del arduino_controller

            except DatabaseError as e:
                self.stderr.write(self.style.ERROR(f'Error accediendo a la base de datos: {e}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error inesperado: {e}'))

            time.sleep(0.1)  # Ajusta este valor según necesites
