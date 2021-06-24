import configparser
import sys
import traceback
from struct import unpack_from

import numpy as np
from manageUDP import mapMsgUdpOUT
from datetime import datetime
import logging
import logging.handlers
import time

mapMsg={}
mapMsgUdpIn={}
listErrors=[]
logger = logging.getLogger( __name__ )
'''
in 'MWV':
            element = Weather_instrument_MWV()
        if messageId == 'XDR':
            element = Weather_instrument_XDR()
        if messageId == 'MTW':
            element = Weather_instrument_MTW()
        if messageId == 'GGA':
            element = Giro_GPGGA()
        if messageId == 'GLL':
            element = Giro_GPGLL()
        if messageId == 'GST':
            element = Giro_GPGST()
        if messageId == 'VTG':
            element = Giro_GPVTG()
'''
def getManagerClass(manager_class):
        '''if manager_class.startswith("NAVS"):
            obj = eval( "navs."+manager_class )
        elif manager_class.startswith("SCGP"):
            #obj_pointer=getattr( module, manager ) #<class 'manageSCGP.SCGP_Multi_health_status_INS'>
            #obj=obj_pointer()
            obj = eval( "scgp." + manager_class )
        elif manager_class.startswith( "SCGF" ):
            obj = eval( "scgf." + manager_class  )
        elif manager_class.startswith( "GW" ):
            obj = eval( "gw." + manager_class )
        else:
            obj=None
        '''
        import manageSCGP as scgp
        import manageSCGF as scgf
        import manageSCGS as scgs
        import manageNAVS as navs
        import manageGW as gw
        obj = None
        pkg = manager_class[0:4].lower()
        if pkg.startswith("gw"):
            pkg = "gw"
        if pkg in ["navs","gw","scgp","scgs","scgf"]:
            obj = eval( f"{pkg}.{manager_class}" )
        return obj
class MessageManager:
    mapMsgAllSerial={}
    mapMsgUDP={}
    @staticmethod
    def getMapMsgSerial():
        from config import listWI, listGiro
        if len(MessageManager.mapMsgAllSerial) == 0:
            listMsgSerial=listWI+listGiro
            for m in listMsgSerial:
                MessageManager.mapMsgAllSerial[m.template[1:6]]=m
        return MessageManager.mapMsgAllSerial

    @staticmethod
    def getMapMsgUDP():
        from config import listUDP_IN
        if len( MessageManager.mapMsgUDP ) == 0:
            for k in listUDP_IN:
                m=k()
                MessageManager.mapMsgUDP[m.getMsgIdentifier()] = k
        return MessageManager.mapMsgUDP

def parseMessage(data,source):
    try:
        messageId = data[1:6]
        from config import listWI, listGiro, listUDP_OUT
        error = False
        element = None
        managerName =None
        if messageId not in MessageManager.getMapMsgSerial():
            logger.info(f"Messaggio non gestito  {messageId}")
            return
        k = MessageManager.getMapMsgSerial()[messageId]
        element = k()
        element.source=source
        element.decode( data )
        #Cambio messageID se esiste la funzione [MWV->Relative or Absolute MWVR, MWVT]
        if source>1:
            messageId+=str(source)
        if hasattr(element, "getMessageId_postfix"):
            messageId += f".{element.getMessageId_postfix()}"
        crc_calcolato = '{:02X}'.format( element.checksum( data ) )
        crc_in = data[data.find( '*' ) + 1:data.find('\r')]
        if crc_calcolato == crc_in:
            error = False
            mapMsg[messageId]=element
            first=False
            for m in listUDP_OUT:
                manager=m()
                if not hasattr(manager,"listMsg"):
                    continue
                if messageId in manager.getNmeaCode():
                    managerName=manager.__class__.__name__
                    first= managerName not in mapMsgUdpOUT #Flag MsgFirst
                    if first:
                        mapMsgUdpOUT[managerName]=manager
                    else:
                        manager=mapMsgUdpOUT[managerName]
                manager.process()
                if first:
                    if hasattr(manager,"timeLoop") and not hasattr(manager,"action_id"):
                        manager.schedule()
                    else:
                        logger.error(f"Sulla classe {managerName} è presente gli attributi timeLoop e action_id")
            #if m.status:
                #m.sendUDP("NAVS_MULTI_wind_and_landing_deck_data_INS")
        else:
            error = True
            logger.error( "Errore", crc_calcolato, "crc diverso da: ", crc_in )
    except Exception as e:
        typeExc, value, tb = sys.exc_info()
        msg = "KO {} {} {}".format( typeExc, value,traceback.format_list( traceback.extract_tb( tb )[-1:] )[-1] )
        logger.error( "Error Parse Msg erial class:{} data: {}, source: {} error: {}".format( managerName, data, source , msg) ,e )

def getConf(class_, config_file, list_sections:list=None):
    config = configparser.ConfigParser()
    config.read( config_file )
    if list_sections is not None or len(list_sections)>0:
        sections = list_sections
        missed = set(list_sections)-set(config.sections())
        if len(missed)>0:
            logger.error(f"MISSED SECTION {missed}")
            sections=[]
    else:
        sections = config.sections()
    for section in sections:
        for item in config.items( section ):
            name = item[0]
            value = item[1]
            logger.info( name+ ": "+value )
            if value != "":
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value is not None and value.startswith("[") and value[-1]=="]":
                    value=eval(value)
            setattr( class_, name, value )

