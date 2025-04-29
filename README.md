# embarque

1- voicechat : Ce dossier contient deux scripts permettant de commander le drone par commandes vocales simples, telles que : "Avancer de X mètres", "Atterrir", "Monter de 5 mètres", etc. Ces scripts utilisent la reconnaissance vocale pour interpréter les ordres de l'utilisateur et les convertir en actions de vol.

2- grid : Ce fichier contient l'implémentation de la fonction Grid_mission. Une mission de type grid rectangulaire consiste à faire voler le drone au-dessus d’une zone selon un motif en lignes parallèles, couvrant ainsi toute la surface de manière uniforme. Ce type de mission est utilisé pour la cartographie, l’inspection ou la surveillance.

3- keyboard : Ce dossier contient deux scripts de commande du drone par clavier : Un script simple permettant un contrôle direct via les touches. Un script multithreadé, qui gère les événements clavier et le contrôle du drone en parallèle pour une meilleure réactivité.

4- weather_and_battery : Ce fichier contient deux parties : Un module de définition de modèles de drones selon leurs caractéristiques environnementales (humidité maximale, température supportée, etc.). Un algorithme de vérification des conditions de vol, qui évalue si la mission peut démarrer en fonction de l’état de la batterie restante et des conditions météorologiques actuelles.
