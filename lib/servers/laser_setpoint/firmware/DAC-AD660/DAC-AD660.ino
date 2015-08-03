/*Code for DAC-AD660*/
/*
Creates bytes to read in on serial commands
*/
word value = 0;
boolean currentvaluebit = 0;
const char startOfNumberDelimiter = '/'; //Before inputing number between 0-32767 you should start with /, for example, input /32767, then you get 32767
const char endOfNumberDelimiter   = '\n'; 

/*
define clock pin, Serial Pin Output, Load DAC pin and Serial Input Enable pin respectively 
*/
const int CLK = 24;
const int SPO = 32;
const int LDAC = 36;
const int SER = 40;
const int DB1 = 30;

void setup()
{
/*
Set baudrate for serial communication
*/
  Serial.begin(57600);
/*
All pins are outputs from arduino to DAC
*/
  pinMode(CLK, OUTPUT); // CLK for CS
  pinMode(SPO, OUTPUT); // Serial Output for DB0
  pinMode(LDAC, OUTPUT); //LDAC for Load DAC
  pinMode(SER, OUTPUT); // Enable
  pinMode(DB1, OUTPUT); // DB1 (used to determine the direction)

  
/*
All pins are set to low except Enable (High means DAC ready for data)
*/
  digitalWrite(CLK, LOW);
  digitalWrite(LDAC, LOW);
  digitalWrite(SER, HIGH);
  digitalWrite(DB1, LOW);

}
// The following code is used to read more than one byte one time from the serial monitor.
//***********************************************************************************
void processInput ()
  {
  static word receivedNumber = 0;  
  int c = Serial.read ();
  int j = 0;

  switch (c)
    {
    if(j >= 6)
    {
      break;
    }
    
    case endOfNumberDelimiter: 
      value = receivedNumber;

    // fall through to start a new number
    case startOfNumberDelimiter: 
      receivedNumber = 0; 
      break;
      
    case '0' ... '9': 
      receivedNumber *= 10; 
      receivedNumber += c-'0'; // Change receivedNumber to a 10-digit number.
      j += 1;
      break;
      
    } // end of switch  
   j = 0;
  }  // end of processInput

//*********************************************************************************************************  


void loop()
{
  while(Serial.available() < 1); //wait for one byte to be in the buffer
  digitalWrite(SER, LOW);
  digitalWrite(DB1, HIGH);
  processInput ();
  Serial.print(value, DEC); // This line is used to check the input of value which can be deleted when used.

  /* 
  insert read function
  Here we need a serial read to get a input number between 0 and  32767 (for unipolar configuration) to be parsed in binary
  */
     /*
     this next loop writes to the dac channel the output voltage from min (0b0000000000000000) to max (0b1111111111111111)
     */
  for (int i = 0; i<16; i++) // hard coded output 0b1111111111111111 (max voltage)
   {
    currentvaluebit = (value & 32768) >> 15; // To Get the first number of value in binary.
    value = value << 1;
    digitalWrite(SPO,currentvaluebit); // The AD660 load data as the rising edge of CLK, so we set the value before the clock rise.
    digitalWrite(CLK, HIGH);
    digitalWrite(CLK, LOW);
    digitalWrite(SPO, LOW);
   }
   
   digitalWrite(LDAC,HIGH);//LDAC loads the data into the dac registry
   digitalWrite(CLK,HIGH);
   digitalWrite(CLK,LOW);
   digitalWrite(LDAC, LOW);   
 }
 //CLR should be kept high.
