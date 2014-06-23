byte input = 0;
byte value = 0;
byte chan = 0;
boolean mode = false;
boolean output = false;


void setup() {
  Serial.begin(57600);
}

void loop() {
  if (Serial.available()){
     // wait for serial input:
   input = Serial.read();
   chan = input >> 2;
   mode = (input & 2) >> 1;
   output = 0b1 & input;
     
   pinMode(chan,mode);
   
   if (mode == 1){
    digitalWrite(chan,output);
    Serial.flush();
   }
    
   else{
    value = digitalRead(chan); 
    Serial.write(value);
    Serial.flush();  
   }
}
}


