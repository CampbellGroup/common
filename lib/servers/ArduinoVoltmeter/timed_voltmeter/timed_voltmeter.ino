unsigned long time_in_us;
unsigned long time_in_ms;
unsigned long output;
int sensorValue;
float v;
int voltage;
unsigned long gatetime = 1000; // default gate time in us
boolean readVoltage = false;
// Arduino has a time counting limit beyond which the micro() value gets reset. 
// The following variable tries to avoid this possibility.
// Can be changed to suit your needs.
int upper_time_limit = 10000; // time in ms
  
void setup() {
  // initialize serial communication at 9600 bauds per second. This is the 
  // fastest I can do without receiving weird stuff from the serial port;
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    readVoltage = Serial.read();
  }
  // use a while loop to reduce the overhead time;
  while (readVoltage) {
    // get time since program started;
    time_in_us = micros();
    time_in_ms = (unsigned long) time_in_us/1000;
    // avoid timing confusion because of Arduino's timer reset;
    while (time_in_ms > upper_time_limit) {
    time_in_ms = time_in_ms - upper_time_limit;
    }
    // get voltage in mV
    sensorValue = analogRead(A0);
    v = sensorValue * (5.0 / 1024.0) * 1000;
    voltage = (int) v;
    // combine the time information to voltage information. Scaling factor of 10000
    // comes from the fact that voltage never exceeds 5000 mV (or 5V).
    output = time_in_ms * 10000 + voltage;
    Serial.println(output);
    //wait gatetime to take the next data
    delayMicroseconds(gatetime);
    if (Serial.available()) {
      readVoltage = Serial.read();
      if (readVoltage=0) {
        break;
      }
    }
  }
}
