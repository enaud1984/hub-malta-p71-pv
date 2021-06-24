import json
import logging
from struct import unpack_from
import utility
from common_struct import *
from manageGW import GW_SCGP_servo_control_INS
from manageUDP import UDPAdapter
import numpy as np
from sender import SCGP,IP_SCGP,IP_SCGP_ACK,IP_SCGP_MULTI
#

logger = logging.getLogger( __name__ )

'''
Messaggi da SCGP(Cannoncino) a WG e viceversa tramite socket UDP
'''

''''
SCGP -> GW
'''
class SCGP_GW_acknowledgment_INS( UDPAdapter):
    # 493092865 SCGP_CS_acknowledgment_INS 226.1.3.227 50220 Multicast UDP
    def getMsgIdentifier(self):
        return 493092865

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP_ACK
    port = 50220
    formato_payload = "IIBh"
    reported_action_id = np.uint(0)  # 16	4	1	UInt	N.A.	[0..(2^32)-1]	Contiene identificativo della singola istanza del comando. Valore ricopiato nell'eventuale messaggio di ACK. Il valore nel Reported Action ID deve sempre copiare il valore dell'Action ID corrispondente, anche se sbagliato.
    reported_message_id = np.uint(0)  # 20	4	1	UInt	N.A.	Indica il tipo del messaggio associato al Reported Action ID.
    message_accepted = b'0'  # 24	1	1	Int	Indica se il messaggio è stato accettato o rifiutato	0: not accepted	1: accepted
    reason = 0  # 25	2	1	Enum	0 : No statement;	1 : State illegality;	2 : Remote controller illegality;

    def getListAttribute(self):
        return ["reported_action_id","reported_message_id","message_accepted","reason"]

    @property
    def payload(self):
        return self.reported_action_id, \
               self.reported_message_id, \
               self.message_accepted, \
               self.reason

    def process(self):
        pass

class SCGP_GW_designation_report_INS( UDPAdapter): #non serve UDPADAPTER
    # 493092867 SCGP_CS_designation_report_INS 226.1.3.228 50223 Multicast UDP
    def getMsgIdentifier(self):
        return 493092867

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    formato_payload = "Ih??hih"
    # DATA
    action_id = np.uint(0)  # 16	4	1	UInt	N.A.	[0..(2^32)-1]
    designation_type = 0  # 20	2	1	Enum		"1: CST; 2:Position "
    threat_key = True  # 22	1	1	Bool		"0: designazione normale 1: designazione prioritaria"
    designation_control_in_pause = True  # 23	1	1	Bool
    firing_authorization = 0  # 24	2	1	Int		"0: firing not authorised 1: firing authorised"
    cstn = np.intc(0)  # 26	4	1	Int		[1..9999]
    designation_status = 0  # 30	2	1	Enum    "0 nDesignation ceased; 1 Designation in pause; 2 Designation in progress; 3 Designation failure"

    def getListAttribute(self):
        return ["action_id","designation_type","threat_key",
                "designation_control_in_pause","firing_authorization",
                "cstn","designation_status"]

    def process(self):
        '''
         if not self.designation_control_in_pause and self.designation_type==2 and self.designation_status==2:
            msg=GW_SCGP_servo_control_INS() #( GUNServo = ON)
            msg.gun_servo=2
            msg.stabilization=2
            from decoder_scg import ActionManager
            ActionManager.AckObj( msg )

            if "SCGP_GW_acknowledgment_INS" in utility.mapMsgUdpIn:
                res=utility.mapMsgUdpIn["SCGP_GW_acknowledgment_INS"]
                if res.message_accepted==1:
                    self.status = True
                    msg.send()
        '''
        pass

    @property
    def payload(self):
        return self.action_id, \
               self.designation_type, \
               self.threat_key, \
               self.designation_control_in_pause, \
               self.firing_authorization, \
               self.cstn, \
               self.designation_status

