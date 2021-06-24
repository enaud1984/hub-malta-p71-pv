import logging
from common_struct import *
from sender import SCGS,IP_SCGS,IP_SCGS_ACK,IP_SCGS,IP_SCGS_MULTI  
from manageSCGP import SCGP_GW_acknowledgment_INS, SCGP_GW_designation_report_INS, SCGP_MULTI_health_status_INS, \
    SCGP_GW_gun_position_report_INS, SCGP_GW_servo_report_INS,SCGP_MULTI_full_status_INS, \
    SCGP_CS_IR_report_INS,SCGP_CS_LRF_inhibition_report_INS,SCGP_CS_LRF_report_INS,SCGP_CS_cursors_report_INS,SCGP_CS_firing_burst_report_INS, \
    SCGP_CS_firing_correction_report_INS,SCGP_CS_firing_report_INS,SCGP_CS_installation_data_INS,SCGP_CS_integrated_safety_settings_report_INS, \
    SCGP_CS_loading_report_INS,SCGP_CS_offset_report_INS,SCGP_CS_offset_report_INS,SCGP_CS_range_report_INS,SCGP_CS_safety_report_INS,SCGP_CS_software_version_INS, \
    SCGP_CS_tracker_report_INS,SCGP_CS_video_setting_report_INS
#

logger = logging.getLogger( __name__ )

'''
Messaggi da SCGS(Cannoncino) a WG e viceversa tramite socket UDP
'''

'''
SCGS -> GW
'''
class SCGS_GW_acknowledgment_INS( SCGP_GW_acknowledgment_INS):
    # 509870081 SCGS_CS_acknowledgment_INS 226.1.3.136 50320 Multicast UDP
    def getMsgIdentifier(self):
        return 509870081

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS_ACK
    port = 50320

class SCGS_GW_designation_report_INS( SCGP_GW_designation_report_INS ): #non serve UDPADAPTER
    # 509870083 SCGS_CS_designation_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870083

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323

    def process(self):
        '''
        if not self.designation_control_in_pause and self.designation_type==2 and self.designation_status==2:
            msg=GW_SCGS_servo_control_INS() #( GUNServo = ON)
            msg.gun_servo=2
            msg.stabilization=2
            from decoder_scg import ActionManager
            ActionManager.AckObj( msg )

            if "SCGS_GW_acknowledgment_INS" in utility.mapMsgUdpIn:
                res=utility.mapMsgUdpIn["SCGS_GW_acknowledgment_INS"]
                if res.message_accepted==1:
                    self.status = True
                    msg.send()
        '''
        pass

class SCGS_MULTI_health_status_INS( SCGP_MULTI_health_status_INS):
    # 509804546 SCGS_MULTI_health_status_INS 226.1.3.138 50327 Multicast UDP
    def getMsgIdentifier(self):
        return 509804546

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS_MULTI
    port = 50327

class SCGS_MULTI_full_status_INS(SCGP_MULTI_full_status_INS):
    # 509804545 SCGS_MULTI_full_status_INS 226.1.3.136 50322 Multicast UDP
    def getMsgIdentifier(self):
        return 509804545

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS_ACK
    port = 50322

class SCGS_GW_servo_report_INS( SCGP_GW_servo_report_INS ):
    # 509870096 SCGS_CS_servo_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870096

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323

class SCGS_GW_gun_position_report_INS( SCGP_GW_gun_position_report_INS ):
    # 509870087 SCGS_CS_gun_position_report_INS 226.1.3.137 50325 Multicast UDP
    def getMsgIdentifier(self):
        return 509870087

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50325

class SCGS_CS_IR_report_INS(SCGP_CS_IR_report_INS):
    # 509870090 SCGS_CS_IR_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870090

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323


class SCGS_CS_LRF_inhibition_report_INS(SCGP_CS_LRF_inhibition_report_INS):
    # 509870100 SCGS_CS_LRF_inhibition_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 476315668

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50123

class SCGS_CS_LRF_report_INS(SCGP_CS_LRF_report_INS):
    # 509870092 SCGS_CS_LRF_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870092

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323

class SCGS_CS_cursors_report_INS(SCGP_CS_cursors_report_INS):
    # 509870082 SCGS_CS_cursors_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870082

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50123

class SCGS_CS_firing_burst_report_INS(SCGP_CS_firing_burst_report_INS):
    # 509870084 SCGS_CS_firing_burst_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870084

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323


class SCGS_CS_firing_correction_report_INS(SCGP_CS_firing_correction_report_INS):
    # 509870085 SCGS_CS_firing_correction_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870085

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323  

class SCGS_CS_firing_report_INS(SCGP_CS_firing_report_INS):
    # 509870086 SCGS_CS_firing_report_INS 226.1.3.137 50324 Multicast UDP
    def getMsgIdentifier(self):
        return 509870086

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50324  

class SCGS_CS_installation_data_INS(SCGP_CS_installation_data_INS):
    # 509870088 SCGS_CS_installation_data_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870088

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323  

class SCGS_CS_integrated_safety_settings_report_INS(SCGP_CS_integrated_safety_settings_report_INS):
    # 509870089 SCGS_CS_integrated_safety_settings_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870089

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323  

class SCGS_CS_loading_report_INS(SCGP_CS_loading_report_INS):
    # 509870091 SCGS_CS_loading_report_INS 226.1.3.136 50321 Multicast UDP
    def getMsgIdentifier(self):
        return 509870091

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS_ACK
    port = 50321  

class SCGS_CS_offset_report_INS( SCGP_CS_offset_report_INS ):
    # 509870093 SCGS_CS_offset_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870093

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323  

class SCGS_CS_range_report_INS( SCGP_CS_range_report_INS ):
    # 509870094 SCGS_CS_range_report_INS 226.1.3.137 50326 Multicast UDP
    def getMsgIdentifier(self):
        return 509870094

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50326 

class SCGS_CS_safety_report_INS( SCGP_CS_safety_report_INS ):
    # 509870095 SCGS_CS_safety_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870095

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323  

class SCGS_CS_software_version_INS( SCGP_CS_software_version_INS ):
    # 509870097 SCGS_CS_software_version_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870097

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323  

class SCGS_CS_tracker_report_INS(SCGP_CS_tracker_report_INS):
    # 509870098 SCGS_CS_tracker_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870098

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323 

class SCGS_CS_video_setting_report_INS( SCGP_CS_video_setting_report_INS ):
    # 509870099 SCGS_CS_video_setting_report_INS 226.1.3.137 50323 Multicast UDP
    def getMsgIdentifier(self):
        return 509870099

    def getMsgSender(self):
        return SCGS

    ip = IP_SCGS
    port = 50323 
