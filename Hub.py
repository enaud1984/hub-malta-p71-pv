import signal
from datetime import datetime
from manageSerial import *
import sys
import getopt
import logging
import logging.handlers
import manageUDP
import os
from flask import Flask
from config import configFile,baseDir,conf
from manageTCP import TCPManager
from collections import namedtuple
managerTask=None
app = Flask(__name__) #create the Flask app

def main(argv):
    try:
        usage = 'Hub.py [-i <inputfile>|-r <inputfile> | -s|-n=1|-t|-a]'
        from decoder_scg import DecodeStruct
        from manageFlask import initServer
        from manageScheduler import initScheduler,sched
        #decoderSCG = DecodeStruct.getInstance()  # Classe di decodifica Enumerati e Failure Bits Enum
        listArgs=[]+argv
        
        if "-a" in listArgs or "--api" in listArgs:
            listArgs = [k for k in argv if k not in ["-a","--api"]]
            conf._enable_api()


        opts, args = getopt.getopt( listArgs, "i:rs:s:n:t:a",
                                 ["ifile=", "routeonserial=","serial","num_serial=","tcp","api"] )


        filename=None
        filenames=[]
        serial=False
        routeonserial=None
        n_serial=1
        tcp_mode = None
        
            
        for opt, arg in opts:
            if opt in ('-i',"--ifile") and "-s" not in opts and "--serial" not in opts \
                    and "-rs" not in opts and "--routeonserial" not in opts:
                filename=arg
                filenames.append(filename)
            elif opt in ("-s", "--serial") and "-i" not in opts and "--ifile" not in opts \
                    and "-rs" not in opts and "--routeonserial" not in opts:
                serial = True
            elif opt in ("-t", "--tcp_mode"):
                tcp_mode = arg
            elif opt in ("-n", "--num_serial"):
                n_serial = arg
            elif opt in ("-rs","--routeonserial") and ("-i" in opts or "--ifile" in opts) \
                    and "-s" not in opts and "--serial" not in opts:
                routeonserial=arg
            else:
                print( usage )
                sys.exit(2)

        server = initServer()
        manager=manageUDP.read_udp(configFile,["UDP"])

       
        if serial and not filename and not routeonserial:
            ManageSerial.start(n_serial, configFile)

        if not serial and filename and not routeonserial:
            #ReadFile("config.ini",["FILE SIMULATOR CONFIGURATION"])
            for i in range(len(filenames)):
                section = "SERIAL PORT CONFIGURATION{}".format(i)
                r=ReadFile(filenames[i],section,source=i+1)
                r.start()
        if not serial and not filename and routeonserial:
            #ReadFile("config.ini",["FILE SIMULATOR CONFIGURATION"])
            for i in range(len(filenames)):
                section = "SERIAL PORT CONFIGURATION{}".format(i)
                ReadFile(routeonserial,section,True,source=i+1).start()
        if tcp_mode is not None:
            tcpManager=TCPManager(configFile,["TCP"])
        print( "Init Scheduler" )
        initScheduler()
        print( "Start gevent WSGI server" )
        server.serve_forever()
    except getopt.GetoptError:
        print( usage )
        sys.exit( 2 )
    except KeyboardInterrupt:
        try:
            print( "richiesto stop" )
            logger.error("richiesto  Stop")
            ManageSerial.stop()
            manageUDP.UDPManager.stop()
            TCPManager.stop()
            sched.shutdown()
        except Exception as e:
            logger.error("Errore chiusura", e)
        finally:
            os._exit(2)



if __name__ == "__main__":
    from utility import MyFormatter
    conf._apply()
    if not os.path.isdir("log"):
        os.mkdir("log")
    else:
        listFile=sorted(os.listdir("log" ))[:-5]
        toDeleted=[k for k in listFile if k.startswith("log") and "{}".format(datetime.strftime(datetime.now(),"%Y%m%d")) not in k]
        for f in toDeleted:
            os.remove(os.path.join(baseDir,"log",f))

    LOG_FILENAME=os.path.join("log","logHUB_{}.log".format(datetime.strftime(datetime.now(),"%Y%m%d_%H%M%S")))
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                               maxBytes=conf.log_rotate,
                                               backupCount=conf.log_max_file,
                                               )
    formatLog="%(asctime)s\t%(module)s\t%(funcName)s\t%(levelname)s\t%(threadName)s\t:%(message)s"
    formatter = MyFormatter(fmt=formatLog,datefmt='%Y-%m-%d,%H:%M:%S.%f')
    handler.setFormatter(formatter)
    logging.basicConfig(format=formatLog,
                        level=logging.INFO,
                        datefmt = '%d/%m/%Y %H:%M:%S',
                        handlers=[handler])
    #logger = logging.getLogger( __name__ )
    main( sys.argv[1:])




