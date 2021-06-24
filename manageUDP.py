import copy
import datetime
import logging
import select
import socket
import sys
import threading
import traceback
from struct import pack, unpack, unpack_from
import numpy as np
import time
import utility as utility

logger = logging.getLogger( __name__ )

"""
    Documentazione = https://docs.python.org/3/library/socket.html
"""

mapMsgUdpOUT = {}
mapMsgUdpIN = {}
CUSTOM_ARGS = ["source", "ip", "port", "formato_payload",
               "timeLoop", "listMsg", "source",
               "instance", "payload",
               "status", "timestamp", "listTypes","fixed_size"]

def read_udp(file, section):
    return UDPManager( file, section )

def timeit(method,*args, **kw):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            if ((te - ts) * 1000)>10:
                logger.warning('timing class %s %r  %2.2f ms' % \
                    (args[1],method.__name__, (te - ts) * 1000))
        return result
    return timed

class UDPManager:
    listClass = []
    listManager = {}
    sockets = []
    _reader = None
    _processThread=None
    def __init__(self, file, section):
        try:
            from config import listUDP_IN,conf,host_ip
            from utility import listErrors
            host_name=None
            host_ip=None
            port = None
            utility.getConf( self, file, section )

            self.start_GW_Multi_health_status_INS()  # parte l'healthstatus ogni secondo

            for c in listUDP_IN:
                port = c.port
                logger.info( f"Class Read from UDP port: {c.port} ip: {c.ip} class: {c.__name__}" )
                if port not in self.listManager:
                    t = c()
                    host_name = socket.gethostname()
                    host_ip = socket.gethostbyname( host_name )
                    host_ip = conf.host_ip
                    self.listManager[c.port] = [f"{t.__class__.__name__}"]
                    server_socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM , socket.IPPROTO_UDP)
                    try:
                        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        server_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32) 
                        server_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
                        server_socket.bind( ('', c.port) )
                        
                        server_socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host_ip))
                        server_socket.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, 
                                socket.inet_aton(c.ip) + socket.inet_aton(host_ip))

                        self.sockets.append( server_socket )
                    except Exception as e:
                        typeExc, value, tb = sys.exc_info()
                        msg= "KO ip:'{}', port:{} {} {} ".format( host_ip, port,typeExc, value )
                        logger.error(msg,e)
                        listErrors.append({"name":"UDPManager","Error":msg,"timestamp":datetime.datetime.now(),"stacktrace":traceback.extract_tb( tb )[-1:]})
                else:
                    self.listManager[c.port].append(f"{c.__name__}")
            self.start()
        except Exception as e:
            logger.error("Error socket {}, {} {}".format(host_name,host_ip,port),e)
     
    def start(self):
        self._reader =ReadUDP()
        UDPManager.processThread = threading.Thread( target=self._reader.runRead, args=(self.sockets,self.listManager) )
        UDPManager.processThread.start()

    @staticmethod
    def stop():
        ReadUDP.closeServer=True
        if UDPManager._processThread:
            UDPManager._processThread.join(1)

    def start_GW_Multi_health_status_INS(self):
        from config import getMulti_health_status_INS
        health_status_class=getMulti_health_status_INS()
        if health_status_class is not None:
            logger.info( f"istanzio : {health_status_class.__name__}" )
            manager = health_status_class()
            mapMsgUdpOUT[health_status_class.__name__] = manager
            manager.schedule()

class ReadUDP():
    closeServer=False
    def runRead(self,sockets,listManager):
        try:
            empty = []
            addr = None
            logger.info(f"Listner Message UDP {listManager}")
            while not ReadUDP.closeServer:
                readable, writable, exceptional = select.select( sockets, [], [] )
                for s in readable:
                    (data, addr) = s.recvfrom( 1024 )
                    utility.parseUDP( data, addr )
        except Exception as e:
            logger.error( f"Eccezione lettura UDP address: {listManager} {addr}", e )
        finally:    
            self.close(sockets)
    
    def close(self,sockets):
        for s in sockets:
            s.close()

