import os

from manageNMEA import *
from manageNAVS import *
#from manageSCGP import *
from manageSCGF import *
from manageGW import *
#***********
localTestUDP=True
#***********
import socket

host_ip = "10.1.65.150"
http_server="10.1.65.150" #per windows 127.0.0.1
http_port=5000
log_rotate=20*1024*1024
log_max_file=10
MAX_RETRY=3
MAX_TIME_TO_SEND=1
SIMULATOR_RESPONSE=True
ENABLE_FIXED_SIZE=True #True se si vuole riempre il payload di zero fino a maxLen
CHECKHOST=False  #True per windows
max_instances_scheduler = 5
max_thread_scheduler = 20
enable_swagger = True
blocking_scheduler = True
baseDir=os.getcwd()
configDir=os.path.join(baseDir, "config")
configFile=os.path.join(configDir, "config.ini")
logDir=os.path.join(baseDir, "log")

failureCsvFile=os.path.join(configDir, "failure.csv")
enumCsvFile=os.path.join(configDir, "enum_udp.csv")

listWI=[Weather_instrument_MWV,Weather_instrument_XDR,Weather_instrument_MTW]
listGiro=[Giro_GPGGA,Giro_GPGLL,Giro_GPGST,Giro_PSXN,Giro_GPVTG,Giro_AIPOV,Giro_HEHDT,Giro_HETHS,
          Giro_HEROT,Giro_GPZDA,Giro_HEALR,Giro_HEALC,Giro_PIXSE,Giro_PSIMSSB]

class HubConf:
    max_instances_scheduler = None
    max_thread_scheduler = None
    http_server = None
    http_port = None
    log_rotate = None
    log_max_file = None
    enable_swagger = None
    blocking_scheduler = None
    host_ip = None
    def __init__(self):
        from utility import getConf
        getConf( self, configFile,["FLASK"] )
    
    def _checkHost(self):
        list_host = socket.gethostbyname_ex(socket.gethostname())
        listIp=[ip for ip in list_host[2] if not ip.startswith("127.")]
        if self.host_ip not in listIp:
            self.host_ip=listIp[-1]

    def _apply(self):
        members=[k for k in self.__class__.__dict__ if not k.startswith("_")]
        for k in members:
            if not k.startswith("_") and hasattr(self,k):
                attr=getattr(self,k)
                if attr is None:
                    setattr(self,k,eval(k))
                else:
                    setattr(self,k,eval(attr))
        if CHECKHOST:
            self._checkHost()

    def _enable_api(self):
        self.enable_swagger=True

conf = HubConf()
       
listUDP_OUT=[NAVS_MULTI_wind_and_landing_deck_data_INS,
             GW_Multi_health_status_INS,
             NAVS_MULTI_gyro_aft_nav_data_10ms_INS,
             NAVS_MULTI_gyro_fore_nav_data_10ms_INS,
             NAVS_MULTI_health_status_INS,
             NAVS_MULTI_nav_data_100ms_INS,
             GW_SCGP_update_cst_kinematics_designation_INS,
             GW_SCGF_update_cst_kinematics_designation_INS,
             GW_SCGP_change_configuration_order_INS,GW_SCGF_change_configuration_order_INS,
             GW_SCGP_designation_order_INS,GW_SCGF_designation_order_INS,
             GW_SCGP_servo_control_INS,GW_SCGF_servo_control_INS
             ] #da inviare



def getManagers():
    import manageSCGF as scgf
    import manageSCGS as scgs
    import manageSCGP as scgp
    #mapClass={"SCGF_":dir(scgf),"SCGS_":dir(scgs),"SCGP_":dir(scgp)}
    mapClass={scgf:dir(scgf),scgs:dir(scgs),scgp:dir(scgp)}
    list_manager =[]
    for k,v in mapClass.items():
        name="{}_".format(k.__name__[-4:])
        list_manager += [getattr(k,m) for m in v if m.startswith(name)]
    return list_manager

listUDP_IN=getManagers()
'''  [SCGP_Multi_health_status_INS,SCGF_Multi_health_status_INS,
            SCGP_GW_acknowledgment_INS,SCGF_GW_acknowledgment_INS,
            SCGP_GW_designation_report_INS,SCGF_GW_designation_report_INS,
            SCGP_GW_servo_report_INS,SCGF_GW_servo_report_INS,
            SCGP_GW_gun_position_report_INS,SCGF_GW_gun_position_report_INS,
            SCGP_MULTI_full_status_INS,SCGF_MULTI_full_status_INS
            ] #ricevuti
'''



timestamp_format="%d/%m/%Y, %H:%M:%S"

startScheduler=True
def getMulti_health_status_INS():
    from manageGW import GW_Multi_health_status_INS
    print("HUB")
    return GW_Multi_health_status_INS
