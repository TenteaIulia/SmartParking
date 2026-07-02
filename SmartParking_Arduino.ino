#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>
#include <SoftwareSerial.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo barrierServo;

SoftwareSerial espLedSerial(A2, A3); // A2 = RX Arduino, A3 = TX Arduino

#define BTN1 2
#define BTN2 3
#define BTN3 4

#define TRIG_PIN A0
#define ECHO_PIN A1

#define ESP_TRIGGER 8
#define ESP_BIT1 10
#define ESP_BIT2 11
#define ESP_OPEN 7
#define ESP_PAYMENT 6

#define SERVO_PIN 9

enum Direction {
  DIR_ENTRY,
  DIR_EXIT
};

Direction currentDirection = DIR_ENTRY;

int selectedType = 0;
int selectedZone = 0;
int selectedSpot = 0;
int availableSpots = 0;

bool selectingSpot = false;
bool waitingForOpen = false;
bool paymentPending = false;
bool showingAvailability = true;

unsigned long waitingStartTime = 0;
unsigned long lastExitTrigger = 0;
unsigned long lastPaymentRetry = 0;

void setup() {
  Serial.begin(9600);
  espLedSerial.begin(9600);

  pinMode(BTN1, INPUT_PULLUP);
  pinMode(BTN2, INPUT_PULLUP);
  pinMode(BTN3, INPUT_PULLUP);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  pinMode(ESP_TRIGGER, OUTPUT);
  pinMode(ESP_BIT1, OUTPUT);
  pinMode(ESP_BIT2, OUTPUT);
  pinMode(ESP_OPEN, INPUT);
  pinMode(ESP_PAYMENT, INPUT);

  digitalWrite(ESP_TRIGGER, LOW);
  digitalWrite(ESP_BIT1, LOW);
  digitalWrite(ESP_BIT2, LOW);

  barrierServo.attach(SERVO_PIN);
  barrierServo.write(90);

  lcd.init();
  lcd.backlight();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SmartParking");
  lcd.setCursor(0, 1);
  lcd.print("Pornire sistem");
  delay(2000);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SmartParking");
  lcd.setCursor(0, 1);
  lcd.print("Bine ati venit!");
  delay(2000);

  showAvailabilityScreen();
}

