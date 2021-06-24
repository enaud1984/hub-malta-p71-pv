import logging

import utility

from manageNAVS import NAVS_MULTI_health_status_INS, NAVS_MULTI_wind_and_landing_deck_data_INS
from manageUDP import UDPAdapter
from common_struct import *
import numpy as np
from struct import unpack_from
from sender import GEIS_WAP,GEIS_IP,IP_GW_SCGP,GEIS_SCGF,IP_GW_SCGP_UPDATE,IP_GW_SCGF_UPDATE,IP_GW_SCGS_UPDATE,GEIS_SCGS
logger = logging.getLogger( __name__ )

class GW_Multi_health_status_INS( UDPAdapter ):
    # 1684229565 CS_MULTI_health_status_INS 226.1.200.1 10020 Multicast UDP

    listMsg = NAVS_MULTI_health_status_INS.listMsg + NAVS_MULTI_wind_and_landing_deck_data_INS.listMsg

    def getMsgIdentifier(self):
        return 1684229565

    def getMsgSender(self):
        return GEIS_WAP

    ip = GEIS_IP
    port = 10020
    formato_payload = "hhhh"
    timeLoop = 1  # frequenza
    # DATA
    cs_status = 2  # 16	2	1	enum		"1 : failure; 2 : operational; 3: training;"
    # non usati
    drmu_status = 2  # RADAR 18	2	1	enum		"1 : non operational; 2 :operational stand-by; 3 : operational recording;"
    spare = 1  # 20	2	1	padding
    css_status = 2  # 22	2	1	enum		"1: non operational; 2: operational;"
    status = True

    def getListAttribute(self):
        return ["cs_status", "drmu_status", "spare", "css_status"]

    def process(self):
        if "NAVS_MULTI_health_status_INS" in utility.mapMsgUdpOUT:
            msg = utility.mapMsgUdpOUT["NAVS_MULTI_health_status_INS"]
            self.cs_status = 2 if msg.status else 1
        else:
            self.cs_status = 3

    @property
    def payload(self):
        return self.cs_status, \
               self.drmu_status, \
               self.spare, \
               self.css_status

    def notify(self):
        from manageFlask import sendMessageMapUDP_IN, sendMessageMapUDP_OUT, sendMessageMapSerial
        from config import timestamp_format
        from copy import deepcopy
        try:
            mapMsg = {} 
            mapMsg.update(utility.mapMsgUdpOUT.copy())
            for k, v in mapMsg.items():
                from manageFlask import sock
                msg = v.values()
                # sock.emit( 'mapMsgOUT', {'data': msg},namespace="/test" )
                if v == self and self.timestamp is not None:
                    msg["timestamp"] = self.timestamp.strftime( timestamp_format )
                sendMessageMapUDP_OUT( msg )

            mapMsg = {} 
            mapMsg.update(utility.mapMsgUdpIn.copy())
            for k, v in mapMsg.items():
                from manageFlask import sock
                msg = v.values()
                if v.timestamp is not None:
                    msg["timestamp"] = v.timestamp.strftime( timestamp_format )
                else:
                    logger.error(f"Timestamp is NONE {k} {v}" )
                # sock.emit( 'mapMsgIN', {'data': msg}, namespace="/test" )
                sendMessageMapUDP_IN( msg )
    
            mapMsg = {} 
            mapMsg.update(utility.mapMsg.copy())
            for k, v in mapMsg.items():
                from manageFlask import sock
                msg = v.values()
                if v.timestamp is not None:
                    msg["timestamp"] = v.timestamp.strftime( timestamp_format )
                # sock.emit( 'mapMsgSerial', {'data': msg}, namespace="/test" )
                sendMessageMapSerial( msg )
        except Exception as e:
            logger.error( f"Error on notify ",e)

'''
GW -> SCGP
'''


