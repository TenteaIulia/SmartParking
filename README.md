# Smart Parking

## Descriere

Smart Parking este o aplicație destinată administrării inteligente a unei parcări, integrând o aplicație web dezvoltată în Python folosind framework-ul Flask, o bază de date MySQL și componente hardware bazate pe Arduino Uno, ESP32 și ESP32-CAM.

Sistemul permite:

- autentificarea și administrarea utilizatorilor;
- înregistrarea autovehiculelor;
- rezervarea locurilor de parcare;
- inițierea unei sesiuni noi de parcare;
- recunoașterea automată a numerelor de înmatriculare folosind EasyOCR;
- controlul automat al barierei;
- ghidarea utilizatorului către locul de parcare prin LED-uri;
- monitorizarea în timp real a locurilor disponibile.

---

# Livrabilele proiectului

Repository-ul conține întregul cod sursă al aplicației Smart Parking, fără fișiere binare compilate.

Structura principală a proiectului este:

```
SmartParking/
│
├── app1.py
├── requirements.txt
├── templates/
├── static/
├── database/
│
├── Arduino/
│
├── ESP32/
│
├── ESP32-CAM/
│
└── README.md
```

Repository-ul conține:

- aplicația web dezvoltată în Python (Flask);
- șabloanele HTML (Jinja2);
- fișiere CSS și JavaScript;
- codul sursă pentru Arduino Uno;
- codul sursă pentru ESP32;
- codul sursă pentru ESP32-CAM;
- scripturile SQL pentru baza de date MySQL;
- documentația proiectului.

Nu sunt incluse fișiere binare compilate (.bin, .hex, .elf, .pyc etc.).

---

# Repository

Adresa repository-ului:

```
https://gitlab.upt.ro/..................
```

(se completează după încărcarea proiectului)

---

# Cerințe hardware

- Arduino Uno
- ESP32 Dev Module
- ESP32-CAM (AI Thinker)
- Cameră OV2640
- LCD 16x2 cu interfață I2C
- Servomotor
- Senzor ultrasonic HC-SR04
- Senzor de lumină BH1750
- LED-uri pentru ghidarea utilizatorului

---

# Cerințe software

- Windows 10/11
- Python 3.11 sau versiune mai nouă
- MySQL Server
- Arduino IDE 2.x
- ESP32 Board Package
- Visual Studio Code

---

# Instalarea aplicației

## 1. Clonarea repository-ului

```bash
git clone https://gitlab.upt.ro/............
```

## 2. Crearea mediului virtual

```bash
python -m venv venv
```

Activarea mediului virtual:

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

## 3. Instalarea bibliotecilor

```bash
pip install -r requirements.txt
```

---

# Configurarea bazei de date

1. Se creează baza de date MySQL:

```
smart_parking
```

2. Se importă scripturile SQL existente în directorul **database**:

- users.sql
- vehicles.sql
- parking_zones.sql
- parking_spots.sql
- parking_sessions.sql
- parking_reservations.sql
- led_events.sql

3. Se configurează datele de conectare în aplicația Flask:

- host
- user
- password
- database

---

# Compilarea firmware-ului

## Arduino Uno

1. Se deschide proiectul în Arduino IDE.
2. Se selectează placa **Arduino Uno**.
3. Se selectează portul serial.
4. Se compilează (**Verify**).
5. Se încarcă firmware-ul (**Upload**).

Biblioteci utilizate:

- Wire
- LiquidCrystal_I2C
- Servo
- SoftwareSerial

---

## ESP32

1. Se deschide proiectul în Arduino IDE.
2. Se selectează placa **ESP32 Dev Module**.
3. Se configurează SSID-ul și parola rețelei Wi-Fi.
4. Se configurează adresa IP a serverului Flask.
5. Se compilează și se încarcă firmware-ul.

Biblioteci utilizate:

- WiFi
- HTTPClient
- ArduinoJson
- Wire
- BH1750

---

## ESP32-CAM

1. Se deschide proiectul în Arduino IDE.
2. Se selectează placa **AI Thinker ESP32-CAM**.
3. Se configurează SSID-ul și parola rețelei Wi-Fi.
4. Se configurează adresa IP a serverului Flask.
5. Se compilează și se încarcă firmware-ul folosind un adaptor USB–TTL.

Biblioteci utilizate:

- esp_camera
- WiFi
- HTTPClient
- WebServer

---

# Lansarea aplicației

Pornirea serverului Flask:

```bash
python app1.py
```

După pornirea aplicației, aceasta este disponibilă la adresa:

```
http://localhost:5000
```

sau

```
http://IP_SERVER:5000
```

în cadrul rețelei locale.

---

# Arhitectura sistemului

```
Browser
    │
HTTP
    │
Flask (Python)
    │
MySQL
    │
REST API
    ├───────────────┐
    │               │
ESP32-CAM        ESP32
    │               │
GPIO           UART
    │               │
Arduino Uno
```

---

# Comunicația dintre componente

- Browser-ul comunică cu aplicația Flask folosind protocolul HTTP.
- ESP32-CAM transmite imagini către server folosind cereri HTTP POST.
- ESP32 interoghează periodic serverul folosind cereri HTTP GET pentru actualizarea LED-urilor și a numărului de locuri disponibile.
- Arduino Uno comunică cu ESP32 prin interfața UART și cu ESP32-CAM prin semnale digitale GPIO.

---

# Biblioteci Python utilizate

Principalele biblioteci utilizate sunt:

- Flask
- Jinja2
- EasyOCR
- OpenCV
- mysql-connector-python
- requests
- NumPy
- Torch
- Torchvision
- Pandas

---

# Observații

Înainte de rularea aplicației trebuie configurate:

- SSID-ul rețelei Wi-Fi;
- parola rețelei Wi-Fi;
- adresa IP a serverului Flask;
- datele de conectare la baza de date MySQL.

Repository-ul conține exclusiv codul sursă și fișierele necesare compilării și rulării aplicației.
