#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <BH1750.h>

const char* ssid = "Orange-H9hGkd-2G";
const char* password = "9QsGDZdNHTz57xQ6UY";

String serverUrl = "http://192.168.1.4:5000/api/led-events";
String freeSpotsUrl = "http://192.168.1.26:5000/api/free-spots";

BH1750 lightMeter;
StaticJsonDocument<512> doc;
#define STREET_LIGHTS 4

int ledPins[9] = {
  13, 12, 14,
  27, 26, 25,
  33, 32, 23
};
float DARK_THRESHOLD = 30;  
unsigned long guideEndTime = 0;

int activeGuideLed = -1;

int getLedIndex(int zone, int spot) {
  return (zone - 1) * 3 + (spot - 1);
}

void turnOffGuideLed() {
  if (activeGuideLed >= 0 && activeGuideLed < 9) {
    digitalWrite(ledPins[activeGuideLed], LOW);
  }
  activeGuideLed = -1;
}

void startGuideLed(int zone, int spot, int durationSeconds) {
  turnOffGuideLed();
  int ledIndex = getLedIndex(zone, spot);
  if (ledIndex >= 0 && ledIndex < 9) {
    activeGuideLed = ledIndex;
    digitalWrite(ledPins[activeGuideLed], HIGH);
    guideEndTime = millis() + durationSeconds * 1000UL;
  }
}
void updateStreetLightsByLux() {
  float lux = lightMeter.readLightLevel();

  Serial.print("Lux: ");
  Serial.println(lux);

  if (lux < DARK_THRESHOLD) {
    digitalWrite(STREET_LIGHTS, HIGH);
    Serial.println("Noapte - stalpi aprinsi");
  } else {
    digitalWrite(STREET_LIGHTS, LOW);
    Serial.println("Zi - stalpi stinsi");
  }
}

void checkLedTimers() {
  if (activeGuideLed != -1 && millis() > guideEndTime) {
    turnOffGuideLed();
    Serial.println("LED ghidaj stins");
  }
}

void checkServerEvents() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi deconectat");
    return;
  }

  HTTPClient http;
  http.begin(serverUrl);

  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    DeserializationError error = deserializeJson(doc, payload);

    if (!error) {
      bool hasEvent = doc["has_event"];

      if (hasEvent) {
        int zone = doc["zone_id"];
        int spot = doc["spot_number"];
        int duration = doc["duration_seconds"];

        Serial.print("Eveniment: zona ");
        Serial.print(zone);
        Serial.print(", loc ");
        Serial.println(spot);

        startGuideLed(zone, spot, duration);
      }
    } else {
      Serial.println("Eroare JSON");
    }
  } else {
    Serial.print("HTTP error: ");
    Serial.println(httpCode);
  }

  http.end();
}
void sendFreeSpotsToArduino() {
  static int lastSentFreeSpots = -1;

  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(freeSpotsUrl);

  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();

    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (!error) {
      int freeSpots = doc["free_spots"];

      if (freeSpots != lastSentFreeSpots) {
        Serial2.print("FREE:");
        Serial2.println(freeSpots);

        Serial.print("Trimis catre Arduino: FREE:");
        Serial.println(freeSpots);

        lastSentFreeSpots = freeSpots;
      }
    }
  }

  http.end();
}


void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, 16, 17);

  for (int i = 0; i < 9; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }

  pinMode(STREET_LIGHTS, OUTPUT);
  digitalWrite(STREET_LIGHTS, LOW);

  Wire.begin(21, 22);

  if (lightMeter.begin()) {
    Serial.println("BH1750 OK");
  } else {
    Serial.println("BH1750 ERROR");
  }

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);

  Serial.print("WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi conectat");
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());

  sendFreeSpotsToArduino();
}

void loop() {
  checkLedTimers();
  checkServerEvents();

  static unsigned long lastFreeSpotsCheck = 0;
  static unsigned long lastLightCheck = 0;

  if (millis() - lastFreeSpotsCheck > 2000) {
    lastFreeSpotsCheck = millis();
    sendFreeSpotsToArduino();
  }

  if (millis() - lastLightCheck > 2000) {
    lastLightCheck = millis();
    updateStreetLightsByLux();
  }

  delay(1000);
}
