#ce code n'est testé 
import json
import requests
from geopy.distance import geodesic
import olympe
from olympe.messages.common.CommonState import BatteryStateChanged
from olympe.messages.battery import health as BatteryHealth


with open("input_weather.json", "r") as file:
    config = json.load(file)

coordinates = config["coordinates"]
lat, lon = coordinates[0]
user_choice = config["drone"].strip().lower()
vitesse = config["vitesse"]
DRONE_IP = config["DRONE_IP"]
api_key = 'f03724961b9858b509d3d011a32f5a5c'


def get_battery_level(drone_ip):
    try:
        drone = olympe.Drone(drone_ip)
        drone.connect()

        battery_state = drone.get_state(BatteryStateChanged)
        battery_level = battery_state.get('percent', 0)

        battery_health_state = drone.get_state(BatteryHealth)
        battery_soh = battery_health_state.get('state_of_health', 0)

        return {
            "battery_level": f"{battery_level}%",
            "battery_soh": f"{battery_soh}%"
        }

    except Exception as e:
        print(f"Erreur lors de la connexion ou récupération de la batterie : {e}")
        return {
            "battery_level": "0%",
            "battery_soh": "0%"
        }



class Drone:
    def __init__(self, name, max_wind_speed, max_clouds, min_temperature, max_temperature, max_humidity, rain_sensitive=True, max_flight_time=30):
        self.name = name
        self.max_wind_speed = max_wind_speed
        self.max_clouds = max_clouds
        self.min_temperature = min_temperature
        self.max_temperature = max_temperature
        self.max_humidity = max_humidity
        self.rain_sensitive = rain_sensitive
        self.max_flight_time = max_flight_time


class Meteo:
    def __init__(self, lat, lon, api_key):
        self.lat = lat
        self.lon = lon
        self.api_key = api_key

    def verify_api_key(self):
        url = f'http://api.openweathermap.org/data/2.5/weather?q=London&appid={self.api_key}'
        return requests.get(url).status_code == 200

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
            print(f"Erreur météo. Code HTTP : {response.status_code}")
            return None

    def can_drone_mission(self, weather_data, drone: Drone):
        if not weather_data:
            return {"mission_risquee": "oui", "raison": "Données météo indisponibles."}

        wind_speed = weather_data['wind_speed']
        clouds = weather_data['clouds']
        description = weather_data['weather_description']
        temp = weather_data['temperature']
        humidity = weather_data['humidity']

        rain_conditions = ['rain', 'drizzle', 'thunderstorm']
        risk_factors = []
        mission_risquee = "non"

        if wind_speed > drone.max_wind_speed:
            risk_factors.append(f"Vent trop fort ({wind_speed} m/s)")
            mission_risquee = "oui"

        if clouds > drone.max_clouds:
            risk_factors.append(f"Trop de nuages ({clouds}%)")
            mission_risquee = "oui"

        if drone.rain_sensitive and any(cond in description for cond in rain_conditions):
            risk_factors.append(f"Pluie détectée : {description}")
            mission_risquee = "oui"

        if not (drone.min_temperature <= temp <= drone.max_temperature):
            risk_factors.append(f"Température hors limites ({temp}°C)")
            mission_risquee = "oui"

        if humidity > drone.max_humidity:
            risk_factors.append(f"Humidité trop élevée ({humidity}%)")
            mission_risquee = "oui"

        return {
            "mission_risquee": mission_risquee,
            "raison": " | ".join(risk_factors) if risk_factors else "Conditions météo favorables."
        }


with open("all_drones.json", "r") as file:
    drones_data = json.load(file)

drones = {
    name: Drone(
        name=name,
        max_wind_speed=specs["max_wind_speed"],
        max_clouds=specs["max_clouds"],
        min_temperature=specs["min_temperature"],
        max_temperature=specs["max_temperature"],
        max_humidity=specs["max_humidity"],
        rain_sensitive=specs.get("rain_sensitive", True),
        max_flight_time=specs["max_flight_time"]
    )
    for name, specs in drones_data.items()
}

if user_choice in drones:
    drone_selected = drones[user_choice]
    meteo = Meteo(lat, lon, api_key)
    weather_data = meteo.get_weather_by_coordinates()
    mission_status = meteo.can_drone_mission(weather_data, drone_selected)

    battery_info = get_battery_level(DRONE_IP)
    battery_level = float(battery_info["battery_level"].replace('%', ''))
    battery_soh = float(battery_info["battery_soh"].replace('%', ''))

    max_flight_time_adjusted = drone_selected.max_flight_time * (battery_soh / 100) * (battery_level / 100)

    real_time_formatted = mission.format_time(max_flight_time_adjusted)

    if mission_duration_min > max_flight_time_adjusted:
        mission_status["mission_risquee"] = "oui"
        mission_status["raison"] = (
            f"Temps de vol max : {real_time_formatted}, "
        )

    result = {
        "mission_risque": mission_status["mission_risquee"],
        "temps_restant_de_la_batterie": real_time_formatted,
        "distance": f"{total_distance_km:.3f}",
        "niveau_batterie": battery_info["battery_level"],
        "mission_status": mission_status["raison"]
    }

    with open("mission_status.json", "w") as outfile:
        json.dump(result, outfile, indent=4)

    print(json.dumps(result, indent=4))

else:
    print(f"Drone inconnu : '{user_choice}'. Choisissez parmi : {', '.join(drones.keys())}.")