class WriteUDP:
    # da spostare?
    sock = None
    def init_socket(self,group,host_ip):
        addrinfo = socket.getaddrinfo(group, None)[0]
        #socket.socket( socket.AF_INET,  # Internet
        #                socket.SOCK_DGRAM,
        #                 )  # UDP
        self.sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM,socket.IPPROTO_UDP)
        # Set Time-to-live (optional)
        ttl_bin = pack('@i', 1)
        self.sock.setsockopt(socket.IPPROTO_IP,
                                 socket.IP_ADD_MEMBERSHIP,
                                 socket.inet_aton(group) +
                                 socket.inet_aton(host_ip))
        #self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        if addrinfo[0] == socket.AF_INET: # IPv4
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
        else:
            self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
            
    def writeUDP(self, data, ip, port, msg_name):
        try:
            host_ip=ip
            if self.sock is None:
                self.init_socket(ip,host_ip)
            # self.sock.setsockopt( socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton( ip ) )
            self.sock.sendto( data, (ip, port) )
            logger.debug( "Pacchetto \"{}\" inviato, porta={}, ip={}".format( msg_name, port, ip ) )
        except Exception as e:
            logger.error( f"Eccezione {msg_name} invio UDP address: {host_ip} verso {ip}:{port}", e )
     

def getListAttribute(obj):
    # variables = [i for i in dir( self ) if not inspect.ismethod( i ) and not i.startswith("__") and not i.startswith("get") and i not in ["notify","sendUDP","test","schedule","w","values","header","process","decodeUdp","send"]]
    import inspect
    attributes = inspect.getmembers( obj, lambda a: not (inspect.isroutine( a )) )

    variables = [a[0] for a in attributes if
                 not ((a[0].startswith( '_' ))
                      or a[0] in CUSTOM_ARGS
                      or inspect.ismethod( a[0] )
                      )
                 ]
    return variables


