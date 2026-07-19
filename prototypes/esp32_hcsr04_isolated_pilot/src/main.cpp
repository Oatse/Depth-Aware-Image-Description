#include <Arduino.h>

#ifndef SENSOR_ENABLED
#define SENSOR_ENABLED 0
#endif

#ifndef SENSOR_COUNT
#define SENSOR_COUNT 2
#endif

#ifndef SENSOR_START_INDEX
#define SENSOR_START_INDEX 0
#endif

#ifndef TRIG_PIN_1
#define TRIG_PIN_1 5
#endif

#ifndef ECHO_PIN_1
#define ECHO_PIN_1 18
#endif

#ifndef TRIG_PIN_2
#define TRIG_PIN_2 19
#endif

#ifndef ECHO_PIN_2
#define ECHO_PIN_2 21
#endif

namespace {
constexpr unsigned long kSerialBaud = 115200;
constexpr unsigned long kEchoTimeoutUs = 30000;
constexpr unsigned long kInterSensorDelayMs = 70;
constexpr float kSoundCmPerUs = 0.0343F;

struct SensorPins {
  const char* id;
  uint8_t trigPin;
  uint8_t echoPin;
};

constexpr SensorPins kSensors[] = {
    {"sensor_1", TRIG_PIN_1, ECHO_PIN_1},
    {"sensor_2", TRIG_PIN_2, ECHO_PIN_2},
};
static_assert(SENSOR_COUNT >= 1 && SENSOR_COUNT <= 2,
              "SENSOR_COUNT must be 1 or 2");
static_assert(SENSOR_START_INDEX >= 0 && SENSOR_START_INDEX <= 1,
              "SENSOR_START_INDEX must be 0 or 1");
static_assert(SENSOR_START_INDEX + SENSOR_COUNT <= 2,
              "selected sensor range exceeds available sensors");
constexpr size_t kSensorCount = SENSOR_COUNT;
constexpr size_t kSensorStartIndex = SENSOR_START_INDEX;

unsigned long sequenceNumber = 0;
unsigned long lastSampleMs = 0;
size_t activeSensorIndex = 0;

void printBoardReady() {
  const uint64_t chipId = ESP.getEfuseMac();
  Serial.printf(
      "{\"type\":\"board_ready\",\"chip_model\":\"%s\","
      "\"chip_revision\":%d,\"cpu_mhz\":%d,\"chip_id\":\"%012llX\","
      "\"sensor_enabled\":%s}\n",
      ESP.getChipModel(), ESP.getChipRevision(), ESP.getCpuFreqMHz(), chipId,
      SENSOR_ENABLED ? "true" : "false");
}

#if SENSOR_ENABLED
void sampleSensor(const SensorPins& sensor) {
  digitalWrite(sensor.trigPin, LOW);
  delayMicroseconds(3);
  digitalWrite(sensor.trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(sensor.trigPin, LOW);

  const unsigned long pulseUs =
      pulseIn(sensor.echoPin, HIGH, kEchoTimeoutUs);
  const float distanceCm = pulseUs * kSoundCmPerUs / 2.0F;
  const bool valid = pulseUs > 0 && distanceCm >= 2.0F && distanceCm <= 400.0F;

  if (valid) {
    Serial.printf(
        "{\"type\":\"sample\",\"sensor_id\":\"%s\",\"seq\":%lu,"
        "\"timestamp_ms\":%lu,"
        "\"pulse_us\":%lu,\"distance_cm\":%.2f,\"valid\":true,"
        "\"status\":\"ok\"}\n",
        sensor.id, sequenceNumber, millis(), pulseUs, distanceCm);
  } else {
    Serial.printf(
        "{\"type\":\"sample\",\"sensor_id\":\"%s\",\"seq\":%lu,"
        "\"timestamp_ms\":%lu,"
        "\"pulse_us\":%lu,\"distance_cm\":null,\"valid\":false,"
        "\"status\":\"%s\"}\n",
        sensor.id, sequenceNumber, millis(), pulseUs,
        pulseUs == 0 ? "echo_timeout" : "out_of_range");
  }

  ++sequenceNumber;
}
#endif
}

void setup() {
  Serial.begin(kSerialBaud);
  delay(1200);
  printBoardReady();

#if SENSOR_ENABLED
  for (size_t index = 0; index < kSensorCount; ++index) {
    const SensorPins& sensor = kSensors[kSensorStartIndex + index];
    pinMode(sensor.trigPin, OUTPUT);
    pinMode(sensor.echoPin, INPUT);
    digitalWrite(sensor.trigPin, LOW);
    Serial.printf(
        "{\"type\":\"sensor_config\",\"sensor_id\":\"%s\","
        "\"sensor\":\"HC-SR04\",\"trig_gpio\":%d,\"echo_gpio\":%d,"
        "\"echo_timeout_us\":%lu}\n",
        sensor.id, sensor.trigPin, sensor.echoPin, kEchoTimeoutUs);
  }
#else
  Serial.println(
      "{\"type\":\"safety_lock\",\"status\":\"sensor_not_triggered\","
      "\"reason\":\"build board_check; confirm ECHO <= 3.3V and GPIO mapping first\"}");
#endif
}

void loop() {
#if SENSOR_ENABLED
  const unsigned long now = millis();
  if (now - lastSampleMs >= kInterSensorDelayMs) {
    lastSampleMs = now;
    sampleSensor(kSensors[kSensorStartIndex + activeSensorIndex]);
    activeSensorIndex = (activeSensorIndex + 1) % kSensorCount;
  }
#else
  delay(1000);
#endif
}
