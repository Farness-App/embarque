import json
import requests
from geopy.distance import geodesic

with open("input_weather.json", "r") as file:
    config = json.load(file)

coordinates = config["coordinates"]
first_point = coordinates[0]
lat = first_point[0]
lon = first_point[1]
user_choice = config["drone"].strip().lower()
vitesse = config["vitesse"]
DRONE_IP = config["DRONE_IP"]
DRONE_IP = f'"{DRONE_IP}"'

api_key = 'f03724961b9858b509d3d011a32f5a5c'

class Mission:
    def __init__(self, coordinates, vitesse):
        self.coordinates = coordinates
        self.vitesse = vitesse

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        point1 = (lat1, lon1)
        point2 = (lat2, lon2)
        distance = geodesic(point1, point2).kilometers
        return distance

    def calculate_total_distance(self):
        total_distance = 0
        for i in range(1, len(self.coordinates)):
            lat1, lon1 = self.coordinates[i-1]
            lat2, lon2 = self.coordinates[i]
            total_distance += self.calculate_distance(lat1, lon1, lat2, lon2)
        return total_distance

    def calculate_mission_time(self, distance):
        time_in_hours = (distance / self.vitesse) + 0.015
        
        hours = int(time_in_hours)  
        minutes = int((time_in_hours - hours) * 60)  
        seconds = int(((time_in_hours - hours) * 60 - minutes) * 60)  

        return f"{hours:02}:{minutes:02}:{seconds:02}"

class Drone:
    def __init__(self, name, max_wind_speed, max_clouds, min_temperature, max_temperature, max_humidity, rain_sensitive=True):
        self.name = name
        self.max_wind_speed = max_wind_speed
        self.max_clouds = max_clouds
        self.min_temperature = min_temperature
        self.max_temperature = max_temperature
        self.max_humidity = max_humidity
        self.rain_sensitive = rain_sensitive

class Meteo:
    def __init__(self, lat, lon, api_key):
        self.lat = lat
        self.lon = lon
        self.api_key = api_key

    def verify_api_key(self):
        url = f'http://api.openweathermap.org/data/2.5/weather?q=London&appid={self.api_key}'
        response = requests.get(url)
        return response.status_code == 200

    def get_weather_by_coordinates(self):
        if not self.verify_api_key():
            print("Clé API invalide.")
            return None

        url = f'http://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&appid={self.api_key}&units=metric'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return {
                'wind_speed': data['wind']['speed'],
                'clouds': data['clouds']['all'],
                'weather_description': data['weather'][0]['description'],
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity']
            }
        else:
            print(f"Erreur lors de la récupération météo. Code HTTP : {response.status_code}")
            return None

    def can_drone_mission(self, weather_data, drone: Drone):
        if not weather_data:
            return {"mission_risquee": "oui", "raison": "Impossible d'obtenir les données météorologiques."}
        
        wind_speed = weather_data['wind_speed']
        clouds = weather_data['clouds']
        weather_description = weather_data['weather_description']
        temperature = weather_data['temperature']
        humidity = weather_data['humidity']

        rain_conditions = ['rain', 'drizzle', 'thunderstorm']
        risk_factors = []
        mission_risquee = "non"

        if wind_speed > drone.max_wind_speed:
            risk_factors.append(f"Vitesse du vent trop élevée ({wind_speed} m/s).")
            mission_risquee = "oui"
        
        if clouds > drone.max_clouds:
            risk_factors.append(f"Couverture nuageuse trop élevée ({clouds}%).")
            mission_risquee = "oui"
        
        if drone.rain_sensitive and any(cond in weather_description for cond in rain_conditions):
            risk_factors.append(f"Conditions de pluie détectées : {weather_description}.")
            mission_risquee = "oui"
        
        if temperature < drone.min_temperature or temperature > drone.max_temperature:
            risk_factors.append(f"Température non adaptée ({temperature}°C).")
            mission_risquee = "oui"
        
        if humidity > drone.max_humidity:
            risk_factors.append(f"Humidité trop élevée ({humidity}%).")
            mission_risquee = "oui"

        if risk_factors:
            return {
                "mission_risquee": mission_risquee,
                "temperature": f"{temperature}°C",
                "vent": f"{wind_speed} m/s",
                "nuages": f"{clouds}%",
                "humidite": f"{humidity}%",
                "pluie": weather_description,
                "raison": " ".join(risk_factors)
            }
        else:
            return {
                "mission_risquee": "non",
                "temperature": f"{temperature}°C",
                "vent": f"{wind_speed} m/s",
                "nuages": f"{clouds}%",
                "humidite": f"{humidity}%",
                "pluie": weather_description,
                "raison": "Les conditions sont favorables."
            }

with open("all_drones.json", "r") as file:
    drones_data = json.load(file)

drones = {}
for name, specs in drones_data.items():
    drones[name] = Drone(
        name=name,
        max_wind_speed=specs["max_wind_speed"],
        max_clouds=specs["max_clouds"],
        min_temperature=specs["min_temperature"],
        max_temperature=specs["max_temperature"],
        max_humidity=specs["max_humidity"],
        rain_sensitive=specs.get("rain_sensitive", True)
    )

if user_choice in drones:
    drone_selected = drones[user_choice]
    meteo = Meteo(lat, lon, api_key)
    weather_data = meteo.get_weather_by_coordinates()
    mission_status = meteo.can_drone_mission(weather_data, drone_selected)

    mission = Mission(coordinates, vitesse)  
    total_distance = mission.calculate_total_distance()
    mission_time = mission.calculate_mission_time(total_distance)  
    total_distance = f"{total_distance:.3f}"

    print(f"Distance totale entre les points: {total_distance} km")
    print(f"Temps estimé pour la mission: {mission_time} heures")  
    
    result = {
    "mission_status": mission_status,
    "total_distance": total_distance,
    "mission_time": mission_time
}
    
    with open("mission_status.json", "w") as file:
        json.dump(result, file, indent=4)
    
    print(mission_status)
else:
    print(f"Drone inconnu : '{user_choice}'. Veuillez choisir parmi : {', '.join(drones.keys())}.")

