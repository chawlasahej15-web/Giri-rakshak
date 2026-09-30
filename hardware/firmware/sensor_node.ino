#include <Wire.h>
#include <math.h>
#include <Adafruit_BMP280.h>
#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>


/*
================================================================
                     GIRI RAKSHAK ESP32
                     MASTER FIRMWARE V10
================================================================

SENSORS
-------
MPU6500
  -> tilt
  -> acceleration
  -> vibration

Soil moisture
  -> moisture %
  -> moisture change
  -> moisture rate

HC-SR04
  -> distance
  -> displacement proxy
  -> distance change/rate

BMP280
  -> pressure
  -> temperature/context

DHT22
  -> temperature
  -> humidity
  -> DISPLAY/CONTEXT ONLY
  -> NOT used for alert triggering

RAIN
  -> not physically connected yet
  -> backend sends null

IMPORTANT
---------
- MPU6500 is handled with RAW Wire/I2C.
- NO MPU6500 library.
- Absolute 15 degree tilt is NOT an alert.
- Current physical orientation becomes baseline.
- Small natural fluctuations are allowed.
- Alert uses change/trend, not absolute angle.
- Buzzer is one-shot per alert event.
- LED remains ON while alert is active.
- Alert can recover at a NEW stable physical position.
- Recovery starts silent recalibration.
- Calibration has NO visible alert.
- If calibration fails, old alert is restored silently.
- If condition gets worse during recalibration,
  calibration is aborted and alert escalates.
- Local alert system works WITHOUT Wi-Fi.
================================================================
*/


// ================================================================
//                          PIN CONFIG
// ================================================================

#define SDA_PIN 21
#define SCL_PIN 22

#define MPU_ADDR 0x68

#define SOIL_PIN 34

#define BUZZER_PIN 25
#define LED_PIN 26

#define DHT_PIN 4
#define DHT_TYPE DHT22

#define HC_TRIG_PIN 27
#define HC_ECHO_PIN 18


// ================================================================
//                      OPTIONAL BACKEND
// ================================================================
//
// BACKEND SENDING ENABLED FOR LIVE ESP32 -> LAPTOP TESTING.
// Keep the Wi-Fi credentials below set to the same values that
// already work on your current hardware.

const bool SEND_TO_BACKEND = true;

const char* WIFI_SSID =
  "Priyanshu";

const char* WIFI_PASSWORD =
  "hello123";

const char* BACKEND_URL =
  "http://192.168.137.17:8000/api/sensor-data";

const char* SENSOR_ID =
  "ESP32_01";

const float SENSOR_LATITUDE =
  23.739000f;

const float SENSOR_LONGITUDE =
  92.719000f;


// ================================================================
//                     SENSOR CALIBRATION
// ================================================================

// Soil ADC calibration.
const int SOIL_DRY_VALUE =
  3000;

const int SOIL_WET_VALUE =
  1300;


// Existing MPU offsets from your tested firmware.
const float ROLL_OFFSET =
  0.3f;

const float PITCH_OFFSET =
  -1.9f;


// ================================================================
//                           TIMING
// ================================================================

const uint32_t FEATURE_INTERVAL_MS =
  1000;

const uint32_t ENVIRONMENT_INTERVAL_MS =
  2000;

const uint32_t DISTANCE_INTERVAL_MS =
  250;

const uint32_t SERIAL_INTERVAL_MS =
  1000;

const uint32_t BACKEND_INTERVAL_MS =
  5000;


// ---------------------------------------------------------------
// BASELINE
// ---------------------------------------------------------------

// User requested short calibration.
const uint32_t BASELINE_DURATION_MS =
  10000;


// Once an alert stops changing,
// 3 seconds of genuine stability starts recalibration.
const uint32_t STABLE_GATE_MS =
  3000;


// Three consecutive abnormal feature windows.
const int ALERT_PERSISTENCE_WINDOWS =
  3;


// ================================================================
//                       MPU FILTERING
// ================================================================

// Filter for displayed / processed tilt.
const float TILT_FILTER_ALPHA =
  0.20f;


// About 60 seconds.
const int TILT_LONG_HISTORY =
  61;


// About 10 seconds.
const int SHORT_HISTORY =
  11;


// Small recent tilt movement below this value is treated as sensor
// fluctuation for RATE purposes only. The normal change/sudden
// alert thresholds below remain unchanged.
const float TILT_RATE_NOISE_FLOOR_10S =
  0.02f;


// ================================================================
//                    TILT CHANGE THRESHOLDS
// ================================================================
//
// These are prototype engineering gates.
// They are NOT universal geotechnical limits.
//
// Absolute 15-degree angle is deliberately NOT used.

const float TILT_WATCH_CHANGE =
  0.50f;

const float TILT_WARNING_CHANGE =
  1.00f;

const float TILT_CRITICAL_CHANGE =
  2.00f;


// Long-term trend thresholds.
const float TILT_WATCH_RATE =
  5.0f;

const float TILT_WARNING_RATE =
  15.0f;

const float TILT_CRITICAL_RATE =
  30.0f;


// Sudden movement over ~10 seconds.
const float TILT_WATCH_SUDDEN =
  0.50f;

const float TILT_WARNING_SUDDEN =
  0.75f;

const float TILT_CRITICAL_SUDDEN =
  1.50f;


// ================================================================
//                  MOVEMENT / VIBRATION
// ================================================================

const float MOVEMENT_WATCH_RATIO =
  3.0f;

const float MOVEMENT_WARNING_RATIO =
  5.0f;

const float MOVEMENT_CRITICAL_RATIO =
  8.0f;


// ================================================================
//                        SOIL
// ================================================================

const float SOIL_WATCH_CHANGE =
  2.0f;

const float SOIL_WARNING_CHANGE =
  4.0f;

const float SOIL_CRITICAL_CHANGE =
  8.0f;


const float SOIL_WATCH_RATE =
  3.0f;

const float SOIL_WARNING_RATE =
  8.0f;

const float SOIL_CRITICAL_RATE =
  15.0f;


// ================================================================
//                       DISTANCE
// ================================================================

const float DIST_WATCH_CHANGE =
  0.75f;

const float DIST_WARNING_CHANGE =
  1.50f;

const float DIST_CRITICAL_CHANGE =
  3.00f;


const float DIST_WATCH_RATE =
  1.5f;

const float DIST_WARNING_RATE =
  3.0f;

const float DIST_CRITICAL_RATE =
  6.0f;


// ================================================================
//                CALIBRATION STABILITY LIMITS
// ================================================================
//
// SMALL FLUCTUATIONS ARE ALLOWED.
//
// MPU test:
// normal variation was around few hundredths of a degree.

const float CAL_TILT_STD_MAX =
  0.20f;

const float CAL_TILT_RANGE_MAX =
  0.60f;


const float CAL_SOIL_STD_MAX =
  3.0f;

const float CAL_SOIL_RANGE_MAX =
  8.0f;


const float CAL_DISTANCE_STD_MAX =
  5.0f;

const float CAL_DISTANCE_RANGE_MAX =
  15.0f;


const float CAL_VIBRATION_STD_MAX =
  0.01f;


// ================================================================
//                           BUZZER
// ================================================================

const uint16_t BUZZER_FREQUENCY =
  2000;

const uint32_t BUZZER_WATCH_MS =
  2000;

const uint32_t BUZZER_WARNING_MS =
  3000;

const uint32_t BUZZER_CRITICAL_MS =
  5000;


uint32_t buzzerUntil =
  0;


bool buzzerTriggeredForEvent =
  false;


// ================================================================
//                         OBJECTS
// ================================================================

Adafruit_BMP280 bmp;

DHT dht(
  DHT_PIN,
  DHT_TYPE
);


bool bmpAvailable =
  false;


// ================================================================
//                       RAW SENSOR VALUES
// ================================================================

// MPU
float accelX =
  0.0f;

float accelY =
  0.0f;

float accelZ =
  0.0f;

float accelMagnitude =
  0.0f;

float previousAccelMagnitude =
  NAN;

float accelMagnitudeJump =
  0.0f;


// Tilt
float rawTiltDegrees =
  0.0f;

float filteredTiltDegrees =
  0.0f;

bool tiltFilterReady =
  false;


// Vibration
float vibrationRms =
  0.0f;


// Soil
float soilMoisture =
  0.0f;


// Distance
float distanceCm =
  NAN;


// Environment
float pressureHpa =
  NAN;

float bmpTemperatureC =
  NAN;

float dhtTemperatureC =
  NAN;

float humidityPercent =
  NAN;


// ================================================================
//                        BASELINES
// ================================================================

float baselineTilt =
  NAN;

float baselineTiltStd =
  0.02f;


float baselineSoil =
  NAN;

float baselineSoilStd =
  0.25f;


float baselineDistance =
  NAN;

float baselineDistanceStd =
  1.0f;


float baselineVibrationRms =
  0.0001f;

float baselineVibrationStd =
  0.0001f;


bool hasAcceptedBaseline =
  false;


// ================================================================
//                       DERIVED FEATURES
// ================================================================

// Tilt
float tiltChange =
  0.0f;

float tiltRateDph =
  0.0f;

float tiltSuddenChange10s =
  0.0f;


// Soil
float soilChange =
  0.0f;

float soilRatePph =
  0.0f;

float soilChange10s =
  0.0f;


// Distance
float distanceChange =
  0.0f;

float distanceRateCmh =
  0.0f;

float distanceChange10s =
  0.0f;


// Movement
float movementRatio =
  0.0f;


// ================================================================
//                       INDICATORS
// ================================================================

bool tiltIndicator =
  false;

bool movementIndicator =
  false;

bool soilIndicator =
  false;

bool distanceIndicator =
  false;


// ================================================================
//                     SAMPLE ACCUMULATORS
// ================================================================

// MPU
float accelSumX =
  0.0f;

float accelSumY =
  0.0f;

float accelSumZ =
  0.0f;

float dynamicAccelSquareSum =
  0.0f;

uint32_t accelSamples =
  0;


// Soil
float soilSum =
  0.0f;

uint32_t soilSamples =
  0;


// Distance
float distanceSum =
  0.0f;

uint32_t distanceSamples =
  0;


// ================================================================
//                           HISTORIES
// ================================================================

// Tilt
float tiltLongHistory[
  TILT_LONG_HISTORY
];

float tiltShortHistory[
  SHORT_HISTORY
];


// Soil
float soilLongHistory[
  TILT_LONG_HISTORY
];

