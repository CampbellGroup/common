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
  /* 
  insert read function
  Here we need a serial read to get a input number between 0 and 4096 to be parsed in binary
  */
  
  /*
  The following function Needs to iterate over the 4 most significant bits of input number in binary
  and output them to pin SPO. This specifies the channel from 1-8.This is currently hard coded to output 0b0001 (DAC A) with the largest
 allowed values are 0b0001 to (DAC A) to 0b1000 (DAC H) 
  */

  for (int j = 0; j<3; j++) // output 000
   {
     digitalWrite(SPO, LOW);
     digitalWrite(clk, HIGH);// The data from SPO is read when clock is HIGH so set SPO before clock pulse
     digitalWrite(clk, LOW);
   }
    digitalWrite(SPO, HIGH);// output 1
    digitalWrite(clk, HIGH);
    digitalWrite(clk, LOW);
    digitalWrite(SPO, LOW);
     /*
     this next loop writes to the dac channel the output voltage from min (0b00000000) to max (0b11111111)
     */
  for (int i = 0; i<8; i++) // hard coded output 0b11111111 (max voltage)
   {
    digitalWrite(SPO,HIGH);
    digitalWrite(clk, HIGH);
    digitalWrite(clk, LOW);
    digitalWrite(SPO, LOW); 
   }
   digitalWrite(LD,HIGH);//LD loads the data into the dac registry
   digitalWrite(clk,HIGH);
   digitalWrite(clk,LOW);
   digitalWrite(LD, LOW);
   delay(1000);//leave at max voltage for 1 second
   
  for (int j = 0; j<3; j++) // choose DAC A
   {
     digitalWrite(SPO, LOW);
     digitalWrite(clk, HIGH);
     digitalWrite(clk, LOW);
   }
    digitalWrite(SPO, HIGH);
    digitalWrite(clk, HIGH);
    digitalWrite(clk, LOW);
    digitalWrite(SPO, LOW);
     
  for (int i = 0; i<8; i++) // Write 0b00000000 (min voltage)
   {
    digitalWrite(SPO,LOW);
    digitalWrite(clk, HIGH);
    digitalWrite(clk, LOW);
   }
   digitalWrite(LD,HIGH);// load data into dac
   digitalWrite(clk,HIGH);
   digitalWrite(clk,LOW);
   digitalWrite(LD, LOW);
   delay(1000);// leave at min voltage for 1 second   // turn to max value
 }