void loop() {
  readFreeSpotsFromESP();

  static bool openHandled = false;
  static bool paymentHandled = false;
  static unsigned long lastBlink = 0;
  static bool blinkState = false;

  static int lastPaymentState = -1;
  static int lastOpenState = -1;

  int paymentState = digitalRead(ESP_PAYMENT);
  int openState = digitalRead(ESP_OPEN);

  if (paymentState != lastPaymentState) {
    Serial.print("ESP_PAYMENT D6 = ");
    Serial.println(paymentState);
    lastPaymentState = paymentState;
  }

  if (openState != lastOpenState) {
    Serial.print("ESP_OPEN D7 = ");
    Serial.println(openState);
    lastOpenState = openState;
  }

  if (digitalRead(ESP_OPEN) == HIGH && !openHandled) {
    openHandled = true;
    openBarrier();
    return;
  }

  if (digitalRead(ESP_OPEN) == LOW) {
    openHandled = false;
  }

  if (digitalRead(ESP_PAYMENT) == HIGH && !paymentHandled) {
    Serial.println("ARDUINO A PRIMIT SEMNAL PE D6");
    paymentHandled = true;
    waitingForOpen = false;

    unsigned long pulseStart = millis();

    while (digitalRead(ESP_PAYMENT) == HIGH && millis() - pulseStart < 9000) {
      readFreeSpotsFromESP();
      delay(10);
    }

    unsigned long pulseDuration = millis() - pulseStart;
    Serial.print("Durata puls D6 = ");
    Serial.println(pulseDuration);

    lcd.clear();

    if (pulseDuration > 4000) {
      paymentPending = false;

      if (currentDirection == DIR_ENTRY && selectedType == 2) {
        lcd.setCursor(0, 0);
        lcd.print("Nu exista");
        lcd.setCursor(0, 1);
        lcd.print("rezervare");
      } else if (currentDirection == DIR_EXIT) {
        lcd.setCursor(0, 0);
        lcd.print("Nu exista");
        lcd.setCursor(0, 1);
        lcd.print("sesiune activa");
      } else {
        lcd.setCursor(0, 0);
        lcd.print("Acces respins");
        lcd.setCursor(0, 1);
        lcd.print("Verifica app");
      }

      delay(3000);
      showAvailabilityScreen();
      return;
    }

    paymentPending = true;
    lastPaymentRetry = millis();

    lcd.setCursor(0, 0);
    lcd.print("Plata necesara");
    lcd.setCursor(0, 1);
    lcd.print("Aplicatia mobila");

    delay(2000);
    return;
  }

  if (digitalRead(ESP_PAYMENT) == LOW) {
    paymentHandled = false;
  }

  if (paymentPending) {
    lcd.setCursor(0, 0);
    lcd.print("Plata necesara ");
    lcd.setCursor(0, 1);
    lcd.print("Aplicatia mobila");

    if (millis() - lastPaymentRetry > 10000) {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Verific plata");
      lcd.setCursor(0, 1);
      lcd.print("Camera OCR");

      currentDirection = DIR_EXIT;
      sendTriggerToESP();

      lastPaymentRetry = millis();
    }

    delay(200);
    return;
  }

  if (waitingForOpen) {
    if (millis() - waitingStartTime > 30000) {
      waitingForOpen = false;

      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Nu s-a citit");
      lcd.setCursor(0, 1);
      lcd.print("Incearca iar");

      delay(2500);
      showAvailabilityScreen();
      return;
    }

    if (millis() - lastBlink > 700) {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Camera OCR");

      lcd.setCursor(0, 1);

      if (blinkState) {
        lcd.print("Procesare...");
      } else {
        lcd.print("Asteapta...");
      }

      blinkState = !blinkState;
      lastBlink = millis();
    }

    delay(50);
    return;
  }

  if (showingAvailability) {
    if (digitalRead(BTN1) == LOW ||
        digitalRead(BTN2) == LOW ||
        digitalRead(BTN3) == LOW) {
          
           if (availableSpots == 0) {

            lcd.clear();
            lcd.setCursor(0,0);
            lcd.print("Parcare plina");
            lcd.setCursor(0,1);
            lcd.print("Acces blocat");

            delay(2500);
            showAvailabilityScreen();
            return;
        }

      showTypeMenu();
      delay(500);
    }

    checkExitSensor();
    delay(50);
    return;
  }

  handleEntryMenu();
  checkExitSensor();

  delay(50);
}

void readFreeSpotsFromESP() {
  if (espLedSerial.available()) {
    String msg = espLedSerial.readStringUntil('\n');
    msg.trim();

    if (msg.startsWith("FREE:")) {
      availableSpots = msg.substring(5).toInt();
      
      Serial.print("Locuri libere primite: ");
      Serial.println(availableSpots);
      
      if (showingAvailability) {
        showAvailabilityScreen();
      }
    }
  }
}

void showAvailabilityScreen() {
  selectedType = 0;
  selectedZone = 0;
  selectedSpot = 0;
  selectingSpot = false;
  waitingForOpen = false;
  paymentPending = false;
  currentDirection = DIR_ENTRY;
  showingAvailability = true;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SmartParking");
  lcd.setCursor(0, 1);
  lcd.print("Libere: ");
  lcd.print(availableSpots);
}

void showTypeMenu() {
  showingAvailability = false;

  selectedType = 0;
  selectedZone = 0;
  selectedSpot = 0;
  selectingSpot = false;
  waitingForOpen = false;
  paymentPending = false;
  currentDirection = DIR_ENTRY;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SmartParking");
  lcd.setCursor(0, 1);
  lcd.print("1:Ses 2:Rez");
}

void handleEntryMenu() {
  if (selectedType == 0) {
    if (digitalRead(BTN1) == LOW) {
      selectedType = 1;
      showZoneMenu();
      delay(500);
    }

    if (digitalRead(BTN2) == LOW) {
      selectedType = 2;
      showZoneMenu();
      delay(500);
    }

    return;
  }

  if (selectedType == 1) {
    if (digitalRead(BTN1) == LOW) {
      selectedZone = 1;
      startEntryProcess();
      delay(500);
    }

    if (digitalRead(BTN2) == LOW) {
      selectedZone = 2;
      startEntryProcess();
      delay(500);
    }

    if (digitalRead(BTN3) == LOW) {
      selectedZone = 3;
      startEntryProcess();
      delay(500);
    }

    return;
  }

  if (selectedType == 2 && !selectingSpot) {
    if (digitalRead(BTN1) == LOW) {
      selectedZone = 1;
      selectingSpot = true;
      showSpotMenu();
      delay(500);
    }

    if (digitalRead(BTN2) == LOW) {
      selectedZone = 2;
      selectingSpot = true;
      showSpotMenu();
      delay(500);
    }

    if (digitalRead(BTN3) == LOW) {
      selectedZone = 3;
      selectingSpot = true;
      showSpotMenu();
      delay(500);
    }

    return;
  }

  if (selectedType == 2 && selectingSpot) {
    if (digitalRead(BTN1) == LOW) {
      selectedSpot = 1;
      startEntryProcess();
      delay(500);
    }

    if (digitalRead(BTN2) == LOW) {
      selectedSpot = 2;
      startEntryProcess();
      delay(500);
    }

    if (digitalRead(BTN3) == LOW) {
      selectedSpot = 3;
      startEntryProcess();
      delay(500);
    }

    return;
  }
}

