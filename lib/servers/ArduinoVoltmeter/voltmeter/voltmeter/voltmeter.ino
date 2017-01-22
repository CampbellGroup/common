unsigned long data_taking_time_window=2000; // time window (in ms) during which voltage data is taken. 
unsigned long gatetime = 1000; // default gate time in us
unsigned long t0; // initial time as reference
unsigned long time_elapsed = 0;
unsigned long time_elapsed_in_us;
unsigned long time_in_us;
int sensorValue;
float v;
int voltage;
byte data[5000];
int counter = 0;
int index;
bool printed = false;

  
void setup() {
  Serial.begin(9600);
}

void loop() {
  //if (Serial.available()) {
    //data_taking_time_window = Serial.read();
  //}
  if (Serial.available()) {
    Serial.read();
    t0 = micros();
    //Serial.print("t0=");
    //Serial.println(t0);
    // use a while loop to reduce the overhead time;
    while (time_elapsed < data_taking_time_window) {
      // get time since program started;
      time_in_us = micros();
      time_elapsed_in_us = time_in_us - t0;
      time_elapsed = (unsigned long) time_elapsed_in_us/1000;
      // get voltage in mV
      sensorValue = analogRead(A0);
      v = sensorValue * (5.0 / 1024.0) * 1000;
      voltage = (int) v;
      // write time
      index = 4 * counter;
      data[index] = (byte)((time_elapsed >> 8) & 0xff);
      data[index+1] = (byte)(time_elapsed & 0xff);
      // write voltage
      data[index+2] = (byte)((voltage >> 8) & 0xff);
      data[index+3] = (byte)(voltage & 0xff);
      counter += 1;
      //wait gatetime to take the next data
      delayMicroseconds(gatetime);
    }
    for (int i=0; i<5000; i++) {
      Serial.write(data[i]);
    }
    time_elapsed = 0;
  }
}

void nothing(){
  
      Serial.print("counter=");
      Serial.println(counter);
      Serial.print("time=");
      Serial.println(time_elapsed);
      Serial.print("time in bytes=");
      Serial.write(data[index]);
      Serial.write(data[index+1]);
      Serial.print(", voltage=");
      Serial.println(voltage);
      Serial.print("V in bytes=");
      Serial.write(data[index+2]);
      Serial.write(data[index+3]);
}

