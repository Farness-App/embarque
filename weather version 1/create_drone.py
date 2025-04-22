import json
import os

class Drone:
    def __init__(self, name, max_wind_speed, max_clouds, min_temperature, max_temperature, max_humidity, rain_sensitive=True):
        self.name = name
        self.max_wind_speed = max_wind_speed
        self.max_clouds = max_clouds
        self.min_temperature = min_temperature
        self.max_temperature = max_temperature
        self.max_humidity = max_humidity
        self.rain_sensitive = rain_sensitive

    def to_dict(self):
        return {
            "name": self.name,
            "max_wind_speed": self.max_wind_speed,
            "max_clouds": self.max_clouds,
            "min_temperature": self.min_temperature,
            "max_temperature": self.max_temperature,
            "max_humidity": self.max_humidity,
            "rain_sensitive": self.rain_sensitive
        }

with open("input_drone.json", "r") as file:
    config = json.load(file)

if os.path.exists("all_drones.json"):
    with open("all_drones.json", "r") as file:
        all_drones_data = json.load(file)
else:
    all_drones_data = {}

if "new_drones" in config:
    for drone_info in config["new_drones"]:
        name = drone_info["name"]
        if name in all_drones_data:
            print(f"Le drone '{name}' existe déjà")
        else:
            new_drone = Drone(
                name=name,
                max_wind_speed=drone_info["max_wind_speed"],
                max_clouds=drone_info["max_clouds"],
                min_temperature=drone_info["min_temperature"],
                max_temperature=drone_info["max_temperature"],
                max_humidity=drone_info["max_humidity"],
                rain_sensitive=drone_info.get("rain_sensitive", True)
            )
            all_drones_data[name] = new_drone.to_dict()
            print(f"Drone ajouté : {name}")

with open("all_drones.json", "w") as file:
    json.dump(all_drones_data, file, indent=4)

print("Fichier 'all_drones.json' mis à jour.")

