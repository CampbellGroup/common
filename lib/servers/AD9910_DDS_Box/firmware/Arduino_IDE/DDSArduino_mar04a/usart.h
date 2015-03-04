/*
 * usart.h
 *
 * Created: 07/12/2011 15:16:27
 *  Author: Boomber
 */ 


#ifndef USART_H_
#define USART_H_


#define FOSC 16000000 // Clock Speed
#define BAUD 57600	  // Baud Rate
#define MYUBRR (((((FOSC * 10) / (16L * BAUD)) + 5) / 10) - 1)

void USART_Init( unsigned int ubrr);

void USART_Send_Byte(unsigned char data );
void USART_Send_String(char *str);
void USART_Send_ConstString(const char *str);
//void USART_Send_int(unsigned int d);

int CharHexByte2Int(unsigned char *str,int idx);
int Str2Int(unsigned char *str);

unsigned char USART_Receive(void);


#endif /* USART_H_ */