class SCGP_MULTI_full_status_INS(UDPAdapter):
    #493027329 SCGP_MULTI_full_status_INS 226.1.3.227 50222 Multicast UDP
    def getMsgIdentifier(self):
        return 493027329

    def getMsgSender(self):
        return SCGP
    ip = IP_SCGP_ACK
    port = 50222
    formato_payload = "I????????????????I"
    # DATA
    health_action_ID=np.uint(0)#Action ID   16  4   1   UInt    N.A.    [0..(2^32)-1]
    psu_ulcm_comms_failure=False#	PSU-ULCM Comms Failure	20	1	1	Bool	Errore di comunicazione tra PSU e ULCM	0: No Failure	1: Failure occurs					
    lcc_ulcm_comms_failure=False#	LCC-ULCM Comms Failure	21	1	1	Bool	Errore di comunicazione tra LCC e ULCM	0: No Failure	1: Failure occurs					
    lcc_vru_comms_failure=False#	LCC-VRU Comms Failure	22	1	1	Bool	Errore di comunicazione tra LCC e VRU	0: No Failure	1: Failure occurs					
    ulcm_status_failure=False#	ULCM Status Failure	23	1	1	Bool	Errore di stato della ULCM	0: No Failure	1: Failure occurs					
    ulcm_input_voltage_failure=False#	ULCM Input Voltage Failure	24	1	1	Bool	Errore di alimentazione della ULCM	0: No Failure	1: Failure occurs					
    ulcm_navs_comms_failure=False#	ULCM-NAVS Comms Failure	25	1	1	Bool	Errore di comunicazione tra ULCM e NAVS	0: No Failure	1: Failure occurs					
    ir_status_failure=False #IR Status Failure	26	1	1	Bool	IR failure	LRF Status Failure	27	1	1	Bool	LRF failure	ID
    lrf_status_failure=False #LRF Status Failure    27    1    1    Bool    LRF failure    ID 47
    box_ulcm_comms_failure=False#	Box-ULCM Comms Failure	28	1	1	Bool	Errore di comunicazione tra ID Box e ULCM	0: No Failure	1: Failure occurs
    vru_status_failure=False#	VRU Status Failure	29	1	1	Bool	VRU in failure							
    gun_gyro_status_failure=False#	Gun Gyro Status Failure	30	1	1	Bool	Gyro in failure							
    day_tv_failure=False#	Day TV Failure	31	1	1	Bool	Errore di comunicazione con la camera diurna							
    misfire=False#	Misfire	32	1	1	Bool	Fuoco mancato	0: No misfire	1: Misfire (fuoco mancato)					
    no_pointing_zone=False#	No_Pointing_Zone	33	1	1	Bool	La posizione comandata ( manuale o traccia) ricevuta non può essere raggiunta a causa di una zona di blind arc.	0: All'esterno di una No Pointing Zone	1: All'interno di una No Pointing Zone					
    no_firing_zone=False#	No_Firing_Zone	34	1	1	Bool	La posizione comandata ( manuale o traccia) ricevuta può essere raggiunta ma il fuoco è inibito	0: All'esterno di una No Firing Zone	1: All'interno di una No Firing Zone					
    ready_to_fire=False#	Ready_To_Fire	35	1	1	Bool	SCG è nello stato pronti al fuoco	0: Not Ready To Fire	1: Ready To Fire					
    round_counter=np.uint(0)#	Round Counter	36	4	1	UInt	N/A	[0..65535]	1	Conta colpi sparati complessimvante dall’arma

    def getListAttribute(self):
        return ["health_action_ID","psu_ulcm_comms_failure","lcc_ulcm_comms_failure","lcc_vru_comms_failure",
            "ulcm_status_failure","ulcm_input_voltage_failure","ulcm_navs_comms_failure",
            "ir_status_failure","lrf_status_failure","box_ulcm_comms_failure","vru_status_failure","gun_gyro_status_failure",
            "day_tv_failure","misfire","no_pointing_zone","no_firing_zone","ready_to_fire","round_counter",
            ]

    def process(self):
        pass

    @property
    def payload(self):
        return self.health_action_ID, \
            self.psu_ulcm_comms_failure, \
            self.lcc_ulcm_comms_failure, \
            self.lcc_vru_comms_failure, \
            self.ulcm_status_failure, \
            self.ulcm_input_voltage_failure, \
            self.ulcm_navs_comms_failure, \
            self.ir_status_failure, \
            self.lrf_status_failure, \
            self.box_ulcm_comms_failure, \
            self.vru_status_failure, \
            self.gun_gyro_status_failure, \
            self.day_tv_failure, \
            self.misfire, \
            self.no_pointing_zone, \
            self.no_firing_zone, \
            self.ready_to_fire, \
            self.round_counter

