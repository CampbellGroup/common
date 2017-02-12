
//int dirPin1 = 3;
//int stepperPin1 = 2;

int dirPin2 = 7;
int stepperPin2 = 6;

String steps;
boolean step_direction = false;

void setup() {
  Serial.begin(115200);
  //pinMode(dirPin1, OUTPUT);
  //pinMode(stepperPin1, OUTPUT);
  pinMode(dirPin2, OUTPUT);
  pinMode(stepperPin2, OUTPUT);
}

void step(boolean dir,int steps){
  //digitalWrite(dirPin1,dir);
  digitalWrite(dirPin2,dir);
  delay(5);
  for(int i=0;i<steps;i++){
    //digitalWrite(stepperPin1, HIGH);
    digitalWrite(stepperPin2, HIGH);
    delayMicroseconds(500);
    //digitalWrite(stepperPin1, LOW);
    digitalWrite(stepperPin2, LOW);
    delayMicroseconds(500);
  }
}

void loop(){
while(Serial.available()) {
  steps = Serial.readString();

  if (steps.toInt() > 0){
    step_direction = false;
  }
  else{
    step_direction = true;
  }  
  step(step_direction, 8*abs(steps.toInt()));
  
}
}
