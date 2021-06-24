import struct
from datetime import datetime
import logging
import logging.handlers
import os
import socket
from struct import unpack_from
from time import sleep
import csv
import pyshark
import sys
import traceback

#set pythonpath=../;
import playerUDP.config as config
from manageGW import GW_Multi_health_status_INS
from manageNAVS import NAVS_MULTI_health_status_INS
from phinx import analyzeUserStatus
from manageUDP import WriteUDP
from utility import MyFormatter

import json

cwd = os.getcwd()

base_dir=os.getcwd() if not os.path.isdir(os.path.join(cwd,'playerUDP')) else os.path.join(cwd,'playerUDP')

logger = logging.getLogger( __name__ )

logDir=os.path.join(cwd,"log")
mapMsg={}
mapManager={}
mapDistinct={}
mapDistinctAction={}

def initLogger():
    LOG_FILENAME="logPlayer_{}.log".format( datetime.strftime( datetime.now(), "%Y%m%d_%H%M%S" ))
    if not os.path.isdir(logDir):
        os.mkdir( logDir)
    else:
        listFile=sorted(os.listdir(logDir))
        listFile=[l for l in listFile if l.startswith("logPlayer_")]
        listFile=listFile[:-5]
        for f in listFile:
            os.remove(os.path.join(logDir,f))

    handler = logging.handlers.RotatingFileHandler(os.path.join(logDir,LOG_FILENAME),
                                                maxBytes=20*1024*1024,
                                                backupCount=5,
                                                )
    formatLog="%(asctime)s\t%(module)s\t%(funcName)s\t%(levelname)s\t%(threadName)s\t:%(message)s"
    formatter = MyFormatter(fmt=formatLog,datefmt='%Y-%m-%d,%H:%M:%S.%f')
    handler.setFormatter(formatter)
    logging.basicConfig( format="%(asctime)s - %(levelname)s:%(message)s",
                        level=logging.INFO,
                        datefmt='%d/%m/%Y %H:%M:%S',handlers=[handler] )

def checkIntegrity(binar,binar2,obj):
    check=True
    if binar2 is None or binar is None:
        logger.error("Valore Null, class: {} {} binar: {} {}".format(obj.__class__.__name__, obj, binar, binar2))
    elif len( binar ) != len( binar2 ) and binar and binar2:
        logger.error( "Differente Lunghezza tra letto e decodificato per scrittura, class: {} {}".format(obj.__class__.__name__,obj) )
        check=False
    else:
        listErrors=[]
        for i in range( len( binar ) ):
            if binar[i] != binar2[i] and i>15:
                listErrors.append("{} {} diversi".format(binar[i], binar2[i]))
                check = False
        if len(listErrors) >0:
            logger.error( "Differente Byte tra letto e decodificato, class{} {}".format( obj.__class__.__name__, obj ) )
    return check

def initMapMsg():
    with open(os.path.join(base_dir,'mappingSCGP.csv'), newline='\r\n') as csvfile:
        reader = csv.reader( csvfile, delimiter='\t')
        i=0
        for row in reader:
            if i==0:
                header=row
            else:

                if row[0]=='N.A.':
                    k=row[2]+":"+row[3]
                else:
                    k=int( row[0] )
                mapMsg[k]={header[i]:row[i] for i in range(len(row))}
            i+=1

def initMapManager():
    list_manager=config.getManagersSimulator()
    for k in list_manager:#config.listUDP_IN + config.listUDP_OUT + [GW_Multi_health_status_INS]:
        obj=k()
        m=obj.getMsgIdentifier()
        if type(m) in [int]:
            mapManager[obj.getMsgIdentifier()]=obj
        else:
            print(f"Errore {k}")
    print("finita init map")