float soilShortHistory[
  SHORT_HISTORY
];


// Distance
float distanceLongHistory[
  TILT_LONG_HISTORY
];

float distanceShortHistory[
  SHORT_HISTORY
];


int tiltLongCount =
  0;

int tiltLongIndex =
  0;


int tiltShortCount =
  0;

int tiltShortIndex =
  0;


int soilLongCount =
  0;

int soilLongIndex =
  0;


int soilShortCount =
  0;

int soilShortIndex =
  0;


int distanceLongCount =
  0;

int distanceLongIndex =
  0;


int distanceShortCount =
  0;

int distanceShortIndex =
  0;


// ================================================================
//                     CALIBRATION BUFFERS
// ================================================================

const int MAX_BASELINE_SAMPLES =
  12;

// A 10-second calibration at the 1-second feature cadence should
// normally produce 10 samples. Accept a run only when at least 9
// valid windows were collected.
const int MIN_BASELINE_SAMPLES =
  9;


float candidateTilt[
  MAX_BASELINE_SAMPLES
];

float candidateSoil[
  MAX_BASELINE_SAMPLES
];

float candidateDistance[
  MAX_BASELINE_SAMPLES
];

float candidateVibration[
  MAX_BASELINE_SAMPLES
];


int candidateCount =
  0;


// ================================================================
//                           STATES
// ================================================================

enum SystemState {

  STATE_CALIBRATING,

  STATE_NORMAL,

  STATE_ALERT,

  STATE_RECALIBRATING
};


enum AlertLevel {

  ALERT_NONE = 0,

  ALERT_WATCH = 1,

  ALERT_WARNING = 2,

  ALERT_CRITICAL = 3
};


SystemState systemState =
  STATE_CALIBRATING;


AlertLevel currentAlert =
  ALERT_NONE;


// Previous alert remains stored during recalibration.
AlertLevel retainedAlert =
  ALERT_NONE;


// ================================================================
//                         TIMERS
// ================================================================

uint32_t calibrationStartTime =
  0;

uint32_t lastFeatureTime =
  0;

uint32_t lastEnvironmentTime =
  0;

uint32_t lastDistanceTime =
  0;

uint32_t lastSerialTime =
  0;

uint32_t lastBackendTime =
  0;


int stableGateCount =
  0;

int recalibrationWorseCount =
  0;


// ================================================================
//                         STATE NAMES
// ================================================================

const char* getStateName() {

  if (
    systemState
    ==
    STATE_CALIBRATING
  ) {

    return "CALIBRATING";
  }


  if (
    systemState
    ==
    STATE_NORMAL
  ) {

    return "NORMAL";
  }


  if (
    systemState
    ==
    STATE_ALERT
  ) {

    return "ALERT";
  }


  if (
    systemState
    ==
    STATE_RECALIBRATING
  ) {

    return "RECALIBRATING";
  }


  return "UNKNOWN";
}


const char* getAlertName(
  AlertLevel level
) {

  if (
    level
    ==
    ALERT_NONE
  ) {

    return "NORMAL";
  }


  if (
    level
    ==
    ALERT_WATCH
  ) {

    return "WATCH";
  }


  if (
    level
    ==
    ALERT_WARNING
  ) {

    return "WARNING";
  }


  if (
    level
    ==
    ALERT_CRITICAL
  ) {

    return "CRITICAL";
  }


  return "UNKNOWN";
}


// ================================================================
//                         STATISTICS
// ================================================================

float meanOf(
  float* values,
  int count
) {

  float sum =
    0.0f;

  int n =
    0;


  for (
    int i = 0;
    i < count;
    i++
  ) {

    if (
      isfinite(
        values[i]
      )
    ) {

      sum +=
        values[i];

      n++;
    }
  }


  if (
    n == 0
  ) {

    return NAN;
  }


  return sum /
         n;
}


float medianOf(
  float* values,
  int count
) {

  float work[
    MAX_BASELINE_SAMPLES
  ];


  int n =
    0;


  for (
    int i = 0;
    i < count
      &&
      i < MAX_BASELINE_SAMPLES;
    i++
  ) {

    if (
      isfinite(
        values[i]
      )
    ) {

      work[n++] =
        values[i];
    }
  }


  if (
    n == 0
  ) {

    return NAN;
  }


  for (
    int i = 1;
    i < n;
    i++
  ) {

    float key =
      work[i];

    int j =
      i - 1;


    while (
      j >= 0
      &&
      work[j] > key
    ) {

      work[j + 1] =
        work[j];

      j--;
    }


    work[j + 1] =
      key;
  }


  if (
    n % 2 == 0
  ) {

    return (
      work[
        (n / 2) - 1
      ]
      +
      work[
        n / 2
      ]
    )
    /
    2.0f;
  }


  return work[
    n / 2
  ];
}


float standardDeviation(
  float* values,
  int count
) {

  float mean =
    meanOf(
      values,
      count
    );


  if (
    !isfinite(
      mean
    )
  ) {

    return NAN;
  }


  float sum =
    0.0f;

  int n =
    0;


  for (
    int i = 0;
    i < count;
    i++
  ) {

    if (
      isfinite(
        values[i]
      )
    ) {

      float d =
        values[i]
        -
        mean;

      sum +=
        d * d;

      n++;
    }
  }


  if (
    n < 2
  ) {

    return 0.0f;
  }


  return sqrtf(
    sum
    /
    (
      n - 1
    )
  );
}


float rangeOf(
  float* values,
  int count
) {

  float minValue =
    INFINITY;

  float maxValue =
    -INFINITY;

  int n =
    0;


  for (
    int i = 0;
    i < count;
    i++
  ) {

    if (
      isfinite(
        values[i]
      )
    ) {

      minValue =
        min(
          minValue,
          values[i]
        );

      maxValue =
        max(
          maxValue,
          values[i]
        );

      n++;
    }
  }


  if (
    n == 0
  ) {

    return NAN;
  }


  return maxValue -
         minValue;
}


// ================================================================
//                     RESET HISTORIES
// ================================================================

void resetHistories() {

  tiltLongCount =
    0;

  tiltLongIndex =
    0;


  tiltShortCount =
    0;

  tiltShortIndex =
    0;


  soilLongCount =
    0;

  soilLongIndex =
    0;


  soilShortCount =
    0;

  soilShortIndex =
    0;


  distanceLongCount =
    0;

  distanceLongIndex =
    0;


  distanceShortCount =
    0;

  distanceShortIndex =
    0;
}


// ================================================================
//                       MPU6500 RAW
// ================================================================

void mpuWriteByte(
  uint8_t reg,
  uint8_t value
) {

  Wire.beginTransmission(
    MPU_ADDR
  );

  Wire.write(
    reg
  );

  Wire.write(
    value
  );

  Wire.endTransmission();
}


bool readMPURaw(
  float& x,
  float& y,
  float& z
) {

  Wire.beginTransmission(
    MPU_ADDR
  );

  Wire.write(
    0x3B
  );


  if (
    Wire.endTransmission(
      false
    )
    !=
    0
  ) {

    return false;
  }


  Wire.requestFrom(
    MPU_ADDR,
    6
  );


  if (
    Wire.available()
    !=
    6
  ) {

    return false;
  }


  int16_t rawX =
    (
      Wire.read()
      <<
      8
    )
    |
    Wire.read();


  int16_t rawY =
    (
      Wire.read()
      <<
      8
    )
    |
    Wire.read();


  int16_t rawZ =
    (
      Wire.read()
      <<
      8
    )
    |
    Wire.read();


  // ±2g
  x =
    rawX
    /
    16384.0f;


  y =
    rawY
    /
    16384.0f;


  z =
    rawZ
    /
    16384.0f;


  return true;
}


void sampleMPU() {

  float x;
  float y;
  float z;


  if (
    !readMPURaw(
      x,
      y,
      z
    )
  ) {

    return;
  }


  float magnitude =
    sqrtf(
      x * x
      +
      y * y
      +
      z * z
    );


  float dynamic =
    fabsf(
      magnitude
      -
      1.0f
    );


  accelSumX +=
    x;

  accelSumY +=
    y;

  accelSumZ +=
    z;


  dynamicAccelSquareSum +=
    dynamic
    *
    dynamic;


  accelSamples++;
}


// ================================================================
//                         SOIL
// ================================================================

void sampleSoil() {

  int raw =
    analogRead(
      SOIL_PIN
    );


  float moisture =
    (
      (
        float
      )(
        SOIL_DRY_VALUE
        -
        raw
      )
      /
      (
        SOIL_DRY_VALUE
        -
        SOIL_WET_VALUE
      )
    )
    *
    100.0f;


  moisture =
    constrain(
      moisture,
      0.0f,
      100.0f
    );


  soilSum +=
    moisture;


  soilSamples++;
}


// ================================================================
//                       HC-SR04 RAW
// ================================================================

float readDistanceRaw() {

  digitalWrite(
    HC_TRIG_PIN,
    LOW
  );

  delayMicroseconds(
    2
  );


  digitalWrite(
    HC_TRIG_PIN,
    HIGH
  );

  delayMicroseconds(
    10
  );


  digitalWrite(
    HC_TRIG_PIN,
    LOW
  );


  uint32_t duration =
    pulseIn(
      HC_ECHO_PIN,
      HIGH,
      30000
    );


  if (
    duration == 0
  ) {

    return NAN;
  }


  float d =
    duration
    *
    0.0343f
    /
    2.0f;


  if (
    d < 2.0f
    ||
    d > 400.0f
  ) {

    return NAN;
  }


  return d;
}


void sampleDistance() {

  float d =
    readDistanceRaw();


  if (
    !isfinite(
      d
    )
  ) {

    return;
  }


  distanceSum +=
    d;


  distanceSamples++;
}


// ================================================================
//                     BMP280 + DHT22
// ================================================================

void readEnvironment() {

  if (
    bmpAvailable
  ) {

    float pressure =
      bmp.readPressure();


    float temperature =
      bmp.readTemperature();


    if (
      isfinite(
        pressure
      )
    ) {

      pressureHpa =
        pressure
        /
        100.0f;
    }


    if (
      isfinite(
        temperature
      )
    ) {

      bmpTemperatureC =
        temperature;
    }
  }


  float humidity =
    dht.readHumidity();


  float temperature =
    dht.readTemperature();


  if (
    isfinite(
      humidity
    )
  ) {

    humidityPercent =
      humidity;
  }


  if (
    isfinite(
      temperature
    )
  ) {

    dhtTemperatureC =
      temperature;
  }
}


