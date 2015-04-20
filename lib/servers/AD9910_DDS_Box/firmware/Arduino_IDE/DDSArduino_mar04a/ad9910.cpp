/*
 * ad9910.cpp
 *
 * Created: 10/11/2012 5:32:52 PM
 *  Author: Peter Yu
 */

#define sbi(var, mask)   ((var) |= (uint8_t)(1 << mask))  // This are nice functions to let you control 1 pin; Makes High
#define cbi(var, mask)   ((var) &= (uint8_t)~(1 << mask)) // This are nice functions to let you control 1 pin; Makes Low

# define F_CPU 16000000L
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>    // including the avr delay lib
#include "spi.h"
#include "usart.h"			// Header for Serial communication

#define DEBUG		0
#define SPI_READ_EN	1

#define SPI_DELAY	1

#define mIDLE		0x00
#define mTEST		0x01
#define mCHECK		0x02
#define mRESET		0x03
#define mIDN        0x06
#define mWRTREG		0x11
#define mRDREG		0x12
#define mFREQ		0x13
#define mAMP		0x14
#define mPHASE		0x15
volatile unsigned char mState=mIDLE;

const unsigned char MR_DDR=0x04,MR_PORT=0x05; // Master Reset
const int			MR_DDRn=DDB1,MR_PORTn=PORTB1; // Master Reset
const unsigned char	CS_DDR[4] ={0x0A,0x0A,0x0A,0x0A},CS_PORT[4] ={0x0B,0x0B,0x0B,0x0B}; // Chip Select
const int			CS_DDRn[4]={DDD6,DDD5,DDD4,DDD3},CS_PORTn[4]={PORTD6,PORTD5,PORTD4,PORTD3}; // Chip Select
const unsigned char	IOU_DDR  =0x04, IOU_PORT  =0x05;   // IO_UPDATE
const int			IOU_DDRn =DDB0, IOU_PORTn =PORTB0; // IO_UPDATE
const unsigned char	IOR_DDR  =0x0A,IOR_PORT =0x0B;   // IO_RESET
const int			IOR_DDRn =DDD7,IOR_PORTn=PORTD7; // IO_RESET
	
unsigned int AD9910_REG_BYTES[16]={4,4,4,4,4,0,0,4,2,4,4,8,8,4,8,8};
unsigned int AD9910_REG_0x00_CFR1_3SPI[4]={0x0,0x0,0x0,0x2};
unsigned int AD9910_REG_0x01_CFR2_AMP[4]={0x1,0x40,0x08,0x20};
unsigned int AD9910_REG_0x02_CFR3[4]={0x1f,0x3f,0xc0,0x00};
unsigned int AD9910_REG_CFR2[4]={0x00,0x00,0x08,0x20};
volatile unsigned int AD9910_REG_READ[8];

#define uIDLE		0x00
#define uTEST		0x01
#define uRESET		0x02
#define uINDEX		0x03
#define	uADDRESS	0x11
#define uDATALEN	0x12
#define uDATA		0x13
#define uFREQ		0x14
#define uAMP		0x15
#define uPHASE		0x16
volatile unsigned char uState=uIDLE;
volatile unsigned char address[2];
volatile unsigned char dataLen=0;
volatile unsigned char data[16];
volatile unsigned char freq[8];
volatile unsigned char amp[4];
volatile unsigned char phase[4];
volatile int uCheckSum=0;
volatile int deviceIdx=0;

char char_buf[50];

