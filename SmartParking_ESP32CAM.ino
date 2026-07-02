#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>

const char* ssid = "DIGI_1a4450";
const char* password = "28e6e5bb";

String serverUrl = "http://192.168.1.4:5000/api/camera/barrier";

WebServer server(80);

#define PIN_TRIGGER 13
#define PIN_B1      14
#define PIN_B2      15
#define PIN_OPEN    4
#define PIN_PAYMENT 12

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

bool lastTrigger = LOW;
String currentDirection = "entry";

bool isReservationMode() {
  int b1 = digitalRead(PIN_B1);
  int b2 = digitalRead(PIN_B2);

  return b1 == HIGH && b2 == HIGH;
}

int getZone() {
  int b1 = digitalRead(PIN_B1);
  int b2 = digitalRead(PIN_B2);

  if (b1 == HIGH && b2 == HIGH) return 0; // rezervare

  if (b1 == LOW && b2 == LOW) return 1;
  if (b1 == HIGH && b2 == LOW) return 2;
  if (b1 == LOW && b2 == HIGH) return 3;

  return 1;
}

void sendOpenSignal() {
  Serial.println("TRIMIT OPEN CATRE ARDUINO");
  digitalWrite(PIN_OPEN, HIGH);
  delay(8000);
  digitalWrite(PIN_OPEN, LOW);
  Serial.println("OPEN OPRIT");
}

void sendPaymentSignal() {
  Serial.println("TRIMIT ALERTA/PLATA CATRE ARDUINO");
  digitalWrite(PIN_PAYMENT, HIGH);
  delay(3000);
  digitalWrite(PIN_PAYMENT, LOW);
  Serial.println("ALERTA/PLATA OPRITA");
}
void sendErrorSignal() {
  Serial.println("TRIMIT EROARE CATRE ARDUINO");

  digitalWrite(PIN_PAYMENT, HIGH);
  Serial.print("PIN_PAYMENT SETAT HIGH, CITIRE = ");
  Serial.println(digitalRead(PIN_PAYMENT));

  delay(6000);

  digitalWrite(PIN_PAYMENT, LOW);
  Serial.print("PIN_PAYMENT SETAT LOW, CITIRE = ");
  Serial.println(digitalRead(PIN_PAYMENT));

  Serial.println("EROARE OPRITA");
}

void handleOpenBarrier() {
  sendOpenSignal();
  server.send(200, "text/plain", "Barrier opened");
}

bool initCamera() {
  camera_config_t config;

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;

  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 15;
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_LATEST;

  esp_err_t err = esp_camera_init(&config);

  if (err != ESP_OK) {
    Serial.print("Camera error: ");
    Serial.println(err);
    return false;
  }

  sensor_t *s = esp_camera_sensor_get();

  if (s != NULL) {
    s->set_vflip(s, 1);
    s->set_hmirror(s, 0);
    s->set_brightness(s, 1);
    s->set_contrast(s, 1);
    s->set_saturation(s, 0);
  }

  return true;
}