// ================================================================
//                    HISTORY STORAGE
// ================================================================

void storeHistories() {

  // --------------------------------------------------------------
  // Tilt long
  // --------------------------------------------------------------

  tiltLongHistory[
    tiltLongIndex
  ] =
    filteredTiltDegrees;


  tiltLongIndex =
    (
      tiltLongIndex
      +
      1
    )
    %
    TILT_LONG_HISTORY;


  if (
    tiltLongCount
    <
    TILT_LONG_HISTORY
  ) {

    tiltLongCount++;
  }


  // --------------------------------------------------------------
  // Tilt short
  // --------------------------------------------------------------

  tiltShortHistory[
    tiltShortIndex
  ] =
    filteredTiltDegrees;


  tiltShortIndex =
    (
      tiltShortIndex
      +
      1
    )
    %
    SHORT_HISTORY;


  if (
    tiltShortCount
    <
    SHORT_HISTORY
  ) {

    tiltShortCount++;
  }


  // --------------------------------------------------------------
  // Soil long
  // --------------------------------------------------------------

  soilLongHistory[
    soilLongIndex
  ] =
    soilMoisture;


  soilLongIndex =
    (
      soilLongIndex
      +
      1
    )
    %
    TILT_LONG_HISTORY;


  if (
    soilLongCount
    <
    TILT_LONG_HISTORY
  ) {

    soilLongCount++;
  }


  // --------------------------------------------------------------
  // Soil short
  // --------------------------------------------------------------

  soilShortHistory[
    soilShortIndex
  ] =
    soilMoisture;


  soilShortIndex =
    (
      soilShortIndex
      +
      1
    )
    %
    SHORT_HISTORY;


  if (
    soilShortCount
    <
    SHORT_HISTORY
  ) {

    soilShortCount++;
  }


  // --------------------------------------------------------------
  // Distance long
  // --------------------------------------------------------------

  distanceLongHistory[
    distanceLongIndex
  ] =
    distanceCm;


  distanceLongIndex =
    (
      distanceLongIndex
      +
      1
    )
    %
    TILT_LONG_HISTORY;


  if (
    distanceLongCount
    <
    TILT_LONG_HISTORY
  ) {

    distanceLongCount++;
  }


  // --------------------------------------------------------------
  // Distance short
  // --------------------------------------------------------------

  distanceShortHistory[
    distanceShortIndex
  ] =
    distanceCm;


  distanceShortIndex =
    (
      distanceShortIndex
      +
      1
    )
    %
    SHORT_HISTORY;


  if (
    distanceShortCount
    <
    SHORT_HISTORY
  ) {

    distanceShortCount++;
  }
}


// ================================================================
//                 60-SECOND TILT REGRESSION
// ================================================================

float calculateTiltRate() {

  if (
    tiltLongCount
    <
    TILT_LONG_HISTORY
  ) {

    return 0.0f;
  }


  const int n =
    TILT_LONG_HISTORY;


  float sumX =
    0.0f;

  float sumY =
    0.0f;

  float sumXY =
    0.0f;

  float sumXX =
    0.0f;


  for (
    int i = 0;
    i < n;
    i++
  ) {

    int idx =
      (
        tiltLongIndex
        +
        i
      )
      %
      TILT_LONG_HISTORY;


    float y =
      tiltLongHistory[
        idx
      ];


    if (
      !isfinite(
        y
      )
    ) {

      return 0.0f;
    }


    float x =
      i;


    sumX +=
      x;

    sumY +=
      y;

    sumXY +=
      x * y;

    sumXX +=
      x * x;
  }


  float denominator =
    (
      n * sumXX
    )
    -
    (
      sumX * sumX
    );


  if (
    fabsf(
      denominator
    )
    <
    0.000001f
  ) {

    return 0.0f;
  }


  float slope =
    (
      (
        n * sumXY
      )
      -
      (
        sumX * sumY
      )
    )
    /
    denominator;


  return
    slope
    *
    3600.0f;
}


// ================================================================
//                       FEATURE UPDATE
// ================================================================

void updateFeatures() {

  // --------------------------------------------------------------
  // MPU one-second average
  // --------------------------------------------------------------

  if (
    accelSamples
    >
    0
  ) {

    float avgX =
      accelSumX
      /
      accelSamples;


    float avgY =
      accelSumY
      /
      accelSamples;


    float avgZ =
      accelSumZ
      /
      accelSamples;


    accelX =
      avgX;


    accelY =
      avgY;


    accelZ =
      avgZ;


    accelMagnitude =
      sqrtf(
        avgX * avgX
        +
        avgY * avgY
        +
        avgZ * avgZ
      );


    if (
      isfinite(
        previousAccelMagnitude
      )
    ) {

      accelMagnitudeJump =
        fabsf(
          accelMagnitude
          -
          previousAccelMagnitude
        );

    } else {

      accelMagnitudeJump =
        0.0f;
    }


    previousAccelMagnitude =
      accelMagnitude;


    // ------------------------------------------------------------
    // Roll / pitch
    // ------------------------------------------------------------

    float roll =
      atan2f(
        avgY,
        avgZ
      )
      *
      180.0f
      /
      PI;


    float pitch =
      atan2f(
        -avgX,
        sqrtf(
          avgY * avgY
          +
          avgZ * avgZ
        )
      )
      *
      180.0f
      /
      PI;


    float correctedRoll =
      roll
      -
      ROLL_OFFSET;


    float correctedPitch =
      pitch
      -
      PITCH_OFFSET;


    rawTiltDegrees =
      max(
        fabsf(
          correctedRoll
        ),
        fabsf(
          correctedPitch
        )
      );


    // ------------------------------------------------------------
    // Tilt smoothing
    // ------------------------------------------------------------

    if (
      !tiltFilterReady
    ) {

      filteredTiltDegrees =
        rawTiltDegrees;


      tiltFilterReady =
        true;

    } else {

      filteredTiltDegrees =
        (
          TILT_FILTER_ALPHA
          *
          rawTiltDegrees
        )
        +
        (
          (
            1.0f
            -
            TILT_FILTER_ALPHA
          )
          *
          filteredTiltDegrees
        );
    }


    // ------------------------------------------------------------
    // Vibration
    // ------------------------------------------------------------

    vibrationRms =
      sqrtf(
        dynamicAccelSquareSum
        /
        accelSamples
      );
  }


  // --------------------------------------------------------------
  // Soil
  // --------------------------------------------------------------

  if (
    soilSamples
    >
    0
  ) {

    soilMoisture =
      soilSum
      /
      soilSamples;
  }


  // --------------------------------------------------------------
  // Distance
  // --------------------------------------------------------------

  if (
    distanceSamples
    >
    0
  ) {

    distanceCm =
      distanceSum
      /
      distanceSamples;
  }


  // --------------------------------------------------------------
  // Reset accumulators
  // --------------------------------------------------------------

  accelSumX =
    0.0f;

  accelSumY =
    0.0f;

  accelSumZ =
    0.0f;

  dynamicAccelSquareSum =
    0.0f;

  accelSamples =
    0;


  soilSum =
    0.0f;

  soilSamples =
    0;


  distanceSum =
    0.0f;

  distanceSamples =
    0;


  // --------------------------------------------------------------
  // Store current values
  // --------------------------------------------------------------

  storeHistories();


  // --------------------------------------------------------------
  // Tilt
  // --------------------------------------------------------------

  if (
    hasAcceptedBaseline
  ) {

    tiltChange =
      filteredTiltDegrees
      -
      baselineTilt;

  } else {

    tiltChange =
      0.0f;
  }


  // --------------------------------------------------------------
  // Recent ~10-second tilt change
  // --------------------------------------------------------------

  if (
    tiltShortCount
    >=
    SHORT_HISTORY
  ) {

    float oldestTilt =
      tiltShortHistory[
        tiltShortIndex
      ];


    tiltSuddenChange10s =
      filteredTiltDegrees
      -
      oldestTilt;

  } else {

    tiltSuddenChange10s =
      0.0f;
  }


  // --------------------------------------------------------------
  // Tilt rate with recent-fluctuation protection
  // --------------------------------------------------------------
  //
  // The original 60-second regression is still used for genuine
  // sustained movement, but old movement must not survive as a huge
  // rate after the sensor has settled. When the latest ~10 seconds
  // are within the small noise floor, the reported trend is zero.

  tiltRateDph =
    calculateTiltRate();


  if (
    tiltShortCount
    >=
    SHORT_HISTORY
    &&
    fabsf(
      tiltSuddenChange10s
    )
    <
    TILT_RATE_NOISE_FLOOR_10S
  ) {

    tiltRateDph =
      0.0f;
  }


  // --------------------------------------------------------------
  // Soil
  // --------------------------------------------------------------

  if (
    hasAcceptedBaseline
  ) {

    soilChange =
      soilMoisture
      -
      baselineSoil;

  } else {

    soilChange =
      0.0f;
  }


  if (
    soilLongCount
    >=
    TILT_LONG_HISTORY
  ) {

    float oldSoil =
      soilLongHistory[
        soilLongIndex
      ];


    if (
      isfinite(
        oldSoil
      )
    ) {

      float longChange =
        soilMoisture
        -
        oldSoil;


      soilRatePph =
        longChange
        *
        60.0f;

    } else {

      soilRatePph =
        0.0f;
    }

  } else {

    soilRatePph =
      0.0f;
  }


  if (
    soilShortCount
    >=
    SHORT_HISTORY
  ) {

    float oldSoilShort =
      soilShortHistory[
        soilShortIndex
      ];


    if (
      isfinite(
        oldSoilShort
      )
    ) {

      soilChange10s =
        soilMoisture
        -
        oldSoilShort;

    } else {

      soilChange10s =
        0.0f;
    }

  } else {

    soilChange10s =
      0.0f;
  }


  // --------------------------------------------------------------
  // Distance
  // --------------------------------------------------------------

  if (
    hasAcceptedBaseline
    &&
    isfinite(
      distanceCm
    )
    &&
    isfinite(
      baselineDistance
    )
  ) {

    distanceChange =
      distanceCm
      -
      baselineDistance;

  } else {

    distanceChange =
      0.0f;
  }


  if (
    distanceLongCount
    >=
    TILT_LONG_HISTORY
  ) {

    float oldDistance =
      distanceLongHistory[
        distanceLongIndex
      ];


    if (
      isfinite(
        oldDistance
      )
      &&
      isfinite(
        distanceCm
      )
    ) {

      float longDistanceChange =
        distanceCm
        -
        oldDistance;


      distanceRateCmh =
        longDistanceChange
        *
        60.0f;

    } else {

      distanceRateCmh =
        0.0f;
    }

  } else {

    distanceRateCmh =
      0.0f;
  }


  if (
    distanceShortCount
    >=
    SHORT_HISTORY
  ) {

    float oldShortDistance =
      distanceShortHistory[
        distanceShortIndex
      ];


    if (
      isfinite(
        oldShortDistance
      )
      &&
      isfinite(
        distanceCm
      )
    ) {

      distanceChange10s =
        distanceCm
        -
        oldShortDistance;

    } else {

      distanceChange10s =
        0.0f;
    }

  } else {

    distanceChange10s =
      0.0f;
  }


  // --------------------------------------------------------------
  // Movement ratio
  // --------------------------------------------------------------

  if (
    hasAcceptedBaseline
  ) {

    movementRatio =
      vibrationRms
      /
      max(
        baselineVibrationRms,
        0.0001f
      );

  } else {

    movementRatio =
      0.0f;
  }
}


