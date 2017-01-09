void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
}

void loop() {
  int sensorValueA0 = analogRead(A0);
  float voltageA0 = sensorValueA0 * (5.0 / 1023.0);
  Serial.println(voltageA0);
}
