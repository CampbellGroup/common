/*
 * usart.cpp
 *
 * Created: 07/12/2011 15:17:35
 *  Author: Boomber
 */ 
#include "usart.h"
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>
#include <stdio.h>			// Conversions
#include <stdlib.h>
#include <math.h>

void USART_Init( unsigned int ubrr)
{
/*Set baud rate */
UBRR0H = (unsigned char)(ubrr>>8);
UBRR0L = (unsigned char)ubrr;
//Enable receiver and transmitter */
UCSR0B = (1<<RXEN0)|(1<<TXEN0);
/* Set frame format: 8data, 2stop bit */
UCSR0C = (1<<USBS0)|(3<<UCSZ00);
}

void USART_Send_Byte(unsigned char data)
{
	/* Wait for empty transmit buffer */
	while ( !( UCSR0A & (1<<UDRE0)) );
	/* Put data into buffer, sends the data */
	UDR0 = char(data);
}

void USART_Send_String(char *str)
{
	while (*str) 
	USART_Send_Byte(*str++);
}

void USART_Send_ConstString(const char *str)
{
	while (*str)
	USART_Send_Byte(*str++);
}
/*
void USART_Send_int(unsigned int d )
{
	char str[10];
	sprintf(str,"%u",d);
	USART_Send_string(str);
	
}
*/

unsigned char USART_Receive( void )
{
/* Wait for data to be received */
while ( !(UCSR0A & (1<<RXC0)) )
;
/* Get and return received data from buffer */
return UDR0;
}


int CharHexByte2Int(unsigned char *str,int idx)
{
	int num=0,cnt=0,base=0;
	char atemp[10];
	while (cnt<2)
	{
		if (cnt==0) {base=16;}
		if (cnt==1) {base=1;}
		if(*(str+idx+cnt)>='0'&&*(str+idx+cnt)<='9') {num=num+(((int) *(str+idx+cnt))-48)*base;};
		if(*(str+idx+cnt)>='a'&&*(str+idx+cnt)<='f') {num=num+(((int) *(str+idx+cnt))-87)*base;};
		cnt++;
	}
	//sprintf(atemp,"%c%c=%d\n",*(str+idx),*(str+idx+1),num);
	//USART_Send_String((unsigned char*)atemp);
	return num;
}

int Str2Int(unsigned char *str)
{
	int cnt=0,cnt1=0;
	int num=0;
	char atemp[10];
	USART_Send_String((char *) str);
	num=atoi((const char*) str);
	//num=655;
	/*
	while (*str)
	{
		cnt=cnt+1;
		str=str+1;
	}
	while (cnt>0)
	{
		str=str-1;
		cnt=cnt-1;
		//USART_Send_String(atemp);
		num=num+atoi(*pow(10,cnt1);
		cnt1=cnt1+1;
	}*/
	sprintf(atemp,"num=%d\n",num);
	USART_Send_String(atemp);
	return cnt;
}

/*
int CharHex2Int(unsigned char *str, int size)
{
	unsigned int cnt,ibase,n;
	unsigned long long int num=0,base=0;
	for(cnt=1;cnt<=size;cnt++)
	{
		base=1;
		for(ibase=1;ibase<=(size-cnt);ibase++) {base=base*16;};
		if(*str>='0'&&*str<='9') {num=num+(((int) *str)-48)*base;};
		if(*str>='A'&&*str<='F') {num=num+(((int) *str)-55)*base;};
		char val[50];
		sprintf(val,"%u\n",num);
		USART_Send_ConstString(val);
		str++;
	}
	return num;
}
*/