// ================================================================
//                     CANDIDATE BUFFER
// ================================================================

void resetCandidateBuffers() {

  candidateCount =
    0;


  for (
    int i = 0;
    i < MAX_BASELINE_SAMPLES;
    i++
  ) {

    candidateTilt[i] =
      NAN;

    candidateSoil[i] =
      NAN;

    candidateDistance[i] =
      NAN;

    candidateVibration[i] =
      NAN;
  }
}


void addCandidateSample() {

  if (
    candidateCount
    >=
    MAX_BASELINE_SAMPLES
  ) {

    return;
  }


  candidateTilt[
    candidateCount
  ] =
    filteredTiltDegrees;


  candidateSoil[
    candidateCount
  ] =
    soilMoisture;


  candidateDistance[
    candidateCount
  ] =
    distanceCm;


  candidateVibration[
    candidateCount
  ] =
    vibrationRms;


  candidateCount++;
}


// ================================================================
//                    BASELINE STABILITY
// ================================================================
//
// The important rule:
//
// EXACT CONSTANT VALUE IS NOT REQUIRED.
//
// Example:
//
// 22.40
// 22.44
// 22.41
// 22.47
// 22.43
//
// => acceptable.

bool candidateIsStable() {

  if (
    candidateCount
    <
    MIN_BASELINE_SAMPLES
  ) {

    return false;
  }


  // --------------------------------------------------------------
  // Tilt
  // --------------------------------------------------------------

  float tiltStd =
    standardDeviation(
      candidateTilt,
      candidateCount
    );


  float tiltRange =
    rangeOf(
      candidateTilt,
      candidateCount
    );


  if (
    !isfinite(
      tiltStd
    )
    ||
    !isfinite(
      tiltRange
    )
  ) {

    Serial.println(
      "Calibration reject: invalid tilt."
    );


    return false;
  }


  if (
    tiltStd
    >
    CAL_TILT_STD_MAX
    ||
    tiltRange
    >
    CAL_TILT_RANGE_MAX
  ) {

    Serial.print(
      "Calibration waiting: tilt std="
    );


    Serial.print(
      tiltStd,
      4
    );


    Serial.print(
      " range="
    );


    Serial.println(
      tiltRange,
      4
    );


    return false;
  }


  // --------------------------------------------------------------
  // Soil
  // --------------------------------------------------------------

  float soilStd =
    standardDeviation(
      candidateSoil,
      candidateCount
    );


  float soilRange =
    rangeOf(
      candidateSoil,
      candidateCount
    );


  if (
    !isfinite(
      soilStd
    )
    ||
    !isfinite(
      soilRange
    )
  ) {

    Serial.println(
      "Calibration reject: invalid soil."
    );


    return false;
  }


  if (
    soilStd
    >
    CAL_SOIL_STD_MAX
    ||
    soilRange
    >
    CAL_SOIL_RANGE_MAX
  ) {

    Serial.print(
      "Calibration waiting: soil std="
    );


    Serial.print(
      soilStd,
      3
    );


    Serial.print(
      " range="
    );


    Serial.println(
      soilRange,
      3
    );


    return false;
  }


  // --------------------------------------------------------------
  // Vibration
  // --------------------------------------------------------------

  float vibrationStd =
    standardDeviation(
      candidateVibration,
      candidateCount
    );


  if (
    !isfinite(
      vibrationStd
    )
    ||
    vibrationStd
    >
    CAL_VIBRATION_STD_MAX
  ) {

    Serial.print(
      "Calibration waiting: vibration std="
    );


    Serial.println(
      vibrationStd,
      6
    );


    return false;
  }


  // --------------------------------------------------------------
  // HC-SR04
  //
  // OPTIONAL.
  //
  // Unstable distance MUST NOT stop the complete system from
  // obtaining a useful MPU/soil/vibration baseline.
  // --------------------------------------------------------------

  int validDistanceCount =
    0;


  float validDistances[
    MAX_BASELINE_SAMPLES
  ];


  for (
    int i = 0;
    i < candidateCount;
    i++
  ) {

    if (
      isfinite(
        candidateDistance[i]
      )
    ) {

      validDistances[
        validDistanceCount
      ] =
        candidateDistance[i];


      validDistanceCount++;
    }
  }


  if (
    validDistanceCount >= 7
  ) {

    float distanceStd =
      standardDeviation(
        validDistances,
        validDistanceCount
      );


    float distanceRange =
      rangeOf(
        validDistances,
        validDistanceCount
      );


    if (
      isfinite(
        distanceStd
      )
      &&
      isfinite(
        distanceRange
      )
      &&
      distanceStd
      <=
      CAL_DISTANCE_STD_MAX
      &&
      distanceRange
      <=
      CAL_DISTANCE_RANGE_MAX
    ) {

      Serial.println(
        "HC-SR04: stable enough."
      );

    } else {

      Serial.println(
        "HC-SR04: unstable; excluded from baseline."
      );
    }

  } else {

    Serial.println(
      "HC-SR04: insufficient stable data; excluded."
    );
  }


  // --------------------------------------------------------------
  // POST-ALERT BEHAVIOR
  // --------------------------------------------------------------
  //
  // A genuinely stable NEW physical position is allowed to become
  // the new reference. This is intentional: after a real movement
  // event, forcing the system to return to the old angle would make
  // recovery impossible if the ground has settled elsewhere.
  //
  // This is still guarded by:
  //   1) the 3-second pre-recalibration stability gate,
  //   2) a complete 10-second candidate window,
  //   3) tilt/soil/vibration fluctuation limits,
  //   4) a worsening check against the OLD baseline during recovery.
  // --------------------------------------------------------------

  Serial.println(
    "Calibration candidate accepted."
  );


  return true;
}


// ================================================================
//                         LOCK BASELINE
// ================================================================

void lockBaseline() {

  // --------------------------------------------------------------
  // Tilt
  // --------------------------------------------------------------

  baselineTilt =
    medianOf(
      candidateTilt,
      candidateCount
    );


  baselineTiltStd =
    standardDeviation(
      candidateTilt,
      candidateCount
    );


  baselineTiltStd =
    max(
      baselineTiltStd,
      0.02f
    );


  // --------------------------------------------------------------
  // Soil
  // --------------------------------------------------------------

  baselineSoil =
    medianOf(
      candidateSoil,
      candidateCount
    );


  baselineSoilStd =
    standardDeviation(
      candidateSoil,
      candidateCount
    );


  baselineSoilStd =
    max(
      baselineSoilStd,
      0.25f
    );


  // --------------------------------------------------------------
  // Vibration
  // --------------------------------------------------------------

  baselineVibrationRms =
    medianOf(
      candidateVibration,
      candidateCount
    );


  baselineVibrationStd =
    standardDeviation(
      candidateVibration,
      candidateCount
    );


  baselineVibrationRms =
    max(
      baselineVibrationRms,
      0.0001f
    );


  // --------------------------------------------------------------
  // Distance
  // --------------------------------------------------------------

  int validDistanceCount =
    0;


  float validDistances[
    MAX_BASELINE_SAMPLES
  ];


  for (
    int i = 0;
    i < candidateCount;
    i++
  ) {

    if (
      isfinite(
        candidateDistance[i]
      )
    ) {

      validDistances[
        validDistanceCount
      ] =
        candidateDistance[i];


      validDistanceCount++;
    }
  }


  bool distanceLocked =
    false;


  if (
    validDistanceCount >= 7
  ) {

    float distanceStd =
      standardDeviation(
        validDistances,
        validDistanceCount
      );


    float distanceRange =
      rangeOf(
        validDistances,
        validDistanceCount
      );


    if (
      isfinite(
        distanceStd
      )
      &&
      isfinite(
        distanceRange
      )
      &&
      distanceStd
      <=
      CAL_DISTANCE_STD_MAX
      &&
      distanceRange
      <=
      CAL_DISTANCE_RANGE_MAX
    ) {

      baselineDistance =
        medianOf(
          validDistances,
          validDistanceCount
        );


      baselineDistanceStd =
        max(
          distanceStd,
          0.10f
        );


      distanceLocked =
        true;
    }
  }


  if (
    !distanceLocked
  ) {

    baselineDistance =
      NAN;


    baselineDistanceStd =
      1.0f;


    Serial.println(
      "HC-SR04 baseline: UNAVAILABLE."
    );


    Serial.println(
      "Distance alert remains disabled until stable."
    );
  }


  hasAcceptedBaseline =
    true;


  Serial.println();
  Serial.println(
    "================================================"
  );


  Serial.println(
    "                 BASELINE LOCKED"
  );


  Serial.println(
    "================================================"
  );


  Serial.print(
    "Tilt baseline      : "
  );


  Serial.print(
    baselineTilt,
    3
  );


  Serial.println(
    " deg"
  );


  Serial.print(
    "Tilt noise std     : "
  );


  Serial.print(
    baselineTiltStd,
    3
  );


  Serial.println(
    " deg"
  );


  Serial.print(
    "Soil baseline      : "
  );


  Serial.print(
    baselineSoil,
    2
  );


  Serial.println(
    " %"
  );


  Serial.print(
    "Vibration baseline : "
  );


  Serial.print(
    baselineVibrationRms,
    6
  );


  Serial.println(
    " g"
  );


  Serial.print(
    "Distance baseline  : "
  );


  if (
    isfinite(
      baselineDistance
    )
  ) {

    Serial.print(
      baselineDistance,
      2
    );


    Serial.println(
      " cm"
    );

  } else {

    Serial.println(
      "UNAVAILABLE"
    );
  }


  Serial.println(
    "================================================"
  );
}


