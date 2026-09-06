#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <math.h>
#include <time.h>

// =====================================================
//                    WIFI SETTINGS
// =====================================================

// Put your WiFi name here
const char* WIFI_SSID = "WIFI NAME";

// Put your WiFi password here
const char* WIFI_PASSWORD = "WIFI PASSWORD";

// IMPORTANT:
// Replace 192.168.1.7 with the IP address you got from
// running: hostname -I
//
// DO NOT use localhost here.
const char* BACKEND_URL =
  "http://IP_ADDRESS:8000/api/sensor-data";


// =====================================================
//                    PIN SETTINGS
// =====================================================

#define SDA_PIN 21
#define SCL_PIN 22

// Your sensor is MPU6500 at I2C address 0x68
#define MPU_ADDR 0x68

#define SOIL_SENSOR_PIN 34

#define BUZZER_PIN 25
#define LED_PIN 26


// =====================================================
//                  SENSOR THRESHOLDS
// =====================================================

// Alarm if tilt is greater than 15 degrees
const float TILT_THRESHOLD = 15.0;

// Alarm if moisture is greater than 80%
const float MOISTURE_THRESHOLD = 80.0;


// =====================================================
//                  MPU CALIBRATION
// =====================================================

// Your existing calibration values
const float ROLL_OFFSET = 0.3;
const float PITCH_OFFSET = -1.9;


// =====================================================
//              SOIL SENSOR CALIBRATION
// =====================================================

// Your existing calibration values
const int DRY_VALUE = 3000;
const int WET_VALUE = 1300;


// =====================================================
//                  LOCATION
// =====================================================

// Hardcoded latitude and longitude
const float LATITUDE = 28.6139;
const float LONGITUDE = 77.2090;


// =====================================================
//                     TIMING
// =====================================================

// Send data to backend every 5 seconds
const unsigned long SEND_INTERVAL = 5000;
unsigned long lastSendTime = 0;

// Print readings every 1 second
const unsigned long PRINT_INTERVAL = 1000;
unsigned long lastPrintTime = 0;


// =====================================================
//                  BUZZER SETTINGS
// =====================================================

// Frequency for passive buzzer
const int BUZZER_FREQUENCY = 2000;


// =====================================================
//                  SENSOR VARIABLES
// =====================================================

float accelX = 0;
float accelY = 0;
float accelZ = 0;

float roll = 0;
float pitch = 0;

float correctedRoll = 0;
float correctedPitch = 0;

float moisturePercent = 0;


// =====================================================
//                       ALERTS
// =====================================================

bool tiltAlert = false;
bool moistureAlert = false;
bool alarmActive = false;


// =====================================================
//                       SETUP
// =====================================================

void setup() {

  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=================================");
  Serial.println("     GIRI RAKSHAK ESP32");
  Serial.println("=================================");


  // ---------------------------------------------------
  // Pins
  // ---------------------------------------------------

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);


  // ---------------------------------------------------
  // Start I2C
  // ---------------------------------------------------

  Wire.begin(SDA_PIN, SCL_PIN);

  Serial.println("I2C started.");


  // ---------------------------------------------------
  // Wake up MPU6500
  // ---------------------------------------------------

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


  // ---------------------------------------------------
  // Check WHO_AM_I
  // ---------------------------------------------------

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


  // ---------------------------------------------------
  // Configure accelerometer
  // ±2g
  // ---------------------------------------------------

  Wire.beginTransmission(MPU_ADDR);

  Wire.write(0x1C);
  Wire.write(0x00);

  Wire.endTransmission();

  Serial.println("MPU6500 ready.");


  // ---------------------------------------------------
  // Connect to WiFi
  // ---------------------------------------------------

  Serial.println();
  Serial.println("Connecting to WiFi...");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long wifiStart = millis();

  while (
    WiFi.status() != WL_CONNECTED &&
    millis() - wifiStart < 10000
  ) {

    delay(250);

    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {

    Serial.println("WiFi connected!");

    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());

  } else {

    Serial.println("WiFi not connected.");
    Serial.println("Local alarms will still work.");
  }


  // ---------------------------------------------------
  // Configure time using NTP
  // ---------------------------------------------------

  // IST = UTC + 5:30 = 19800 seconds
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

  Serial.println("Alarm conditions:");
  Serial.println("Tilt     : > 15 degrees");
  Serial.println("Moisture : > 80 percent");
  Serial.println();

  Serial.print("Backend: ");
  Serial.println(BACKEND_URL);
}


// =====================================================
//                    READ MPU6500
// =====================================================

void readMPU() {

  // Tell MPU6500 that we want accelerometer data
  Wire.beginTransmission(MPU_ADDR);

  Wire.write(0x3B);

  Wire.endTransmission(false);

  // Request 6 bytes:
  // X high + X low
  // Y high + Y low
  // Z high + Z low
  Wire.requestFrom(MPU_ADDR, 6);

  if (Wire.available() == 6) {

    int16_t ax =
      (Wire.read() << 8) | Wire.read();

    int16_t ay =
      (Wire.read() << 8) | Wire.read();

    int16_t az =
      (Wire.read() << 8) | Wire.read();


    // ±2g = 16384 LSB/g
    accelX = ax / 16384.0;
    accelY = ay / 16384.0;
    accelZ = az / 16384.0;


    // -------------------------------------------------
    // Calculate roll
    // -------------------------------------------------

    roll =
      atan2(accelY, accelZ)
      * 180.0 / PI;


    // -------------------------------------------------
    // Calculate pitch
    // -------------------------------------------------

    pitch =
      atan2(
        -accelX,
        sqrt(
          accelY * accelY +
          accelZ * accelZ
        )
      )
      * 180.0 / PI;


    // -------------------------------------------------
    // Apply calibration
    // -------------------------------------------------

    correctedRoll =
      roll - ROLL_OFFSET;

    correctedPitch =
      pitch - PITCH_OFFSET;

  } else {

    Serial.println("ERROR: MPU data unavailable.");
  }
}


