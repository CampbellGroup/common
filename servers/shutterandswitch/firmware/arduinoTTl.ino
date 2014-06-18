byte input = 0;
byte value = 0;
byte chan = 0;
boolean mode = false;
boolean output = false;


void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()){
     // wait for serial input:
   input = Serial.read();
   Serial.println(input,BIN);
   chan = input >> 2;
   Serial.println(chan,BIN);
   mode = (input >> 8) & 1;
   output = 0b1 | input;
   mode = (0b11 | input) >> 1;
     
   pinMode(chan,mode);
   
   if (mode == 1){
    digitalWrite(chan,output);
   }
    
   else{
    value = digitalRead(chan); 
    Serial.write(value);
    Serial.flush();  
   }
}
}


