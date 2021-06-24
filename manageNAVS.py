import logging

import phinx
from common_struct import *
from manageUDP import UDPAdapter
from sender import NAVS,IP_NAVS_MULTI_WI,IP_NAVS_MULTI_GYRYO_AFT,IP_NAVS_MULTI_GYRYO_FORE,IP_NAVS_MULTI_HEALTH,IP_NAVS_MULTI_DATA
logger = logging.getLogger( __name__ )


# Message Sender Enum
class NAVS_MULTI_wind_and_landing_deck_data_INS( UDPAdapter ):
    # 425920945 NAVS_MULTI_wind_and_landing_deck_data_INS 226.1.50.4 6203 Multicast UDP
    listMsg = ["WIMWVR", "WIMWVT", "WIMTW", "WIXDR"]  # XDR si deve differenziare per deck e sea
    sensor_availability = 0
    absWindSpeed = 0.0
    absWindDir = 0.0
    relWindSpeed = 0.0
    relWindDir = 0.0
    air_temp_origin = 2  # AUTOMATIC MODE;
    airTemp = 0.0
    status = False
    ui = False
    air_hum_ori = 1  # AUTOMATIC MODE
    airHum = np.uint( 0 )
    dew_point_temp_origin = 1
    dewPointTemp = 0.0
    atm_pres_orig = 1
    landDeckAtmPres = 0.0
    seaSurfaceAtmPres = 0.0
    sea_surface_temp_origin = 2  # SENSOR MODE
    seaSurfaceTemp = 0.0

    formato_payload = "hffffhfhIhfhffhf"
    ip = IP_NAVS_MULTI_WI  
    port = 6203  # 6203
    timeLoop = 0.1

    def getListAttribute(self):
        return ["sensor_availability",
                "absWindSpeed",
                "absWindDir",
                "relWindSpeed",
                "relWindDir",
                "air_temp_origin",
                "airTemp",
                "air_hum_ori",
                "airHum",
                "dew_point_temp_origin",
                "dewPointTemp",
                "atm_pres_orig",
                "landDeckAtmPres",
                "seaSurfaceAtmPres",
                "sea_surface_temp_origin",
                "seaSurfaceTemp"]

    def getMsgIdentifier(self):
        return 425920945

    def getMsgSender(self):
        return NAVS

    def process(self):
        valid = 0
        prefix_ui = 0
        mapMsg = self.getMapMsgSerial()
        for k in self.listMsg:
            if k in mapMsg:
                msg = mapMsg[k]
                if k == "WIMWVT":
                    self.absWindSpeed = self.getValueFromInput( msg, k, "wind_speed" )
                    self.absWindDir = self.getValueFromInput( msg, k, "wind_direction" )
                elif k == "WIMWVR":
                    self.relWindSpeed = self.getValueFromInput( msg, k, "wind_speed" )
                    self.relWindDir = self.getValueFromInput( msg, k, "wind_direction" )
                elif k == "WIXDR":
                    self.airTemp = self.getValueFromInput( msg, k, "measurement_data",
                                                           {"field_control": "transducer_id", "expected_value": "TA1"} )
                    self.airHum = int(
                        self.getValueFromInput( msg, k, "measurement_data", {"field_control": "transducer_id",
                                                                             "expected_value": "RH1"} ) )
                    self.dewPointTemp = self.getValueFromInput( msg, k, "measurement_data",
                                                                {"field_control": "transducer_id",
                                                                 "expected_value": "DP1"} )
                    self.landDeckAtmPres = self.getValueFromInput( msg, k, "measurement_data",
                                                                   {"field_control": "transducer_id",
                                                                    "expected_value": "PA1"} )
                    self.seaSurfaceAtmPres = self.getValueFromInput( msg, k, "measurement_data",
                                                                     {"field_control": "transducer_id",
                                                                      "expected_value": "PA1"} )
                elif k == "WIMTW":
                    self.seaSurfaceTemp = self.getValueFromInput( msg, k, "water_temperature" )
                    self.sea_surface_temp_origin = 2 if mapMsg[k].prefix == "WI" else 1
                if mapMsg[k].prefix == "UI":
                    prefix_ui += 1
                if mapMsg[k].prefix == "WI" and mapMsg[k].isValid():
                    valid += 1

        '''
                    for v in mapMsg[k].element_msg:
                        mapValues.update(v)
                    valid+=1
        tupleValue=[]
                for k in self.listValues:
            tupleValue.append(mapValues[k])
        '''
        self.status = (valid == len( self.listMsg ))

        #self.status = True  # TODO: da rimuovere! solo per test con Nmea APP di Chrome

        self.ui = prefix_ui > 0

    @property
    def _sensorAvailability(self):
        '''
        0 = AVAILABLE; Wind data are provided by environmental sensors (sensors 1 and 2)
        1= DEGRADED; Wind data are manually introduced by the operator
        2 = FAILED; Wind data are not available
        '''

        if self.ui:
            self.sensor_availability = 1
            return 1
        if self.status:
            self.sensor_availability = 0
            return 0
        else:
            self.sensor_availability = 2
            return 2

    @property
    def payload(self):

        return self._sensorAvailability, \
               self.absWindSpeed, \
               self.absWindDir, \
               self.relWindSpeed, \
               self.relWindDir, \
               self.air_temp_origin, \
               self.airTemp, \
               self.air_hum_ori, \
               self.airHum, \
               self.dew_point_temp_origin, \
               self.dewPointTemp, \
               self.atm_pres_orig, \
               self.landDeckAtmPres, \
               self.seaSurfaceAtmPres, \
               self.sea_surface_temp_origin, \
               self.seaSurfaceTemp