// ================================================================
//                     START CALIBRATION
// ================================================================

void startCalibration(
  const char* reason
) {

  systemState =
    STATE_CALIBRATING;


  calibrationStartTime =
    millis();


  resetCandidateBuffers();

  resetHistories();


  currentAlert =
    ALERT_NONE;


  stableGateCount =
    0;


  recalibrationWorseCount =
    0;


  buzzerTriggeredForEvent =
    false;


  buzzerUntil =
    0;


  noTone(
    BUZZER_PIN
  );


  digitalWrite(
    LED_PIN,
    LOW
  );


  Serial.println();
  Serial.println(
    "================================================"
  );


  Serial.print(
    "CALIBRATION START: "
  );


  Serial.println(
    reason
  );


  Serial.println(
    "Visible ALERT : NORMAL"
  );


  Serial.println(
    "LED           : OFF"
  );


  Serial.println(
    "BUZZER        : OFF"
  );


  Serial.println(
    "Small normal fluctuations are allowed."
  );


  Serial.println(
    "Collecting stable 10-second baseline..."
  );
  Serial.println(
    "Baseline is accepted only if fluctuation stays inside stability limits."
  );


  Serial.println(
    "================================================"
  );
}


// ================================================================
//                  START POST-ALERT RECALIBRATION
// ================================================================

void beginRecalibration() {

  retainedAlert =
    currentAlert;


  Serial.println();
  Serial.println(
    "************************************************"
  );


  Serial.println(
    "ALERT CONDITION SETTLED"
  );


  Serial.println(
    "STARTING SILENT RECALIBRATION"
  );


  Serial.print(
    "Previous alert retained: "
  );


  Serial.println(
    getAlertName(
      retainedAlert
    )
  );


  Serial.println(
    "Visible alert during calibration: NORMAL"
  );


  Serial.println(
    "************************************************"
  );


  startCalibration(
    "post-alert stable"
  );


  systemState =
    STATE_RECALIBRATING;


  currentAlert =
    ALERT_NONE;
}


// ================================================================
//                WORSE DURING RECALIBRATION
// ================================================================

AlertLevel detectWorseningDuringRecalibration() {

  if (
    !hasAcceptedBaseline
  ) {

    return ALERT_NONE;
  }


  // --------------------------------------------------------------
  // Current difference from the OLD baseline.
  // This is intentional during recalibration.
  // --------------------------------------------------------------

  float currentTiltDifference =
    fabsf(
      filteredTiltDegrees
      -
      baselineTilt
    );


  float currentSoilIncrease =
    soilMoisture
    -
    baselineSoil;


  float currentDistanceDifference =
    0.0f;


  if (
    isfinite(
      distanceCm
    )
    &&
    isfinite(
      baselineDistance
    )
  ) {

    currentDistanceDifference =
      fabsf(
        distanceCm
        -
        baselineDistance
      );
  }


  // --------------------------------------------------------------
  // Critical
  // --------------------------------------------------------------

  bool criticalTilt =
    currentTiltDifference
    >=
    max(
      2.0f,
      8.0f * baselineTiltStd
    );


  bool criticalMovement =
    movementRatio
    >=
    MOVEMENT_CRITICAL_RATIO;


  bool criticalSoil =
    currentSoilIncrease
    >=
    SOIL_CRITICAL_CHANGE;


  bool criticalDistance =
    currentDistanceDifference
    >=
    DIST_CRITICAL_CHANGE;


  if (
    criticalTilt
    ||
    (
      criticalMovement
      &&
      (
        criticalTilt
        ||
        criticalSoil
        ||
        criticalDistance
      )
    )
  ) {

    return ALERT_CRITICAL;
  }


  // --------------------------------------------------------------
  // Warning
  // --------------------------------------------------------------

  bool warningTilt =
    currentTiltDifference
    >=
    max(
      1.0f,
      6.0f * baselineTiltStd
    );


  bool warningMovement =
    movementRatio
    >=
    MOVEMENT_WARNING_RATIO;


  bool warningSoil =
    currentSoilIncrease
    >=
    SOIL_WARNING_CHANGE;


  bool warningDistance =
    currentDistanceDifference
    >=
    DIST_WARNING_CHANGE;


  int warningEvidence =
    0;


  if (
    warningTilt
  ) {

    warningEvidence++;
  }


  if (
    warningMovement
  ) {

    warningEvidence++;
  }


  if (
    warningSoil
  ) {

    warningEvidence++;
  }


  if (
    warningDistance
  ) {

    warningEvidence++;
  }


  if (
    warningEvidence
    >=
    2
  ) {

    return ALERT_WARNING;
  }


  if (
    warningTilt
    ||
    warningMovement
    ||
    warningSoil
    ||
    warningDistance
  ) {

    return ALERT_WARNING;
  }


  return ALERT_NONE;
}


// ================================================================
//                   ALERT EVALUATION
// ================================================================

AlertLevel evaluateAlert() {

  if (
    !hasAcceptedBaseline
  ) {

    return ALERT_NONE;
  }


  // --------------------------------------------------------------
  // TILT
  // --------------------------------------------------------------

  float adaptiveTiltWatchGate =
    max(
      TILT_WATCH_CHANGE,
      5.0f * baselineTiltStd
    );


  bool tiltWatch =
    (
      fabsf(
        tiltChange
      )
      >=
      adaptiveTiltWatchGate

      &&

      fabsf(
        tiltRateDph
      )
      >=
      TILT_WATCH_RATE
    )
    ||
    (
      fabsf(
        tiltSuddenChange10s
      )
      >=
      TILT_WATCH_SUDDEN
    );


  bool tiltWarning =
    (
      fabsf(
        tiltChange
      )
      >=
      max(
        TILT_WARNING_CHANGE,
        6.0f * baselineTiltStd
      )

      &&

      fabsf(
        tiltRateDph
      )
      >=
      TILT_WARNING_RATE
    )
    ||
    (
      fabsf(
        tiltSuddenChange10s
      )
      >=
      TILT_WARNING_SUDDEN
    );


  bool tiltCritical =
    (
      fabsf(
        tiltChange
      )
      >=
      max(
        TILT_CRITICAL_CHANGE,
        8.0f * baselineTiltStd
      )

      &&

      fabsf(
        tiltRateDph
      )
      >=
      TILT_CRITICAL_RATE
    )
    ||
    (
      fabsf(
        tiltSuddenChange10s
      )
      >=
      TILT_CRITICAL_SUDDEN
    );


  // --------------------------------------------------------------
  // MOVEMENT
  // --------------------------------------------------------------

  bool movementWatch =
    movementRatio
    >=
    MOVEMENT_WATCH_RATIO;


  bool movementWarning =
    movementRatio
    >=
    MOVEMENT_WARNING_RATIO;


  bool movementCritical =
    movementRatio
    >=
    MOVEMENT_CRITICAL_RATIO;


  // --------------------------------------------------------------
  // SOIL
  // --------------------------------------------------------------

  float soilWatchGate =
    max(
      SOIL_WATCH_CHANGE,
      5.0f * baselineSoilStd
    );


  bool soilWatch =
    soilChange
    >=
    soilWatchGate
    &&
    soilRatePph
    >=
    SOIL_WATCH_RATE;


  bool soilWarning =
    soilChange
    >=
    max(
      SOIL_WARNING_CHANGE,
      7.0f * baselineSoilStd
    )
    &&
    soilRatePph
    >=
    SOIL_WARNING_RATE;


  bool soilCritical =
    soilChange
    >=
    max(
      SOIL_CRITICAL_CHANGE,
      10.0f * baselineSoilStd
    )
    &&
    soilRatePph
    >=
    SOIL_CRITICAL_RATE;


  // --------------------------------------------------------------
  // DISTANCE
  // --------------------------------------------------------------

  float distanceWatchGate =
    max(
      DIST_WATCH_CHANGE,
      5.0f * baselineDistanceStd
    );


  bool distanceWatch =
    isfinite(
      distanceCm
    )
    &&
    isfinite(
      baselineDistance
    )
    &&
    fabsf(
      distanceChange
    )
    >=
    distanceWatchGate
    &&
    fabsf(
      distanceRateCmh
    )
    >=
    DIST_WATCH_RATE;


  bool distanceWarning =
    isfinite(
      distanceCm
    )
    &&
    isfinite(
      baselineDistance
    )
    &&
    fabsf(
      distanceChange
    )
    >=
    max(
      DIST_WARNING_CHANGE,
      7.0f * baselineDistanceStd
    )
    &&
    fabsf(
      distanceRateCmh
    )
    >=
    DIST_WARNING_RATE;


  bool distanceCritical =
    isfinite(
      distanceCm
    )
    &&
    isfinite(
      baselineDistance
    )
    &&
    fabsf(
      distanceChange
    )
    >=
    max(
      DIST_CRITICAL_CHANGE,
      10.0f * baselineDistanceStd
    )
    &&
    fabsf(
      distanceRateCmh
    )
    >=
    DIST_CRITICAL_RATE;


  // --------------------------------------------------------------
  // Indicators
  // --------------------------------------------------------------

  tiltIndicator =
    tiltWatch;


  movementIndicator =
    movementWatch;


  soilIndicator =
    soilWatch;


  distanceIndicator =
    distanceWatch;


  // ==============================================================
  // CRITICAL
  // ==============================================================

  if (
    tiltCritical
  ) {

    return ALERT_CRITICAL;
  }


  if (
    movementCritical
    &&
    (
      tiltWatch
      ||
      soilWatch
      ||
      distanceWatch
    )
  ) {

    return ALERT_CRITICAL;
  }


  if (
    distanceCritical
    &&
    (
      movementWatch
      ||
      tiltWatch
    )
  ) {

    return ALERT_CRITICAL;
  }


  if (
    soilCritical
    &&
    (
      movementWatch
      ||
      tiltWatch
    )
  ) {

    return ALERT_CRITICAL;
  }


  // ==============================================================
  // WARNING
  // ==============================================================

  int warningEvidence =
    0;


  if (
    tiltWarning
  ) {

    warningEvidence++;
  }


  if (
    movementWarning
  ) {

    warningEvidence++;
  }


  if (
    soilWarning
  ) {

    warningEvidence++;
  }


  if (
    distanceWarning
  ) {

    warningEvidence++;
  }


  if (
    warningEvidence
    >=
    2
  ) {

    return ALERT_WARNING;
  }


  if (
    tiltWarning
    ||
    movementWarning
    ||
    soilWarning
    ||
    distanceWarning
  ) {

    return ALERT_WARNING;
  }


  // ==============================================================
  // WATCH
  // ==============================================================

  if (
    tiltWatch
    ||
    movementWatch
    ||
    soilWatch
    ||
    distanceWatch
  ) {

    return ALERT_WATCH;
  }


  return ALERT_NONE;
}


