#p_camara_etapa10
titulo = """
p_camara_etapa10
detecta cambio de estado en gpio
17 detecta falling con pulsador
27 detecta rising con un sensor rf
inicia el sistema deshabilitado
habilitar con el pushbutton de habilitacion

quedaria escribirlo mas a mi manera

etapa9 agrego un pin en pullup
gpio22
para el sensor pir
el pir me lo va a mantener en 0 en estado normal

quiero agregarle un limite de foto fijo, mas adelante doy opcion de elegir valor maximo

"""
print(titulo)

# Imports ---------------
from guizero import App, Picture, PushButton, Text
import cv2
import os
from datetime import datetime
import RPi.GPIO as GPIO
#import threading  #esto esta al pedo 
import time

# Variables -------------
camera = cv2.VideoCapture(0)
filename = ""
habilitacion = False
numero_maximo_fotos = 500

# Configuración GPIO
GPIO_PIN_PULLUP = 17   # Pin original con Pull-up
GPIO_PIN_PULLDOWN = 27 # NUEVO: Pin con Pull-down
GPIO_PIN_PULLUP_PIR = 22 #sensorPIR

GPIO.setmode(GPIO.BCM) # se refiere a la numeracion del gpio - es distnta a la numeracion fisica

# Configuración de los pines de entrada
GPIO.setup(GPIO_PIN_PULLUP, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Pull-up interno
GPIO.setup(GPIO_PIN_PULLDOWN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pull-down interno
GPIO.setup(GPIO_PIN_PULLUP_PIR, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Pull-up interno pir


# Variables de control
last_trigger_time = 0
DEBOUNCE_TIME = 0.5  # Segundos entre disparos para evitar rebotes

# Functions -------------
def capture_image():
    global filename
    global habilitacion
    global numero_maximo_fotos
    
    if habilitacion:
        ret, frame = camera.read()
        if ret:
            # Redimensiona la imagen
            frame_resized = cv2.resize(frame, (600, 400))
            
            # Cuenta cuántas fotos ya hay en la carpeta
            existing_files = [f for f in os.listdir("foto_capturas") if f.endswith(".jpg")]
            next_number = len(existing_files) + 1
            
            if next_number <= numero_maximo_fotos:
                # Crea el nombre con la fecha y hora actual
                #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
                filename = f"foto_capturas/foto_{next_number:03d}_{timestamp}.jpg"
                
                # Guarda la imagen
                cv2.imwrite(filename, frame_resized)
                total_frames.value = f"fotos capturadas: {next_number}"
                
                # Actualiza el visor
                viewer.image = filename
                print(f"Foto capturada: {filename}")
            else:
                total_frames.value = f"fotos capturadas MAXIMA: {next_number}"
                habilitacion = False
                

def delete_frame():
    global filename
    foto_vacia = "foto_capturas/foto_vacia.jpg"
    
    if filename and os.path.exists(filename):
        os.remove(filename)
        print("archivo eliminado")
        viewer.image = foto_vacia
        # Actualiza el contador
        existing_files = [f for f in os.listdir("foto_capturas") if f.endswith(".jpg")]
        total_frames.value = f"fotos capturadas: {len(existing_files)}"
    else:
        print("no se elimino nada")

def gpio_callback(channel):
    """Función que se ejecuta cuando se detecta un evento en cualquier GPIO asignado"""
    global last_trigger_time
    global habilitacion
    
    current_time = time.time()
    # Verifica que haya pasado suficiente tiempo desde el último disparo
    if current_time - last_trigger_time >= DEBOUNCE_TIME:
        last_trigger_time = current_time
        
        # Evaluamos cuál pin disparó la interrupción
        if channel == GPIO_PIN_PULLUP:
            print(f"¡Señal GPIO pulsador detectada! {habilitacion}")
        elif channel == GPIO_PIN_PULLDOWN:
            print(f"¡Señal GPIO RF detectada! {habilitacion}")
        elif channel == GPIO_PIN_PULLUP_PIR:
            print(f"¡Señal GPIO PIR detectada! {habilitacion}")
            
        # Ejecuta la captura en el hilo principal
        app.after(0, capture_image) 

def setup_gpio():
    """Configura las interrupciones GPIO"""
    try:
        # 1. Interrupción para el Pin en Pull-up: Detecta flanco de bajada (va a LOW / GND)
        GPIO.add_event_detect(GPIO_PIN_PULLUP, GPIO.FALLING, 
                             callback=gpio_callback, 
                             bouncetime=300)
        print(f"GPIO {GPIO_PIN_PULLUP} detecta falling de pulsador.")

        # 2. Interrupción para el Pin en Pull-down: Detecta flanco de subida (va a HIGH / 3.3V)
        GPIO.add_event_detect(GPIO_PIN_PULLDOWN, GPIO.RISING, 
                             callback=gpio_callback, 
                             bouncetime=300)
        print(f"GPIO {GPIO_PIN_PULLDOWN} detecta rising de RF.")
        
        # 2. Interrupción para el Pin en Pull-down: Detecta flanco de subida (va a HIGH / 3.3V)
        GPIO.add_event_detect(GPIO_PIN_PULLUP_PIR, GPIO.RISING, 
                             callback=gpio_callback, 
                             bouncetime=300)
        
        print(f"GPIO {GPIO_PIN_PULLUP_PIR} detecta cuando el PIR rising")
        
    except Exception as e:
        print(f"Error configurando GPIO: {e}")

def cleanup_gpio():
    """Limpia la configuración GPIO al cerrar"""
    try:
        GPIO.cleanup()
        print("GPIO limpiado")
    except:
        pass
    
def habilitar_sistema():
    global habilitacion
    habilitacion = True
    print(f"habilitacion: {habilitacion}")
    estado_habilitacion.value = f"estado_habilitacion: {habilitacion}"

def deshabilitar_sistema():
    global habilitacion
    habilitacion = False 
    print(f"habilitacion: {habilitacion}")
    estado_habilitacion.value = f"estado_habilitacion: {habilitacion}"


# App -------------------
app = App(title="mi programa de fotos - etapa 8", width=700, height=700)

# Crea la carpeta si no existe
os.makedirs("foto_capturas", exist_ok=True)

# Crea imagen vacía de placeholder si no existe
placeholder_path = "foto_capturas/foto_vacia.jpg"
if not os.path.exists(placeholder_path):
    # Crea una imagen gris de placeholder
    import numpy as np
    placeholder = np.full((400, 600, 3), 128, dtype=np.uint8)
    cv2.imwrite(placeholder_path, placeholder)

# Widgets de la interfaz
total_frames = Text(app, text="fotos capturadas: 0")
estado_habilitacion = Text(app, text=f"estado_habilitacion: {habilitacion}")
take_next_picture = PushButton(app, text="Take picture (GUI)", command=capture_image)
delete_last_picture = PushButton(app, text="Delete last", command=delete_frame)
habilitar_sistema = PushButton(app, text="habilitar_sistema", command=habilitar_sistema)
deshabilitar_sistema = PushButton(app, text="deshabilitar_sistema", command=deshabilitar_sistema)
viewer = Picture(app, image=placeholder_path)

# Configura GPIO
setup_gpio()

# Asegura que el GPIO se limpie al cerrar
app.when_closed = cleanup_gpio

# Inicia la aplicación
app.display()
camera.release()
