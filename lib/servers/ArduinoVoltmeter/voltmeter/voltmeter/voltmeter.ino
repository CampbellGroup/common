unsigned long data_taking_time_window=2000; // time window (in ms) during which voltage data is taken. 
unsigned long gatetime = 1000; // default gate time in us
unsigned long t0; // initial time as reference
int time_elapsed = 0;
unsigned long time_elapsed_in_us;
unsigned long time_in_us;
int sensorValue;
float v;
int voltage;
byte t[2];
byte V[2];
byte data[20000];
  
void setup() {
  Serial.begin(9600);
}

void loop() {
  //if (Serial.available()) {
    //data_taking_time_window = Serial.read();
  //}
  if (Serial.available()) {
    t0 = micros();
    // use a while loop to reduce the overhead time;
    while (time_elapsed < data_taking_time_window) {
      // get time since program started;
      time_in_us = micros();
      time_elapsed_in_us = time_in_us - t0;
      time_elapsed = (int) time_elapsed_in_us/1000;
      // get voltage in mV
      sensorValue = analogRead(A0);
      v = sensorValue * (5.0 / 1024.0) * 1000;
      voltage = (int) v;
      // write time
      t[1] = (byte)((time_elapsed >> 8) & 0xff);
      t[0] = (byte)(time_elapsed & 0xff);
      for (int i=0; i<2; i++) {
        Serial.write(t[i]);  
      }
      // write voltage
      V[1] = (byte)((voltage >> 8) & 0xff);
      V[0] = (byte)(voltage & 0xff);
      for (int i=0; i<2; i++) {
        Serial.write(V[i]);  
      }      
      //wait gatetime to take the next data
      delayMicroseconds(gatetime);
    }
  }
}