def play(filepcap,send=False):
    cap=None
    try:
        mapTime={}
        test_alarm=True
        cap = pyshark.FileCapture(filepcap)
        w=WriteUDP()
        for packet in cap:
            if hasattr(packet,"data") and hasattr(packet,"udp"):
                message=packet.data.data
                port_dst=int(packet.udp.dstport)
                if hasattr(packet,"ip"):
                    ip_dst=str( packet.ip.dst_host )
                else:
                    ip_dst=str( packet.ipv6.dst_host )
                binar=(bytearray.fromhex(str(message)))
                s=float(packet.frame_info.time_delta)
                if send:
                    sleep(s)
                '''
                Message  Identifier: 32 bit (4 byte)
                Message Sender( IOS ): 16bit (2byte)
                Message Length: 16bit (2 byte)
                TimeStamp( s ): 32bit (4 byte)
                TimeStamp( ms ): 32bit (4 byte)
                '''
                id,sender,length,timestamp_s, timestamp_ms = unpack_from( ">Ihhll", binar)
                
                if id in mapMsg:
                    logger.info(f"id :{id},sender:{sender},length{length},timestamp_s:{timestamp_s}, timestamp_ms:{timestamp_ms}")
                    msgName=mapMsg[id].get("Messaggio")
                    if msgName not in mapDistinct.keys():
                        mapDistinct[msgName]=0
                    mapDistinct[msgName]+=1
                    if msgName not in mapTime:
                        mapTime[msgName]=[]
                    mapTime[msgName].append(s)
                    if id in mapManager:
                        obj=mapManager[id]
                        obj.decode(binar)
                        obj.status = True  # Per eveitare il problema di status(messaggi arrivati) ad esempio _sensorAvailability in NAVS_MULTI_wind_and_landing_deck_data_INS
                        #if obj.__class__.__name__=="GW_SCGF_designation_order_INS":
                        #    print("sto qui")
                        binar2=obj.getData(True)
                        checkIntegrity( binar, binar2,obj)
                        #Test modifica byte Failure
                        if test_alarm:
                            if obj.__class__.__name__=="SCGF_MULTI_health_status_INS":
                                obj.warning_list.failure_byte_01=b'38' #0011 1000
                                analyzeUserStatus(NAVS_MULTI_health_status_INS,0x40000002)
                                test_alarm = False
                            if obj.__class__.__name__=="GW_SCGP_designation_order_INS":
                                print(f"{obj}")
                                #obj.warning_list.failure_byte_01=b'38' #0011 1000
                            
                        else:
                            logger.info("{} length: {} id: {} {}".format(obj.__class__,length,id,str(obj.values())))
                        if hasattr(obj,"action_id"):
                            mapDistinctAction[f"{msgName}[{obj.action_id}]"]=obj.values()
                        elif hasattr(obj,"reported_action_id"):
                            mapDistinctAction[f"{msgName}[{obj.reported_action_id}]"]=obj.values()
                        else:
                            mapDistinctAction[f"{msgName}"]=obj.values()
                    else:
                        logger.info("{} {}".format(id,msgName))
                    if config.localTestUDP:
                        host_name = socket.gethostname()
                        ip_dst= socket.gethostbyname( host_name )
                    if send:
                        w.writeUDP(binar,ip_dst,port_dst,msgName)
                else:
                    logger.info(packet)
                    logger.info("{} {} {} {}".format(id,sender,length,timestamp_s, timestamp_ms))
        logger.info(repr(mapDistinct))
        for msgName in mapTime:
            mapTime[msgName]=reversed(mapTime[msgName])
        logger.info(repr(mapTime))
        logger.info(repr(mapDistinctAction))
        msg=f"fine pacchetti msg {filepcap}"
        logger.info(msg+"\r\n\r\n")
        print(msg)
    except struct.error as e:
        logger.error("Erorre nel {filepcap} pacchetto {packet}")
        logger.error("ERROR DETAIL: ", e )
    except KeyError as e:
        typeExc, value, tb = sys.exc_info()
        msg = "KO {} {} {}".format( typeExc, value,
                                                         traceback.format_list( traceback.extract_tb( tb )[-1:] )[-1] )
        logger.error(f"key ERROR play: {msg}", e )
    except Exception as e:
        typeExc, value, tb = sys.exc_info()
        msg = "KO {} {} {}".format( typeExc, value,
                                                         traceback.format_list( traceback.extract_tb( tb )[-1:] )[-1] )
        logger.error(f"ERROR play: {msg}", e )
        print("fine pacchetti msg con errore")
        print(msg)
    finally:
        if cap:
            cap.close()