bool captureAndSendOnce() {
  server.handleClient();

  const int maxAttempts = 3;

  for (int attempt = 1; attempt <= maxAttempts; attempt++) {
    Serial.print("OCR incercare ");
    Serial.println(attempt);

    camera_fb_t *fb = esp_camera_fb_get();

    if (!fb) {
      Serial.println("Camera capture failed");
      delay(500);
      continue;
    }

    int zone = getZone();
    String direction = currentDirection;
    String accessType = isReservationMode() ? "reservation" : "session";

    Serial.print("Access type: ");
    Serial.println(accessType);
    Serial.print("Zone sent: ");
    Serial.println(zone);

    WiFiClient client;
    HTTPClient http;

    String boundary = "----ESP32CAMBOUNDARY";

    String head = "";

    head += "--" + boundary + "\r\n";
    head += "Content-Disposition: form-data; name=\"zone_id\"\r\n\r\n";
    head += String(zone) + "\r\n";

    head += "--" + boundary + "\r\n";
    head += "Content-Disposition: form-data; name=\"direction\"\r\n\r\n";
    head += direction + "\r\n";

    head += "--" + boundary + "\r\n";
    head += "Content-Disposition: form-data; name=\"access_type\"\r\n\r\n";
    head += accessType + "\r\n";

    head += "--" + boundary + "\r\n";
    head += "Content-Disposition: form-data; name=\"image\"; filename=\"cam.jpg\"\r\n";
    head += "Content-Type: image/jpeg\r\n\r\n";

    String tail = "\r\n--" + boundary + "--\r\n";

    int totalLen = head.length() + fb->len + tail.length();
    uint8_t *body = (uint8_t*) malloc(totalLen);

    if (!body) {
      esp_camera_fb_return(fb);
      delay(500);
      continue;
    }

    memcpy(body, head.c_str(), head.length());
    memcpy(body + head.length(), fb->buf, fb->len);
    memcpy(body + head.length() + fb->len, tail.c_str(), tail.length());

    http.begin(client, serverUrl);
    http.setTimeout(20000);
    http.setReuse(false);
    http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

    int code = http.POST(body, totalLen);
    String response = http.getString();

    Serial.println("========== RASPUNS FLASK ==========");
    Serial.print("HTTP CODE = ");
    Serial.println(code);
    Serial.print("RESPONSE = ");
    Serial.println(response);
    Serial.println("====================================");


    free(body);
    esp_camera_fb_return(fb);
    http.end();

    if (code >= 200 && code < 300) {
      Serial.println("ACCES PERMIS - TRIMIT OPEN");
      sendOpenSignal();
      return true;
    }

    if (code == 402 || response.indexOf("payment_required") >= 0) {
      Serial.println("PLATA NECESARA - TRIMIT PAYMENT");
      sendPaymentSignal();
      return true;
    }

    if (code == 400) {
      Serial.println("########################");
      Serial.println("AM INTRAT PE RAMURA 400");
      Serial.println("########################");
      sendErrorSignal();
      return true;
    }

    Serial.println("OCR nereusit, reincerc...");
    delay(1000);
  }

  Serial.println("OCR esuat dupa toate incercarile");
  sendPaymentSignal();
  return false;
}

void setup() {
  Serial.begin(115200);
  delay(2000);

  pinMode(PIN_TRIGGER, INPUT_PULLDOWN);
  pinMode(PIN_B1, INPUT_PULLDOWN);
  pinMode(PIN_B2, INPUT_PULLDOWN);

  pinMode(PIN_OPEN, OUTPUT);
  digitalWrite(PIN_OPEN, LOW);

  pinMode(PIN_PAYMENT, OUTPUT);
  digitalWrite(PIN_PAYMENT, LOW);


  Serial.println("TEST PIN_PAYMENT");
  Serial.print("PIN_PAYMENT = ");
  Serial.println(PIN_PAYMENT);

  digitalWrite(PIN_PAYMENT, HIGH);
  delay(5000);
  Serial.print("CITIRE HIGH = ");
  Serial.println(digitalRead(PIN_PAYMENT));

  digitalWrite(PIN_PAYMENT, LOW);
  delay(1000);
  Serial.print("CITIRE LOW = ");
  Serial.println(digitalRead(PIN_PAYMENT));

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);

  Serial.print("WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WIFI OK");
  Serial.print("ESP IP: ");
  Serial.println(WiFi.localIP());

  server.on("/open-barrier", handleOpenBarrier);
  server.begin();

  Serial.println("HTTP server started");

  if (!initCamera()) {
    Serial.println("Camera failed");
  } else {
    Serial.println("Camera ready");
  }

  lastTrigger = digitalRead(PIN_TRIGGER);
}

void loop() {
  server.handleClient();

  static unsigned long lastDebug = 0;

  if (millis() - lastDebug > 500) {
    lastDebug = millis();
    Serial.print("GPIO13 trigger = ");
    Serial.println(digitalRead(PIN_TRIGGER));
  }


  bool current = digitalRead(PIN_TRIGGER);

  if (current == HIGH && lastTrigger == LOW) {
    Serial.println("TRIGGER PRIMIT");

    unsigned long startPulse = millis();

    while (digitalRead(PIN_TRIGGER) == HIGH) {
      server.handleClient();
      delay(10);
    }

    unsigned long pulseDuration = millis() - startPulse;

    Serial.print("Durata puls: ");
    Serial.println(pulseDuration);

    if (pulseDuration > 1500) {
      currentDirection = "exit";
    } else {
      currentDirection = "entry";
    }

    Serial.print("Directie: ");
    Serial.println(currentDirection);

    delay(300);

    bool result = captureAndSendOnce();

    if (result) {
      Serial.println("OCR finalizat cu raspuns valid");
    } else {
      Serial.println("OCR esuat");
    }

    Serial.println("Blochez retrigger 5 secunde");
    delay(5000);

    while (digitalRead(PIN_TRIGGER) == HIGH) {
      server.handleClient();
      delay(10);
    }

    lastTrigger = digitalRead(PIN_TRIGGER);
    return;
  }

  lastTrigger = current;
  delay(20);
}