// ================================================================
//                    ALERT CLEAR LOGIC
// ================================================================
//
// IMPORTANT:
//
// This does NOT require the sensor to go back to the old baseline.
//
// It only asks:
// "Has the physical situation stopped changing?"
//
// Therefore:
// old baseline = 2.70
// current stable = 2.40
// => alert can clear and 2.40 becomes new baseline.

bool conditionsAreStable() {

  if (
    !hasAcceptedBaseline
  ) {

    return false;
  }


  // --------------------------------------------------------------
  // Tilt
  // --------------------------------------------------------------

  bool tiltStable =
    fabsf(
      tiltSuddenChange10s
    )
    <
    0.15f
    &&
    fabsf(
      tiltRateDph
    )
    <
    2.0f;


  // --------------------------------------------------------------
  // Movement
  // --------------------------------------------------------------

  bool movementStable =
    movementRatio
    <
    2.0f;


  // --------------------------------------------------------------
  // Soil
  // --------------------------------------------------------------

  bool soilStable =
    fabsf(
      soilChange10s
    )
    <
    0.50f;


  // --------------------------------------------------------------
  // Distance
  // --------------------------------------------------------------

  bool distanceStable =
    true;


  if (
    isfinite(
      distanceCm
    )
    &&
    isfinite(
      baselineDistance
    )
  ) {

    distanceStable =
      fabsf(
        distanceChange10s
      )
      <
      0.50f;
  }


  return
    tiltStable
    &&
    movementStable
    &&
    soilStable
    &&
    distanceStable;
}


// ================================================================
//                      BUZZER CONTROL
// ================================================================

uint32_t getBuzzerDuration(
  AlertLevel level
) {

  if (
    level
    ==
    ALERT_WATCH
  ) {

    return BUZZER_WATCH_MS;
  }


  if (
    level
    ==
    ALERT_WARNING
  ) {

    return BUZZER_WARNING_MS;
  }


  if (
    level
    ==
    ALERT_CRITICAL
  ) {

    return BUZZER_CRITICAL_MS;
  }


  return 0;
}


void beepOnce(
  AlertLevel level
) {

  if (
    level
    ==
    ALERT_NONE
  ) {

    return;
  }


  if (
    buzzerTriggeredForEvent
  ) {

    return;
  }


  uint32_t duration =
    getBuzzerDuration(
      level
    );


  if (
    duration
    ==
    0
  ) {

    return;
  }


  tone(
    BUZZER_PIN,
    BUZZER_FREQUENCY
  );


  buzzerUntil =
    millis()
    +
    duration;


  buzzerTriggeredForEvent =
    true;
}


// ================================================================
//                      LOCAL OUTPUTS
// ================================================================

void stopOutputs() {

  noTone(
    BUZZER_PIN
  );


  buzzerUntil =
    0;


  digitalWrite(
    LED_PIN,
    LOW
  );
}


