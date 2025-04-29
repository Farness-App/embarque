import speech_recognition as sr
import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, Landing, moveBy, PCMD
from olympe.messages.ardrone3.PilotingState import GpsLocationChanged
from olympe.messages.rth import return_to_home
from olympe.messages.obstacle_avoidance import set_mode
from olympe.enums.obstacle_avoidance import mode as ObstacleAvoidanceModes
import cv2
import threading
import re
from time import sleep
 
 
current_command = None
command_lock = threading.Lock()
 
# Initialisation du drone
drone = olympe.Drone("10.202.0.1")
drone.connect()
 
class DroneState:
    def __init__(self, drone):
        self.drone = drone
        self.home_latitude = None
        self.home_longitude = None
        self.shutdown_flag = False
 
    def check_gps_fix(self):
        """Vérifie si le GPS est fixé et enregistre la position home"""
        try:
            if not self.drone.connected:
                print("Drone non connecté pour vérification GPS")
                return False
            gps_state = self.drone.get_state(GpsLocationChanged)
            if gps_state and gps_state["latitude"] != 500.0:
                self.home_latitude = gps_state["latitude"]
                self.home_longitude = gps_state["longitude"]
                print(f"Position home enregistrée: {self.home_latitude}, {self.home_longitude}")
                return True
            return False
        except Exception as e:
            print(f"Erreur GPS: {e}")
            return False
 
    def return_to_home(self):
        """Exécute la procédure de retour à la maison"""
        print("Début du retour à la maison...")
        try:
            self.drone(PCMD(0, 0, 0, 0, 0, 0)).wait().success()
            self.drone(return_to_home()).wait().success()
            print("Retour à la maison en cours...")
 
            while not self.shutdown_flag:
                gps_state = self.drone.get_state(GpsLocationChanged)
                if (gps_state and 
                    abs(gps_state["latitude"] - self.home_latitude) < 0.0001 and 
                    abs(gps_state["longitude"] - self.home_longitude) < 0.0001):
                    print("Drone revenu au point initial.")
                    break
                sleep(1)
 
            print("Atterrissage...")
            self.drone(Landing()).wait()
            sleep(5)
            return True
        except Exception as e:
            print(f"Erreur lors du retour à la maison : {e}")
            return False
 
drone_state = DroneState(drone)
 
def start_video_stream():
    cap = cv2.VideoCapture("rtsp://10.202.0.1/live")
    if not cap.isOpened():
        print("Erreur: Impossible d'ouvrir le flux vidéo.")
        return
    print("Flux vidéo ouvert avec succès.")
    scale_factor = 0.5
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resized_width = int(original_width * scale_factor)
    resized_height = int(original_height * scale_factor)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erreur: Impossible de lire une image depuis le flux vidéo.")
            break
        resized_frame = cv2.resize(frame, (resized_width, resized_height))
        cv2.imshow("Drone Video", resized_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
 
def update_ui_color(command):
    """Change la couleur de l'interface selon la commande"""
    color_map = {
        "avancer": "#90EE90",  # Vert clair
        "reculer": "#FFCCCB",  # Rouge clair
        "gauche": "#ADD8E6",   # Bleu clair
        "droite": "#FFFFE0",   # Jaune clair
        "monter": "#E6E6FA",   # Lavande
        "descendre": "#D3D3D3",# Gris
        "atterrissage": "#FFA07A", # Saumon
        "home": "#FFD700",     # Or
        "revenir": "#FFD700",  # Or
        "default": "#F0F0F0"   # Gris clair
    }
    color = color_map.get(command, color_map["default"])
    commands_frame.config(bg=color)
    status_label.config(bg=color)
    fenetre.update()
 
def extract_command_data(command):
    command = command.lower().strip()

    # Mouvement linéaire : avancer, reculer, monter, descendre
    movement_match = re.search(r"\b(avancer|reculer|monter|descendre)\b.*?(-?\d+(?:[.,]\d+)?)", command)

    # Rotation gauche/droite
    rotation_match = re.search(r"\brotation\b.*?\b(gauche|droite)\b.*?(-?\d+(?:[.,]\d+)?)", command)

    if movement_match:
        action = movement_match.group(1)
        value = float(movement_match.group(2).replace(',', '.'))
        return action, value
    elif rotation_match:
        direction = rotation_match.group(1)
        value = float(rotation_match.group(2).replace(',', '.'))
        return f"rotation {direction}", value
   
    return command, None


def execute_command(command):
    action, value = extract_command_data(command)
    
    default_value = 1.0  # Valeur par défaut en mètres ou en degrés
    value = value if value is not None else default_value
    
    actions = {
        "monter": lambda v: drone(moveBy(0, 0, -v, 0)).wait().success(),
        "descendre": lambda v: drone(moveBy(0, 0, v, 0)).wait().success(),
        "avancer": lambda v: drone(moveBy(v, 0, 0, 0)).wait().success(),
        "reculer": lambda v: drone(moveBy(-v, 0, 0, 0)).wait().success(),
        "rotation gauche": lambda v: drone(moveBy(0, 0, 0, -v * 3.14159 / 180)).wait().success(),
        "rotation droite": lambda v: drone(moveBy(0, 0, 0, v * 3.14159 / 180)).wait().success(),
        "atterrissage": lambda _: drone(Landing()).wait().success(),
        "home": lambda _: drone_state.return_to_home()
    }
    
    if action in actions:
        threading.Thread(target=actions[action], args=(value,), daemon=True).start()
    else:
        print("Commande non reconnue !")

def listen_for_commands():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("En attente d'une commande vocale...")
        while True:
            try:
                audio = recognizer.listen(source)
                command = recognizer.recognize_google(audio, language="fr-FR").strip().lower()
                print("Commande vocale détectée :", command)
                execute_command(command)
            except sr.UnknownValueError:
                print("Commande non comprise.")
            except sr.RequestError:
                print("Erreur de reconnaissance vocale.")
                
# Activation de l'évitement d'obstacles
print("Activation de l'évitement d'obstacles...")
try:
    drone(set_mode(ObstacleAvoidanceModes.standard)).wait().success()
    print("Évitement d'obstacles activé.")
except Exception as e:
    print(f"Erreur lors de l'activation de l'évitement d'obstacles : {e}")
 
# Démarrer le flux vidéo
video_thread = threading.Thread(target=start_video_stream, daemon=True)
video_thread.start()
 
# Décollage
print("Décollage en cours...")
drone(TakeOff()).wait().success()
sleep(5)
 
# Enregistrer la position home
if drone_state.check_gps_fix():
    print("Position home enregistrée avec succès")
else:
    print("Attention: Impossible d'enregistrer la position home")
 
# Démarrer l'écoute des commandes
threading.Thread(target=listen_for_commands, daemon=True).start()

while True:
    sleep(0.001)
 
# Nettoyage à la fermeture
drone.disconnect()