class NAVS_MULTI_gyro_aft_nav_data_10ms_INS( UDPAdapter ):
    # 425920941 NAVS_MULTI_gyro_aft_nav_data_10ms_INS 226.1.50.6 10013 Multicast UDP
    sensor_reference = 0  # {"0 : GYRO AFT; 1: GYRO FORE;}
    gyro_readiness_state = 0  # { 0 :OPERATIONAL; 1 : SIMULATION; 2 : ALIGNMENT;}
    gyro_availability = 0  # {0 : AVAILABLE; 1 : DEGRADED; 2 : FAILED;}
    # time_of_validity=struct
    time_of_validity = Struct_time_of_validity()

    # ship_attitude=struct
    ship_attitude = Struct_Ship_Attitude()

    source = 1

    def getListAttribute(self):
        return ["sensor_reference",
                "gyro_readiness_state",
                "gyro_availability","time_of_validity","ship_attitude"]

    def decode(self, buffer):
        instance, format = self.decodeUdp( None, buffer, 16 )
        self.time_of_validity, format_time = self.decodeUdp( Struct_time_of_validity, buffer, 22 )
        self.ship_attitude, format_att = self.decodeUdp( Struct_Ship_Attitude, buffer, 30 )
        format_val = format + format_time + format_att
        if format_val.replace( ">", "" ) != self.formato_payload:
            logger.error(
                str( self.__class__ ) + " Formato payload errato" + format_val + "---" + self.formato_payload )

    @property
    def payload(self):
        return self.sensor_reference, \
               self.gyro_readiness_state, \
               self.gyro_availability, \
               self.time_of_validity.seconds, \
               self.time_of_validity.microseconds, \
               self.ship_attitude.heading, \
               self.ship_attitude.relative_roll, \
               self.ship_attitude.absolute_pitch, \
               self.ship_attitude.heading_rate, \
               self.ship_attitude.relative_roll_rate, \
               self.ship_attitude.absolute_pitch_rate, \
               self.ship_attitude.north_velocity, \
               self.ship_attitude.east_velocity, \
               self.ship_attitude.vertical_velocity

    formato_payload = "hhhIIfffffffff"
    ip = IP_NAVS_MULTI_GYRYO_AFT
    port = 10013
    timeLoop = 0.01

    def getMsgIdentifier(self):
        return 425920941

    def getMsgSender(self):
        return NAVS

    listMsg = ["AIPOV", "GPGGA", "HEROT", "GPZDA"]

    def analyzeMessages(self,listMsg,recovery=False):
        valid = 0
        dateZDA = None
        mapValid = {}
        mapDegraded = {}
        mapFailure = {}
        mapMsg = utility.mapMsg
        for k in listMsg:  # range(len(self.listMsg)):
            # k=self.listMsg[i]
            if k in mapMsg:
                valid += 1 if mapMsg[k].isValid() else 0
                msg = mapMsg[k]
                if k.startswith( "GPZDA" ):
                    continue
                elif k.startswith( "GPGGA" ):
                    gps_quality = self.getValueFromInput( msg, k, "gps_quality" )
                    if gps_quality is not None and gps_quality > 0:
                        if self.source==1:
                           gpzda = "GPZDA" 
                           pixse_time = "PIXSE.TIME__"
                        else:
                           gpzda = "GPZDA2" 
                           pixse_time = "PIXSE2.TIME__"
                        msg = mapMsg.get(gpzda)
                        msg_time = mapMsg.get(pixse_time)
                        if msg is not None:
                            giorno = self.getValueFromInput( msg, gpzda, "day" )
                            mese = self.getValueFromInput( msg, gpzda, "month" )
                            anno = self.getValueFromInput( msg, gpzda, "year" )
                            if giorno and mese and anno:
                                dateZDA = "{}/{}/{}".format( giorno, mese, anno )
                                utc =self.getValueFromInput( msg, k, "utc_of_position" )
                                self.time_of_validity.seconds, self.time_of_validity.microseconds = utility.convertUTC(dateZDA,utc)
                        elif msg_time is not None:
                            utc = self.getValueFromInput( msg_time, pixse_time, "utc_time" )
                            self.time_of_validity.seconds, self.time_of_validity.microseconds = utility.convertUTC(None ,utc )
                            
                elif k.startswith( "HEROT" ):
                    status = self.getValueFromInput( msg, k, "status" )
                    if status == "A":
                        self.ship_attitude.heading_rate = self.getValueFromInput( msg, k, "heading_rate" )
                    self.gyro_readiness_state = 1 if status == "A" else 0
                elif k.startswith( "PSXN" ):
                    status_ph = self.getValueFromInput( msg, k, "status_ph" )
                    user_identification = self.getValueFromInput( msg, k, "user identification" )
                    if status_ph == 10 and user_identification == "014":
                        self.ship_attitude.heading = self.getValueFromInput( msg, k, "heading" )
                        self.ship_attitude.relative_roll = self.getValueFromInput( msg, k, "roll" )
                        self.ship_attitude.absolute_pitch = self.getValueFromInput( msg, k, "pitch" )
                        self.ship_attitude.heading_rate = self.getValueFromInput( msg, k, "heading rate" )
                        self.ship_attitude.relative_roll_rate = self.getValueFromInput( msg, k, "roll rate" )
                        self.ship_attitude.absolute_pitch_rate = self.getValueFromInput( msg, k, "pitch rate" )
                elif k.startswith( "AIPOV" ):
                    utc = self.getValueFromInput( msg, k, "utc_time" )
                    self.time_of_validity.seconds, self.time_of_validity.microseconds = utility.convertUTC(None ,utc )
                    self.ship_attitude.north_velocity = self.getValueFromInput( msg, k, "north_velocity" )
                    self.ship_attitude.east_velocity = self.getValueFromInput( msg, k, "east_velocity" )
                    self.ship_attitude.vertical_velocity = self.getValueFromInput( msg, k, "down_velocity_xv3" )

                    #"$AIPOV, 010622.7125, 47.764, 47.764, -47.764, 100.000, -100.000, -100.000, 0.00, 0.00, 0.00, 41.90278199, 012.49636600, 0.000, 203.758, 200.000, -200.000, 203.758, -200.000, -200.000, 47.764, 00000001 * 60"
                    if not recovery:
                        status_gyro = self.getValueFromInput( msg, k,"user_status" )
                        mapValid, mapDegraded, mapFailure = phinx.analyzeUserStatus( self, status_gyro )
                        self.gyro_availability = phinx.gyro_availability( mapValid, mapDegraded, mapFailure  )
                        self.gyro_readiness_state = phinx.gyro_readiness_state( mapValid )
                        self.status = mapDegraded is None and mapFailure is None and len( mapValid ) > 0
        return valid,dateZDA,mapValid, mapDegraded, mapFailure
    
    def process(self):
        listMsg = self.listMsg
        valid, dateZDA, mapValid, mapDegraded, mapFailure = self.analyzeMessages(self.listMsg)
        self.allMsgReceived = valid == len( listMsg )
        if not self.status:
            logger.info("Messaggio non pronto")
        elif not self.allMsgReceived:
            if self.source==1:
                listMsg = NAVS_MULTI_gyro_fore_nav_data_10ms_INS.listMsg
            elif self.source==2:
                listMsg = NAVS_MULTI_gyro_aft_nav_data_10ms_INS.listMsg
            valid, dateZDA, mapValid, mapDegraded, mapFailure = self.analyzeMessages(listMsg,True)
            self.allMsgReceived = valid == len( listMsg )
            self.sensor_reference = 1 if self.source == 1 else 0  # FORE=1 | AFT=0
            self.gyro_availability = 2
        elif self.allMsgReceived:
            self.sensor_reference = 0 if self.source == 1 else 1  # FORE=1 | AFT=0