class SCGP_MULTI_health_status_INS( UDPAdapter):
    # 493027330 SCGP_MULTI_health_status_INS 226.1.3.229 50227 Multicast UDP
    def getMsgIdentifier(self):
        return 493027330

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP_MULTI
    port = 50220
    formato_payload = "hhhBBBBBBBBBBBBBBBB"
    # DATA
    configuration = 0  # 16	2	1	Enum	0 : Local;	1 : Autonomous;	2 : Integrated;	Indica la Configurazione corrente del Sottosistema.
    mode = 0  # 18	2	1	Enum	1 : Local Indipendent;	2 : Local Training;	3 : Remote Integrated;	4 : Remote Autonomous;	Specifica la modalità di controllo dell'arma.
    state = 0  # 20	2	1	Enum	0 : Full Operative;	1 : Fault;	2 : Degraded
    template= ""
    warning_list=Struct_WarningCode()

    def getListAttribute(self):
        return ["configuration","mode","state","warning_list"]

    def decode(self, buffer):
        instance, format=self.decodeUdp( None, buffer, 16 )
        self.warning_list,format_warn= self.decodeUdp( Struct_WarningCode, buffer, 22 )
        format_val = format + format_warn
        if format_val.replace(">","") != self.formato_payload:
            logger.error( str(self.__class__)+" Formato payload errato" + format_val + "---" + self.formato_payload )


    def process(self):
        pass

    @property
    def payload(self):
        return self.configuration, \
               self.mode, \
               self.state, \
               self.warning_list.failure_byte_01, \
               self.warning_list.failure_byte_02, \
               self.warning_list.failure_byte_03, \
               self.warning_list.failure_byte_04, \
               self.warning_list.failure_byte_05, \
               self.warning_list.failure_byte_06, \
               self.warning_list.failure_byte_07, \
               self.warning_list.failure_byte_08, \
               self.warning_list.failure_byte_09, \
               self.warning_list.failure_byte_10, \
               self.warning_list.failure_byte_11, \
               self.warning_list.failure_byte_12, \
               self.warning_list.failure_byte_13, \
               self.warning_list.failure_byte_14, \
               self.warning_list.failure_byte_15, \
               self.warning_list.failure_byte_16

