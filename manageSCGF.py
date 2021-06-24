import logging
from common_struct import *
from sender import SCGF,IP_SCGF,IP_SCGF_ACK,IP_SCGF,IP_SCGF_MULTI  
from manageSCGP import SCGP_GW_acknowledgment_INS, SCGP_GW_designation_report_INS, SCGP_MULTI_health_status_INS, \
    SCGP_GW_gun_position_report_INS, SCGP_GW_servo_report_INS,SCGP_MULTI_full_status_INS, \
    SCGP_CS_IR_report_INS,SCGP_CS_LRF_inhibition_report_INS,SCGP_CS_LRF_report_INS,SCGP_CS_cursors_report_INS,SCGP_CS_firing_burst_report_INS, \
    SCGP_CS_firing_correction_report_INS,SCGP_CS_firing_report_INS,SCGP_CS_installation_data_INS,SCGP_CS_integrated_safety_settings_report_INS, \
    SCGP_CS_loading_report_INS,SCGP_CS_offset_report_INS,SCGP_CS_offset_report_INS,SCGP_CS_range_report_INS,SCGP_CS_safety_report_INS,SCGP_CS_software_version_INS, \
    SCGP_CS_tracker_report_INS,SCGP_CS_video_setting_report_INS
#

logger = logging.getLogger( __name__ )

'''
Messaggi da SCGF(Cannoncino) a WG e viceversa tramite socket UDP
'''

'''
SCGF -> GW
'''
class SCGF_GW_acknowledgment_INS( SCGP_GW_acknowledgment_INS):
    # 476315649 SCGF_CS_acknowledgment_INS 226.1.3.59 50120 Multicast UDP
    def getMsgIdentifier(self):
        return 476315649

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF_ACK
    port = 50120

class SCGF_GW_designation_report_INS( SCGP_GW_designation_report_INS ): #non serve UDPADAPTER
    # 476315651 SCGF_CS_designation_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315651

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123

    def process(self):
        '''
        if not self.designation_control_in_pause and self.designation_type==2 and self.designation_status==2:
            msg=GW_SCGF_servo_control_INS() #( GUNServo = ON)
            msg.gun_servo=2
            msg.stabilization=2
            from decoder_scg import ActionManager
            ActionManager.AckObj( msg )

            if "SCGF_GW_acknowledgment_INS" in utility.mapMsgUdpIn:
                res=utility.mapMsgUdpIn["SCGF_GW_acknowledgment_INS"]
                if res.message_accepted==1:
                    self.status = True
                    msg.send()
        '''
        pass

class SCGF_MULTI_health_status_INS( SCGP_MULTI_health_status_INS):
    # 476250114 SCGF_MULTI_health_status_INS 226.1.3.69 50127 Multicast UDP
    def getMsgIdentifier(self):
        return 476250114

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF_MULTI
    port = 50127

class SCGF_MULTI_full_status_INS(SCGP_MULTI_full_status_INS):
    # 476250113 SCGF_MULTI_full_status_INS 226.1.3.59 50122 Multicast UDP
    def getMsgIdentifier(self):
        return 476250113

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF_ACK
    port = 50122

class SCGF_GW_servo_report_INS( SCGP_GW_servo_report_INS ):
    # 476315664 SCGF_CS_servo_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315664

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123

class SCGF_GW_gun_position_report_INS( SCGP_GW_gun_position_report_INS ):
    # 476315655 SCGF_CS_gun_position_report_INS 226.1.3.60 50125 Multicast UDP
    def getMsgIdentifier(self):
        return 476315655

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50125

class SCGF_CS_IR_report_INS(SCGP_CS_IR_report_INS):
    #476315658 SCGF_CS_IR_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315658

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123


class SCGF_CS_LRF_inhibition_report_INS(SCGP_CS_LRF_inhibition_report_INS):
    #476315668 SCGF_CS_LRF_inhibition_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315668

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123

class SCGF_CS_LRF_report_INS(SCGP_CS_LRF_report_INS):
    #476315660 SCGF_CS_LRF_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315660

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123

class SCGF_CS_cursors_report_INS(SCGP_CS_cursors_report_INS):
    #476315650 SCGF_CS_cursors_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315650

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123

class SCGF_CS_firing_burst_report_INS(SCGP_CS_firing_burst_report_INS):
    #476315652 SCGF_CS_firing_burst_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315652

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123


class SCGF_CS_firing_correction_report_INS(SCGP_CS_firing_correction_report_INS):
    #476315653 SCGF_CS_firing_correction_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315653

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123  

class SCGF_CS_firing_report_INS(SCGP_CS_firing_report_INS):
    #476315654 SCGF_CS_firing_report_INS 226.1.3.60 50124 Multicast UDP
    def getMsgIdentifier(self):
        return 476315654

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50124  

class SCGF_CS_installation_data_INS(SCGP_CS_installation_data_INS):
    #476315656 SCGF_CS_installation_data_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315656

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123  

class SCGF_CS_integrated_safety_settings_report_INS(SCGP_CS_integrated_safety_settings_report_INS):
    #476315657 SCGF_CS_integrated_safety_settings_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315657

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123  

class SCGF_CS_loading_report_INS(SCGP_CS_loading_report_INS):
    #476315659 SCGF_CS_loading_report_INS 226.1.3.59 50121 Multicast UDP
    def getMsgIdentifier(self):
        return 476315659

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF_ACK
    port = 50121  

class SCGF_CS_offset_report_INS( SCGP_CS_offset_report_INS ):
    #476315661 SCGF_CS_offset_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315661

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123  

class SCGF_CS_range_report_INS( SCGP_CS_range_report_INS ):
    #476315662 SCGF_CS_range_report_INS 226.1.3.60 50126 Multicast UDP
    def getMsgIdentifier(self):
        return 476315662

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50126 

class SCGF_CS_safety_report_INS( SCGP_CS_safety_report_INS ):
    #476315663 SCGF_CS_safety_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315663

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123  

class SCGF_CS_software_version_INS( SCGP_CS_software_version_INS ):
    #476315665 SCGF_CS_software_version_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315665

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123  

class SCGF_CS_tracker_report_INS(SCGP_CS_tracker_report_INS):
    #476315666 SCGF_CS_tracker_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315666

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123 

class SCGF_CS_video_setting_report_INS( SCGP_CS_video_setting_report_INS ):
    #476315667 SCGF_CS_video_setting_report_INS 226.1.3.60 50123 Multicast UDP
    def getMsgIdentifier(self):
        return 476315667

    def getMsgSender(self):
        return SCGF

    ip = IP_SCGF
    port = 50123 