void showZoneMenu() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Zona parcare");
  lcd.setCursor(0, 1);
  lcd.print("Alege 1 2 3");
}

void showSpotMenu() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Alege locul");
  lcd.setCursor(0, 1);
  lcd.print("Loc 1 2 3");
}

void startEntryProcess() {
  currentDirection = DIR_ENTRY;

  sendZoneToESP(selectedZone);

  lcd.clear();

  if (selectedType == 1) {
    lcd.setCursor(0, 0);
    lcd.print("Sesiune");
    lcd.setCursor(0, 1);
    lcd.print("Zona ");
    lcd.print(selectedZone);
  } else {
    lcd.setCursor(0, 0);
    lcd.print("Rezervare Z");
    lcd.print(selectedZone);
    lcd.setCursor(0, 1);
    lcd.print("Loc ");
    lcd.print(selectedSpot);
  }

  delay(1200);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Camera OCR");
  lcd.setCursor(0, 1);
  lcd.print("Scaneaza placa");

  sendTriggerToESP();

  waitingForOpen = true;
  waitingStartTime = millis();
}

void checkExitSensor() {
  float distance = readDistance();
  Serial.print("Distanta: ");
  Serial.println(distance);
  if (distance > 2.5 && distance < 3.5 &&
      millis() - lastExitTrigger > 8000 &&
      !waitingForOpen) {

    lastExitTrigger = millis();
    currentDirection = DIR_EXIT;

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Iesire detect.");
    lcd.setCursor(0, 1);
    lcd.print("Camera OCR");

    sendTriggerToESP();

    waitingForOpen = true;
    waitingStartTime = millis();
  }
}

void openBarrier() {
  waitingForOpen = false;
  paymentPending = false;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Acces permis");
  lcd.setCursor(0, 1);
  lcd.print("Bariera desch.");

  barrierServo.write(0);
  delay(2000);

  lcd.clear();

  if (currentDirection == DIR_ENTRY && selectedType != 0) {
    lcd.setCursor(0, 0);
    lcd.print("Urmariti LED-ul");
    lcd.setCursor(0, 1);
    lcd.print("Loc indicat");
  } else {
    lcd.setCursor(0, 0);
    lcd.print("Multumim!");
    lcd.setCursor(0, 1);
    lcd.print("Drum bun!");
  }

  delay(2000);

  barrierServo.write(90);

  delay(1000);
  showAvailabilityScreen();
}

void sendZoneToESP(int zone) {
  if (selectedType == 2) {
    digitalWrite(ESP_BIT1, HIGH);
    digitalWrite(ESP_BIT2, HIGH);
    return;
  }

  if (zone == 1) {
    digitalWrite(ESP_BIT1, LOW);
    digitalWrite(ESP_BIT2, LOW);
  }

  if (zone == 2) {
    digitalWrite(ESP_BIT1, HIGH);
    digitalWrite(ESP_BIT2, LOW);
  }

  if (zone == 3) {
    digitalWrite(ESP_BIT1, LOW);
    digitalWrite(ESP_BIT2, HIGH);
  }
}

void sendTriggerToESP() {
  if (currentDirection == DIR_ENTRY) {
    digitalWrite(ESP_TRIGGER, HIGH);
    delay(800);
    digitalWrite(ESP_TRIGGER, LOW);
  } else {
    digitalWrite(ESP_TRIGGER, HIGH);
    delay(4000);
    digitalWrite(ESP_TRIGGER, LOW);
  }
}

float readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duration == 0) {
    return -1;
  }

  return duration * 0.034 / 2;
}