class SCGP_GW_servo_report_INS( UDPAdapter ):
    # 493092880 SCGP_CS_servo_report_INS 226.1.3.228 50223 Multicast UDP
    def getMsgIdentifier(self):
        return 493092880

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    formato_payload = "Ihhhhhhh?"
    # DATA
    action_id = np.uint(0)  # 16	4	1	UInt	N.A.	[0..(2^32)-1]	Contiene identificativo della singola istanza del comando. Valore ricopiato nell'eventuale messaggio di ACK.
    gun_servo = 0  # 20	2	1	Enum	1 : Servo Off;	2 : Servo On;	3 : Servo Failure;	Specifica lo stato dei servo
    stabilization_state = 0  # 22	2	1	Enum	1 : Stab off;	2 : Stab on;	3 : Stab failure;	indica lo stato della stabilizzazione
    manual_control = 0  # 24	2	1	Enum	0 : No change (Not Used);	1 : Slow;	2 : Fast;	indica la velocità selezionata per il controllo manuale
    parking_position = 0  # 26	2	1	Enum	0 : No parking position requested;	1 : Slewing to parking position;	2 : Parking position reached;	3 : Parking position cannot be reached;	Specifica se è in corso un rifasamento nella posizione di parcheggio.
    left_loading_position = 0  # 28	2	1	Enum	0 : No loading position requested;	1 : Slewing to loading position;	2 : Loading position reached;	3 : Loading position cannot be reached;	Specifica se è in corso un rifasamento alla posizione di loading sinistra.
    right_loading_position = 0  # 30	2	1	Enum	0 : No loading position requested;	1 : Slewing to loading position;	2 : Loading position reached;	3 : Loading position	Specifica se è in corso un rifasamento alla posizione di loading destra
    drift_compensation_status = 0  # 32	2	1	Enum	1 : OFF;	2 : ON;	Indica lo stato del recupero derive
    misalignment = True  # 34	1	1	Bool	Indica che il cannone sta puntando verso la posizione comandata.	0: Alignment (arma allineata alla posizione comandata);	1: Misalignment (allineamento in corso)

    def getListAttribute(self):
        return ["action_id","gun_servo","stabilization_state","manual_control","parking_position",
                "left_loading_position","right_loading_position","drift_compensation_status","misalignment"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
               self.gun_servo, \
               self.stabilization_state, \
               self.manual_control, \
               self.parking_position, \
               self.left_loading_position, \
               self.right_loading_position, \
               self.drift_compensation_status, \
               self.misalignment

class SCGP_GW_gun_position_report_INS( UDPAdapter ):
    # 493092871 SCGP_CS_gun_position_report_INS 226.1.3.228 50225 Multicast UDP
    def getMsgIdentifier(self):
        return 493092871

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50225
    formato_payload = "fffffI"
    # DATA
    azimuth = 0.0  # 16	4	1	Float	deg	[0..360]	Angolo di Azimuth. L’origine è il centro meccanico del cannone (DCS)
    elevation = 0.0  # 20	4	1	Float	deg	[-90..90]	Angolo di Elevazione. L’origine è il centro meccanico del cannone (DCS)
    azimuth_cursor = 0.0  # 24	4	1	Float	deg	[0..360]	Angolo di Azimuth.	L’origine è il centro meccanico del cannone (DCS)
    elevation_cursor = 0.0  # 28	4	1	Float	deg	[-90..90]	Angolo di Elevazione.	L’origine è il centro meccanico del cannone (DCS)
    time_of_flight = 0.0  # 32	4	1	Float	s	[0..30]	Tempo di volo della munizione.
    range_future = np.uint(0)  # 36	4	1	UInt	m	[0..20000]	Range calcolo punto futuro

    def getListAttribute(self):
        return ["azimuth","elevation","azimuth_cursor","elevation_cursor","time_of_flight","range_future"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.azimuth, \
               self.elevation, \
               self.azimuth_cursor, \
               self.elevation_cursor, \
               self.time_of_flight, \
               self.range_future


class SCGP_CS_IR_report_INS( UDPAdapter ):
    #493092874	SCGP_CS_IR_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092874

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #data 
    action_id = np.uint(0)  #16	4	1	UInt	N.A.	[0..(2^32)-1]
    state = 0               #20	2	1	Enum		0 : OFF;1 : Initialization;2 : Ready;3 : Failure;
    polarity_color = 0      #22	2	1	Enum		1 : White_HOT;2 : Black_HOT;
    gain = 0                #24	2	1	Enum		1 : Negative step;2 : Positive step;
    calibrate = 0           #26	2	1	Enum		1 : OFF;2 : In progress;
    brightness = 0          #28	2	1	Enum		1 : Negative step;2 : Positive step;
    normal_focus_reset = 0  #30	2	1	Enum		1 : OFF;2 : ON;
    focus = 0               #32	2	1	Enum		1 : Negative step; 2 : Positive step;
    agc_control = 0         #34	2	1	Enum		0 : No change (Not Used);1 : Semi automatic;2 : Full automatic;
    
    formato_payload = "Ihhhhhhhh"
    def getListAttribute(self):
        return ["action_id","state","polarity_color","gain","calibrate","brightness","normal_focus_reset","focus","agc_control"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
            self.state, \
            self.polarity_color, \
            self.gain, \
            self.calibrate, \
            self.brightness, \
            self.normal_focus_reset, \
            self.focus, \
            self.agc_control


class SCGP_CS_LRF_inhibition_report_INS( UDPAdapter ):
    #493092884	SCGP_CS_LRF_inhibition_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092884

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0) #16	4	1	UInt	N.A.	[0..(2^32)-1]
    inhibition_constraint = 0 #20	2	1	Enum		0 : Authorized;1 : Inhibited;	CEMCON Laser constraint
    
    formato_payload = "Ih"
    def getListAttribute(self):
        return ["action_id","inhibition_constraint"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
            self.inhibition_constraint

class SCGP_CS_LRF_report_INS( UDPAdapter ):
    #493092876	SCGP_CS_LRF_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092876

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0) #16	4	1	UInt	N.A.	[0..(2^32)-1]
    state = 0       #20	2	1	Enum	0 : Standby;1 : Emitting;2 : Failure;	Specifica lo stato del laser.
    frequency = 0   #22	2	1	Enum	0 : No change (Not Used);1 : 0,33 Hz;2 : 1 Hz;	Specifica la frequenza di funzionamento del sensore.Valore No Change non utilizzato
    range_val = 0   #24	2	1	Enum	0 : No echo;1 : Echo in minimum distance;2 : Valid range;	Specifica la validità dell’ultima misurazione effettuata (1 = la misura risulta inferiore ad una distanza minima pre-impostata dal sistema)
    
    formato_payload = "Ihhh"
    def getListAttribute(self):
        return ["action_id","state","frequency","range_val"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
            self.state, \
            self.frequency, \
            self.range_validity

class SCGP_CS_cursors_report_INS( UDPAdapter ):
    #493092866	SCGP_CS_cursors_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092866

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0) #16	4	1	UInt	N.A.	[0..(2^32)-1]
    kinematic_cursors_state=0 #20	2	1	Enum	1 : Cursors Disabled;2 : Cursors Enabled;3 : Cursors Updating;	Riporta lo stato dei cursori cinematici per il calcolo balistico.

    formato_payload = "Ih"
    def getListAttribute(self):
        return ["action_id","kinematic_cursors_state"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
            self.kinematic_cursors_state

class SCGP_CS_firing_burst_report_INS( UDPAdapter ):
    #493092868	SCGP_CS_firing_burst_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092868

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0) #16	4	1	UInt	N.A.	[0..(2^32)-1]
    burst_mode_selected = 0 	#20	2	1	Enum	1 : Single shot;2 : Short burst;3 : Long burst;4 : Continuous burst;	Specifica la lunghezza della raffica

    formato_payload = "Ih"
    def getListAttribute(self):
        return ["action_id","burst_mode_selected"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
            self.burst_mode_selected

class SCGP_CS_firing_correction_report_INS( UDPAdapter ):
    #493092869	SCGP_CS_firing_correction_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092869

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0)       #16	4	1	UInt	N.A.	[0..(2^32)-1]
    fire_correction_azimuth = 0  #20	2	Int	mrad[-100..100]	0.1	Correzione in Azimuth fra -10 mrad e +10 mrad
    fire_correction_elevation = 0 #22	2	Int	mrad[-100..100]	0.1	Correzione in Elevation fra -10 mrad e +10 mrad
    
    formato_payload = "Ihh"
    def getListAttribute(self):
        return ["action_id","fire_correction_azimuth","fire_correction_elevation"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
            self.fire_correction_azimuth, \
            self.fire_correction_elevation

class SCGP_CS_firing_report_INS( UDPAdapter ):
    #493092870	SCGP_CS_firing_report_INS	226.1.3.228	50224	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092870

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50224
    #DATA
    action_id = np.uint(0)       #16	4	1	UInt	N.A.	[0..(2^32)-1]
    fire = True                  #20	1	Bool			Specifica se l'arma sta sparando 0: No firing;1: Firing.
    formato_payload = "I?"
    def getListAttribute(self):
        return ["action_id","fire"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
            self.fire

class SCGP_CS_installation_data_INS( UDPAdapter ):
    #493092872	SCGP_CS_installation_data_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092872

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0)       #16	4	1	UInt	N.A.	[0..(2^32)-1]
    type_of_gun = 0#	20	2	1	Enum		0 : None;1 : 25 mm;2 : Spare;	Specifica il tipo di arma installata
    no_pointing_zones = [Struct_NoPointingZone() for i in range(10)]
    no_firing_zones = [Struct_NoFiringZone() for i in range(10)]
    relative_mounting_position = Struct_CRP_relative_mounting_position()
    @property
    def formato_payload(self):
        formato_payload = "Ihh"
        for k in self.no_pointing_zone:
            formato_payload+=k.formato_payload.replace(">","")
        for k in self.no_firing_zones:
            formato_payload+=k.formato_payload.replace(">","")
        formato_payload+=self.relative_mounting_position.formato_payload
        return formato_payload
    
    def decode(self, buffer):
        instance, formatSelf = self.decodeUdp( None, buffer, 16 )
        self.no_pointing_zone = []
        self.no_firing_zones = []
        format_pointing_zones = ""
        format_firing_zones = ""
        for i in range(10):
            noPointingZone,format_pointing_zone = self.decodeUdp( Struct_NoPointingZone, buffer, 22+(i*17) )#22	17	10	Struct			Definisce un settore volumetrico di No Pointing
            format_pointing_zones+=format_pointing_zone
            self.no_pointing_zones.append(noPointingZone)
            no_firing_zones,format_firing_zone = self.decodeUdp( Struct_NoFiringZone, buffer, 192+(i*17) )#192	17	10	Struct			Definisce un settore volumetrico di No Firing
            format_firing_zones+=format_firing_zone
            self.no_firing_zones.append(no_firing_zones)
        self.relative_mounting_position,formatmounting = self.decodeUdp( Struct_CRP_relative_mounting_position, buffer, 378 ) #	378	12	1	Struct			Struttura contenente le coordinate della posizione relativa dell'affusto della SCG rispetto al CRP nave. 
        format_val = formatSelf[:-1] + format_pointing_zones + format_firing_zones+formatmounting
        format_struct=self.formato_payload
        if format_val.replace(">","") != format_struct.replace(">",""):
            logger.error( str(self.__class__)+" Formato payload errato" + format_val + "---" + format_struct )
    
    def getListAttribute(self):
        return ["action_id","type_of_gun","no_pointing_zones","no_firing_zones","relative_mounting_position"]

    def process(self):
        pass

    @property
    def payload(self):
        ret=[self.action_id,self.type_of_gun]
        for no_pointing_zone in self.no_pointing_zones:
            ret.append(no_pointing_zone.validity)
            ret.append(no_pointing_zone.no_pointing_zone_start_azimuth)
            ret.append(no_pointing_zone.no_pointing_zone_end_azimuth)
            ret.append(no_pointing_zone.no_pointing_zone_start_elevation)
            ret.append(no_pointing_zone.no_pointing_zone_end_elevation)
            ret.append(no_pointing_zone.no_firing_zone)
        for no_firing_zone in self.no_firing_zones:
            ret.append(no_firing_zone.validity)
            ret.append(no_firing_zone.no_firing_zone_start_azimuth)
            ret.append(no_firing_zone.no_firing_zone_end_azimuth)
            ret.append(no_firing_zone.no_firing_zone_start_elevation)
            ret.append(no_firing_zone.no_firing_zone_end_elevation)
            ret.append(no_firing_zone.start_azimuth_limit)
            ret.append(no_firing_zone.end_azimuth_limit)
            ret.append(no_firing_zone.start_elevation_limit)
            ret.append(no_firing_zone.end_elevation_limit)
            ret.append(no_firing_zone.crp_relative_mounting_position)
        ret.append(self.relative_mounting_position.x_position)
        ret.append(self.relative_mounting_position.y_position)
        ret.append(self.relative_mounting_position.z_position)
        return  ret

class SCGP_CS_integrated_safety_settings_report_INS( UDPAdapter ):
    #493092873	SCGP_CS_integrated_safety_settings_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092873

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0)              #16	4	1	UInt	N.A.	[0..(2^32)-1]
    fire_enable_state=0                 #20	2	1	Enum	1 : Firing Disabled; 2 : Firing Enabled;	Specifica l’abilitazione al fuoco software di alto livello da parte del CMS
    fire_without_tracking_state=0       #22	2	1	Enum	1 : Not Authorised;2 : Authorised;	Specifica l’autorizzazione (da dottrina) a fare fuoco anche senza autotracking in corso
    free_engagement_authorisation_state=0#24	2	1	Enum	1 : Not Authorised;2 : Authorised;	Specifica l’autorizzazione (da dottrina) per movimentazione manuale e autotracking senza designazione.Nota: rimangono sempre applicabili i comandi contenuti in CS_SCG_Servo_Control_INS
    formato_payload = "Ihhh"
    def getListAttribute(self):
        return ["action_id","fire_enable_state","fire_without_tracking_state","free_engagement_authorisation_state"]
    
    def process(self):
        pass
    
    @property
    def payload(self):
        return self.action_id, \
            self.fire_enable_state, \
            self.fire_without_tracking_state, \
            self.free_engagement_authorisation_state
    
class SCGP_CS_loading_report_INS( UDPAdapter ):
    #493092875	SCGP_CS_loading_report_INS	226.1.3.227	50221	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092875

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP_ACK
    port = 50221
    #DATA
    action_id = np.uint(0)      #	16	4	1	UInt	N.A.	[0..(2^32)-1]Contiene identificativo della singola istanza del comando. Valore ricopiato nell'eventuale messaggio di ACK.
    last_round_left = 0	        #  20	2	1	Enum	0 : No Last Round; 1 : Last Round Reached; 2 : Last Round Bypass; 	Indica lo stato di utilizzo degli ultimi colpi del serbatoio sinistro.
    last_round_right = 0	    #  22	2	1	Enum	0 : No Last Round; 1 : Last Round Reached; 2 : Last Round Bypass;	Indica lo stato di utilizzo degli ultimi colpi del serbatoio destro
    recocking_state = 0 	    #  24	2	1	Enum	0 : Not recocking; 1 : Recocking executed; 2 : Recocking in progress; 3 : Recocking failure;	Indica lo stato di recock dell’arma (riarmo dell’otturatore).Precondizioni: Fire Safety=ON ( Safe). NOTA: Recocking non è una precondizione per entrare nello stato Pronti a fuoco (Ready To Fire). 
    round_type_left = 0 	    #  26	2	1	Enum	1 : MULTI_HE; 2 : APFSDS; 3 : APDS; 4 : FAPDS; 5 : TPDS;	Specifica il tipo di munizioni caricate nel magazzino sinistro.Tale dato consente al sistema di caricare le tavole di tiro corrette. NOTA: L’errata selezione delle munizioni caricate manualmente nel magazzino introduce un errore nel calcolo balistico
    round_num_left = np.uint(0) #  28	2	1	UInt	[0..136]	Specifica il numero di munizioni disponibili nel magazzino di sinistra
    round_type_right = 0 	    #  30	2	1	Enum	1 : MULTI_HE; 2 : APFSDS; 3 : APDS; 4 : FAPDS; 5 : TPDS;	Specifica il tipo di munizioni caricate nel magazzino destro.Tale dato consente al sistema di caricare le tavole di tiro corrette. NOTA: L’errata selezione delle munizioni caricate manualmente nel magazzino introduce un errore nel calcolo balistico.
    round_num_right = np.uint(0)#  32	2	1	UInt	[0..136]	Specifica il numero di munizioni disponibili nel magazzino di destra
    ammunition_box_selected = 0	#  34	2	1	Enum	1 : Left; 2 : Neutral; 3 : Right;	Specifica il magazzino selezionato Neutral significa: Magazzino non selezionato. Comandando il fuoco arma se il colpo è in canna verrà sparato. Successivamente l’otturatore sarà sollecitato ma nessun colpo sarà sparato.
    ballistic_distance_round_left=np.uint(0)# 36	4	1	Int	m[0..10000]	Contiene la massima distanza balistica definita secondo le tavole di tiro della munizione caricata nel serbatoio sinistro.
    ballistic_distance_round_right=np.uint(0)#	40	4	1	Int	m[0..10000]	Contiene la massima distanza balistica definita secondo le tavole di tiro della munizione caricata nel serbatoio destro.
    
    formato_payload = "IhhhhIhIhII"
    def getListAttribute(self):
        return ["action_id","last_round_left","last_round_right","recocking_state", \
            "round_type_left","round_num_left","round_type_right","ammunition_box_selected", \
            "ballistic_distance_round_left","ballistic_distance_round_right"]
    
    def process(self):
        pass
    
    @property
    def payload(self):
        return self.action_id, \
            self.last_round_left, \
            self.last_round_right, \
            self.recocking_state, \
            self.round_type_left, \
            self.round_num_left, \
            self.round_type_right, \
            self.round_num_right, \
            self.ammunition_box_selected, \
            self.ballistic_distance_round_left, \
            self.ballistic_distance_round_right

class SCGP_CS_offset_report_INS( UDPAdapter ):
    #493092877	SCGP_CS_offset_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092877

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0)      #	16	4	1	UInt	N.A.	[0..(2^32)-1]Contiene identificativo della singola istanza del comando. Valore ricopiato nell'eventuale messaggio di ACK.
    offset_azimuth = 0          #	20	2	1	Int	mrad[-100..100]0,1	Totale offset in brandeggio fra -10 mrad e +10 mrad
    offset_elevation = 0        #   22	2	1	Int	mrad[-100..100]0,1	Totale offset in elevazione fra -10 mrad e +10 mrad
    
    formato_payload = "Ihh"
    def getListAttribute(self):
        return ["action_id","offset_azimuth","offset_elevation"]
    
    def process(self):
        pass
    
    @property
    def payload(self):
        return self.action_id, \
            self.offset_azimuth, \
            self.offset_elevation


class SCGP_CS_range_report_INS( UDPAdapter ):
    #493092878	SCGP_CS_range_report_INS	226.1.3.228	50226	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092877

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0)  #	16	4	1	UInt	N.A.	[0..(2^32)-1]Contiene identificativo della singola istanza del comando. Valore ricopiato nell'eventuale messaggio di ACK.
    range_source = 0        #	20	2	1	Enum	0 : No change (Not Used);1 : Designation; 2 : Manual Range; 3 : LRF range;	Indica la sorgente del valore di range
    range_in_use = 0 	    #   22	2	1	UInt	m[0..20000]	Specifica il valore di distanza attualmente usato dal SCG
           
    formato_payload = "Ihh"
    def getListAttribute(self):
        return ["action_id","range_source","range_in_use"]
    
    def process(self):
        pass
    
    @property
    def payload(self):
        return self.action_id, \
            self.range_source, \
            self.range_in_use