void maintainOutputs() {

  // LED
  if (
    systemState
    ==
    STATE_ALERT
    &&
    currentAlert
    !=
    ALERT_NONE
  ) {

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


  // Buzzer timing
  if (
    buzzerUntil
    >
    0
    &&
    millis()
    >=
    buzzerUntil
  ) {

    noTone(
      BUZZER_PIN
    );


    buzzerUntil =
      0;
  }


  // Never buzzer during calibration.
  if (
    systemState
    ==
    STATE_CALIBRATING
    ||
    systemState
    ==
    STATE_RECALIBRATING
  ) {

    noTone(
      BUZZER_PIN
    );


    buzzerUntil =
      0;
  }


  if (
    currentAlert
    ==
    ALERT_NONE
  ) {

    noTone(
      BUZZER_PIN
    );


    buzzerUntil =
      0;
  }
}


// ================================================================
//                     ALERT STATE MACHINE
// ================================================================

void processAlerts() {

  AlertLevel detected =
    evaluateAlert();


  static int watchPersistence =
    0;

  static int warningPersistence =
    0;

  static int criticalPersistence =
    0;


  // --------------------------------------------------------------
  // New abnormal evidence
  // --------------------------------------------------------------

  if (
    detected
    ==
    ALERT_NONE
  ) {

    watchPersistence =
      0;

    warningPersistence =
      0;

    criticalPersistence =
      0;

  } else {

    watchPersistence++;


    if (
      detected
      >=
      ALERT_WARNING
    ) {

      warningPersistence++;

    } else {

      warningPersistence =
        0;
    }


    if (
      detected
      >=
      ALERT_CRITICAL
    ) {

      criticalPersistence++;

    } else {

      criticalPersistence =
        0;
    }
  }


  AlertLevel persistentLevel =
    ALERT_NONE;


  if (
    criticalPersistence
    >=
    ALERT_PERSISTENCE_WINDOWS
  ) {

    persistentLevel =
      ALERT_CRITICAL;

  } else if (
    warningPersistence
    >=
    ALERT_PERSISTENCE_WINDOWS
  ) {

    persistentLevel =
      ALERT_WARNING;

  } else if (
    watchPersistence
    >=
    ALERT_PERSISTENCE_WINDOWS
  ) {

    persistentLevel =
      ALERT_WATCH;
  }


  // --------------------------------------------------------------
  // NEW ALERT / ESCALATION
  // --------------------------------------------------------------

  if (
    persistentLevel
    >
    currentAlert
  ) {

    currentAlert =
      persistentLevel;


    systemState =
      STATE_ALERT;


    stableGateCount =
      0;


    buzzerTriggeredForEvent =
      false;


    beepOnce(
      currentAlert
    );


    Serial.println();
    Serial.println(
      "************************************************"
    );


    Serial.print(
      "SENSOR ALERT -> "
    );


    Serial.println(
      getAlertName(
        currentAlert
      )
    );


    Serial.println(
      "BUZZER: ONE-SHOT"
    );


    Serial.println(
      "LED: ON"
    );


    Serial.println(
      "************************************************"
    );


    return;
  }


  // --------------------------------------------------------------
  // ACTIVE ALERT
  // --------------------------------------------------------------
  //
  // An active alert is not cleared immediately.
  // The physical situation must first remain stable for STABLE_GATE_MS.
  // Only then does silent 10-second recalibration begin.

  if (
    currentAlert
    !=
    ALERT_NONE
  ) {

    if (
      conditionsAreStable()
    ) {

      stableGateCount++;


      int requiredStableWindows =
        (
          int
        )(
          STABLE_GATE_MS
          /
          FEATURE_INTERVAL_MS
        );


      if (
        stableGateCount
        >=
        requiredStableWindows
      ) {

        beginRecalibration();


        return;
      }

    } else {

      stableGateCount =
        0;
    }
  }


  maintainOutputs();
}


// ================================================================
//                     CALIBRATION STATE
// ================================================================

void processCalibration() {

  // --------------------------------------------------------------
  // Calibration has NO visible alert.
  // --------------------------------------------------------------

  currentAlert =
    ALERT_NONE;


  stopOutputs();


  // --------------------------------------------------------------
  // During post-alert recalibration:
  // watch ONLY for something clearly worse than the old event.
  // --------------------------------------------------------------

  if (
    systemState
    ==
    STATE_RECALIBRATING
    &&
    hasAcceptedBaseline
    &&
    retainedAlert
    !=
    ALERT_NONE
  ) {

    AlertLevel worsening =
      detectWorseningDuringRecalibration();


    if (
      worsening
      >
      retainedAlert
    ) {

      recalibrationWorseCount++;

    } else {

      recalibrationWorseCount =
        0;
    }


    // Two consecutive checks = genuine worsening,
    // not one noisy reading.
    if (
      recalibrationWorseCount
      >=
      2
    ) {

      currentAlert =
        worsening;


      systemState =
        STATE_ALERT;


      retainedAlert =
        ALERT_NONE;


      recalibrationWorseCount =
        0;


      stableGateCount =
        0;


      buzzerTriggeredForEvent =
        false;


      beepOnce(
        currentAlert
      );


      Serial.println();
      Serial.println(
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      );


      Serial.println(
        "RECALIBRATION ABORTED"
      );


      Serial.print(
        "CONDITION WORSENED -> "
      );


      Serial.println(
        getAlertName(
          currentAlert
        )
      );


      Serial.println(
        "NEW ONE-SHOT BUZZER"
      );


      Serial.println(
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      );


      return;
    }
  }


  // --------------------------------------------------------------
  // Collect candidate baseline.
  // --------------------------------------------------------------

  addCandidateSample();


  // --------------------------------------------------------------
  // The candidate window is exactly 10 seconds.
  // Samples arrive at the 1-second feature cadence, so the stability
  // check evaluates the full calibration window rather than one instant.
  // --------------------------------------------------------------

  if (
    millis()
    -
    calibrationStartTime
    <
    BASELINE_DURATION_MS
  ) {

    currentAlert =
      ALERT_NONE;


    stopOutputs();


    return;
  }


  // --------------------------------------------------------------
  // Candidate is stable.
  // --------------------------------------------------------------

  if (
    candidateIsStable()
  ) {

    Serial.println(
      "10-second calibration window is STABLE."
    );

    lockBaseline();


    retainedAlert =
      ALERT_NONE;


    currentAlert =
      ALERT_NONE;


    systemState =
      STATE_NORMAL;


    buzzerTriggeredForEvent =
      false;


    stableGateCount =
      0;


    resetHistories();


    stopOutputs();


    Serial.println();
    Serial.println(
      "================================================"
    );


    Serial.println(
      "          NEW BASELINE ACCEPTED"
    );


    Serial.println(
      "          SYSTEM -> NORMAL"
    );


    Serial.println(
      "================================================"
    );


    return;
  }


  // --------------------------------------------------------------
  // Candidate unstable.
  // --------------------------------------------------------------

  Serial.println();
  Serial.println(
    "================================================"
  );


  Serial.println(
    "       CALIBRATION CANDIDATE UNSTABLE"
  );

  Serial.println(
    "Baseline was NOT updated."
  );


  // --------------------------------------------------------------
  // Post-alert:
  // restore old alert silently.
  // --------------------------------------------------------------

  if (
    systemState
    ==
    STATE_RECALIBRATING
    &&
    retainedAlert
    !=
    ALERT_NONE
  ) {

    currentAlert =
      retainedAlert;


    retainedAlert =
      ALERT_NONE;


    systemState =
      STATE_ALERT;


    stableGateCount =
      0;


    // Same physical event.
    // Do NOT beep again.
    buzzerTriggeredForEvent =
      true;


    noTone(
      BUZZER_PIN
    );


    buzzerUntil =
      0;


    digitalWrite(
      LED_PIN,
      HIGH
    );


    Serial.print(
      "RESTORED ALERT -> "
    );


    Serial.println(
      getAlertName(
        currentAlert
      )
    );


    Serial.println(
      "No new buzzer."
    );


    Serial.println(
      "Waiting for another genuinely stable period."
    );


    Serial.println(
      "================================================"
    );


    return;
  }


  // --------------------------------------------------------------
  // Startup:
  // simply restart silent calibration.
  // --------------------------------------------------------------

  Serial.println(
    "Startup calibration restarting..."
  );


  startCalibration(
    "candidate unstable"
  );


  systemState =
    STATE_CALIBRATING;
}


// ================================================================
//                       SERIAL OUTPUT
// ================================================================

void printReadings() {

  Serial.println();
  Serial.println(
    "---------------------------------------------"
  );


  Serial.print(
    "STATE       : "
  );


  Serial.println(
    getStateName()
  );


  Serial.print(
    "ALERT       : "
  );


  Serial.println(
    getAlertName(
      currentAlert
    )
  );


  // --------------------------------------------------------------
  // Tilt
  // --------------------------------------------------------------

  Serial.print(
    "Tilt        : "
  );


  Serial.print(
    filteredTiltDegrees,
    3
  );


  Serial.println(
    " deg"
  );


  Serial.print(
    "Tilt base   : "
  );


  if (
    isfinite(
      baselineTilt
    )
  ) {

    Serial.print(
      baselineTilt,
      3
    );


    Serial.println(
      " deg"
    );

  } else {

    Serial.println(
      "calibrating"
    );
  }


  Serial.print(
    "Tilt change : "
  );


  Serial.print(
    tiltChange,
    3
  );


  Serial.println(
    " deg"
  );


  Serial.print(
    "Tilt rate   : "
  );


  Serial.print(
    tiltRateDph,
    3
  );


  Serial.println(
    " deg/h"
  );


  Serial.print(
    "Tilt 10s chg: "
  );


  Serial.print(
    tiltSuddenChange10s,
    3
  );


  Serial.println(
    " deg"
  );


  // --------------------------------------------------------------
  // Acceleration
  // --------------------------------------------------------------

  Serial.print(
    "Accel X/Y/Z : "
  );


  Serial.print(
    accelX,
    4
  );


  Serial.print(
    " / "
  );


  Serial.print(
    accelY,
    4
  );


  Serial.print(
    " / "
  );


  Serial.println(
    accelZ,
    4
  );


  Serial.print(
    "Accel mag   : "
  );


  Serial.print(
    accelMagnitude,
    4
  );


  Serial.println(
    " g"
  );


  Serial.print(
    "Accel jump  : "
  );


  Serial.print(
    accelMagnitudeJump,
    4
  );


  Serial.println(
    " g"
  );


  Serial.print(
    "Vibration   : "
  );


  Serial.print(
    vibrationRms,
    6
  );


  Serial.print(
    " g ("
  );


  Serial.print(
    movementRatio,
    2
  );


  Serial.println(
    "x baseline)"
  );


  // --------------------------------------------------------------
  // Soil
  // --------------------------------------------------------------

  Serial.print(
    "Soil        : "
  );


  Serial.print(
    soilMoisture,
    2
  );


  Serial.println(
    " %"
  );


  Serial.print(
    "Soil change : "
  );


  Serial.print(
    soilChange,
    2
  );


  Serial.println(
    " %"
  );


  Serial.print(
    "Soil rate   : "
  );


  Serial.print(
    soilRatePph,
    2
  );


  Serial.println(
    " %/h"
  );


  // --------------------------------------------------------------
  // Distance
  // --------------------------------------------------------------

  Serial.print(
    "Distance    : "
  );


  if (
    isfinite(
      distanceCm
    )
  ) {

    Serial.print(
      distanceCm,
      2
    );


    Serial.println(
      " cm"
    );

  } else {

    Serial.println(
      "unavailable"
    );
  }


  Serial.print(
    "Dist change : "
  );


  Serial.print(
    distanceChange,
    3
  );


  Serial.println(
    " cm"
  );


  Serial.print(
    "Dist rate   : "
  );


  Serial.print(
    distanceRateCmh,
    2
  );


  Serial.println(
    " cm/h"
  );


  // --------------------------------------------------------------
  // Environment
  // --------------------------------------------------------------

  Serial.print(
    "BMP pressure: "
  );


  if (
    isfinite(
      pressureHpa
    )
  ) {

    Serial.print(
      pressureHpa,
      2
    );


    Serial.println(
      " hPa"
    );

  } else {

    Serial.println(
      "unavailable"
    );
  }


  Serial.print(
    "BMP temp    : "
  );


  if (
    isfinite(
      bmpTemperatureC
    )
  ) {

    Serial.print(
      bmpTemperatureC,
      2
    );


    Serial.println(
      " C"
    );

  } else {

    Serial.println(
      "unavailable"
    );
  }


  Serial.print(
    "DHT temp    : "
  );


  if (
    isfinite(
      dhtTemperatureC
    )
  ) {

    Serial.print(
      dhtTemperatureC,
      2
    );


    Serial.println(
      " C"
    );

  } else {

    Serial.println(
      "unavailable"
    );
  }


  Serial.print(
    "Humidity    : "
  );


  if (
    isfinite(
      humidityPercent
    )
  ) {

    Serial.print(
      humidityPercent,
      2
    );


    Serial.println(
      " %"
    );

  } else {

    Serial.println(
      "unavailable"
    );
  }


  // --------------------------------------------------------------
  // Indicators
  // --------------------------------------------------------------

  Serial.print(
    "Indicators  : tilt="
  );


  Serial.print(
    tiltIndicator
      ?
    1
      :
    0
  );


  Serial.print(
    " movement="
  );


  Serial.print(
    movementIndicator
      ?
    1
      :
    0
  );


  Serial.print(
    " soil="
  );


  Serial.print(
    soilIndicator
      ?
    1
      :
    0
  );


  Serial.print(
    " distance="
  );


  Serial.println(
    distanceIndicator
      ?
    1
      :
    0
  );


  Serial.print(
    "WiFi        : "
  );


  Serial.println(
    WiFi.status()
    ==
    WL_CONNECTED
      ?
    "CONNECTED"
      :
    "OFFLINE"
  );


  Serial.println(
    "---------------------------------------------"
  );
}


// ================================================================
//                      JSON HELPERS
// ================================================================

String jsonNumber(
  float value,
  int decimals
) {

  if (
    !isfinite(
      value
    )
  ) {

    return "null";
  }


  return String(
    value,
    decimals
  );
}


String timestampUTC() {

  struct tm timeInfo;


  if (
    getLocalTime(
      &timeInfo,
      50
    )
  ) {

    char buffer[32];


    strftime(
      buffer,
      sizeof(buffer),
      "%Y-%m-%dT%H:%M:%SZ",
      &timeInfo
    );


    return String(
      buffer
    );
  }


  return "1970-01-01T00:00:00Z";
}


// ================================================================
//                       BACKEND SEND
// ================================================================

void sendSensorData() {

  if (
    !SEND_TO_BACKEND
  ) {

    return;
  }


  if (
    WiFi.status()
    !=
    WL_CONNECTED
  ) {

    return;
  }


  HTTPClient http;


  http.setTimeout(
    3000
  );


  if (
    !http.begin(
      BACKEND_URL
    )
  ) {

    return;
  }


  http.addHeader(
    "Content-Type",
    "application/json"
  );


  float displacementProxy =
    isfinite(
      distanceChange
    )
    ?
    fabsf(
      distanceChange
    )
    :
    NAN;


  String json =
    "{";


  json +=
    "\"sensor_id\":\"";

  json +=
    SENSOR_ID;

  json +=
    "\",";


  json +=
    "\"lat\":";

  json +=
    String(
      SENSOR_LATITUDE,
      6
    );

  json +=
    ",";


  json +=
    "\"lon\":";

  json +=
    String(
      SENSOR_LONGITUDE,
      6
    );

  json +=
    ",";


  json +=
    "\"tilt_deg\":";

  json +=
    jsonNumber(
      filteredTiltDegrees,
      3
    );

  json +=
    ",";


  json +=
    "\"tilt_change_deg\":";

  json +=
    jsonNumber(
      tiltChange,
      3
    );

  json +=
    ",";


  json +=
    "\"tilt_rate_dph\":";

  json +=
    jsonNumber(
      tiltRateDph,
      3
    );

  json +=
    ",";


  json +=
    "\"tilt_sudden_change_10s_deg\":";

  json +=
    jsonNumber(
      tiltSuddenChange10s,
      3
    );

  json +=
    ",";


  json +=
    "\"accel_x_g\":";

  json +=
    jsonNumber(
      accelX,
      4
    );

  json +=
    ",";


  json +=
    "\"accel_y_g\":";

  json +=
    jsonNumber(
      accelY,
      4
    );

  json +=
    ",";


  json +=
    "\"accel_z_g\":";

  json +=
    jsonNumber(
      accelZ,
      4
    );

  json +=
    ",";


  json +=
    "\"accel_magnitude_g\":";

  json +=
    jsonNumber(
      accelMagnitude,
      4
    );

  json +=
    ",";


  json +=
    "\"accel_jump_g\":";

  json +=
    jsonNumber(
      accelMagnitudeJump,
      4
    );

  json +=
    ",";


  json +=
    "\"vibration_rms_g\":";

  json +=
    jsonNumber(
      vibrationRms,
      6
    );

  json +=
    ",";


  json +=
    "\"movement_ratio\":";

  json +=
    jsonNumber(
      movementRatio,
      2
    );

  json +=
    ",";


  json +=
    "\"moisture_pct\":";

  json +=
    jsonNumber(
      soilMoisture,
      2
    );

  json +=
    ",";


  json +=
    "\"moisture_change_pct\":";

  json +=
    jsonNumber(
      soilChange,
      2
    );

  json +=
    ",";


  json +=
    "\"moisture_rate_pph\":";

  json +=
    jsonNumber(
      soilRatePph,
      2
    );

  json +=
    ",";


  json +=
    "\"distance_cm\":";

  json +=
    jsonNumber(
      distanceCm,
      2
    );

  json +=
    ",";


  json +=
    "\"distance_change_cm\":";

  json +=
    jsonNumber(
      distanceChange,
      3
    );

  json +=
    ",";


  json +=
    "\"distance_rate_cmh\":";

  json +=
    jsonNumber(
      distanceRateCmh,
      2
    );

  json +=
    ",";


  json +=
    "\"displacement_cm\":";

  json +=
    jsonNumber(
      displacementProxy,
      3
    );

  json +=
    ",";


  json +=
    "\"pressure_hpa\":";

  json +=
    jsonNumber(
      pressureHpa,
      2
    );

  json +=
    ",";


  json +=
    "\"temperature_c\":";

  json +=
    jsonNumber(
      dhtTemperatureC,
      2
    );

  json +=
    ",";


  json +=
    "\"humidity_pct\":";

  json +=
    jsonNumber(
      humidityPercent,
      2
    );

  json +=
    ",";


  // No rain sensor installed yet.
  json +=
    "\"rainfall_mm\":null,";


  json +=
    "\"alert_level\":\"";

  json +=
    getAlertName(
      currentAlert
    );

  json +=
    "\",";


  json +=
    "\"system_state\":\"";

  json +=
    getStateName();

  json +=
    "\",";


  json +=
    "\"timestamp\":\"";

  json +=
    timestampUTC();

  json +=
    "\"";


  json +=
    "}";


  int code =
    http.POST(
      json
    );


  Serial.print(
    "Backend HTTP: "
  );


  Serial.println(
    code
  );


  http.end();
}


// ================================================================
//                            SETUP
// ================================================================

void setup() {

  Serial.begin(
    115200
  );


  delay(
    1000
  );


  // --------------------------------------------------------------
  // GPIO
  // --------------------------------------------------------------

  pinMode(
    LED_PIN,
    OUTPUT
  );


  pinMode(
    BUZZER_PIN,
    OUTPUT
  );


  pinMode(
    SOIL_PIN,
    INPUT
  );


  pinMode(
    HC_TRIG_PIN,
    OUTPUT
  );


  pinMode(
    HC_ECHO_PIN,
    INPUT
  );


  digitalWrite(
    LED_PIN,
    LOW
  );


  noTone(
    BUZZER_PIN
  );


  // --------------------------------------------------------------
  // I2C
  // --------------------------------------------------------------

  Wire.begin(
    SDA_PIN,
    SCL_PIN
  );


  Wire.setClock(
    400000
  );


  Serial.println();
  Serial.println(
    "================================================"
  );


  Serial.println(
    "             GIRI RAKSHAK ESP32"
  );


  Serial.println(
    "                MASTER V10"
  );


  Serial.println(
    "================================================"
  );


  // --------------------------------------------------------------
  // MPU6500
  // --------------------------------------------------------------

  Serial.println();
  Serial.println(
    "Checking MPU6500..."
  );


  Wire.beginTransmission(
    MPU_ADDR
  );


  Wire.write(
    0x6B
  );


  Wire.write(
    0x00
  );


  byte mpuStatus =
    Wire.endTransmission();


  if (
    mpuStatus
    ==
    0
  ) {

    Serial.println(
      "MPU6500 FOUND at 0x68"
    );

  } else {

    Serial.print(
      "MPU6500 ERROR: "
    );


    Serial.println(
      mpuStatus
    );
  }


  // WHO_AM_I
  Wire.beginTransmission(
    MPU_ADDR
  );


  Wire.write(
    0x75
  );


  Wire.endTransmission(
    false
  );


  Wire.requestFrom(
    MPU_ADDR,
    1
  );


  if (
    Wire.available()
  ) {

    byte id =
      Wire.read();


    Serial.print(
      "MPU WHO_AM_I: 0x"
    );


    Serial.println(
      id,
      HEX
    );
  }


  // ±2g accelerometer.
  mpuWriteByte(
    0x1C,
    0x00
  );


  // Digital low-pass filter.
  mpuWriteByte(
    0x1D,
    0x03
  );


  Serial.println(
    "MPU6500 RAW I2C ready."
  );


  // --------------------------------------------------------------
  // BMP280
  // --------------------------------------------------------------

  Serial.println();
  Serial.println(
    "Checking BMP280..."
  );


  bmpAvailable =
    bmp.begin(
      0x76
    );


  if (
    !bmpAvailable
  ) {

    bmpAvailable =
      bmp.begin(
        0x77
      );
  }


  if (
    bmpAvailable
  ) {

    Serial.println(
      "BMP280 FOUND"
    );


    bmp.setSampling(
      Adafruit_BMP280::MODE_NORMAL,
      Adafruit_BMP280::SAMPLING_X2,
      Adafruit_BMP280::SAMPLING_X16,
      Adafruit_BMP280::FILTER_X16,
      Adafruit_BMP280::STANDBY_MS_500
    );

  } else {

    Serial.println(
      "WARNING: BMP280 not found."
    );
  }


  // --------------------------------------------------------------
  // DHT22
  // --------------------------------------------------------------

  Serial.println();
  Serial.println(
    "Starting DHT22..."
  );


  dht.begin();


  delay(
    2000
  );


  readEnvironment();


  if (
    isfinite(
      dhtTemperatureC
    )
    &&
    isfinite(
      humidityPercent
    )
  ) {

    Serial.println(
      "DHT22 OK"
    );

  } else {

    Serial.println(
      "WARNING: DHT22 check."
    );
  }


  // --------------------------------------------------------------
  // HC-SR04
  // --------------------------------------------------------------

  Serial.println();
  Serial.println(
    "Checking HC-SR04..."
  );


  float firstDistance =
    readDistanceRaw();


  if (
    isfinite(
      firstDistance
    )
  ) {

    distanceCm =
      firstDistance;


    Serial.print(
      "HC-SR04 OK: "
    );


    Serial.print(
      firstDistance,
      2
    );


    Serial.println(
      " cm"
    );

  } else {

    Serial.println(
      "HC-SR04 no valid initial echo."
    );


    Serial.println(
      "Distance remains optional."
    );
  }


  // --------------------------------------------------------------
  // Wi-Fi
  // --------------------------------------------------------------

  if (
    SEND_TO_BACKEND
  ) {

    WiFi.mode(
      WIFI_STA
    );


    WiFi.setAutoReconnect(
      true
    );


    WiFi.begin(
      WIFI_SSID,
      WIFI_PASSWORD
    );


    Serial.println(
      "Wi-Fi backend mode ENABLED."
    );


    configTime(
      19800,
      0,
      "pool.ntp.org",
      "time.nist.gov"
    );

  } else {

    Serial.println(
      "OFFLINE MODE ENABLED."
    );


    Serial.println(
      "Local sensing + alerts work without Wi-Fi."
    );
  }


  // --------------------------------------------------------------
  // Startup calibration
  // --------------------------------------------------------------

  startCalibration(
    "startup"
  );


  Serial.println();
  Serial.println(
    "ABSOLUTE 15-DEGREE TILT IS NOT AN ALERT."
  );


  Serial.println(
    "Mounted orientation becomes the baseline."
  );


  Serial.println(
    "RAIN SENSOR: NOT CONNECTED."
  );


  Serial.println();
}


// ================================================================
//                             LOOP
// ================================================================

void loop() {

  uint32_t now =
    millis();


  // --------------------------------------------------------------
  // Continuous local sampling
  // --------------------------------------------------------------

  sampleMPU();

  sampleSoil();


  // --------------------------------------------------------------
  // Distance
  // --------------------------------------------------------------

  if (
    now
    -
    lastDistanceTime
    >=
    DISTANCE_INTERVAL_MS
  ) {

    lastDistanceTime =
      now;


    sampleDistance();
  }


  // --------------------------------------------------------------
  // Environment
  // --------------------------------------------------------------

  if (
    now
    -
    lastEnvironmentTime
    >=
    ENVIRONMENT_INTERVAL_MS
  ) {

    lastEnvironmentTime =
      now;


    readEnvironment();
  }


  // --------------------------------------------------------------
  // Feature window
  // --------------------------------------------------------------

  if (
    now
    -
    lastFeatureTime
    >=
    FEATURE_INTERVAL_MS
  ) {

    lastFeatureTime =
      now;


    updateFeatures();


    if (
      systemState
      ==
      STATE_CALIBRATING
      ||
      systemState
      ==
      STATE_RECALIBRATING
    ) {

      processCalibration();

    } else {

      processAlerts();
    }
  }


  // --------------------------------------------------------------
  // Local outputs
  // --------------------------------------------------------------

  maintainOutputs();


  // --------------------------------------------------------------
  // Serial
  // --------------------------------------------------------------

  if (
    now
    -
    lastSerialTime
    >=
    SERIAL_INTERVAL_MS
  ) {

    lastSerialTime =
      now;


    printReadings();
  }


  // --------------------------------------------------------------
  // Backend
  // --------------------------------------------------------------

  if (
    SEND_TO_BACKEND
    &&
    now
    -
    lastBackendTime
    >=
    BACKEND_INTERVAL_MS
  ) {

    lastBackendTime =
      now;


    sendSensorData();
  }


  delay(
    5
  );
}


// ================================================================
// V10 CHANGE SUMMARY
// ================================================================
// 1. Absolute tilt remains telemetry only; baseline-relative logic
//    remains unchanged.
// 2. The existing ~60-second tilt regression remains available for
//    genuine sustained movement.
// 3. A small ~10-second tilt change (< 0.02 deg) is treated as normal
//    fluctuation for RATE purposes, forcing stale regression rate to 0.
// 4. Alert thresholds themselves are unchanged.
// 5. Backend sending is enabled and points to 192.168.137.17:8000.
// ================================================================