def dump(filepcap,send=False):
    cap=None
    try:
        mapTime={}
        mapMsgDump=[]
        cap = pyshark.FileCapture(filepcap)
        for packet in cap:
            if hasattr(packet,"data") and hasattr(packet,"udp"):
                message=packet.data.data
                port_dst=int(packet.udp.dstport)
                if hasattr(packet,"ip"):
                    ip_dst=str( packet.ip.dst_host )
                else:
                    ip_dst=str( packet.ipv6.dst_host )
                binar=(bytearray.fromhex(str(message)))
                '''
                Message  Identifier: 32 bit (4 byte)
                Message Sender( IOS ): 16bit (2byte)
                Message Length: 16bit (2 byte)
                TimeStamp( s ): 32bit (4 byte)
                TimeStamp( ms ): 32bit (4 byte)
                '''
                msgName=""
                id,sender,length,timestamp_s, timestamp_ms = unpack_from( ">Ihhll", binar)
                if id in mapManager:
                    obj=mapManager[id]
                    msgName=type(obj)
                    obj.decode(binar)
                    mapMsgDump.append(obj)
                    if obj.__class__.__name__=="SCGF_MULTI_health_status_INS":
                            obj.warning_list.failure_byte_01=b'38' #0011 1000
                            analyzeUserStatus(NAVS_MULTI_health_status_INS,0x40000002)
                            test_alarm = False
                    elif obj.__class__.__name__=="GW_SCGP_designation_order_INS":
                            print(f"{obj}")
                            #obj.warning_list.failure_byte_01=b'38' #0011 1000
                    else:
                        logger.info("{} length: {} id: {} {}".format(obj.__class__,length,id,str(obj.values())))
                    if hasattr(obj,"action_id"):
                        mapDistinctAction[f"{msgName}[{obj.action_id}]"]=obj.values()
                    elif hasattr(obj,"reported_action_id"):
                        mapDistinctAction[f"{msgName}[{obj.reported_action_id}]"]=obj.values()
                    else:
                        mapDistinctAction[f"{msgName}"]=obj.values()
                elif sender !=25:
                    logger.info("{} {}".format(id,msgName))
            else:
                logger.debug(packet)
                logger.debug("{} {} {} {}".format(id,sender,length,timestamp_s, timestamp_ms))
        logger.info(repr(mapDistinct))
        for msgName in mapTime:
            mapTime[msgName]=reversed(mapTime[msgName])
        logger.info(repr(mapDistinctAction))
        msg=f"fine pacchetti msg {filepcap}"
        logger.info(msg+"\r\n\r\n")
        resp=repr(mapMsgDump)
        print(resp)
        logger.info(resp+"\r\n\r\n")
        
    except struct.error as e:
        logger.error("Erorre nel {filepcap} pacchetto {packet}")
        logger.error("ERROR DETAIL: ", e )
    except KeyError as e:
        typeExc, value, tb = sys.exc_info()
        msg = "KO {} {} {}".format( typeExc, value,
                                                         traceback.format_list( traceback.extract_tb( tb )[-1:] )[-1] )
        logger.error(f"key ERROR dump: {msg}", e )
    except Exception as e:
        typeExc, value, tb = sys.exc_info()
        msg = "KO {} {} {}".format( typeExc, value,
                                                         traceback.format_list( traceback.extract_tb( tb )[-1:] )[-1] )
        logger.error(f"ERROR dump: {msg}", e )
        print("fine pacchetti msg con errore")
        print(msg)
    finally:
        if cap:
            cap.close()

if __name__ == "__main__":
    try:
        initLogger()
        initMapMsg()
        initMapManager()
        for f in ['designation.pcapng']:
            fileCapture=os.path.join(base_dir,f)
            dump(fileCapture,False)
        for f in ['health_status.pcap','prova_sede.pcapng','servo.pcapng']:
            fileCapture=os.path.join(base_dir,f)
            play(fileCapture,True)
    except Exception as e:
        print("Eccezione",e)