class SCGP_CS_safety_report_INS( UDPAdapter ):
    #493092879	SCGP_CS_safety_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092879

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0) #	16	4	1	UInt	N.A.	[0..(2^32)-1]Contiene identificativo della singola istanza del comando. Valore ricopiato nell'eventuale messaggio di ACK.
    fire_safety_mfc=False               #	20	1	1	Bool		Specifica il setting di safety da MFC di controllo dell’arma 0 : Not Safe; 1 : Safe
    lcc_emergency=False                 #	21	1	1	Bool		Specifica l’attivazione del Emergency Stop da console locale 0 : Move; 1 : Not Move;
    sfp_safety_status=False             #	22	1	1	Bool		Specifica lo stato di safety HW del SCG da SFP 0 : Fire;1 : Safe
    safety_box_status_activated=False   #	23	1	1	Bool		Specifica lo stato di safety HW del SCG da Safety Box 0 : Move;1 : Not Move;
    azimuth_locked=False                #	24	1	1	Bool		Specifica se la rizza di brandeggio (fermo meccanico) è attiva o meno 0 : Unlocked;1 : Locked;
    elevation_locked=False              #	25	1	1	Bool		Specifica se la rizza di elevazione (fermo meccanico) è attiva o meno 0 : OFF (Unlocked);1 : ON (Locked)
    formato_payload = "I??????"
    def getListAttribute(self):
        return ["action_id","fire_safety_mfc","lcc_emergency","sfp_safety_status",\
            "safety_box_status_activated","azimuth_locked","elevation_locked"]
    
    def process(self):
        pass
    
    @property
    def payload(self):
        return self.action_id, \
            self.fire_safety_mfc, \
            self.lcc_emergency, \
            self.sfp_safety_status, \
            self.safety_box_status_activated, \
            self.azimuth_locked, \
            self.elevation_locked 