// =====================================================
//                  READ MOISTURE
// =====================================================

void readMoisture() {

  // Read analog value from soil sensor
  int rawValue =
    analogRead(SOIL_SENSOR_PIN);


  // Convert raw value to percentage
  //
  // DRY_VALUE  = 3000
  // WET_VALUE  = 1300
  //
  // Higher percentage = wetter soil

  moisturePercent =
    (
      (float)(DRY_VALUE - rawValue)
      /
      (DRY_VALUE - WET_VALUE)
    ) * 100.0;


  // Keep percentage between 0 and 100

  moisturePercent =
    constrain(
      moisturePercent,
      0,
      100
    );
}


// =====================================================
//                    CHECK ALERTS
// =====================================================

void checkAlerts() {

  // ---------------------------------------------------
  // Tilt alarm
  // ---------------------------------------------------

  tiltAlert =
    (
      fabs(correctedRoll) > TILT_THRESHOLD
    )
    ||
    (
      fabs(correctedPitch) > TILT_THRESHOLD
    );


  // ---------------------------------------------------
  // Moisture alarm
  // ---------------------------------------------------

  moistureAlert =
    moisturePercent > MOISTURE_THRESHOLD;


  // ---------------------------------------------------
  // Overall alarm
  // ---------------------------------------------------

  alarmActive =
    tiltAlert || moistureAlert;


  // ---------------------------------------------------
  // LED
  // ---------------------------------------------------

  if (alarmActive) {

    digitalWrite(
      LED_PIN,
      HIGH
    );

  } else {

    digitalWrite(
      LED_PIN,
      LOW
    );
  }


  // ---------------------------------------------------
  // Passive buzzer
  // ---------------------------------------------------

  if (alarmActive) {

    tone(
      BUZZER_PIN,
      BUZZER_FREQUENCY
    );

  } else {

    noTone(BUZZER_PIN);
  }
}


// =====================================================
//                 GET TIMESTAMP
// =====================================================

String getTimestamp() {

  struct tm timeinfo;

  // Try to get current time
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


  // If NTP time is not available,
  // return a fallback timestamp.
  //
  // Normally this should not happen after WiFi
  // and NTP synchronization.

  return "2026-01-01T00:00:00";
}


// =====================================================
//                 SEND DATA TO BACKEND
// =====================================================

void sendSensorData() {

  // ---------------------------------------------------
  // Check WiFi
  // ---------------------------------------------------

  if (WiFi.status() != WL_CONNECTED) {

    Serial.println(
      "WiFi not connected - data not sent."
    );

    return;
  }


  // ---------------------------------------------------
  // Create HTTP client
  // ---------------------------------------------------

  HTTPClient http;

  // Short timeout so network problems don't hold
  // the ESP32 for too long.
  http.setTimeout(2000);

  http.begin(BACKEND_URL);

  http.addHeader(
    "Content-Type",
    "application/json"
  );


  // ---------------------------------------------------
  // Calculate tilt value
  // ---------------------------------------------------

  float tiltDegrees =
    max(
      fabs(correctedRoll),
      fabs(correctedPitch)
    );


  // ---------------------------------------------------
  // Get timestamp
  // ---------------------------------------------------

  String timestamp =
    getTimestamp();


  // ---------------------------------------------------
  // Create JSON
  // ---------------------------------------------------

  String json = "{";

  json += "\"sensor_id\":\"ESP32_01\",";

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

  // No displacement sensor is currently connected,
  // so we send 0.0 for now.
  json += "\"displacement_cm\":0.0,";

  json += "\"timestamp\":\"";
  json += timestamp;
  json += "\"";

  json += "}";


  // ---------------------------------------------------
  // Print JSON for debugging
  // ---------------------------------------------------

  Serial.println();
  Serial.println("===== SENDING JSON =====");
  Serial.println(json);
  Serial.println("========================");


  // ---------------------------------------------------
  // Send POST request
  // ---------------------------------------------------

  int responseCode =
    http.POST(json);


  // ---------------------------------------------------
  // Check response
  // ---------------------------------------------------

  Serial.print("HTTP Response Code: ");
  Serial.println(responseCode);


  if (responseCode > 0) {

    String response =
      http.getString();

    Serial.print("Backend Response: ");
    Serial.println(response);

  } else {

    Serial.print("POST failed: ");
    Serial.println(
      http.errorToString(responseCode)
    );
  }


  // Close HTTP connection
  http.end();
}


// =====================================================
//                  PRINT READINGS
// =====================================================

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


// =====================================================
//                      LOOP
// =====================================================

void loop() {

  // ===================================================
  // IMPORTANT:
  // Sensors are read continuously.
  //
  // This means the LED and buzzer do NOT wait for
  // WiFi or the 5-second POST interval.
  // ===================================================

  readMPU();

  readMoisture();

  checkAlerts();


  // ---------------------------------------------------
  // Print sensor readings every 1 second
  // ---------------------------------------------------

  if (
    millis() - lastPrintTime >= PRINT_INTERVAL
  ) {

    lastPrintTime = millis();

    printReadings();
  }


  // ---------------------------------------------------
  // Send sensor data to backend every 5 seconds
  // ---------------------------------------------------

  if (
    millis() - lastSendTime >= SEND_INTERVAL
  ) {

    lastSendTime = millis();

    sendSensorData();
  }


  // Small delay
  delay(20);
}
