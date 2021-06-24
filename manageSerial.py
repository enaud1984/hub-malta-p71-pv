import os
from time import sleep

import serial

from config import configFile, baseDir, logDir
from utility import parseMessage,setup_logger
from utility import getConf

import threading
import logging


logger = logging.getLogger( __name__ )

def serial_read(reader,file,section,source):
    return reader(file,section,source).start()

class ManageSerial:
    listThreads=[]
    @staticmethod
    def start(n_serial,configFile):
        for i in range( n_serial ):
            thread = threading.Thread( target=serial_read, args=(ReadSerial,
                                                                 configFile,
                                                                 ["SERIAL PORT CONFIGURATION" + str( i + 1 )], i + 1), )
            ManageSerial.listThreads.append(thread)
            thread.start()
    @staticmethod
    def stop():
        for t in ManageSerial.listThreads:
            t.join(1)

class WriteSerial():
    def __init__(self, conf,section):
        getConf( self, conf,section )
        self.ser = serial.Serial(
            port=self.port,  # "/dev/ttyS0",
            baudrate=int( self.baudrate ),
            parity=eval( self.parity ),
            stopbits=eval( self.stopbits ),
            bytesize=eval( self.bytesize )
        )
        '''
        timeout=int( self.timeout ),
        rtscts=self.rtscts,
        dsrdtr=self.dsrdtr
        '''
        logger.info(f" PORTA {self.port} baudrate={self.baudrate}, parity={self.parity },stopbits={self.stopbits}, bytesize={self.bytesize} APERTA CORRETTAMENTE...")

    def writeOnSerial(self,data):
        self.ser.write(data.encode())
        logger.info("Scrittura su seriale {} OK".format(self.port))

    def close(self):
        if self.ser:
            self.ser.close()
            logger.info(f"PORTA {self.port} CHIUSA CORRETTAMENTE...")

class ReadSerial():
    closeServer=False
    def __init__(self, conf,section,source=1):
        getConf( self, conf,section )
        self.source=source
        self.ser = serial.Serial(
            port=self.port,  # "/dev/ttyS0",
            baudrate=int( self.baudrate ),
            parity=eval( self.parity ),
            stopbits=eval( self.stopbits ),
            bytesize=eval( self.bytesize ),
            timeout=float( self.timeout ),
            rtscts=self.rtscts,
            dsrdtr=self.dsrdtr
        )
        self.logger = setup_logger(f'serial_{source}', os.path.join(logDir,f'serial{source}.log'))

        # ser.rs485_mode = serial.RS485Settings() da vedere se dobbiamo impostare paramentri per la 485

    def start(self):
        if (self.ser.isOpen() == True):
            self.ser.close()
        try:
            self.ser.open()
        except Exception as e:
            logger.error(f"Errore apertura {self.source} PORTA {self.port}  ",e)
            raise e
        logger.info( f"{self.source} PORTA {self.port} baudrate={self.baudrate},parity={self.parity },stopbits={self.stopbits}," + \
            f" bytesize={self.bytesize}, bytesize={self.bytesize},timeout={ self.timeout },rtscts={self.rtscts},dsrdtr={self.dsrdtr} APERTA CORRETTAMENTE..." )
        self.ser.reset_input_buffer()
        try:
            while not ReadSerial.closeServer:
                pending=self.ser.inWaiting()
                if pending:
                    data = self.ser.readline().decode()
                    self.logger.info(data.replace("\r\n",""))
                    if len( data ) > 3:
                        logger.debug("Messaggio Ricevuto:" + data )
                    else:
                        continue
                    parseMessage(data,self.source)
        except Exception as e:
            logger.error( f"Error {self.port} ",e)
        finally:
            if self.ser:
                self.ser.close()
            logger.info( f"{self.source} PORTA {self.port} CHIUSA CORRETTAMENTE..." )
            
    @staticmethod
    def stop():
        ReadSerial.closeServer = True
        
    def close(self): #da fare a servizio
        if self.ser:
            self.ser.close()
            logger.info( f"{self.source} PORTA {self.port} CHIUSA CORRETTAMENTE..." )

class ReadFile():#(WriteSerial)

    def __init__(self, file,section="SERIAL PORT CONFIGURATION",routeOnSerial=False,source=None):
        self.section = section
        self.file = file
        self.source = source
        self.routeOnSerial=routeOnSerial

        if self.routeOnSerial:
            self.t=threading.Thread(target=self.startSerialRead)
            ser = WriteSerial( configFile, [section] )
            self.ser = ser
        else:
            self.t=threading.Thread(target=self.startFile)

    def startFile(self):
        sleep(10)
        logger.info( f"lettura {self.source} {self.file} ..." )
        i=1
        with open( self.file ) as fp:
            for data in fp:
                if self.routeOnSerial:
                    self.ser.writeOnSerial(data)
                else:
                    parseMessage( data, self.source)
                    sleep(0.001)
                    if data.startswith("$AIPOV"):
                        sleep(0.1)
                i+=1
        #self.closeSerial()
        logger.info( f"fine {self.source} lettura {self.file} righe {i}")
        print(f"fine {self.source} lettura {self.file} righe {i} ")
    
    def start(self):
        self.t.start()

    def startSerialRead(self):
        ReadSerial( configFile, [self.section] ).start()
        self.startFile()

    def stopSerialRead(self):
        logger.info( f"stop serial {self.source} file {self.file} ")
        del self.t