class SCGP_CS_software_version_INS( UDPAdapter ):
    #493092881	SCGP_CS_software_version_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092881

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0)            #	16	4	1	UInt	N.A.	[0..(2^32)-1]Contiene identificativo della singola istanza del comando. Valore ricopiato nell'eventuale messaggio di ACK.
    sw_version_ulcm="123456789"          #	20	9	1	String		Versione software dell’Unità Logica Controllo Movimentazione
    sw_version_servo_system="123456789"  # 29	9	1	String		Versione software apparato Servo
    sw_version_lcc="123456789"	          # 38	9	1	String		Versione software apparato LCC
    sw_version_id_box="123456789"	      # 47	9	1	String		Versione software apparato Id Box
    formato_payload = "I"+"ccccccccc"+"ccccccccc"+"ccccccccc"+"ccccccccc"
    def getListAttribute(self):
        return ["action_id","sw_version_ulcm","sw_version_servo_system","sw_version_lcc","sw_version_id_box"]
    
    def process(self):
        pass
    
    @property
    def payload(self):
        return self.action_id, \
               self.sw_version_ulcm, \
               self.sw_version_servo_system, \
               self.sw_version_lcc, \
               self.sw_version_id_box

class SCGP_CS_tracker_report_INS( UDPAdapter ):
    #493092882	SCGP_CS_tracker_report_INS	226.1.3.228	50223	Multicast	UDP
    def getMsgIdentifier(self):
        return 493092882

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0)    #	16	4	1	UInt	N.A.	[0..(2^32)-1]Contiene identificativo della singola istanza del comando. Valore ricopiato nell'eventuale messaggio di ACK.
    enabled=0                 #	20	2	1	Enum	1 : OFF; 2 : ON;	Specifica se il tracker è abilitato o disabilitato. Quando abilitato compare a video la finestra di tracker.
    algorithm=0               # 22	2	1	Enum	1 : Correlation; 2 : Contrast;	Specifica l’algoritmo di tracker selezionato.
    state=0                   # 24	2	1	Enum	0 : Not tracking;1 : Tracking; 2 : Memory;	Specifica lo stato del tracking (Memory: bersaglio perso, tentativo di riaggancio automatico in corso)
    window_resize=0           #	26	1	1	Enum	0 : No change (Not Used); 1 : Window Size Decreased; 2 : Window Size Increased;	Tellback del commando di ridimensionamento della finestra di tracker.

    formato_payload = "Ihhhh"
    def getListAttribute(self):
        return ["action_id","enabled","algorithm","state","window_resize"]
    
    def process(self):
        pass
    
    @property
    def payload(self):
        return self.action_id, \
            self.enabled,   \
            self.algorithm, \
            self.state, \
            self.window_resize    
    