void ad9910_write(unsigned int idx,unsigned int addr,unsigned int *dat)
{
	_delay_ms(SPI_DELAY);
	if(DEBUG) 
	{
		sprintf(char_buf,">>AD9910 Write: ID=%d, Addr=0x%02X Data=0x", idx, addr);
		USART_Send_ConstString(char_buf);
	}	
	sbi(_SFR_IO8(IOR_PORT),IOR_PORTn); // IOReset high to enable IO reset
	_delay_ms(SPI_DELAY);
	cbi(_SFR_IO8(IOR_PORT),IOR_PORTn); // IOReset low to disable IO reset
	_delay_ms(SPI_DELAY);
	cbi(_SFR_IO8(CS_PORT[idx]),CS_PORTn[idx]); // CS Low to enable SPI
	_delay_ms(SPI_DELAY);
	send_spi(addr); // Address
	_delay_ms(SPI_DELAY);
	int cnt;
	for(cnt=0; cnt<AD9910_REG_BYTES[addr]; cnt++)
	{
		send_spi(*(dat+cnt));
		if(DEBUG)
		{
			sprintf(char_buf,"%02X ",*(dat+cnt));
			USART_Send_ConstString(char_buf);
		}			
	}
	_delay_ms(SPI_DELAY);
	sbi(_SFR_IO8(CS_PORT[idx]),CS_PORTn[idx]); // CS High to disable SPI
	_delay_ms(SPI_DELAY);
	sbi(_SFR_IO8(IOU_PORT),IOU_PORTn); // IOUpdate High
	_delay_ms(SPI_DELAY);
	cbi(_SFR_IO8(IOU_PORT),IOU_PORTn); // IOUpdate Low
	_delay_ms(SPI_DELAY);
	if(DEBUG)
	{
		sprintf(char_buf,"\n");
		USART_Send_ConstString(char_buf);
	}	
	_delay_ms(SPI_DELAY);
}

void ad9910_read(unsigned int idx, unsigned int addr, unsigned int show=0)
{
	show=show|(SPI_READ_EN & DEBUG);
	_delay_ms(SPI_DELAY);
	if(show) 
	{
		sprintf(char_buf, ">>AD9910 Read: ID=%d, Addr=0x%02X, Data=0x", idx, addr);
		USART_Send_ConstString(char_buf);
	}
	sbi(_SFR_IO8(IOR_PORT),IOR_PORTn); // IOReset high to enable IO reset
	_delay_ms(SPI_DELAY);
	cbi(_SFR_IO8(IOR_PORT),IOR_PORTn); // IOReset low to disable IO reset
	_delay_ms(SPI_DELAY);
	cbi(_SFR_IO8(CS_PORT[idx]),CS_PORTn[idx]); // CS Low to enable SPI
	_delay_ms(SPI_DELAY);
	send_spi(addr+128); // Address
	_delay_ms(SPI_DELAY);
	char char_buff[10];
	unsigned int cnt, data_buf;
	for(cnt=0; cnt<AD9910_REG_BYTES[addr]; cnt++)
	{
		data_buf = send_spi(0);
		AD9910_REG_READ[cnt] = data_buf;
		if(show)
		{
			sprintf(char_buf,"%02X ",data_buf);
			USART_Send_ConstString(char_buf);
		}		
		//_delay_ms(SPI_DELAY);
	}
	_delay_ms(SPI_DELAY);
	sbi(_SFR_IO8(CS_PORT[idx]),CS_PORTn[idx]); // CS High to disable SPI
	if(show)
	{
		sprintf(char_buf,"\n");
		USART_Send_ConstString(char_buf);
	}	
	_delay_ms(SPI_DELAY);
}