class UDPAdapter:
    _writer = WriteUDP()
    status = False
    timestamp = None  # dell'header di sendUDP
    listTypes = None  # problema garbage collector types

    def __repr__(self):
        try:
            from decoder_scg import decoder
            names = self.getListAttribute()
            values = [getattr( self, k ) for k in names]
            descr = "'name': '{}', ".format( self.__class__.__name__ )
            for i in range( len( names ) ):
                val = decoder.decodeValueEnum( self, names[i], values[i] )
                if type( val ) == str:
                    val = f"'{val}'"
                descr += f" '{names[i]}':{val},"
            ret=descr
            return "{" + ret + "}"
        except Exception as e:
            logger.error("Errore Repr names: {} class: {}".format(names,self.__class__.__name__),e)
            return e
    
    def getMapMsgSerial(self):
        from copy import deepcopy
        from utility import mapMsg
        ret={}
        ret.update(mapMsg)
        #ret = deepcopy(ret)
        return ret

    # associo valore a variabile in dict val
    def values(self, decode=True,api=False):
        val = {}
        variables = self.getListAttribute()
        from common_struct import BaseStruct      
        import json
        nameMsg = self.__class__.__name__
        for k in variables:
            value = getattr( self, k )
            if decode:
                from decoder_scg import decoder
                obj = self
                value = decoder.decodeValueEnum( obj, k, value )
            
            if api and isinstance(value,BaseStruct):
                j=f"{repr(value)}".replace("'",'"').replace(",}","}")
                v=json.loads(j)
                val[k]=v
            else:    
                val[k] = value
             
        val["name"] = nameMsg
        if hasattr(self,"source"):
            val["source"] = self.source
        else:
            val["source"] = 1
        return val

    def getListAttribute(self):
        # variables = [i for i in dir( self ) if not inspect.ismethod( i ) and not i.startswith("__") and not i.startswith("get") and i not in ["notify","sendUDP","test","schedule","w","values","header","process","decodeUdp","send"]]
        return getListAttribute( self )

    def header(self, data):
        '''
        Message  Identifier: 32 bit (4 byte)
        Message Sender( IOS ): 16bit (2byte)
        Message Length: 16bit (2 byte)
        TimeStamp( s ): 32bit (4 byte)
        TimeStamp( ms ): 32bit (4 byte)
        '''
        now = datetime.datetime.now()
        dt_s = now.timestamp()
        self.timestamp = now
        dt_us = dt_s % 1

        return pack( '>Ihhll',  # >: bigEndian
                     self.getMsgIdentifier(),
                     self.getMsgSender(),
                     int( len( data ) + 16 ),
                     int( dt_s ),
                     int( dt_us * 1000000 ) )
    @staticmethod
    def decodeHeader(data):
        return unpack( '>Ihhll', data[0:16] )

    def getNmeaCode(self):
        #return [k[2:5] for k in self.listMsg]
        return [k for k in self.listMsg]

    def getMsgIdentifier(self):
        pass

    def getMsgSender(self):
        pass

    def getValueFromInput(self, msg, k, element, condition=None):  # condition è un dict
        if condition is not None:
            for e in msg._values:
                if e[condition["field_control"]] == condition["expected_value"]:
                    return e[element]
        else:
            return msg._values[0][element]
        return None

    def process(self):
        pass

    def decode(self, buffer):
        return self.decodeUdp( None, buffer, 16 )

    def decodeUdp(self, struct_class, data, offset=0):
        try:
            buffer = copy.deepcopy( data )
            instance = None
            if struct_class is not None:
                instance = struct_class()
                if hasattr( instance, "getListAttribute" ):
                    names = instance.getListAttribute()
                else:
                    names = getListAttribute( instance )
            else:
                instance = self
                names = instance.getListAttribute()
            if instance.listTypes is None:
                types = [type( getattr( instance, k ) ) for k in names if
                         type( getattr( instance, k ) ) in [float, bool, int, str, bytes, np.intc, np.uint]]
                values ={ k:getattr( instance, k )  for k in names if
                           type( getattr( instance, k ) ) in [float, bool, int, str, bytes, np.intc, np.uint]}
                instance.listTypes = {"types":types,"values":values}
            else:
                types = instance.listTypes["types"]
                values = instance.listTypes["values"]
            formatUnpack, calculate_len = utility.getType( types, names,values )
            if len( formatUnpack ) - 1 + offset > len( buffer ):
                logger.error(
                    f"error len decodeudp class {self.__class__} buffer {buffer} formatUnpack {formatUnpack} instance_class:{instance.__class__}" )
            self.checkPacket( calculate_len, offset, buffer, formatUnpack, instance )
            obj = unpack_from( formatUnpack, buffer, offset )
            dirV = {}
            for i in range( len( types ) ):
                dirV[names[i]] = obj[i]

            for k, v in dirV.items():
                setattr( instance, k, v )

            return instance, formatUnpack
        except AttributeError as error:
            # Output expected AttributeErrors.
            path_class = self.__class__.__name__ + "." + instance.__class__.__name__ if self != instance else str(
                instance.__class__ )
            if len( buffer ) > 16:
                id, sender, length, timestamp_s, timestamp_ms = UDPAdapter.decodeHeader( buffer )
                logger.error( "Errore decodeUDP on {} id:{} sender:{} length:{} k:{} v:{}".format(
                    path_class, id, sender, length, k, v ) )
            else:
                logger.error( "Errore decodeUDP on {} setting k:{} on obj:{}".format( path_class, k, obj ) )

            logger.error( "ATTRIBUTE ERROR: ", error )
        except Exception as exception:
            # Output unexpected Exceptions.
            path_class = self.__class__.__name__ + "." + instance.__class__.__name__ if self != instance else str(
                instance.__class__ )
            if len( buffer ) > 16:
                id, sender, length, timestamp_s, timestamp_ms = UDPAdapter.decodeHeader( buffer )
                logger.error( "Errore decodeUDP on {} id:{} sender:{} length:{} timestamp_s:{} timestamp_ms:{}".format(
                    path_class, id, sender, length, timestamp_s, timestamp_ms ) )
            else:
                logger.error( "Errore decodeUDP on {} obj:{}".format( path_class, obj ) )
            logger.error( "DETTAGLIO Exception: ", exception )

    def test(self):
        try:
            test = [type( k ) for k in [*self.payload]]
            err = {}
            formato = self.formato_payload
            for i in range( len( test ) ):
                expected = test[i]
                current = formato[i].replace( 'l', 'i' ).replace( 'h', 'i' ).replace( 'I', 'i' )
                if expected in [np.uint, np.intc, int]:
                    expected = "i"
                elif expected==float:
                    expected = "f"
                elif expected == bool:
                    expected = "?"
                elif expected == bytes:
                    expected = "B"
                elif expected == str:
                    expected = "c"
                if (current != expected):
                    err[i] = "Error colonna: %d tipo atteso: %s tipo ricevuto: %s " % (i, formato[i], test[i])
            return err
        except Exception as e:
            logger.error( "ERRORE test()" )

    def setActionID(self,action_id):
        from decoder_scg import ActionManager
        # non va incrementato quando siamo nel player altrimenti sono diversi
        ActionManager.NextActionId( self,action_id)

    def getData(self, test=False):
        err = {}
        data = None
        try:
            if test:
                err = self.test()
            payload=list(self.payload)
            formato_payload=self.formato_payload
            data_payload = pack( ">" + formato_payload, *payload )

            data_payload,formato_payload=self.manageFixedSize(data_payload,formato_payload)
            header = self.header( data_payload )
            data = header + data_payload
            return data
        except Exception as e:
            typeExc, value, tb = sys.exc_info()
            err["Error sendUDP"] = "KO {} {} {}".format( typeExc, value,
                                                         traceback.format_list( traceback.extract_tb( tb )[-1:] )[-1] )
        if len( err ) > 0:
            if data is not None:
                logger.error( "Lista errori %s %s" % (err, unpack( self.formato_payload, data[16:] )) )
            else:
                logger.error( "Lista errori %s classe: %s" % (err, self.__class__.__name__) )
        return None

    def manageFixedSize(self,data_payload,formato_payload):
        from config import ENABLE_FIXED_SIZE
        if ENABLE_FIXED_SIZE and hasattr( self, "fixed_size" ):
            zeros = (self.fixed_size - len( data_payload )) * b'0'
            data_payload += zeros
            formato_payload += 'B' * len( zeros )
        return data_payload,formato_payload

    #@timeit
    def sendUDP(self, msg_name,setActionID=True):
        try:
            data = self.getData()
            if data is not None:
                if hasattr( self, "action_id" ):
                    self.setActionID(self.action_id)
                    logger.info(f"{msg_name} Action ID: {self.action_id}")
                ip = self.ip
                #ip = "226.1.3.69"
                self._writer.writeUDP( data, ip , self.port, msg_name )
            else:
                logger.error( f"Messsaggio vuoto {msg_name} ")    
        except:
            typeExc, value, tb = sys.exc_info()
            logger.error( "Error {} descr:{} {} {}".format( msg_name,typeExc, value,
                                                traceback.format_list( traceback.extract_tb( tb )[-1:] )[-1] ) )

    def schedule(self):
        timeLoop=self.timeLoop
        from manageScheduler import add_job
        add_job(self.send,self.__class__.__name__,timeLoop)
       

    def send(self):
        try:
            if self.status:
                self.sendUDP( self.__class__.__name__ )
            self.notify()
        except Exception as e:
            logger.error( "ERROR SEND MESSAGE " + e ,e)

    def notify(self):
        pass

    def checkPacket(self, calculate_len, offset, buffer, formatUnpack, instance):
        if instance is None or self != instance:
            return
        if (calculate_len + offset > len( buffer ) or formatUnpack[1:] != self.formato_payload[:len(
                formatUnpack ) - 1]):
            logger.error(
                "Errore formato classe {}, lunghezza_calcolata: {}, formatoUnpack: {}, formato_payload: {}".format(
                    instance.__class__, calculate_len, formatUnpack, self.formato_payload ) )