class SCGP_CS_video_setting_report_INS( UDPAdapter ):
    #493092883 SCGP_CS_video_setting_report_INS 226.1.3.228 50223 Multicast UDP
    def getMsgIdentifier(self):
        return 493092883

    def getMsgSender(self):
        return SCGP

    ip = IP_SCGP
    port = 50223
    #DATA
    action_id = np.uint(0)    #16	4	1	UInt	N.A.	[0..(2^32)-1]Contiene identificativo della singola istanza del comando. Valore ricopiato nell'eventuale messaggio di ACK.
    selected_camera = 0 	  #20	2	1	Enum	1 : IR camera;2 : Day camera;3 : Spare Channel 1;4 : Spare Channel 2;Camera selezionata	
    fov_ir =0                 #22	2	1	Enum	1 : Wide;2 : Narrow;	Indica il FOV della camera IR.
    zoom_fov_day = np.uint(0) #24	2	1	UInt	[1..30]	Indica lo zoom della camera TV.
    reticle = 0  	          #26	2	1	Enum	0 : No change (Not Used);1 : Aiming;2 : Ballistic;3 : Calibrated;	Reticolo attualmente in uso.
    washer = False	          #28	1	1	Bool		Stato del Washer 0: Washer OFF;1: Washer ON
    azimut_video_angle=0.0    #29	4	1	Float	deg[0..360]	Riporta la coordinata in bearing del punto selezionato su video operatore per inserire le correzioni al fuoco direttamente sul video.
    elevation_video_angle=0.0 #33	4	1	Float	deg[-90..90]	Riporta la coordinata in elevazione del punto selezionato su video operatore per inserire le correzioni al fuoco direttamente sul video.

    formato_payload = "IhhIh?ff"
    def getListAttribute(self):
        return ["action_id","selected_camera","fov_ir","zoom_fov_day","reticle","washer","azimut_video_angle","elevation_video_angle"]
    
    def process(self):
        pass
    
    @property
    def payload(self):
        return self.action_id, \
            self.fov_ir, \
            self.zoom_fov_day, \
            self.reticle, \
            self.washer, \
            self.azimut_video_angle, \
            self.elevation_video_angle



