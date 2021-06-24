import os
from manageNMEA import *
from manageNAVS import *
#from manageSCGP import *
from manageSCGF import *
from manageGW import *
#***********
localTestUDP=True
ENABLE_FIXED_SIZE=False
MAX_RETRY=3
MAX_TIME_TO_SEND=1
SIMULATOR_RESPONSE=True
#***********
http_server="127.0.0.1"
http_port=5000
log_rotate=20*1024*1024
log_max_file=10
cwd = os.getcwd()
baseDir=os.getcwd()
configDir=os.path.join(baseDir) if not os.path.isdir(os.path.join(cwd,'config')) else os.path.join(cwd,'config')
configFile=os.path.join(configDir, "config.ini")
logDir=os.path.join(baseDir, "log")

failureCsvFile=os.path.join(configDir, "failure.csv")
enumCsvFile=os.path.join(configDir, "enum_udp.csv")

listWI=[Weather_instrument_MWV,Weather_instrument_XDR,Weather_instrument_MTW]
listGiro=[Giro_GPGGA,Giro_GPGLL,Giro_GPGST,Giro_PSXN,Giro_GPVTG,Giro_AIPOV,
          Giro_HEROT,Giro_GPZDA,Giro_HEALR,Giro_HEALC,Giro_PIXSE,Giro_PSIMSSB]

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
            GW_SCGP_servo_control_INS,GW_SCGF_servo_control_INS,
            SCGP_CS_IR_report_INS,SCGP_CS_LRF_inhibition_report_INS,SCGP_CS_LRF_report_INS,SCGP_CS_cursors_report_INS,SCGP_CS_firing_burst_report_INS, 
            SCGP_CS_firing_correction_report_INS,SCGP_CS_firing_report_INS,SCGP_CS_installation_data_INS,SCGP_CS_integrated_safety_settings_report_INS, 
            SCGP_CS_loading_report_INS,SCGP_CS_offset_report_INS,SCGP_CS_offset_report_INS,SCGP_CS_range_report_INS,SCGP_CS_safety_report_INS,SCGP_CS_software_version_INS, 
            SCGP_CS_tracker_report_INS,SCGP_CS_video_setting_report_INS,
            SCGF_CS_IR_report_INS,SCGF_CS_LRF_inhibition_report_INS,SCGF_CS_LRF_report_INS,SCGF_CS_cursors_report_INS,SCGF_CS_firing_burst_report_INS, 
            SCGF_CS_firing_correction_report_INS,SCGF_CS_firing_report_INS,SCGF_CS_installation_data_INS,SCGF_CS_integrated_safety_settings_report_INS, 
            SCGF_CS_loading_report_INS,SCGF_CS_offset_report_INS,SCGF_CS_offset_report_INS,SCGF_CS_range_report_INS,SCGF_CS_safety_report_INS,SCGF_CS_software_version_INS, 
            SCGF_CS_tracker_report_INS,SCGF_CS_video_setting_report_INS
            ] #da inviare
listUDP_IN=[]
'''listUDP_IN=[SCGP_Multi_health_status_INS,SCGP_GW_acknowledgment_INS,
            SCGP_GW_designation_report_INS,SCGP_GW_servo_report_INS,
            SCGF_GW_gun_position_report_INS,SCGP_MULTI_full_status_INS,
            SCGP_GW_gun_position_report_INS,SCGF_Multi_health_status_INS,SCGF_MULTI_full_status_INS,
            SCGF_GW_acknowledgment_INS,SCGF_GW_designation_report_INS,
            SCGF_GW_servo_report_INS] #ricevuti
'''

# Message Sender Enum
NAVS = 25
GEIS_WAP = 100  # CMS
SCGF = 28
SCGP = 29
SCGS = 30
timestamp_format="%d/%m/%Y, %H:%M:%S"

startScheduler=False
def getMulti_health_status_INS():
    print( "playerUDP" )
    return None

def getManagersSimulator():
    import manageSCGF as scgf
    import manageSCGS as scgs
    import manageSCGP as scgp
    import manageGW as gw
    #mapClass={"SCGF_":dir(scgf),"SCGS_":dir(scgs),"SCGP_":dir(scgp)}
    mapClass={scgf:dir(scgf),scgs:dir(scgs),scgp:dir(scgp),gw:dir(gw)}
    list_manager =[]
    for k,v in mapClass.items():
        if k.__name__[-2:]=="GW":
            name = "{}_".format( k.__name__[-2:] )
        else:
            name="{}_".format(k.__name__[-4:])
        list_manager += [getattr(k,m) for m in v if m.startswith(name)]
    return list_manager
