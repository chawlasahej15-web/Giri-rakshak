#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <math.h>
#include <time.h>

// ===================== CONFIG =====================

const char* WIFI_SSID = "Ayush Mahapatra";
const char* WIFI_PASSWORD = "ayush@2006";

// Replace YOUR_LAPTOP_IP with the current IP of the laptop
// running FastAPI. Do NOT use localhost.
// Example: http://172.22.202.89:8000/api/sensor-data
const char* BACKEND_URL =
  "http://172.22.202.89:8000/api/sensor-data";

const char* SENSOR_ID = "ESP32_01";

// Aizawl demo-node location; matches the frontend ESP marker.
const float LATITUDE = 23.739000;
const float LONGITUDE = 92.719000;

// ===================== PINS ======================

#define SDA_PIN 21
#define SCL_PIN 22
#define MPU_ADDR 0x68
#define SOIL_SENSOR_PIN 34
#define BUZZER_PIN 25
#define LED_PIN 26

// ===================== THRESHOLDS =================

const float TILT_THRESHOLD = 15.0;
const float MOISTURE_THRESHOLD = 80.0;

// ===================== CALIBRATION ================

const float ROLL_OFFSET = 0.3;
const float PITCH_OFFSET = -1.9;

const int DRY_VALUE = 3000;
const int WET_VALUE = 1300;

// ===================== TIMING =====================

const unsigned long SEND_INTERVAL = 5000;
const unsigned long PRINT_INTERVAL = 1000;
const unsigned long WIFI_RETRY_INTERVAL = 10000;

const int BUZZER_FREQUENCY = 2000;

unsigned long lastSendTime = 0;
unsigned long lastPrintTime = 0;
unsigned long lastWiFiRetryTime = 0;

// ===================== SENSOR STATE ==============

float accelX = 0.0;
float accelY = 0.0;
float accelZ = 0.0;

float roll = 0.0;
float pitch = 0.0;

float correctedRoll = 0.0;
float correctedPitch = 0.0;

float moisturePercent = 0.0;

bool tiltAlert = false;
bool moistureAlert = false;
bool alarmActive = false;

// ===================== WIFI ======================

bool connectWiFi() {
  Serial.println();
  Serial.println("Connecting to WiFi...");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - start < 15000) {
    delay(250);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected!");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
    return true;
  }

  Serial.println("WiFi connection failed.");
  Serial.println("Local buzzer/LED fail-safe remains active.");
  return false;
}

void maintainWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  if (millis() - lastWiFiRetryTime < WIFI_RETRY_INTERVAL) {
    return;
  }

  lastWiFiRetryTime = millis();
  Serial.println("WiFi disconnected. Retrying...");
  connectWiFi();
}

// ===================== SETUP =====================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=================================");
  Serial.println("       GIRI RAKSHAK ESP32");
  Serial.println("=================================");

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  Wire.begin(SDA_PIN, SCL_PIN);
  Serial.println("I2C started.");

  // Wake MPU6500.
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);

  byte result = Wire.endTransmission();

  if (result == 0) {
    Serial.println("MPU6500 found at 0x68.");
  } else {
    Serial.println("ERROR: MPU6500 not found!");
    Serial.print("I2C error code: ");
    Serial.println(result);
  }

  // WHO_AM_I.
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x75);
  Wire.endTransmission(false);

  Wire.requestFrom(MPU_ADDR, 1);

  if (Wire.available()) {
    byte whoAmI = Wire.read();

    Serial.print("WHO_AM_I = 0x");
    Serial.println(whoAmI, HEX);

    if (whoAmI == 0x70) {
      Serial.println("Confirmed: MPU6500");
    } else {
      Serial.println("WARNING: Unexpected MPU ID.");
    }
  }

  // Accelerometer ±2g.
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1C);
  Wire.write(0x00);
  Wire.endTransmission();

  Serial.println("MPU6500 ready.");

  connectWiFi();

  // IST = UTC + 5:30.
  configTime(
    19800,
    0,
    "pool.ntp.org",
    "time.nist.gov"
  );

  Serial.println("Time synchronization started.");

  Serial.println();
  Serial.println("=================================");
  Serial.println("          SYSTEM READY");
  Serial.println("=================================");
  Serial.println();

  Serial.print("Node ID   : ");
  Serial.println(SENSOR_ID);

  Serial.println("Location  : Aizawl demonstration node");

  Serial.println("Alarm conditions:");
  Serial.println("Tilt     : > 15 degrees");
  Serial.println("Moisture : > 80 percent");

  Serial.print("Backend: ");
  Serial.println(BACKEND_URL);
}

// ===================== MPU ========================

void readMPU() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);

  Wire.requestFrom(MPU_ADDR, 6);

  if (Wire.available() != 6) {
    Serial.println("ERROR: MPU data unavailable.");
    return;
  }

  int16_t ax = (Wire.read() << 8) | Wire.read();
  int16_t ay = (Wire.read() << 8) | Wire.read();
  int16_t az = (Wire.read() << 8) | Wire.read();

  // ±2g = 16384 LSB/g.
  accelX = ax / 16384.0;
  accelY = ay / 16384.0;
  accelZ = az / 16384.0;

  roll =
    atan2(accelY, accelZ) *
    180.0 / PI;

  pitch =
    atan2(
      -accelX,
      sqrt(
        accelY * accelY +
        accelZ * accelZ
      )
    ) *
    180.0 / PI;

  correctedRoll = roll - ROLL_OFFSET;
  correctedPitch = pitch - PITCH_OFFSET;
}