void ad9910_init(void)
{
	_delay_ms(SPI_DELAY);
	int idx=0,cnt=0;
	for(idx = 0; idx < sizeof(CS_DDR); idx++)
	{
		_SFR_IO8(CS_DDR[idx]) |= (1 << CS_DDRn[idx]); // CS set output direction
		sbi(_SFR_IO8(CS_PORT[idx]),CS_PORTn[idx]); // CS high to disable SPI
	}
	_SFR_IO8(IOU_DDR) |= (1 << IOU_DDRn); // IOUpdate set output direction
	cbi(_SFR_IO8(IOU_PORT),IOU_PORTn); // IOUpdate low to disable IOUpdate
	_SFR_IO8(IOR_DDR) |= (1 << IOR_DDRn); // IOReset set output direction
	sbi(_SFR_IO8(IOR_PORT),IOR_PORTn); // IOReset high to enable IO reset
	_delay_ms(SPI_DELAY);
	cbi(_SFR_IO8(IOR_PORT),IOR_PORTn); // IOReset low to disable IO reset
	_delay_ms(SPI_DELAY);
	_SFR_IO8(MR_DDR) |= (uint8_t)(1 << MR_DDRn); // MR set direction
	_delay_ms(SPI_DELAY);
	_SFR_IO8(MR_PORT) &= (uint8_t)(0 << MR_PORTn); // MR Low
	_delay_ms(SPI_DELAY);
	_SFR_IO8(MR_PORT) |= (uint8_t)(1 << MR_PORTn); // MR High
	_delay_ms(SPI_DELAY);
	_SFR_IO8(MR_PORT) &= (uint8_t)(0 << MR_PORTn); // MR Low
	_delay_ms(SPI_DELAY);
	for(cnt=0; cnt<sizeof(CS_DDR); cnt++)
	{
		ad9910_write(cnt,0x02,AD9910_REG_0x02_CFR3); // Disable REF CLK Division
		_delay_ms(SPI_DELAY);
	}
	if(SPI_READ_EN)
	{
		for(cnt=0; cnt<sizeof(CS_DDR); cnt++)
		{
			ad9910_write(cnt,0x00,AD9910_REG_0x00_CFR1_3SPI); // Enable 3 wire SPI on AD9910
			_delay_ms(SPI_DELAY);
			ad9910_write(cnt,0x01,AD9910_REG_0x01_CFR2_AMP); // Enable Amplitude Control
			_delay_ms(SPI_DELAY);
		}
	}
}