def convertUTC(dateZDA,time):
    dateZDA=(datetime.now().strftime("%d/%m/%Y")) if not dateZDA else dateZDA
    dateForEpoch=datetime.strptime("{} {}".format(dateZDA,time), '%d/%m/%Y %H%M%S.%f')
    dateEpoch=dateForEpoch.timestamp()
    return int(dateEpoch),(datetime.now()-dateForEpoch).microseconds

def parseUDP(data,addr):
    try:

        '''
        se le prime cifre dell'header sono SCGP_GW_ACK e addr= SCGP_GW_acknowledgment_INS.port
        allore utility.mapMsgUdpOUT[SCGP_GW_acknowledgment_INS]=data
        elif le prime cifre dell'header sono SCGP_GW_designation_report_INS e addr= SCGP_GW_designation_report_INS.port
        allora utility.mapMsgUdpOUT[SCGP_GW_designation_report_INS]=data
        '''
        from config import listUDP_IN,localTestUDP
        from manageUDP import UDPAdapter
        message_id, sender,messageLength,timestamp_s,ms= UDPAdapter.decodeHeader(data)
        mapManager=MessageManager.getMapMsgUDP()
        if message_id not in mapManager:
            logger.error(f"Received UDP unmapped Message: {message_id} sender:{sender}, {addr[0]}:{addr[1]} messageLength:{messageLength} ms: {ms}" )
        else:
            k=mapManager[message_id]
            if (k.port == addr[1] and k.ip == addr[0]) or localTestUDP:
                m = k()
                '''
                Message  Identifier: 32 bit (4 byte)
                Message Sender( IOS ): 16bit (2byte)
                Message Length: 16bit (2 byte)
                TimeStamp( s ): 32bit (4 byte)
                TimeStamp( ms ): 32bit (4 byte)
                 '''
                cls=m.__class__.__name__
                logger.debug(f"Received UDP Message: {cls}, {addr[0]}:{addr[1]}" )
                if message_id==m.getMsgIdentifier() and sender==m.getMsgSender():
                    if cls not in mapMsgUdpIn:
                        mapMsgUdpIn[cls]=m
                    else:
                        m=mapMsgUdpIn[cls]
                    if timestamp_s > 0:
                        m.timestamp=datetime.fromtimestamp(timestamp_s)
                    m.decode(data)
                    if hasattr(m,"reported_action_id"):
                        from decoder_scg import ActionManager
                        logger.info(f"Received UDP Message: {cls},{m.reported_action_id}, {addr[0]}:{addr[1]}" )
                        ActionManager.AckObj(m)
                    elif hasattr(m,"action_id") and hasattr(m,"process"):
                        m.process()
                        logger.info(f"Sended UDP Message: {cls}, {m.action_id},{addr[0]}:{addr[1]}" )
    except Exception as e:
        logger.error(f"Error Parse Udp: class_name={cls}, data: {data}, address: {addr[0]} port: {addr[1]}",e)

def getType(types,names,values={}):
    formatUnpack = ">"  # >" if instance == self and offset==0 else """
    calculate_len = 0
    for i in range( len( types ) ):
        t = types[i]
        if t in [np.uint]:  # "action_id", "seconds", "microseconds"
            formatUnpack += "I"
            calculate_len += 4
        elif t in [np.intc]:
            formatUnpack += "i"
            calculate_len += 4
        elif t in [float]:
            formatUnpack += "f"
            calculate_len += 4
        elif t in [bool]:
            formatUnpack += "?"
            calculate_len += 1
        elif t in [int]:
            formatUnpack += "h"
            calculate_len += 2
        elif t in [str]:
            formatUnpack += "c"
            if names[i] in values:
                size=len(values[names[i]])
                formatUnpack += "c"*size
                calculate_len += size
            else:
                formatUnpack += "c"
                calculate_len += 1
        elif t in [bytes]:
            formatUnpack += "B"
            calculate_len += 1
        else:
            raise Exception( "Tipo non gestito:" + names[i] )
    return formatUnpack,calculate_len

class MyFormatter(logging.Formatter):
    converter=datetime.fromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s

def setup_logger(name, log_file, level=logging.INFO,log=None):
    from config import  logDir,conf
    """To setup as many loggers as you want"""
    formatter = MyFormatter('%(asctime)s\t%(levelname)s\t%(message)s')
    #handler = logging.FileHandler(log_file)
    #handler.setFormatter(formatter)

    rotateHandler = logging.handlers.RotatingFileHandler(
                                                    filename=log_file,
                                                    mode='a',
                                                    maxBytes=conf.log_rotate,
                                                    backupCount=conf.log_max_file,
                                                    delay=False
                                                    )

    if log is None:
        log = logging.getLogger(name)
        rotateHandler.setFormatter(formatter)
    log.setLevel(level)
    #logger.addHandler(handler)
    log.addHandler(rotateHandler)
    return log