// ===================== MOISTURE ===================

void readMoisture() {
  int rawValue = analogRead(SOIL_SENSOR_PIN);

  moisturePercent =
    (
      (float)(DRY_VALUE - rawValue) /
      (DRY_VALUE - WET_VALUE)
    ) * 100.0;

  moisturePercent =
    constrain(
      moisturePercent,
      0.0,
      100.0
    );
}

// ===================== FAIL-SAFE ==================

void checkAlerts() {
  tiltAlert =
    fabs(correctedRoll) > TILT_THRESHOLD ||
    fabs(correctedPitch) > TILT_THRESHOLD;

  moistureAlert =
    moisturePercent > MOISTURE_THRESHOLD;

  alarmActive =
    tiltAlert || moistureAlert;

  // Local fail-safe outputs work independently of WiFi.
  digitalWrite(
    LED_PIN,
    alarmActive ? HIGH : LOW
  );

  if (alarmActive) {
    tone(
      BUZZER_PIN,
      BUZZER_FREQUENCY
    );
  } else {
    noTone(BUZZER_PIN);
  }
}

// ===================== TIME =======================

String getTimestamp() {
  struct tm timeinfo;

  if (getLocalTime(&timeinfo, 1000)) {
    char timestamp[30];

    strftime(
      timestamp,
      sizeof(timestamp),
      "%Y-%m-%dT%H:%M:%S",
      &timeinfo
    );

    return String(timestamp);
  }

  // Only a fallback if NTP is not ready yet.
  return "2026-01-01T00:00:00";
}

// ===================== BACKEND ===================

void sendSensorData() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(
      "WiFi not connected - data not sent."
    );
    return;
  }

  HTTPClient http;
  http.setTimeout(3000);
  http.begin(BACKEND_URL);

  http.addHeader(
    "Content-Type",
    "application/json"
  );

  float tiltDegrees =
    max(
      fabs(correctedRoll),
      fabs(correctedPitch)
    );

  String timestamp = getTimestamp();

  String json = "{";

  json += "\"sensor_id\":\"";
  json += SENSOR_ID;
  json += "\",";

  json += "\"lat\":";
  json += String(LATITUDE, 6);
  json += ",";

  json += "\"lon\":";
  json += String(LONGITUDE, 6);
  json += ",";

  json += "\"tilt_deg\":";
  json += String(tiltDegrees, 2);
  json += ",";

  json += "\"moisture_pct\":";
  json += String(moisturePercent, 1);
  json += ",";

  // No displacement sensor is connected.
  json += "\"displacement_cm\":0.0,";

  json += "\"timestamp\":\"";
  json += timestamp;
  json += "\"";

  json += "}";

  Serial.println();
  Serial.println("===== SENDING JSON =====");
  Serial.println(json);
  Serial.println("========================");

  int responseCode =
    http.POST(json);

  Serial.print("HTTP Response Code: ");
  Serial.println(responseCode);

  if (responseCode >= 200 &&
      responseCode < 300) {

    String response =
      http.getString();

    Serial.print("Backend Response: ");
    Serial.println(response);

  } else {

    Serial.print("POST failed: ");

    if (responseCode > 0) {
      Serial.println(
        http.getString()
      );
    } else {
      Serial.println(
        http.errorToString(
          responseCode
        )
      );
    }
  }

  http.end();
}

// ===================== SERIAL ====================

void printReadings() {
  Serial.println();
  Serial.println("---------------------------------");

  Serial.print("X        = ");
  Serial.print(accelX, 2);
  Serial.println(" g");

  Serial.print("Y        = ");
  Serial.print(accelY, 2);
  Serial.println(" g");

  Serial.print("Z        = ");
  Serial.print(accelZ, 2);
  Serial.println(" g");

  Serial.print("Roll     = ");
  Serial.print(correctedRoll, 1);
  Serial.println(" deg");

  Serial.print("Pitch    = ");
  Serial.print(correctedPitch, 1);
  Serial.println(" deg");

  Serial.print("Moisture = ");
  Serial.print(moisturePercent, 1);
  Serial.println(" %");

  Serial.print("Tilt Alert     = ");
  Serial.println(
    tiltAlert ? "YES" : "NO"
  );

  Serial.print("Moisture Alert = ");
  Serial.println(
    moistureAlert ? "YES" : "NO"
  );

  Serial.print("Alarm          = ");
  Serial.println(
    alarmActive ? "ON" : "OFF"
  );

  Serial.println("---------------------------------");
}

// ===================== LOOP ======================

void loop() {
  // These run continuously, independent of WiFi.
  readMPU();
  readMoisture();
  checkAlerts();

  if (
    millis() - lastPrintTime >=
    PRINT_INTERVAL
  ) {
    lastPrintTime = millis();
    printReadings();
  }

  maintainWiFi();

  if (
    millis() - lastSendTime >=
    SEND_INTERVAL
  ) {
    lastSendTime = millis();
    sendSensorData();
  }

  delay(20);
}