int main(void)
{
	unsigned int cnt,dataByte[16];
	char synclk=0;
	// SPI
	setup_spi(SPI_MODE_0, SPI_MSB, SPI_NO_INTERRUPT, SPI_MSTR_CLK128); // Setup SPI
	// USART
	//// Go to USART.H AND CHANGE YOUR FOSC AND BAUD
	USART_Init(MYUBRR); // Initializes the serial communication
	UCSR0B |= (1 << RXCIE0); // Enable the USART Receive Complete interrupt (USART_RXC)
	// AD9910
	ad9910_init();
	// Options
	sei(); // Enable the Global Interrupt Enable flag so that interrupts can be processed
	// Start
	mState=mIDLE;
	uState=uIDLE;
	while(1)
	{
		_delay_ms(1);
		switch(mState)
		{
			case mIDLE:
				break;
			case mTEST:
				USART_Send_ConstString(">Test Mode\n");
				if (synclk>0)
				{
					AD9910_REG_CFR2[1] = 64;
				}
				else
				{
					AD9910_REG_CFR2[1] = 0;
				}
				ad9910_write(deviceIdx,0x01,AD9910_REG_CFR2); // SYS_CLK
				synclk = ~synclk;
				mState=mIDLE;
				break;
			case mCHECK:
				USART_Send_ConstString(">AD9910 Controller by Peter Yu (peter.yu.eshop@gmail.com)\n");
				USART_Send_ConstString(">>Present Devices: ");
				for(cnt=0; cnt<4; cnt++) // Check Register 0x00
				{
					ad9910_read(cnt,4);
					//sprintf(char_buf,"I%d=",cnt+1);
					//USART_Send_ConstString(char_buf);
					//sprintf(char_buf,"%d",AD9910_REG_READ[3]);
					//USART_Send_ConstString(char_buf);
					if(AD9910_REG_READ[3]>0)
					{
						sprintf(char_buf,"I%d ",cnt+1);
						USART_Send_ConstString(char_buf);
					}
				}
				USART_Send_ConstString("\n>Done\n");								
				mState=mIDLE;
				break;
			case mIDN:
				// Returns GPIB compatible device identification, in response to '*IDN?' query.
				// The end is custom on a per device basis.
				USART_Send_ConstString("CAMPBELLGROUP,AD9910_DDS_Box_Arduino,\n");	
				// Reset the state to idle.
				mState=mIDLE;
				break;
			case mRESET:
				USART_Send_ConstString(">Master Reset\n");
				ad9910_init();
				mState=mIDLE;
				USART_Send_ConstString(">Done\n");
				break;
			case mWRTREG:
				USART_Send_ConstString(">Write Mode\n");
				for(cnt=0; cnt<8; cnt++)
				{
					dataByte[cnt] = CharHexByte2Int((unsigned char*) data,cnt*2);
				}
				ad9910_write(deviceIdx,CharHexByte2Int((unsigned char*) address,0),dataByte);
				mState=mIDLE;
				USART_Send_ConstString(">Done\n");
				break;
			case mRDREG:
				USART_Send_ConstString(">Read Mode\n");
				ad9910_read(deviceIdx,CharHexByte2Int((unsigned char*) address,0),1);
				mState=mIDLE;
				USART_Send_ConstString(">Done\n");
				break;
			case mFREQ:
				USART_Send_ConstString(">Frequency Mode\n");
				//Str2Int((unsigned char*) freq);
				if(SPI_READ_EN)
				{
					ad9910_read(deviceIdx,0x0E); // Read Register Profile 0
					for(cnt=0; cnt<4; cnt++) // Reuse Non-Frequency Values from Profile 0 Read
					{
						dataByte[cnt] = AD9910_REG_READ[cnt];
					}
				}	
				else
				{
					dataByte[0]=8;
					dataByte[1]=181;
					dataByte[2]=0;
					dataByte[3]=0;
				}		
				
				for(cnt=4; cnt<8; cnt++) // Change Frequency Value
				{
					dataByte[cnt] = CharHexByte2Int((unsigned char*) freq,(cnt-4)*2);
				}
				ad9910_write(deviceIdx,0x0E,dataByte); // Write to DDS
				mState=mIDLE;
				USART_Send_ConstString(">Done\n");
				break;
			case mAMP:
				USART_Send_ConstString(">Amplitude Mode\n");
				for(cnt=0; cnt<2; cnt++) // Change Amplitude Value
				{
					dataByte[cnt] = CharHexByte2Int((unsigned char*) amp,cnt*2);
				}
				ad9910_read(deviceIdx,0x0E); // Read Register Profile 0
				for(cnt=2; cnt<8; cnt++) // Reuse Non-Amplitude Values from Profile 0 Read
				{
					dataByte[cnt] = AD9910_REG_READ[cnt];
				}
				ad9910_write(deviceIdx,0x0E,dataByte); // Write to DDS
				mState=mIDLE;
				USART_Send_ConstString(">Done\n");
				break;
			case mPHASE:
				mState=mIDLE;
				break;
			default:
				mState=mIDLE;
				break;
		}
	}
}
// A: Amplitude
// D: Data
// F: Frequency
// I: Device Index
// L: Data Length
// P: Phase
// R: Register
// T: Test
// X: Master Reset

