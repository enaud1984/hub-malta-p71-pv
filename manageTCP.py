import copy
import os 
import datetime
import logging
import select
import socket
import sys
import threading
import traceback
from struct import pack, unpack, unpack_from
import numpy as np


import utility as utility
from utility import setup_logger,listErrors

logger=logging.getLogger(__name__)

class TCPManager:
    mapSockets = {}
    sockets = []
    map_ip = {}
    _processThread=None
    def setSockets(self,list_ip,ports):
        for ip in list_ip:
            for port in ports:
                logger.info( f"source configured from TCP ip: {ip} port: {port} " )
                if port not in self.mapSockets:
                    server_socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                    try:
                        server_socket.connect( (ip, port) )
                        self.mapSockets[port] = server_socket
                        self.sockets.append( server_socket )
                    except Exception as e:
                        typeExc, value, tb = sys.exc_info()
                        msg= "KO ip:'{}', port:{} {} {} ".format( ip, port,typeExc, value )
                        logger.error(msg,e)
                        listErrors.append({"name":"TCPManager","Error":msg,"timestamp":datetime.datetime.now(),"stacktrace":traceback.extract_tb( tb )[-1:]})
                        continue
        i=1
        for ip in list_ip:
            if ip not in self.map_ip:
                self.map_ip[ip] = i
                i += 1
    
    def __init__(self, file, section):
        try:
            from config import listUDP_IN
            
            utility.getConf( self, file, section )
            if type(self.list_ip_gyro)==list:
                list_ip=self.list_ip_gyro
            else:
                list_ip=[self.list_ip_gyro]
            ports=[int(p) for p in self.ports_gyro]
            
            self.setSockets(list_ip,ports)
            if type(self.list_ip_meteo)==list:
                list_ip=self.list_ip_meteo
            else:
                list_ip=[self.list_ip_meteo]
            ports=[int(p) for p in self.ports_meteo]
            self.setSockets(list_ip,ports)
            self.start()
        except Exception as e:
            logger.error( "Error socket {}, {}".format( list_ip, ports ), e )
    
    def start(self):
        self._reader = ReadTCP()
        TCPManager._processThread = threading.Thread( target=self._reader.runRead, args=(self.sockets,self.map_ip) )
        TCPManager._processThread.start()

    @staticmethod
    def stop():
        ReadTCP.closeServer=True
        if TCPManager._processThread:
            TCPManager._processThread.join(1)

class ReadTCP:
    mapResiduo = {}
    mapIp={}
    mapTot={}
    closeServer=False
        
    def initMaps(self,map_ip):
        from config import logDir
        self.commonLog=setup_logger(f'tcp_common', os.path.join(logDir,f'tcp.log'))
        for ip in map_ip:
            self.mapIp[ip]=map_ip[ip]
            self.mapTot[ip]=0
     
    def parseMessage(self,addr,port,data_s,count):
        residuo = self.mapResiduo.get(f"{addr}_{port}")
        if residuo is not None:
            data_s=residuo+data_s
            residuo=None
            del self.mapResiduo[f"{addr}_{port}"]
        msg = data_s.split("\r\n")
        for m in msg:
            if count is not None:
                self.mapTot[addr]=+1
            if m.startswith("$") and len(m)>3 and m[-3]=="*":
                try:
                    utility.parseMessage(f"{m}\r\n",self.mapIp.get(addr) or 1)
                    logger.debug(f"Message TCP in input from: {addr}:{port} msg: {m}")
                except Exception as e:
                    logger.error( f"Eccezione lettura messaggio: {addr} {port} at row {self.mapTot.get(addr)}", e )
                    self.commonLog.error(f"{addr}\t{m}",e)
                finally:
                    self.commonLog.info(f"{addr}\t{m}")
            elif m.startswith("$") or len(m)<3 or m[-3]=="*":
                residuo=m
                self.mapResiduo[f"{addr}_{port}"]=residuo
    
    def checkData(self,count,addr,port,data_s):
        if count is not None and count==0 and not data_s.startswith("$"):
            init = data_s.find("$")
            if init<0:
                self.commonLog.info(f"init not Found: {addr} {port} {data_s}")
                logger.warning( f"init not Found: {addr} {port} {data_s}" )
                return None
            else:
                header = data_s[:init]
                data_s = data_s[init:]
                logger.info( f"risp: {addr} {port} header: {header} pos_first:{init} data:{data_s}" )
        return data_s

    def runRead(self,sockets,map_ip):
        try:
            addr = None
            port = None
            self.initMaps(map_ip)
            logger.info(f"Listner Message TCP {map_ip}")
            while not ReadTCP.closeServer:
                readable, writable, exceptional = select.select( sockets, [], [] )
                for s in readable:
                    data,addr = s.recvfrom( 1024 )
                    port = s.getsockname()[1]
                    addr = s.getsockname()[0]
                    count = self.mapTot.get(addr)
                    data_s = data.decode("utf-8")
                    data_s = self.checkData(count,addr,port,data_s)
                    if data_s is not None:
                        self.parseMessage(addr,port,data_s,count)
                      
            self.close(sockets)
        except Exception as e:
            logger.error( f"Eccezione lettura TCP address: {addr} {port} at row {self.mapTot.get(addr)}", e )
            self.close(sockets)
    
    def close(self,sockets):
        for s in sockets:
            s.close()