class NAVS_MULTI_gyro_fore_nav_data_10ms_INS( NAVS_MULTI_gyro_aft_nav_data_10ms_INS ):
    # 425920942 NAVS_MULTI_gyro_fore_nav_data_10ms_INS 226.1.50.7 10014 Multicast UDP
    source = 2
    ip = IP_NAVS_MULTI_GYRYO_FORE
    port = 10014
    timeLoop = 0.01
    listMsg = ["AIPOV","GPGGA2", "AIPOV2", "HEROT2", "GPZDA2"] #AIPOV ha lo stato quindi mando sempre il messaggio di FORE
    sensor_reference = 1

    def getMsgIdentifier(self):
        return 425920942

    def process(self):
        super().process()

class NAVS_MULTI_health_status_INS( UDPAdapter ):
    # 425920943 NAVS_MULTI_health_status_INS 226.1.50.1 10017 Multicast UDP
    def getMsgIdentifier(self):
        return 425920943

    def getMsgSender(self):
        return NAVS

    ip = IP_NAVS_MULTI_HEALTH
    port = 10017
    timeLoop = 0.01
    listMsg = ["AIPOV", "AIPOV2", "HEALC", "HEALR", "HEALC2", "HEALR2"]
    formato_payload = "hh"
    # DATA
    readiness_state = 0  # 16	2	1	Enum	0 : OPERATIONAL;1 : SIMULATION;Indicates the operative mode of the Navigation Equipment.	The Simulation mode is only used for off-line tests purposes
    availability = 0  # 18	2	1	Enum	0 : AVAILABLE;1 : DEGRADED;2 : FAILED;
    instance = None

    def getListAttribute(self):
        return ["readiness_state", "availability"]

    def process(self):
        self.readiness_state = 1
        self.availability = 2
        valid = [0, 0]
        status_giros = [False, False]
        total_alert = [0, 0]
        healr_status = [{}, {}]
        mapMsg = self.getMapMsgSerial()
        for k in self.listMsg:
            if k in mapMsg:
                msg = mapMsg[k]
                source = 2 if k.endswith("2") else 1
                if k.startswith( "AIPOV" ):
                    user_status = self.getValueFromInput( msg, k, "user_status" )
                    mapValid, mapDegraded, mapFailure = phinx.analyzeUserStatus( self, user_status )
                    status_giros[source - 1] = mapDegraded is None and mapFailure is None and len( mapValid ) > 0
                    valid[source - 1] += 1
                elif k.startswith( "HEALC" ):
                    total_alert[source - 1] = self.getValueFromInput( msg, k, "tot_alert" )
                    valid[source - 1] += 1
                elif k.startswith( "HEALR" ):
                    if self.getValueFromInput( msg, k, "unique_alertID" ) == 240:
                        healr_status[msg.source - 1] = {
                            "alert_condition": self.getValueFromInput( msg, k, "alert_condition" ) == 'A',
                            "alert_desc": self.getValueFromInput( msg, k, "desc" )}
                        valid[msg.source - 1] += 1
        if valid[0] > 0 or valid[1] > 0:
            self.readiness_state = 0
            self.availability = 1 if status_giros[0] and status_giros[0] else 2
            self.instance = {"valid": valid,
                             "status_giros": status_giros,
                             "tot_alert": total_alert,
                             "healr_status": healr_status
                             }
            self.status = True
        else:
            validOne = 0
            self.readiness_state = 1

            if "NAVS_MULTI_wind_and_landing_deck_data_INS" in utility.mapMsgUdpOUT:
                msg = utility.mapMsgUdpOUT["NAVS_MULTI_wind_and_landing_deck_data_INS"]
                if msg.status:
                    self.readiness_state = 0
                    validOne += 1
            if "NAVS_MULTI_nav_data_100ms_INS" in utility.mapMsgUdpOUT:
                msg = utility.mapMsgUdpOUT["NAVS_MULTI_nav_data_100ms_INS"]
                if msg.allMsgReceived and msg.status:
                    validOne += 1
            if "NAVS_MULTI_gyro_aft_nav_data_10ms_INS" in utility.mapMsgUdpOUT:
                msg = utility.mapMsgUdpOUT["NAVS_MULTI_gyro_aft_nav_data_10ms_INS"]
                if msg.status:
                    validOne += 1
                if validOne > 1:
                    self.availability = 1
            elif validOne > 1:
                self.availability = 1
            self.status = validOne > 0

    @property
    def payload(self):
        return self.readiness_state, \
               self.availability

