# Smart Parking

## Descriere

Smart Parking este un sistem inteligent de administrare a unei parcări, dezvoltat în cadrul lucrării de licență. Proiectul integrează o aplicație web dezvoltată în **Python** folosind framework-ul **Flask**, o bază de date **MySQL** și componente hardware bazate pe **Arduino Uno**, **ESP32** și **ESP32-CAM**.

Sistemul permite:
- autentificarea și administrarea utilizatorilor;
- înregistrarea autovehiculelor;
- rezervarea locurilor de parcare;
- inițierea unei sesiuni noi de parcare;
- recunoașterea automată a numerelor de înmatriculare utilizând **EasyOCR**;
- controlul automat al barierei;
- ghidarea utilizatorului către locul de parcare prin LED-uri;
- monitorizarea în timp real a locurilor disponibile.

---

# Livrabilele proiectului

Repository-ul conține întregul cod sursă al aplicației Smart Parking, fără fișiere binare compilate.

Acesta include:

- aplicația web dezvoltată în Python (Flask);
- șabloanele HTML (Jinja2), fișierele CSS și JavaScript;
- codul sursă pentru Arduino Uno;
- codul sursă pentru ESP32;
- codul sursă pentru ESP32-CAM;
- scripturile SQL pentru baza de date MySQL;
- fișierul `requirements.txt`;
- fișierul `README.md`.

**Nu sunt incluse fișiere binare compilate (.bin, .hex, .elf, .pyc etc.).**

---

# Repository

Adresa repository-ului:

**https://github.com/TenteaIulia/SmartParking**

---

# Cerințe software

- Python 3.11 sau o versiune mai nouă;
- MySQL Server;
- Arduino IDE 2.x;
- ESP32 Board Package pentru Arduino IDE;
- Visual Studio Code (opțional, pentru dezvoltare).

---

# Cerințe hardware

- Arduino Uno;
- ESP32 Dev Module;
- ESP32-CAM (AI Thinker);
- Cameră OV2640;
- LCD 16×2 cu interfață I2C;
- Servomotor;
- Senzzor ultrasonic HC-SR04;
- Senzor de lumină BH1750;
- LED-uri pentru ghidarea utilizatorului.

---

# Instalarea aplicației

## 1. Clonarea repository-ului

```bash
git clone https://github.com/TenteaIulia/SmartParking.git
```

## 2. Crearea unui mediu virtual

```bash
python -m venv venv
```

## 3. Activarea mediului virtual

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

## 4. Instalarea bibliotecilor necesare

```bash
pip install -r requirements.txt
```

## 5. Configurarea bazei de date

1. Se creează baza de date **smart_parking** în MySQL.
2. Se importă scripturile SQL incluse în proiect:
   - smart_parking_users.sql
   - smart_parking_vehicles.sql
   - smart_parking_parking_zones.sql
   - smart_parking_parking_spots.sql
   - smart_parking_parking_sessions.sql
   - smart_parking_parking_reservations.sql
   - smart_parking_led_events.sql
3. Se configurează datele de conectare la baza de date în aplicația Flask.

## 6. Configurarea modulelor ESP

În codul sursă al modulelor **ESP32** și **ESP32-CAM** trebuie configurate:

- numele rețelei Wi-Fi (SSID);
- parola rețelei Wi-Fi;
- adresa IP a serverului Flask.

---

# Compilarea aplicației

## Aplicația web

Pornirea aplicației Flask:

```bash
python app1.py
```

## Arduino Uno

1. Se deschide proiectul în Arduino IDE.
2. Se selectează placa **Arduino Uno**.
3. Se selectează portul serial.
4. Se compilează și se încarcă programul pe placă.

## ESP32

1. Se deschide proiectul în Arduino IDE.
2. Se selectează placa **ESP32 Dev Module**.
3. Se compilează și se încarcă firmware-ul.

## ESP32-CAM

1. Se deschide proiectul în Arduino IDE.
2. Se selectează placa **AI Thinker ESP32-CAM**.
3. Se compilează și se încarcă firmware-ul utilizând un adaptor USB–TTL.

---

# Lansarea aplicației

1. Se pornește serverul MySQL.
2. Se rulează aplicația Flask:

```bash
python app1.py
```

3. Se alimentează și se pornesc modulele Arduino Uno, ESP32 și ESP32-CAM.
4. Aplicația poate fi accesată din browser la adresa:

```
http://localhost:5000
```

sau, în cadrul rețelei locale:

```
http://<IP_SERVER>:5000
```

---

# Tehnologii utilizate

- Python
- Flask
- Jinja2
- HTML
- CSS
- JavaScript
- MySQL
- EasyOCR
- OpenCV
- Arduino Uno
- ESP32
- ESP32-CAM
- REST API
- UART

---

# Observații

Înainte de rularea aplicației trebuie configurate:

- conexiunea la baza de date MySQL;
- SSID-ul și parola rețelei Wi-Fi;
- adresa IP a serverului Flask utilizată de modulele ESP32 și ESP32-CAM.

Repository-ul conține exclusiv codul sursă și fișierele necesare compilării și rulării aplicației.Proiectul este organizat modular, fiecare componentă software (aplicația web, Arduino Uno, ESP32 și ESP32-CAM) fiind dezvoltată independent și comunicând prin intermediul protocolului HTTP (REST API), al comunicației UART și al semnalelor digitale GPIO.