ISR(USART_RX_vect)
{
	char rxByte=UDR0;
	char printout[50];
	if(mState==mIDLE)
	{
		if(rxByte=='/') {uState=uIDLE;}
		switch(uState)
		{
		case uIDLE: // Home
			if(rxByte=='I')
			{
				uState=uINDEX;
				uCheckSum=0;
			}
			else if(rxByte=='X') // Reset Mode (X)
			{
				mState=mRESET;
				uState=uIDLE;
				uCheckSum=0;
			}
			else if(rxByte=='?') // Check Mode (?)
			{
				mState=mCHECK;
				uState=uIDLE;
				uCheckSum=0;
			}
			else if(rxByte=='*IDN?') // GPIB compatible device ID
			{
				mState=mIDN;
				uState=uIDLE;
				uCheckSum=0;
			}
			break;
		case uINDEX:
			if ((uCheckSum==0)&&(rxByte>='1'&&rxByte<='8'))
			{
				deviceIdx=rxByte-48-1;
				//USART_Send_Byte(rxByte);
				uCheckSum++;
			}
			else if(uCheckSum==1)
			{
				if(rxByte=='T') // Test Mode (T)
				{
					mState=mTEST;
					uState=uIDLE;
				}
				else if(rxByte=='R') // Register Mode (R)
				{
					uState=uADDRESS;
					uCheckSum=0;
				}
				else if(rxByte=='F') // Frequency (F)
				{
					uState=uFREQ;
					uCheckSum=0;
				}
				else if(rxByte=='A') // Amplitude (A)
				{
					uState=uAMP;
					uCheckSum=0;
				}
				else if(rxByte=='P') // Phase (P)
				{
					uState=uPHASE;
					uCheckSum=0;
				}
			}
			else
			{
				uState=uIDLE;
			}
			break;
		case uADDRESS: // Register Mode > Address
			if ((uCheckSum<=1)&&((rxByte>='0'&&rxByte<='9')||(rxByte>='a'&&rxByte<='f')))
			{
				address[uCheckSum]=rxByte;
				uCheckSum++;
			}
			else if ((uCheckSum==2)&&(rxByte=='L'))
			{
				uState=uDATALEN;
				uCheckSum=0;
			}
			else
			{
				mState=mRDREG;
				uState=uIDLE;
			}					
			break;
		case uDATALEN: // Address > Data Length
			if ((uCheckSum==0)&&(rxByte>='1'&&rxByte<='9'))
			{
				dataLen=atoi(&rxByte);
				uCheckSum++;
			}
			else if ((uCheckSum==1)&&(rxByte=='D'))
			{
				uState=uDATA;
				uCheckSum=0;
			}
			else
			{
				uState=uIDLE;			
			}
			break;
		case uDATA: // Data Length > Data
			if ((uCheckSum<(dataLen*2))&&((rxByte>='0'&&rxByte<='9')||(rxByte>='a'&&rxByte<='f')))
			{
				data[uCheckSum]=rxByte;
				uCheckSum++;
				if(uCheckSum==dataLen*2)
				{
					mState=mWRTREG;
					uState=uIDLE;
				}
			}
			else
			{
				sprintf(printout,"DataIdle=%d,%c\n",uCheckSum,rxByte);
				USART_Send_String(printout);
				uState=uIDLE;
			}
			break;
		case uFREQ: // Frequency
			/*
				if ((uCheckSum<6)&&(rxByte>='0'&&rxByte<='9'))
				{
					freq[uCheckSum]=rxByte;
					uCheckSum++;
					if(uCheckSum==6)
					{
						mState=mFREQ;
						uState=uIDLE;
					}
				}
			*/
			if ((uCheckSum<8)&&((rxByte>='0'&&rxByte<='9')||(rxByte>='a'&&rxByte<='f')))
			{
				freq[uCheckSum]=rxByte;		
				uCheckSum++;
				if(uCheckSum==8)
				{
					mState=mFREQ;
					uState=uIDLE;
				}
			}
			else 
			{
				uState=uIDLE;
			}
			break;
		case uAMP: // Amplitude
			if ((uCheckSum<4)&&((rxByte>='0'&&rxByte<='9')||(rxByte>='a'&&rxByte<='f')))
			{
				amp[uCheckSum]=rxByte;
				uCheckSum++;
				if(uCheckSum==4)
				{
					mState=mAMP;
					uState=uIDLE;
				}
			}
			else
			{
				uState=uIDLE;
			}
			break;
		case uPHASE: // Phase
			if ((uCheckSum<4)&&((rxByte>='0'&&rxByte<='9')||(rxByte>='a'&&rxByte<='f')))
			{
				phase[uCheckSum]=rxByte;
				uCheckSum++;
				if(uCheckSum==4)
				{
					mState=mPHASE;
					uState=uIDLE;
				}
			}
			else
			{
				uState=uIDLE;
			}
			break;
		default:
			uState=uIDLE;
		}
	}
	else
	{
		//USART_Send_Byte('X');
	}
}