class NAVS_MULTI_nav_data_100ms_INS( UDPAdapter ):
    # 425920944 NAVS_MULTI_nav_data_100ms_INS 226.1.50.2 10015 Multicast UDP
    # time_of_validity=struct
    time_of_validity = Struct_time_of_validity()
    # ship_position=struct
    ship_position = Struct_Ship_Position()
    ship_attitude = Struct_Ship_Attitude()
    # data
    ship_heave = 0.0
    water_depth = 0.0
    attitude_and_velocities_validity = 2  # {0 : AVAILABLE; Own ship attitude and velocities are provided by the Gyros. 1 : DEGRADED; Own ship attitude and}
    heading_validity = 1  # {0 : AVAILABLE; Heading is provided by the Gyros, 1 : DEGRADED; Heading is provided by the Magnetic Compass, 2 : FAILED; Heading is not available Heading validity.}
    course_and_speed_over_ground_validity = 1  # {0 : AVAILABLE; Course and Speed over ground are provided by the Gyros ,1 : DEGRADED; Course and Speed over ground are provided by the GPSs ,2 : FAILED; Course and Speed over ground are not available Course and Speed over ground validity.}
    position_validity = 1  # {0 : AVAILABLE; The ship position is provided by the Gyros ,1 : DEGRADED; The ship position is provided by the GPSs or is entered manuallyby the operator ,2 : FAILED; The ship position is not available}
    set_and_drift_validity = 1  # {0 : AVAILABLE and drift are provided by the Gyros ,1 = DEGRADED; The ship position is entered manually by the operator ,2 = FAILED; The ship position is not available}
    water_depth_validity = 2  # {0 : AVAILABLE; The water depth is provided by the Echosounder ,1 : DEGRADED; The water depth is entered manually by the operator;2 : FAILED; The water depth is not available r}

    def getListAttribute(self):
        return ["ship_heave", "water_depth", "attitude_and_velocities_validity",
                "heading_validity", "course_and_speed_over_ground_validity",
                "position_validity", "set_and_drift_validity", "water_depth_validity","time_of_validity","ship_position","ship_attitude"]

    def getMsgIdentifier(self):
        return 425920944

    def getMsgSender(self):
        return NAVS

    formato_payload = "IIffffffffffffffffffffhhhhhh"
    ip = IP_NAVS_MULTI_DATA
    port = 10015  # 6203
    timeLoop = 0.1
    listMsg = ["GPGGA", "GPGLL", "GPGST", "HEROT", "PSXN", "AIPOV", "GPZDA","GPVTG","PSIMSSB",
               "PIXSEATITUD","PIXSESTATUS","PIXSEDEPIN_","PIXSEPOSITI",
               "PIXSESPEED_","PIXSEUTMWGS","PIXSEHEAVE_","PIXSETIME__",
               "PIXSESTDHRP","PIXSESTDPOS","PIXSESTDSPD","PIXSEALGSTS",
               "PIXSEHT_STS" ]

    @property
    def payload(self):  # self.sp.vset
        return self.time_of_validity.seconds, \
               self.time_of_validity.microseconds, \
               self.ship_position.latitude, \
               self.ship_position.longitude, \
               self.ship_position.log_speed, \
               self.ship_position.course_made_good, \
               self.ship_position.speed_over_ground, \
               self.ship_position.set, \
               self.ship_position.drift, \
               self.ship_position.latitude_accuracy, \
               self.ship_position.longitude_accuracy, \
               self.ship_attitude.heading, \
               self.ship_attitude.relative_roll, \
               self.ship_attitude.absolute_pitch, \
               self.ship_attitude.heading_rate, \
               self.ship_attitude.relative_roll_rate, \
               self.ship_attitude.absolute_pitch_rate, \
               self.ship_attitude.north_velocity, \
               self.ship_attitude.east_velocity, \
               self.ship_attitude.vertical_velocity, \
               self.ship_heave, \
               self.water_depth, \
               self.attitude_and_velocities_validity, \
               self.heading_validity, \
               self.course_and_speed_over_ground_validity, \
               self.position_validity, \
               self.set_and_drift_validity, \
               self.water_depth_validity

    def process(self):
        valid = 0
        timestamp = [0, 0]
        timestampMAX = {}
        mapMsg = self.getMapMsgSerial()
        for k in self.listMsg:
            timestamp = [0, 0]
            if k in mapMsg:
                timestamp[0] = datetime.datetime.timestamp( mapMsg[k].timestamp )
            if k + "2" in mapMsg:
                timestamp[1] = datetime.datetime.timestamp( mapMsg[k + "2"].timestamp )
            if timestamp[0] == timestamp[1] and timestamp[0] == 0:
                continue
            elif timestamp[0] > timestamp[1]:
                timestampMAX[k] = timestamp
            else:
                timestampMAX[k] = timestamp

        listMsg = self.listMsg
        source = 1
        if len(timestampMAX)>0:
            msgMaxTimestamp = max( timestampMAX, key=timestampMAX.get )
            if msgMaxTimestamp.endswith( "2" ):
                listMsg = [k + "2" for k in self.listMsg]
                source = 2
        for k in listMsg:  # range(len(self.listMsg)):
            # k=self.listMsg[i]
            if k in mapMsg:
                msg = mapMsg[k]
                valid += 1 if msg.isValid() else 0
                if k.startswith( "PIXSEHEAVE" ):
                    self.ship_heave = self.getValueFromInput( msg, k, "heave" )
                elif k.startswith( "PIXSEDEPIN" ):
                    self.water_depth = self.getValueFromInput( msg, k, "deep" )
                    self.water_depth_validity = 0
                elif k.startswith( "GPZDA" ):
                    continue
                elif k.startswith( "GPGGA" ):
                    gps_quality = self.getValueFromInput( msg, k, "gps_quality" )
                    if gps_quality is not None and gps_quality > 0:
                        self.ship_position.latitude = self.getValueFromInput( msg, k, "latitude" )
                        self.ship_position.longitude = self.getValueFromInput( msg, k, "longitude" )
                        gpzda = "GPZDA" 
                        pixse_time = "PIXSE.TIME__"
                        msg = mapMsg.get(gpzda) or mapMsg.get(gpzda+"2")
                        msg_time = mapMsg.get(pixse_time)or mapMsg.get("PIXSE2.TIME__")
                        if msg is not None:
                            giorno = self.getValueFromInput( msg, "GPZDA", "day" )
                            mese = self.getValueFromInput( msg, "GPZDA", "month" )
                            anno = self.getValueFromInput( msg, "GPZDA", "year" )
                            if giorno and mese and anno:
                                dateZDA = "{}/{}/{}".format( giorno, mese, anno )
                                self.time_of_validity.seconds, self.time_of_validity.microseconds = \
                                    utility.convertUTC( dateZDA, self.getValueFromInput( msg, k, "utc_of_position" ) )
                        elif msg_time is not None:
                            utc = self.getValueFromInput( msg_time, pixse_time, "utc_time" )
                            self.time_of_validity.seconds, self.time_of_validity.microseconds = utility.convertUTC(None ,utc )
                       
                elif k.startswith( "GPGLL" ):
                    status = self.getValueFromInput( msg, k, "status" )
                    if status == "A":
                        self.ship_position.latitude = self.getValueFromInput( msg, k, "latitude" )
                        self.ship_position.longitude = self.getValueFromInput( msg, k, "longitude" )
                        self.position_validity = 0
                elif k.startswith( "HEROT" ):
                    status = self.getValueFromInput( msg, k, "status" )
                    if status == "A":
                        self.ship_attitude.heading_rate = self.getValueFromInput( msg, k, "heading_rate" )
                elif k.startswith( "PSXN" ):
                    status_ph = self.getValueFromInput( msg, k, "status_ph" )
                    user_identification = self.getValueFromInput( msg, k, "user identification" )
                    if status_ph == 10 and user_identification == "014":
                        self.ship_attitude.heading = self.getValueFromInput( msg, k, "heading" )
                        self.ship_attitude.relative_roll = self.getValueFromInput( msg, k, "roll" )
                        self.ship_attitude.absolute_pitch = self.getValueFromInput( msg, k, "pitch" )
                        self.ship_attitude.heading_rate = self.getValueFromInput( msg, k, "heading rate" )
                        self.ship_attitude.relative_roll_rate = self.getValueFromInput( msg, k, "roll rate" )
                        self.ship_attitude.absolute_pitch_rate = self.getValueFromInput( msg, k, "pitch rate" )
                        self.heading_validity = 0
                elif k.startswith( "GPGST" ):
                    self.ship_position.latitude_accuracy = self.getValueFromInput( msg, k, "SD_Lat" )
                    self.ship_position.longitude_accuracy = self.getValueFromInput( msg, k, "SD_Long" )
                elif k.startswith("AIPOV"):
                    utc = self.getValueFromInput( msg, k, "utc_time" )
                    self.time_of_validity.seconds, self.time_of_validity.microseconds = utility.convertUTC(None ,utc )
                    self.ship_position.latitude = self.getValueFromInput( msg, k, "latitude" )
                    self.ship_position.longitude = self.getValueFromInput( msg, k, "longitude" )
                    self.ship_attitude.north_velocity = self.getValueFromInput( msg, k, "north_velocity" )
                    self.ship_attitude.east_velocity = self.getValueFromInput( msg, k, "east_velocity" )
                    self.ship_attitude.vertical_velocity = self.getValueFromInput( msg, k, "velocity" )
                    self.ship_attitude.heading = self.getValueFromInput( msg, k, "heading" )
                    self.ship_attitude.absolute_pitch = self.getValueFromInput( msg, k, "pitch" )
                    self.relative_roll = self.getValueFromInput( msg, k, "roll" )
                    self.ship_position.log_speed = self.getValueFromInput( msg, k, "along_velocity_xv1" )
                    self.ship_position.speed_over_ground = self.getValueFromInput( msg, k, "down_velocity_xv3" )
                    self.ship_position.course_made_good = self.getValueFromInput( msg, k, "true_course" )
                    mapValid, mapDegraded, mapFailure = phinx.analyzeUserStatus( self, self.getValueFromInput( msg, k,
                                                                                                               "user_status" ) )
                    self.status = mapDegraded is None and mapFailure is None and len( mapValid ) > 0
                    self.set_and_drift_validity = 2 #0:Available and drift are provided by the Gyros.1: DEGRADED; The ship position is entered manually by the operator.2:FAILED; The ship position is not available
                    msgDDreck = mapMsg.get("PIXSE.DDRECK") or mapMsg.get("PIXSE2.DDRECK")
                    if msgDDreck is not None:
                        self.set_and_drift_validity = 0
                        self.ship_position.set = self.getValueFromInput( msgDDreck, k, "dead_reck_heading" )
                        self.ship_position.drift = self.getValueFromInput( msgDDreck, k, "dead_reck_scale" )
                        
                    self.attitude_and_velocities_validity = 0
                    self.course_and_speed_over_ground_validity = 0
                    

        self.allMsgReceived = valid == len( self.listMsg )
        if valid == len( self.listMsg ):
            self.sensor_reference = 0 if source == 1 else 1  # AFT
        else:
            self.sensor_reference = 1 if source == 2 else 0  # FORE

    def decode(self, buffer):
        self.time_of_validity, format_time = self.decodeUdp( Struct_time_of_validity, buffer, 16 )
        self.ship_position, format_pos = self.decodeUdp( Struct_Ship_Position, buffer, 24 )
        self.ship_attitude, format_att = self.decodeUdp( Struct_Ship_Attitude, buffer, 60 )
        instance, format = self.decodeUdp( None, buffer, 96 )
        format_val = format_time + format_pos + format_att + format
        if format_val.replace( ">", "" ) != self.formato_payload:
            logger.error(
                str( self.__class__ ) + " Formato payload errato " + format_val + "---" + self.formato_payload )

    def checkPacket(self, calculate_len, offset, buffer, formatUnpack, instance):
        pass
