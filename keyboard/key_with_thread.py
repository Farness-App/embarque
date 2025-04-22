import tkinter as tk
import math
import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, Landing, moveBy
from time import sleep
from olympe.messages.obstacle_avoidance import set_mode
from olympe.enums.obstacle_avoidance import mode as ObstacleAvoidanceModes
import cv2
import threading

drone = olympe.Drone("10.202.0.1") 
drone.connect()

def start_video_stream():
    cap = cv2.VideoCapture("rtsp://10.202.0.1/live")
    if not cap.isOpened():
        print("Erreur: Impossible d'ouvrir le flux vidéo.")
        return
    print("Flux vidéo ouvert avec succès.")
    scale_factor = 0.5
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erreur: Impossible de lire une image depuis le flux vidéo.")
            break
        resized_frame = cv2.resize(frame, (int(frame.shape[1] * scale_factor), int(frame.shape[0] * scale_factor)))
        cv2.imshow("Drone Video (Resized)", resized_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def execute_movement(x, y, z, yaw):
    success = drone(moveBy(x, y, z, yaw)).wait().success()
    if not success:
        print("Erreur de déplacement !")

def mouvement_thread(x, y, z, yaw):
    thread = threading.Thread(target=execute_movement, args=(x, y, z, yaw))
    thread.start()

def fonction_haut(event=None):
    print("Démarrage du mouvement vers le haut...")
    mouvement_thread(0, 0, -1, 0)

def fonction_bas(event=None):
    print("Démarrage du mouvement vers le bas...")
    mouvement_thread(0, 0, 1, 0)

def fonction_avance(event=None):
    print("Démarrage du mouvement vers l'avant...")
    mouvement_thread(1, 0, 0, 0)

def fonction_arriere(event=None):
    print("Démarrage du mouvement vers l'arrière...")
    mouvement_thread(-1, 0, 0, 0)

def fonction_gauche(event=None):
    print("Rotation de 5° vers la gauche...")
    mouvement_thread(0, 0, 0, math.radians(-5))

def fonction_droite(event=None):
    print("Rotation de 5° vers la droite...")
    mouvement_thread(0, 0, 0, math.radians(5))

def fonction_atterrissage(event=None):
    print("Atterrissage en cours...")
    drone(Landing()).wait().success()
    drone.disconnect()
    fenetre.quit()

fenetre = tk.Tk()
fenetre.title("Contrôle de la drone avec boutons")

btn_haut = tk.Button(fenetre, text="Haut", command=fonction_haut)
btn_bas = tk.Button(fenetre, text="Bas", command=fonction_bas)
btn_avance = tk.Button(fenetre, text="Avance", command=fonction_avance)
btn_arriere = tk.Button(fenetre, text="Arrière", command=fonction_arriere)
btn_gauche = tk.Button(fenetre, text="Gauche", command=fonction_gauche)
btn_droite = tk.Button(fenetre, text="Droite", command=fonction_droite)
btn_atterrissage = tk.Button(fenetre, text="Atter", command=fonction_atterrissage)

btn_haut.grid(row=3, column=2)
btn_bas.grid(row=3, column=0)
btn_avance.grid(row=1, column=1)
btn_arriere.grid(row=2, column=1)
btn_gauche.grid(row=2, column=0)
btn_droite.grid(row=2, column=2)
btn_atterrissage.grid(row=0, column=2)

fenetre.bind("<Up>", fonction_avance)
fenetre.bind("<Down>", fonction_arriere)
fenetre.bind("<Left>", fonction_gauche)
fenetre.bind("<Right>", fonction_droite)
fenetre.bind("h", fonction_haut)
fenetre.bind("b", fonction_bas)
fenetre.bind("a", fonction_atterrissage)

print("Activation de l'évitement d'obstacles...")
try:
    drone(set_mode(ObstacleAvoidanceModes.standard)).wait().success()
    print("Évitement d'obstacles activé.")
except Exception as e:
    print(f"Erreur lors de l'activation de l'évitement d'obstacles : {e}")

video_thread = threading.Thread(target=start_video_stream)
video_thread.daemon = True 
video_thread.start()

print("Décollage en cours...")
drone(TakeOff()).wait().success()
sleep(5)

fenetre.mainloop()

