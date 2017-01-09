unsigned long time;
long gatetime = 1000
  
  void setup() {
  // initialize serial communication at 115200 bauds per second:
  Serial.begin(115200);

}

void loop() {
  //using a while loop to reduce the overhead time
  while (true)
  {
    Serial.print("Time: ");
    time = micros();
    //prints time since program started
    Serial.println(time);
    int sensorValue = analogRead(A0);
    float voltage = sensorValue * (5.0 / 1023.0);
    Serial.print("V: ");
    Serial.println(voltage);
    //wait 1 ms and take the next data
    delayMicroseconds(1000);
  }
}
