import math
from shapely.geometry import Polygon, Point
import numpy as np
import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, Landing, moveTo, moveBy
from time import sleep
from olympe.messages.obstacle_avoidance import set_mode
from olympe.enums.obstacle_avoidance import mode as ObstacleAvoidanceModes
import cv2
import threading

num_points = 5
polygon_points = [
    (36.8008, 10.1800),
    (36.8015, 10.1825),
    (36.8002, 10.1840),
    (36.7989, 10.1820),
    (36.7995, 10.1795)
]

def start_video_stream():
    cap = cv2.VideoCapture("rtsp://10.202.0.1/live")

    if not cap.isOpened():
        print("Erreur: Impossible d'ouvrir le flux vidéo.")
        return

    print("Flux vidéo ouvert avec succès.")

    scale_factor = 0.5  # Facteur d'échelle (par exemple, 0.5 = réduction de moitié)
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resized_width = int(original_width * scale_factor)
    resized_height = int(original_height * scale_factor)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erreur: Impossible de lire une image depuis le flux vidéo.")
            break

        # Redimensionner l'image
        resized_frame = cv2.resize(frame, (resized_width, resized_height))

        # Afficher la vidéo redimensionnée
        cv2.imshow("Drone Video (Resized)", resized_frame)

        # Quitter si 'q' est pressé
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Libérer les ressources
    cap.release()
    cv2.destroyAllWindows()
    

# H représente l'altitude de la drone et distance entre puis succevice= 2* circle_radius 
circle_radius = float(input("Entrez la moitié de la distance entre 2 points successives : "))

while True:
    H = float(input("Entrez l'altitude du drone (entre 0 et 100) : "))
    if 0 <= H <= 100:
        print(f"Altitude valide : {H} mètres")
        break
    else:
        print("Erreur : L'altitude doit être comprise entre 0 et 100 mètres. Réessayez.")

k=int(H/2);

# Vérification des coordonnées GPS
def validate_gps_coordinates(polygon_points):
    for lat, lon in polygon_points:
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError(f"Coordonnées invalides : latitude={lat}, longitude={lon}")
    print("Toutes les coordonnées GPS sont valides.")

# Fonction pour diviser la surface en cercles
def divide_into_circles(polygon_points, circle_radius_m):
    polygon_coords = [(lon, lat) for lat, lon in polygon_points]
    polygon = Polygon(polygon_coords)
    min_x, min_y, max_x, max_y = polygon.bounds

    step_lat = circle_radius_m / 111320  # Conversion de mètres en degrés latitude
    circle_centers = []

    lat = min_y
    while lat <= max_y:
        cos_lat = math.cos(math.radians(lat))
        current_lon_step = circle_radius_m / (111320 * cos_lat) if cos_lat != 0 else 0
        if current_lon_step == 0:
            lat += step_lat
            continue

        lon = min_x
        while lon <= max_x:
            point = Point(lon, lat)
            if polygon.contains(point):
                circle_centers.append((lat, lon))
            lon += current_lon_step
        lat += step_lat

    return circle_centers

def count_circles_in_polygon(polygon_points, circle_radius_m):
    polygon_coords = [(lon, lat) for lat, lon in polygon_points]
    polygon = Polygon(polygon_coords)
    min_x, min_y, max_x, max_y = polygon.bounds

    step_lat = circle_radius_m / 111320  
    circle_count = 0  

    lat = min_y
    while lat <= max_y:
        cos_lat = math.cos(math.radians(lat))
        current_lon_step = circle_radius_m / (111320 * cos_lat) if cos_lat != 0 else 0
        if current_lon_step == 0:
            lat += step_lat
            continue

        lon = min_x
        while lon <= max_x:
            if polygon.contains(Point(lon, lat)):
                circle_count += 1  
            lon += current_lon_step
        lat += step_lat

    return circle_count
    
# Fonction pour trier les centres des cercles
def sort_circle_centers(circle_centers):
    if not circle_centers:
        return []

    circle_centers.sort(key=lambda p: (p[0], p[1]))
    circle_centers = np.array(circle_centers)
    unique_lats = np.unique(circle_centers[:, 0])
    sorted_centers = []

    for i, lat in enumerate(unique_lats):
        row_points = [tuple(p) for p in circle_centers if p[0] == lat]
        row_points.sort(key=lambda p: p[1], reverse=(i % 2 == 1))
        sorted_centers.extend(row_points)

    return sorted_centers

# Lecture du polygone
def read_polygon():
    return polygon_points

# Appel des fonctions
validate_gps_coordinates(polygon_points)  # Validation des coordonnées GPS
polygon_points = read_polygon()

polygon_coords = [(lon, lat) for lat, lon in polygon_points]
poly = Polygon(polygon_coords)
centroid = poly.centroid
center_lat, center_lon = centroid.y, centroid.x

circle_centers = divide_into_circles(polygon_points, circle_radius)
circle_centers = sort_circle_centers(circle_centers)

area=count_circles_in_polygon(polygon_points, 0.5)*math.pi*0.5**2

# affichage de la trajet et de la surface
print(f"Nombre total de cercles : {len(circle_centers)}")
print("Les points du trajet sont :", circle_centers)
print(f"Surface totale couverte : {area:.2f} m²")

# Connexion au drone
drone = olympe.Drone("10.202.0.1") 
drone.connect()

# Activation explicite de l'évitement d'obstacles
print("Activation de l'évitement d'obstacles...")
try:
    drone(set_mode(ObstacleAvoidanceModes.standard)).wait().success()
    print("Évitement d'obstacles activé.")
except Exception as e:
    print(f"Erreur lors de l'activation de l'évitement d'obstacles : {e}")

# Démarrer le streaming vidéo dans un thread séparé
video_thread = threading.Thread(target=start_video_stream)
video_thread.daemon = True  # Le thread se terminera lorsque le programme principal se terminera
video_thread.start()

# Décollage
print("Décollage en cours...")
drone(TakeOff()).wait().success()
sleep(5)  # Attendre que le drone atteigne une altitude stable

# Utilisation de moveBy pour des déplacements relatifs
for _ in range(k):  # Répéter k fois
    drone(moveBy(0, 0, -2 , 0)).wait().success()

# Exécuter le trajet avec des points simples pour tester
for latitude, longitude in circle_centers:
    print(f"Déplacement vers : {latitude}, {longitude}")
    response = drone(
        moveTo(
            latitude=latitude,
            longitude=longitude,
            altitude=H,
            orientation_mode="TO_TARGET",  # Mode d'orientation vers la cible
            heading=0  # Orientation par défaut (cap à 0 degré)
        )
    ).wait()
    sleep(10)  # Augmentez ce délai si nécessaire

    if not response.success():
        print(f"Erreur lors du déplacement vers le point ({latitude}, {longitude}).")
    else:
        print(f"Point atteint : ({latitude}, {longitude})")
    sleep(3)  # Pause entre les mouvements pour éviter les surcharges

# Atterrissage
print("Atterrissage en cours...")
drone(Landing()).wait().success()
drone.disconnect()