class GW_SCGP_change_configuration_order_INS( UDPAdapter ):
    # 1679622145 CS_SCGP_change_configuration_order_INS 226.1.3.224 50211 Multicast UDP
    def getMsgIdentifier(self):
        return 1679622145

    def getMsgSender(self):
        return GEIS_WAP

    ip = IP_GW_SCGP
    port = 50211
    formato_payload = "Ih"
    # DATA
    action_id = np.uint( 0 )  # 16	4	1	UInt	N.A.	[0..(2^32)-1]
    configuration_request = 0  # 20	2	1	Enum	0: Local; 1: Autonomous 2: Integrated	Specifies the required configuration for the S / S

    def getListAttribute(self):
        return ["action_id", "configuration_request"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
               self.configuration_request


class GW_SCGP_designation_order_INS( UDPAdapter ):
    # 1679622147 CS_SCGP_designation_order_INS 226.1.3.224 50211 Multicast UDP
    def getMsgIdentifier(self):
        return 1679622147

    def getMsgSender(self):
        return GEIS_WAP

    ip = IP_GW_SCGP
    port = 50211
    fixed_size=66
    # DATA
    action_id = np.uint( 0 )  # 16	4	1	UInt
    designation_type = 0  # 20	2	1	Enum{1 : CST; 2: Position;}
    threat_key = True  # 22	1	1	Bool
    designation_control_pause = True  # 23	1	1	bool
    firing_authorization = 0  # 24	2	1	Enum{0: firing not authorised;1: firing authorised;}
    cstn = np.intc( 0 )  # 26	4	1	int
    # kinematics_time_of_validity	30	36	1	struct
    kinematics_time_of_validity = Struct_time_of_validity()

    # kinematics	38	28	1	union
    kinematics_type = 0  # 38	2	1	enum{1: 3D CARTESIAN KINEMATICS; 2:3D CARTESIAN POSITION; 3:2D CARTESIAN KINEMATICS; 4:2D CARTESIAN POSITION;5 : 2D POLAR KINEMATICS; 6:2D POLAR SURFACE KINEMATICS; 7 :2D POLAR POSITION; 8 : 2D POLAR SURFACE POSITION; 9 : 1D POLAR POSITION; 10 : EW 1D POLAR POSITION; 11 : EW 2D POLAR POSITION;}
    kinematics_class = [Struct_3d_cartesian_kinematics, Struct_3d_cartesian_position, Struct_2d_cartesian,
                        Struct_2d_cartesian_position, Struct_2d_polar_kinematics, Struct_2d_polar_surface,
                        Struct_2d_polar_position, Struct_2d_polar_surface_position, Struct_1d_polar_position,
                        Struct_ew_1d_polar_position, Struct_ew_2d_polar_position, ]
    kinematics = None

    # TODO: response_class = [SCGP_GW_acknowledgment_INS, SCGP_GW_designation_report_INS]  # Messaggi da SCGP a GW

    def getListAttribute(self):
        return ["action_id", "designation_type", "threat_key", "designation_control_pause", "firing_authorization",
                "cstn", "kinematics_time_of_validity", "kinematics_type", "kinematics"]

    @property
    def formato_payload(self):
        form_payload = "Ih??hi"
        form_payload += "IIh"
        if self.kinematics is not None and self.kinematics_type > 0:
            form_payload += self.kinematics.formato_payload.replace( ">", "" )
        return form_payload

    def decode(self, buffer):
        instance, format = self.decodeUdp( None, buffer, 16 )
        self.kinematics_time_of_validity, format_time = self.decodeUdp( Struct_time_of_validity, buffer, 30 )
        self.kinematics_type = unpack_from( ">" + format[-1], buffer, 38 )[0]
        if self.kinematics_type in range( len( self.kinematics_class ) ):
            struct_class = self.kinematics_class[self.kinematics_type - 1]
            self.kinematics, format_kinematics = self.decodeUdp( struct_class, buffer, 40 )
            format_val = format[:-1] + format_time + 'h' + format_kinematics
            if format_val.replace( ">", "" ) != self.formato_payload:
                logger.error(
                    str( self.__class__ ) + " Formato payload errato" + format_val + "---" + self.formato_payload )
        else:
            logger.error( "Formato non riconosciuto" )

    def process(self):
        pass

    def setValues(self, variables: dict):
        if "kinematics_type" in variables and variables["kinematics_type"] > -1:
            self.kinematics_type = variables["kinematics_type"]
            struct_class = self.kinematics_class[self.kinematics_type]
            init = {k: v for k, v in variables.items() if k in struct_class.__dict__}
            self.kinematics = struct_class()
            types = self.kinematics.getTypes()
            for k in init:
                value=types[k](init[k])
                setattr( self.kinematics, k, value )
            for k in self.getListAttribute(): #["action_id", "designation_type", "threat_key", "designation_control_pause","firing_authorization", "cstn", ]:
                if k in variables and "STRUCT" not in str(type(getattr(self,k))).upper():
                    setattr( self, k, variables[k] )
            self.kinematics_time_of_validity.seconds = 0
            self.kinematics_time_of_validity.microseconds = 0

    @property
    def payload(self):
        common = self.action_id, \
                 self.designation_type, \
                 self.threat_key, \
                 self.designation_control_pause, \
                 self.firing_authorization, \
                 self.cstn, \
                 self.kinematics_time_of_validity.seconds, \
                 self.kinematics_time_of_validity.microseconds, \
                 self.kinematics_type
        k = self.getkinematics()
        if k is None:
            logger.error( "k is None" )
        return common + k

    def getkinematics(self):
        if type( self.kinematics ) == Struct_3d_cartesian_kinematics:  # 40	26	1	struct
            return self.kinematics.spare, \
                   self.kinematics.x, \
                   self.kinematics.y, \
                   self.kinematics.z, \
                   self.kinematics.vx, \
                   self.kinematics.vy, \
                   self.kinematics.vz
        elif type( self.kinematics ) == Struct_3d_cartesian_position:  # 40	14	1	struct
            return self.kinematics.spare, \
                   self.kinematics.x, \
                   self.kinematics.y, \
                   self.kinematics.z

        elif type( self.kinematics ) == Struct_2d_cartesian:  # kinematics	40	18	1
            return self.kinematics.spare, \
                   self.kinematics.x, \
                   self.kinematics.y, \
                   self.kinematics.vx, \
                   self.kinematics.vy
        elif type( self.kinematics ) == Struct_2d_cartesian_position:  # 40	10	1	struct
            return self.kinematics.spare, \
                   self.kinematics.x, \
                   self.kinematics.y
        elif type( self.kinematics ) == Struct_2d_polar_kinematics:  # 40	18	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.angle_of_sight, \
                   self.kinematics.true_bearing_rate, \
                   self.kinematics.angle_of_sight_rate
        elif type( self.kinematics ) == Struct_2d_polar_surface:  # kinematics	40	18	1
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.range_2d, \
                   self.kinematics.true_bearing_rate, \
                   self.kinematics.range_rate
        elif type( self.kinematics ) == Struct_2d_polar_position:  # 40	10	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.angle_of_sight
        elif type( self.kinematics ) == Struct_2d_polar_surface_position:  # 40	10	1
            return self.kinematics.spare, \
                   self.kinematics.padding_range, \
                   self.kinematics.true_bearing
        elif type( self.kinematics ) == Struct_1d_polar_position:  # 40	6	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing  ##	42	4	1	float
        elif type( self.kinematics ) == Struct_ew_1d_polar_position:  # 40	14	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.origin_Latitude, \
                   self.kinematics.origin_Longitude  ##	50	4	1	Float	deg	[-180..+180]
        elif type( self.kinematics ) == Struct_ew_2d_polar_position:  # 40	18	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.angle_of_sight, \
                   self.kinematics.origin_latitude, \
                   self.kinematics.origin_longitude  ##	50	4	1	float	deg	[-180..+180]

    def checkPacket(self, calculate_len, offset, buffer, formatUnpack, instance):
        pass


class GW_SCGP_update_cst_kinematics_designation_INS( UDPAdapter ):
    # 1679622167 CS_SCGP_update_cst_kinematics_designation_INS 226.1.3.226 50213 Multicast UDP
    def getMsgIdentifier(self):
        return 1679622167

    def getMsgSender(self):
        return GEIS_WAP

    ip = IP_GW_SCGP_UPDATE
    port = 50213
    timeLoop = 0.5
    # DATA
    cstn = np.intc( 0 )  # 16	4	1	int
    # kinematics_time_of_validity	20	36	1	struct
    kinematics_time_of_validity = Struct_time_of_validity()

    # kinematics	28	28	1	union
    kinematics_type = 0  # 28	2	1	enum{1: 3D CARTESIAN KINEMATICS; 2:3D CARTESIAN POSITION; 3:2D CARTESIAN KINEMATICS; 4:2D CARTESIAN POSITION;5 : 2D POLAR KINEMATICS; 6:2D POLAR SURFACE KINEMATICS; 7 :2D POLAR POSITION; 8 : 2D POLAR SURFACE POSITION; 9 : 1D POLAR POSITION; 10 : EW 1D POLAR POSITION; 11 : EW 2D POLAR POSITION;}
    kinematics_class = [Struct_3d_cartesian_kinematics, Struct_3d_cartesian_position, Struct_2d_cartesian,
                        Struct_2d_cartesian_position, Struct_2d_polar_kinematics, Struct_2d_polar_surface,
                        Struct_2d_polar_position, Struct_2d_polar_surface_position, Struct_1d_polar_position,
                        Struct_ew_1d_polar_position, Struct_ew_2d_polar_position, ]
    kinematics = None

    # TODO: response_class = [SCGP_GW_acknowledgment_INS, SCGP_GW_designation_report_INS]  # Messaggi da SCGP a GW

    def getListAttribute(self):
        return ["cstn", "kinematics_time_of_validity", "kinematics_type", "kinematics"]

    @property
    def formato_payload(self):
        form_payload = "i"
        form_payload += "IIh"
        if self.kinematics is not None and self.kinematics_type > 0:
            k = self.kinematics
            k_format = k.formato_payload
            form_payload += k_format.replace( ">", "" )
        return form_payload

    def decode(self, buffer):
        instance, formatSelf = self.decodeUdp( None, buffer, 16 )
        self.kinematics_time_of_validity, format_time = self.decodeUdp( Struct_time_of_validity, buffer, 20 )
        self.kinematics_type = unpack_from( ">h", buffer, 28 )[0]

        if self.kinematics_type in range( len( self.kinematics_class ) ):
            struct_class = self.kinematics_class[self.kinematics_type - 1]
            self.kinematics, format_kinematics = self.decodeUdp( struct_class, buffer, 30 )
            format_val = formatSelf[:-1] + format_time + "h" + format_kinematics

            format_struct = self.formato_payload

            if format_val.replace( ">", "" ) != format_struct.replace( ">", "" ):
                logger.error( str( self.__class__ ) + " Formato payload errato" + format_val + "---" + format_struct )
        else:
            logger.error( "Formato non riconosciuto" )

    def checkPacket(self, calculate_len, offset, buffer, formatUnpack, instance):
        pass

    def process(self):
        pass

    def setValues(self, variables: dict):
        if "kinematics_type" in variables and variables["kinematics_type"] > -1:
            self.kinematics_type = variables["kinematics_type"]
            struct_class = self.kinematics_class[self.kinematics_type]
            init = {k: v for k, v in variables.items() if k in struct_class.__dict__}
            self.kinematics = struct_class()
            for k in init:
                setattr( self.kinematics, k, init[k] )
            for k in ["action_id", "designation_type", "threat_key", "designation_control_pause",
                      "firing_authorization", "cstn", ]:
                if k in variables:
                    setattr( self, k, variables[k] )
            self.kinematics_time_of_validity.seconds = 0
            self.kinematics_time_of_validity.microseconds = 0

    @property
    def payload(self):
        common = self.cstn, \
                 self.kinematics_time_of_validity.seconds, \
                 self.kinematics_time_of_validity.microseconds, \
                 self.kinematics_type
        k = self.getkinematics()
        if k is None:
            logger.error( "k is None" )
        return common + k

    def getkinematics(self):
        if type( self.kinematics ) == Struct_3d_cartesian_kinematics:  # 40	26	1	struct
            return self.kinematics.spare, \
                   self.kinematics.x, \
                   self.kinematics.y, \
                   self.kinematics.z, \
                   self.kinematics.vx, \
                   self.kinematics.vy, \
                   self.kinematics.vz
        elif type( self.kinematics ) == Struct_3d_cartesian_position:  # 40	14	1	struct
            return self.kinematics.spare, \
                   self.kinematics.x, \
                   self.kinematics.y, \
                   self.kinematics.z

        elif type( self.kinematics ) == Struct_2d_cartesian:  # kinematics	40	18	1
            return self.kinematics.spare, \
                   self.kinematics.x, \
                   self.kinematics.y, \
                   self.kinematics.vx, \
                   self.kinematics.vy
        elif type( self.kinematics ) == Struct_2d_cartesian_position:  # 40	10	1	struct
            return self.kinematics.spare, \
                   self.kinematics.x, \
                   self.kinematics.y
        elif type( self.kinematics ) == Struct_2d_polar_kinematics:  # 40	18	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.angle_of_sight, \
                   self.kinematics.true_bearing_rate, \
                   self.kinematics.angle_of_sight_rate
        elif type( self.kinematics ) == Struct_2d_polar_surface:  # kinematics	40	18	1
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.range_2d, \
                   self.kinematics.true_bearing_rate, \
                   self.kinematics.range_rate
        elif type( self.kinematics ) == Struct_2d_polar_position:  # 40	10	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.angle_of_sight
        elif type( self.kinematics ) == Struct_2d_polar_surface_position:  # 40	10	1
            return self.kinematics.spare, \
                   self.kinematics.padding_range, \
                   self.kinematics.true_bearing
        elif type( self.kinematics ) == Struct_1d_polar_position:  # 40	6	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing  ##	42	4	1	float
        elif type( self.kinematics ) == Struct_ew_1d_polar_position:  # 40	14	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.origin_Latitude, \
                   self.kinematics.origin_Longitude  ##	50	4	1	Float	deg	[-180..+180]
        elif type( self.kinematics ) == Struct_ew_2d_polar_position:  # 40	18	1	struct
            return self.kinematics.spare, \
                   self.kinematics.true_bearing, \
                   self.kinematics.angle_of_sight, \
                   self.kinematics.origin_latitude, \
                   self.kinematics.origin_longitude  ##	50	4	1	float	deg	[-180..+180]


class GW_SCGP_servo_control_INS( UDPAdapter ):
    # 1679622161 CS_SCGP_servo_control_INS 226.1.3.224 50211 Multicast UDP
    def getMsgIdentifier(self):
        return 1679622161

    def getMsgSender(self):
        from config import GEIS_WAP
        return GEIS_WAP

    ip = IP_GW_SCGP
    port = 50211
    formato_payload = "Ihhh???h"
    # DATA
    action_id = np.uint( 0 )  # 16	4	1	uint
    gun_servo = 0  # 20	2	1	enum 0 : No change;1 : OFF;2 : ON;
    stabilization = 0  # 22	2	1	enum 0 : No change;1 : OFF;2 : ON;
    manual_control = 0  # 24	2	1	enum 0: No change;1 : Slow;2 : Fast;
    # 0:_no_change;_1:slew_to_parking_position_precondition:_a.starttracking_=_off_b.fire_safety_=n(safe)_c._left/right_loading_position_=_no_loading_position_requested_d.._servo_=_on
    parking_position = True  # 26	1	1	bool
    left_loading_position = True  # 27	1	1	bool
    right_loading_position = True  # 28	1	1	bool
    drift_compensation = 0  # 29	2	1	enum		"0=no_change;1=off;2=on"

    def getListAttribute(self):
        return ["action_id", "gun_servo", "stabilization", "manual_control", "parking_position",
                "left_loading_position",
                "right_loading_position", "drift_compensation"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
               self.gun_servo, \
               self.stabilization, \
               self.manual_control, \
               self.parking_position, \
               self.left_loading_position, \
               self.right_loading_position, \
               self.drift_compensation

class GW_SCGP_integrated_safety_settings_INS( UDPAdapter ):
    #1679622153 CS_SCGP_integrated_safety_settings_INS 226.1.3.224 50211 Multicast UDP
    def getMsgIdentifier(self):
        return 1679622153

    def getMsgSender(self):
        from config import GEIS_WAP
        return GEIS_WAP

    ip = IP_GW_SCGP
    port = 50211
    formato_payload = "Ihhh"
    # DATA
    action_id = np.uint( 0 )  # 16	4	1	uint
    fire_enable = 0  # 20	2	1	enum 0 : No change; 1 : Firing Disabled; 2 : Firing Enabled;
    fire_without_tracking = 0  # 22	2	1	0 : No change; 1 : Not Authorised; 2 : Authorised;
    free_engagement_authorization = 0  # 24	2	1	0 : No change; 1 : Not Authorised; 2 : Authorised;

    def getListAttribute(self):
        return ["action_id", "fire_enable", "fire_without_tracking", "free_engagement_authorization"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
               self.fire_enable, \
               self.fire_without_tracking, \
               self.free_engagement_authorization


class GW_SCGP_movement_control_INS( UDPAdapter ):
    # 1679622158 CS_SCGP_movement_control_INS 226.1.3.225 50212 Multicast UDP
    def getMsgIdentifier(self):
        return 1679622158

    def getMsgSender(self):
        from config import GEIS_WAP
        return GEIS_WAP

    ip = "226.1.3.225"
    port =50212
    formato_payload = "hh"
    joystick_x_position=0
    joystick_y_position = 0

    def getListAttribute(self):
        return ["joystick_x_position", "joystick_y_position"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.joystick_x_position, \
               self.joystick_y_position


class GW_SCGP_tracker_control_INS( UDPAdapter ):
    # 1679622165 CS_SCGP_tracker_control_INS 226.1.3.224 50211 Multicast UDP
    def getMsgIdentifier(self):
        return 1679622165

    def getMsgSender(self):
        from config import GEIS_WAP
        return GEIS_WAP

    ip = IP_GW_SCGP
    port =50211
    formato_payload = "Ihhh"
    # DATA
    action_id = np.uint( 0 )  # 16	4	1	uint
    enable = 0  # 20	2	1	enum 0 : No change; 1 : OFF; 2 : ON;
    algorithm = 0  # 22	2	1	0 : No change; 1 : Correlation; 2 : Contrast;
    start_stop_tracker = 0  # 24	2	1	0 : No change; 1 : Stop tracker; 2 : Start tracker;
    window_resize=0 #26 2   1 0 : Stop; 1 : Decrease window size; 2 : Increase window size;

    def getListAttribute(self):
        return ["action_id", "enable", "algorithm", "start_stop_tracker","window_resize"]

    def process(self):
        pass

    @property
    def payload(self):
        return self.action_id, \
               self.enable, \
               self.algorithm, \
               self.start_stop_tracker, \
               self.window_resize



'''
GW -> SCGF
'''

class GW_SCGF_change_configuration_order_INS( GW_SCGP_change_configuration_order_INS ):
    # 1679556609 CS_SCGF_change_configuration_order_INS 226.1.3.56 50111 Multicast UDP
    def getMsgIdentifier(self):
        return 1679556609

    def getMsgSender(self):
        return GEIS_WAP

    ip = GEIS_SCGF
    port = 50111


class GW_SCGF_designation_order_INS( GW_SCGP_designation_order_INS ):
    # 1679556611 CS_SCGF_designation_order_INS 226.1.3.56 50111 Multicast UDP
    def getMsgIdentifier(self):
        return 1679556611

    def getMsgSender(self):
        return GEIS_WAP

    ip = GEIS_SCGF
    port = 50111


class GW_SCGF_update_cst_kinematics_designation_INS( GW_SCGP_update_cst_kinematics_designation_INS ):
    # 1679556631 CS_SCGF_update_cst_kinematics_designation_INS 226.1.3.58 50113 Multicast UDP
    def getMsgIdentifier(self):
        return 1679556631

    def getMsgSender(self):
        return GEIS_WAP

    ip = IP_GW_SCGF_UPDATE
    port = 50113


class GW_SCGF_servo_control_INS( GW_SCGP_servo_control_INS ):
    # 1679556625 CS_SCGF_servo_control_INS 226.1.3.56 50111 Multicast UDP
    def getMsgIdentifier(self):
        return 1679556625

    ip = GEIS_SCGF
    port = 50111

class GW_SCGF_integrated_safety_settings_INS( GW_SCGP_integrated_safety_settings_INS ):
    #1679556617 CS_SCGF_integrated_safety_settings_INS 226.1.3.56 50111 Multicast UDP
    def getMsgIdentifier(self):
        return 1679556617

    ip = GEIS_SCGF
    port = 50111

class GW_SCGF_movement_control_INS(GW_SCGP_movement_control_INS):
    #1679556622 CS_SCGF_movement_control_INS 226.1.3.57 50112 Multicast UDP
    def getMsgIdentifier(self):
        return 1679556622

    ip = "226.1.3.57"
    port = 50112

class GW_SCGF_tracker_control_INS(GW_SCGP_tracker_control_INS):
    #1679556629 CS_SCGF_tracker_control_INS 226.1.3.56 50111 Multicast UDP
    def getMsgIdentifier(self):
        return 1679556629

    ip = GEIS_SCGF
    port = 50111

'''
GW -> SCGS
'''


class GW_SCGS_change_configuration_order_INS( GW_SCGP_change_configuration_order_INS ):
    # 1679687681 CS_SCGS_change_configuration_order_INS 226.1.3.127 50311 Multicast UDP
    def getMsgIdentifier(self):
        return 1679687681

    def getMsgSender(self):
        return GEIS_WAP

    ip = GEIS_SCGS
    port = 50311


class GW_SCGS_designation_order_INS( GW_SCGP_designation_order_INS ):
    # 1679687683 CS_SCGS_designation_order_INS 226.1.3.127 50311 Multicast UDP
    def getMsgIdentifier(self):
        return 1679556611

    def getMsgSender(self):
        return GEIS_WAP

    ip = GEIS_SCGS
    port = 50111


class GW_SCGS_update_cst_kinematics_designation_INS( GW_SCGP_update_cst_kinematics_designation_INS ):
    # 1679687703 CS_SCGS_update_cst_kinematics_designation_INS 226.1.3.129 50313 Multicast UDP
    def getMsgIdentifier(self):
        return 1679687703

    def getMsgSender(self):
        return GEIS_WAP

    ip = IP_GW_SCGS_UPDATE
    port = 50313


class GW_SCGS_servo_control_INS( GW_SCGP_servo_control_INS ):
    # 1679687697 CS_SCGS_servo_control_INS 226.1.3.127 50311 Multicast UDP
    def getMsgIdentifier(self):
        return 1679687697

    def getMsgSender(self):
        return GEIS_WAP

    ip = GEIS_SCGS
    port = 50311

class GW_SCGS_integrated_safety_settings_INS( GW_SCGP_integrated_safety_settings_INS ):
    #1679687689 CS_SCGS_integrated_safety_settings_INS 226.1.3.127 50311 Multicast UDP
    def getMsgIdentifier(self):
        return 1679687689

    ip = GEIS_SCGS
    port = 50311

class GW_SCGS_movement_control_INS(GW_SCGP_movement_control_INS):
    #1679687694 CS_SCGS_movement_control_INS 226.1.3.128 50312 Multicast UDP
    def getMsgIdentifier(self):
        return 1679687694

    ip = "226.1.3.128"
    port = 50312

class GW_SCGS_tracker_control_INS(GW_SCGP_tracker_control_INS):
    #1679687701 CS_SCGS_tracker_control_INS 226.1.3.127 50311 Multicast UDP
    def getMsgIdentifier(self):
        return 1679687701

    ip = GEIS_SCGS
    port = 50311
