/*
Creates bytes to read in on serial commands
*/
byte chan = 0;
byte value = 0;

/*
define clock pin, Serial Pin Output, Load DAC pin and Preset input pin respectively 
*/
const int clk = 52;
const int SPO = 51;
const int LD = 24;
const int PR = 25;
void setup()
{
/*
Set baudrate for serial communication
*/
  Serial.begin(57600);
/*
All pins are outputs from arduino to DAC
*/
  pinMode(clk, OUTPUT);
  pinMode(SPO, OUTPUT);
  pinMode(LD, OUTPUT);
  pinMode(PR, OUTPUT);
  
/*
All pins are set to low except preset (High means DAC ready for data)
*/
  digitalWrite(clk, LOW);
  digitalWrite(LD, LOW);
  digitalWrite(PR, LOW);
  digitalWrite(PR, HIGH);
}

void loop()
{
  while(Serial.available() < 2); //wait for two bytes to be in the buffer
  chan = Serial.read();
  value = Serial.read();
  /* 
  insert read function
  Here we need a serial read to get a input number between 0 and 4096 to be parsed in binary
  */
  
  /*
  The following function Needs to iterate over the 4 most significant bits of input number in binary
  and output them to pin SPO. This specifies the channel from 1-8.This is currently hard coded to output 0b0001 (DAC A) with the largest
 allowed values are 0b0001 to (DAC A) to 0b1000 (DAC H) 
  */

  for (int j = 0; j<4; j++) // output 000
   {
     boolean currentchanbit = chan & 9;
     currentchanbit  = currentchanbit >> 3;
//     if (currentbit == 1){
//         Serial.print(1);
//     }
//     else{
//         Serial.print(0);
//     }
     chan = chan << 1;
     digitalWrite(SPO,currentchanbit);
     digitalWrite(clk, HIGH);// The data from SPO is read when clock is HIGH so set SPO before clock pulse
     digitalWrite(clk, LOW);
     digitalWrite(SPO, LOW);
   }
     /*
     this next loop writes to the dac channel the output voltage from min (0b00000000) to max (0b11111111)
     */
  for (int i = 0; i<8; i++) // hard coded output 0b11111111 (max voltage)
   {
    boolean currentvaluebit = value & 255;
    currentvaluebit = currentvaluebit >> 7;
    value = value << 1;
    digitalWrite(SPO,currentvaluebit);
    digitalWrite(clk, HIGH);
    digitalWrite(clk, LOW);
    digitalWrite(SPO, LOW); 
   }
   digitalWrite(LD,HIGH);//LD loads the data into the dac registry
   digitalWrite(clk,HIGH);
   digitalWrite(clk,LOW);
   digitalWrite(LD, LOW);
 }
