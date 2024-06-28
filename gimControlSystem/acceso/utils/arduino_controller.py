import serial
import time

class ArduinoController:
    def __init__(self, port, baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.arduino = None

    def open(self):
        try:
            self.arduino = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(1)  # Espera para la conexión se establezca
            print("Conexión serial establecida con Arduino")
        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial: {e}")

    def close(self):
        if self.arduino and self.arduino.isOpen():
            self.arduino.close()
            print("Conexión serial cerrada")

    def send_command(self, command):
        if self.arduino and self.arduino.isOpen():
            try:
                self.arduino.write(command.encode())
                time.sleep(0.1)  # Da tiempo para que Arduino procese el comando
                response = self.arduino.readline().decode().strip()  # Lee la respuesta
                return response
            except serial.SerialException as e:
                print(f"Error al enviar el comando: {e}")
        else:
            print("La conexión serial no está abierta")
            return None

    def output(self, pin, duration=0.1):
        command = f"OUT{pin}"
        self.send_command(command)
        time.sleep(duration)  # Espera para mantener el estado

    def input(self, pin):
        command = f"IN{pin}"
        response = self.send_command(command)
        return response
    
    def cleanup(self):
        self.close()
        print("Conexion cerrada y recursos liberados.")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Limpieza y liberación de recursos
        self.cleanup()