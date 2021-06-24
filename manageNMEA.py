import copy
import datetime
import logging
from functools import reduce
import operator
from time import strftime

logger = logging.getLogger(__name__)
#Want to accept np arrays for these
def dd2dms(dd):
    """Convert decimal degrees to degrees, minutes, seconds
    """
    n = dd < 0
    dd = abs(dd)
    m,s = divmod(dd*3600,60)
    d,m = divmod(m,60)
    if n:
        d = -d
    return d,m,s

def dms2dd(d,m,s):
    """Convert degrees, minutes, seconds to decimal degrees
    """
    if d < 0:
        sign = -1
    else:
        sign = 1
    dd = sign * (int(abs(d)) + float(m) / 60 + float(s) / 3600)
    return dd

#Note: this needs some work, not sure what input str format was supposed to be
def dms2dd_str(dms_str, delim=' ', fmt=None):
    import re
    #dms_str = re.sub(r'\s', '', dms_str)
    if re.search('[swSW]', dms_str):
        sign = -1
    else:
        sign = 1
    #re.split('\s+', s)
    #(degree, minute, second, frac_seconds) = map(int, re.split('\D+', dms_str))
    #(degree, minute, second) = dms_str.split(delim)[0:3]
    #Remove consequtive delimiters (empty string records)
    (degree, minute, second) = [s for s in dms_str.split(delim) if s]
    #dd = sign * (int(degree) + float(minute) / 60 + float(second) / 3600 + float(frac_seconds) / 36000)
    dd = dms2dd(int(degree)*sign, int(minute), float(second))
    return dd

def dm2dd(d,m):
    """Convert degrees, decimal minutes to decimal degrees
    """
    dd = dms2dd(d,m,0)
    return dd

def dd2dm(dd):
    """Convert decimal to degrees, decimal minutes
    """
    d,m,s = dd2dms(dd)
    m = m + float(s)/3600
    return d,m,s


def str_dd2dms(deg):
    d,m,s=dd2dm(deg)
    ret="{}".format(d*100+m)
    return ret

class NmeaManager:
    timestamp = datetime.datetime.now()
    prefix=""
    _values=[]
    multiple_values = False

    def getValue(self, k, i=0):
        return self._values[i][k]

    def isValid(self):
        curr = datetime.datetime.now()
        avaiableStatus = True

        if hasattr( self, "validityTime" ):
            avaiableStatus = (curr - self.timestamp) < datetime.timedelta(seconds=self.validityTime)
        if avaiableStatus and "status" in self.element_msg:
            avaiableStatus = self.element_msg["status"] == "A"

        self.timestamp=curr
        return avaiableStatus

    # Calcolo CRC
    def checksum(self, nmea_str):
        if '$' in nmea_str and '*' in nmea_str:
            payload_start = nmea_str.find( '$' ) + 1  # trova il primo carattere dopo $
            payload_end = nmea_str.find( '*' )  # trova il carattere *
            payload = nmea_str[payload_start: payload_end]  # dati di cui fare XOR
            # nmea_str è una sottostringa tra $ e *
        else:
            # nmea_str è già il messaggio estratto.
            payload = nmea_str
        return reduce( operator.xor, [ord( s ) for s in payload], 0 )

    # Ritorno messaggio + crc
    def getMsgNmea(self, msg):
        calc_cksum = self.checksum( msg )
        if '$' not in msg and '*' not in msg:
            msg = "${}*{:02X}\r\n".format( msg, calc_cksum )
        else:
            msg = "{}{}\r\n".format( msg, calc_cksum )
        return msg

    # Calcolo value se è stringa o numero(int o float)
    def convertValue(self, var_name, value):
        if var_name is not None and not type( var_name ) is str:
            ret=None
            if type(value)==str and len(value)==0:
                return None
            elif type(var_name) in [float]:
                ret=float( value )
            elif type(var_name) in [int]:
                ret = int( value )
            elif type( var_name ) in [bool]:
                ret = bool( value )
            return ret
        elif type(var_name)==type(value):
            if type(value)==str and len(value)==0:
                return None
            if var_name.startswith("0x"):
                ret=int("0x"+value,16)
            elif "hhmmss.ssss" in var_name:
                #ret=datetime.datetime.strptime(value,"%H%M%S.%f") #del pomeriggio?  sulla documentazione AIPOV:
                #UTC time hhmmss.ssss second 10-4 s UTC time in hour,minutes, seconds
                ret=value  #perchè poi in convertValue io uso la stringa col formato giusto.
            else:
                ret = value
            #elif type( var_name ) in [bytes]:
            #    ret = int( "0x" + str(value), 16 )

            return ret
        else:
            return value

    # prendo tutto il payload e metto ogni valore (separata da ',' in un array vals
    def decode(self, msg):
        if msg.startswith( "$" ) and "*" in msg:
            payload_start = msg.find( '$' ) + 1  # trova il primo carattere dopo $
            payload_end = msg.find( '*' )  # trova il carattere *
            payload = msg[payload_start: payload_end]  # dati di cui fare XOR
            vals = payload.split( "," )
            self.setValues( vals, self.multiple_values )

    def setValues2(self, vals, multiple):
        i = 1  # il primo è l'identificativo (MVW ad esempio)
        if multiple:
            for elem in vals:
                for k, v in self.element_msg.items():
                    v = self.convertValue( k, elem )
                    self.element_msg[k] = v
                    i += 1
                self._values.append( self.element_msg )  # array di n dict
        else:
            for k, v in self.element_msg.items():
                v = self.convertValue( k, vals[i] )
                self.element_msg[k] = v
                i += 1
            self._values.append( self.element_msg )  # array di 1 dict

    def setValues(self, vals, multiple):
        try:
            #if self.__class__.__name__=="Giro_GPGGA":
            #    print("sono qui")
            self._values=[]
            element_msg=copy.deepcopy(self.element_msg)
            i=1 # il primo è l'identificativo (MVW ad esempio)
            while i < len(vals): # serve per Weather_instrument_XDR: che ha struttura di lunghezza variabile
                if hasattr(self,"getElements"):
                    elements=self.getElements(vals[1]).items() # Giro_PIXSE: se REFERENCE cambia la struttura in base a elements
                else:
                    elements=element_msg.items()
                for k, v in elements:
                    v = self.convertValue( v, vals[i] )
                    element_msg[k] = v
                    i += 1
                    if i==len(vals):
                        if len(vals)-1 <len(element_msg.keys()):
                            logger.debug( "ERRORE Manca l'attributo {}, {}, {}".format( i, list( element_msg )[i-2], vals ) )
                        break

                self._values.append( element_msg )
            if len( self._values )==0:
                logger.error("ERRORE values vuota {},  {}".format( i, vals ) )
        except Exception as e:
            logger.error("ERRORE setValues: {}, i:{}, {}".format(self.__class__,i,vals),e)
            raise e
    source=None
    def values(self):
        data={}
        data["name"]=self.__class__.__name__
        if hasattr(self,"source") and self.source:
            data["source"] = self.source
        
        data["timestamp"]=datetime.datetime.strftime(self.timestamp,"%H:%M:%S")
        i=0
        for m in self._values:
            for k,v in m.items():
                if i>0:
                    data[k+"_"+i]=v
                else:
                    data[k]=v
            i+=1
        return data

class Weather_instrument_MWV( NmeaManager ):  # Wind speed and angle

    """
    wind_direction = 0
    reference = "R"  # R = relative T = True
    wind_speed = 2.4
    wind_speed_unit = "M"  # K = km/h; M = m/s; N = kt
    status = "V"  # A:VALID ; otherwise error
    """

    template = "$WIMWV,xxx,a,x.x,a,A*HH\r\n"
    validityTime = 1

    element_msg = {"wind_direction": 0.0,
                   "reference": "R",
                   "wind_speed": 2.4,
                   "wind_speed_unit": "M",
                   "status": "V",
                   }

    def getMessageId_postfix(self):
        return self.getValue( "reference" )


    coding = [
        {"xxx": "Wind direction"},
        {"a": "Reference"},
        {"x.x": "Wind_speed"},
        {"a": "Wind speed unit"},
        {"A": ["Status", {"A": True, "E": False}]}
    ]

    examples = ["$WIMWV,180,R,2.4,M,A*31",
                "$WIMWV,100,T,2.0,M,A*3B"
                ]

class Weather_instrument_XDR( NmeaManager ):  # Transducer measurements
    multiple_values = True;

    element_msg = {"transducer_type": "P",
                   "measurement_data": 0.0,
                   "units_of_measure": "P",
                   "transducer_id": "PA1",
                   }
    template = "$WIXDR,a,x.x,a,c—c,[1..n]*HH\r\n"
    validityTime = 10

    '''
    transducer_type = "P"
    measurement_data = 0.0
    units_of_measure = "P"
    transducer_id = "PA1"

    def getContainer(self):
        return self.__init__()

    template = "$WIXDR,a,x.x,a,c—c,[1..n]*HH\r\n"
    '''
    coding = [
        {"a": ["Transducer type", {"C": "Air Temperature", "H": "Relative Humidity", "P": "Pressure"}]},
        {"x.x": "Measurement data"},
        {"a": ["Units of measure", {"C": "°C", "P": "Pressure"}]},
        {"c--c": ["Transducer ID",
                  {"TA1": "Air Temperature", "RH1": "Relative Humidity", "DP1": "Dew point Temperature",
                   "PA1": "Dew point Temperature"}]}
    ]
    '''
    Air Temperature	C	C	TA1
    Relative Humidity	H	P	RH1
    Dew point Temperature	C	C	DP1
    Air Pressure	P	P	PA1
    
    examples = ["$WIXDR,C,20.3,C,TA1,H,90,P,RH1,C,15.3,C,DP1,P,101310,P,PA1*6F\r\n"]
    '''

class Weather_instrument_MTW( NmeaManager ):
    multiple_values = True
    validityTime = 10
    element_msg = {"water_temperature": 0.0,
                   "units_of_measure": "C"
                   }
    template = "$WIXDR,a,x.x,a,c—c,[1..n]*HH\r\n"


class Giro_GPZDA( NmeaManager ):
    element_msg={"utc_of_position":"hhmmss.ss",
                 "day":"dd",
                 "month":"mm",
                 "year":"yyyy",
                 "local_zone_hour":"hh",
                 "local_zone_minute":"mm"
                 }
    template="$GPZDA,hhmmss.ss,dd,mm,yyyy,hh,mm*HH\r\n"


class Giro_GPGGA( NmeaManager ):
    element_msg = {"utc_of_position": "hhmmss.ssss",
                   "latitude": 0.0,
                   "hemisphere": "N",
                   "longitude": 0.0,
                   "longitude_sign": "E",
                   "gps_quality": 0,
                   "number_of_satellites": 0,
                   "horizontal_dilution": 0.0,
                   "antenna_altitude": 0.0,
                   "units_of_antenna_altitude": "M",
                   "geoidal_separation": 0.0,
                   "units_of_geoidal_separation": "M",
                   "age_gps": 0.0,
                   "differential_reference": 0}

    template = "$GPGGA,hhmmss.ss,llmm.mm,a,LLLmm.mm,b,q,ss,y.y,x.x,M,g.g,M,a.a,zzzz*HH\r\n"

class Giro_GPGLL( NmeaManager ):
    element_msg = {"latitude": 0.0,
                   "hemisphere": "N",
                   "longitude": 0.0,
                   "longitude_sign": "E",
                   "utc_of_position": "hhmmss.ssss",
                   "status": "A",
                   "mode_indicator": "D"
                   }

    template = "$GPGLL,llmm.mm,a,LLLmm.mm,b,hhmmss.ss,S,M*HH\r\n"

class Giro_HEHDT( NmeaManager ):
    element_msg = {
        "true_heading": 0.0,
        "status":"T"
        }
    template="$HEHDT,x.xxx,T*hh\r\n"
    coding = [
        {"x.xxx", "true heading"},
        {"T", "status Fixed character ='T'"},
    ]

class Giro_HETHS( NmeaManager ):
    """ true_heading:
        2 digits after the decimal point in default mode
        5 digits after the decimal point in military mode
     Mode indicator Set condition Output priority level
        A = Autonomous                                  Default value      Low
        E = Estimated (dead-reckoning)                  N/A                N/A
        M = Manual input                                N/A                N/A
        S = Simulator Mode System status 2:             SIMULATION_MODE    Medium
        V = Data not valid User status:                 HRP_INVALID        High
    """
    template ="$HETHS,x.x,a*hh\r\n"
    element_msg = {
        "true_heading": 0.0,
        "status":"A"
    }
    coding = [
        {"x.xxx", "true heading"},
        {"a", "Status"},
    ]
class Giro_PIXSE( NmeaManager ):

    template = "$PIXSE,reference,x.xxx,y.yyy*hh\r\n"
    coding = [
        {"x.xxx", "roll"},
        {"y.yyy", "pitch"},
        {"hhhhhhhh":"status hexadecimal value of the 32 LSB bits"},
        {"llllllll":"status hexadecimal value of the 32 MSB bits"}
    ]

    element_msg={}

    def getMessageId_postfix(self):
        return self.getValue( "reference" )

    def getElements(self,reference):
        ret={"reference":reference,"value_serial":0.0}
        if reference=="ATITUD":
            ret={"reference":reference,"roll":0.0,"pitch":0.0}
        elif reference=="STATUS":
            ret={"reference":reference,"status_lsb":"0xhhhhhhhh","status_msb":"0xllllllll"}
        elif reference == "HEAVE":
            ret = {"reference": reference, "surge": 0.0, "sway": 0.0,"heave":0.0}
        elif reference == "POSITI":
            ret = {"reference": reference, "lat": 0.0, "lon": 0.0,"altitude":0.0}
        elif reference == "SPEED_":
            ret = {"reference": reference, "vx": 0.0, "vy": 0.0,"vz":0.0}
        elif reference == "UTMWGS":
            ret = {"reference": reference, "hemisphere":"N","longitude_UTM_zone":0,"lat_m": 0.0, "long_m": 0.0,"altitude_m":0.0}
        elif reference == "STDHRP":
            ret = {"reference": reference, "heading_std_dev": 0.0, "roll_std_dev": 0.0,"pitch_std_dev":0.0}
        elif reference == "STDPOS":
            ret = {"reference": reference, "lat_std_dev": 0.0, "lon_std_dev": 0.0,"altitude_std_dev":0.0}
        elif reference == "STDSPD":
            ret = {"reference": reference, "vx_std_dev": 0.0, "vy_std_dev": 0.0,"vz_std_dev":0.0}
        elif reference == "ALGSTS":
            ret = {"reference": reference, "status_lsb":"0xhhhhhhhh","status_msb":"0xllllllll"}
        elif reference == "HT_STS":
            ret = {"reference": reference, "status_ins":"0xhhhhhhhh"}
        elif reference == "HEAVE_":
            ret = {"reference": reference, "surge": 0.0,"sway":0.0,"heave":0.0}
        elif reference == "DEPIN_":
            ret = {"reference": reference, "deep": 0.0, "validity": "hhmmss.ssss"}
        elif reference == "TIME__":
            ret = {"reference": reference, "utc_time": "hhmmss.ssss"}
        elif reference == "DDRECK":
            '''
            x.xxxxxxxx	is the dead reckoning latitude in degrees
            y.yyyyyyyy	is the dead reckoning longitude in degrees
            z.zzz	is the dead reckoning altitude in meters
            m.mmm	is the heading misalignment dead reckoning estimation in degrees
            f.ffffff	is the scale factor dead reckoning estimation (*)
            p.ppp	is the pitch dead reckoning estimation in degrees
            '''
            ret = {"reference": reference, 
                "dead_reck_lat": 0.0,
                "dead_reck_lon": 0.0,
                "dead_reck_altitude": 0.0,
                "dead_reck_heading": 0.0,
                "dead_reck_scale": 0.0,
                "dead_reck_pitch": 0.0,
            }
        else:
            logger.warning(f"reference non gestita {reference}")
        return ret

    templates=[
        "$PIXSE,ATITUD,x.xxx,y.yyy*hh\r\n",
        "$PIXSE,STATUS,hhhhhhhh,llllllll*hh\r\n",
        "$PIXSE,DEPIN_,x.xxx,hhmmss.ssss*hh\r\n",
        "$PIXSE,POSITI,x.xxx,y.yyy,z.zzz*hh\r\n",
        "$PIXSE,SPEED_,x.xxx,y.yyy,z.zzz*hh\r\n",
        "$PIXSE,UTMWGS,C,nn,x.xxx,y.yyy,z.zzz*hh\r\n",
        "$PIXSE,HEAVE_,x.xxx,y.yyy,z.zzz*hh\r\n",#x.xxx  is the surge in meters (signed)  y.yyy  is the sway in meters (signed) z.zzz is the heave in meters (signed)
        "$PIXSE,TIME__,hhmmss.ssssss*hh\r\n",
        "$PIXSE,STDHRP,x.xxx,y.yyy,z.zzz*hh\r\n",#x.xxx is the heading std dev (degrees) y.yyy is the roll std dev (degrees) z.zzz is the pitch std dev (degrees)
        "$PIXSE,STDPOS,x.xx,y.yy,z.zz*hh\r\n",#x.xx is the latitude std dev (meters) y.yy is the longitude std dev (meters) z.zz is the altitude std dev (meters)
        "$PIXSE,STDSPD,x.xxx,y.yyy,z.zzz*hh\r\n",#x.xxx is the east speed std dev (m/s) y.yyy is the north speed std dev (m/s) z.zzz is the vertical speed std dev (m/s)
        "$PIXSE,ALGSTS,hhhhhhhh,llllllll*63\r\n",
        "$PIXSE,HT_STS,hhhhhhhh*45\r\n",#is the hexadecimal value of INS High Level status is only used by iXRepeater MMI software to flag PHINS status
        "$PIXSE,DDRECK,x.xxxxxxxx,y.yyyyyyyy,z.zzz,m.mmm,f.fffffff,p.ppp*hh\r\n"
    ]
    examples=[
        "$PIXSE,POSITI,0.00000000,0.00000000,0.000*61\r\n",
        "$PIXSE,SPEED_,0.000,0.000,0.000*61\r\n",
        "$PIXSE,UTMWGS,N,31,166021.443,0.000,0.000*0B\r\n",
        "$PIXSE,HEAVE_,0.000,0.000,0.000*79\r\n",
        "$PIXSE,TIME__,032458.768379*60\r\n",
        "$PIXSE,STDHRP,60.000,5.000,5.000*46\r\n",
        "$PIXSE,STDPOS,50.00,50.00,10.00*77\r\n",
        "$PIXSE,STDSPD,10.000,10.000,0.100*7C\r\n",
        "$PIXSE,ALGSTS,00000042,00000000*63\r\n",
        "$PIXSE,STATUS,00000000,00200000*6D\r\n",
        "$PIXSE,HT_STS,FFFD5552*45"
        
    ]

class Giro_PSXN( NmeaManager ):
    template="$PSXN,S,ddd,X1,X2,X3,X4,X5,X6,*hh\r\n"
    element_msg = {"status_ph": 0.0,
                "user identification": "014",
                "pitch":0.0,
                "roll":0.0,
                "heading":0.0,
                "pitch rate":0.0,
                "roll rate":0.0,
                "heading rate":0.0,
    }
    coding = [
        {"S", "status phinx"},# S=10 for data valid S = 11 for data invalid
        {"ddd","User identification"},#014 fixed
        {"X1", "pitch"},
        {"X2", "roll"},
        {"X3", "heading"},
        {"X4", "pitch speed"},
        {"X5", "roll speed"},
        {"X6", "heading speed"},
    ]

class Giro_GPGST( NmeaManager ):
    template = "$GPGST,hhmmss.sss,x.x,x.x,x.x,x.x,x.x,x.x,x.x*HH\r\n"
    element_msg = {"utc_of_position": "hhmmss.ssss",
                   "SD_RI": 0.0,
                   "SD_MR": 0.0,
                   "SD_SH": 0.0,
                   "Angle_Ellipse_Error": 0.0,
                   "SD_Lat": 0.0,
                   "SD_Long": 0.0,
                   "SD_Alt": 0.0
                   }
class Giro_HEROT( NmeaManager ):
    template = "$HEROT,x.x,S*HH\r\n"
    element_msg = {"heading_rate": 0.0,
                   "status": "A"
                }
    coding = [
        {"x.x", "heading rate"},
        {"s", "Status"}
    ]

class Giro_GPVTG( NmeaManager ):
    template = "$GPVTG,x.xxx,T,x.xxx,M,x.xxx,N,x.xxx,K,a*hh\r\n"
    element_msg = {"trueCourse": 0.0,
                   "fixCarT": "T",
                   "magneticCourse": 0.0,
                   "fixCarM": "M",
                   "speedM": 0.0,
                   "fixCarN": "N",
                   "speedN": 0.0,
                   "fixCarK": "K",
                   "posFixMode": "A",

                   }
    #
class Giro_AIPOV( NmeaManager ):
    utc_time = "hhmmss.ssss"
    element_msg = {
        "utc_time" :"hhmmss.ssss",
        "heading" : 0.0,
        "roll": 0.0,
        "pitch" :0.0,
        "rotation_rate_xv1":0.0,
        "rotation_rate_xv2":0.0,
        "rotation_rate_xv3":0.0,
        "linear_acceleration_xv1":0.0,
        "linear_acceleration_xv2":0.0,
        "linear_acceleration_xv3":0.0,
        "latitude": 0.0,
        "longitude":0.0,
        "altitude":0.0,
        "north_velocity":0.0,
        "east_velocity":0.0,
        "velocity":0.0,
        "along_velocity_xv1": 0.0,
        "across_velocity_xv2":0.0,
        "down_velocity_xv3":0.0,
        "true_course":0.0,
        "user_status":"0x0",
    }
    template = "$AIPOV,hhmmss.ssss,h.hhh,r.rrr,p.ppp,x.xxx,y.yyy,z.zzz,e.ee,f.ff,g.gg,LL.LLLLLLLL,ll.llllllll,a.aaa,i.iii,j.jjj,k.kkk,m.mmm,n.nnn,o.ooo,c.ccc,hhhhhhhh*HH\r\n"
    examples = [
        "$AIPOV,050930.3419,5.000,0.000,0.000,0.000,0.000,0.000,0.00,0.00,0.00,00.00000000,000.00000000,0.000,0.000,0.000,0.000,0.000,0.000,0.000,5.000,00000000*6D"]
    coding = [
        {"hhmmss.ssss", "UTC time"},
        {"h.hhh", "Heading"},
        {"+/-r.rrr", "Roll"},
        {"+/-p.ppp", "Pitch"},
        {"+/-x.xxx", "Rotation Rate XV1"},
        {"+/-y.yyy", "Rotation Rate XV2"},
        {"+/-z.zzz", "Rotation Rate XV3"},
        {"+/-e.ee", "Linear Acceleration XV1  m/s²"},
        {"+/-f.ff", "Linear acceleration XV2  m/s²"},
        {"+/-g.gg", "Linear Acceleration XV3  m/s²"},
        {"+/-LL.LLLLLLLL", "Latitude"},
        {"+/-ll.llllllll", "Longitude"},
        {"a.aaa", "Altitude"},
        {"+/-I.iii", "North Velocity"},
        {"+/-j.jjj", "East Velocity"},
        {"+/-k.kkk", "Velocity"},
        {"+/-m.mmm", "Along Velocity XV1"},
        {"+/-n.nnn", "Across Velocity XV2"},
        {"+/-o.ooo", "Down Velocity XV3"},
        {"c.ccc", "True course"},
        {"hhhhhhhh", "User Status"}
    ]

class Giro_PSIMSSB( NmeaManager ):
    template = "$PSIMSSB,hhmmss.ss,TpC,s,eee,C,O,F,x.x,y.y,d.d,a.a,I,A.A,B.B[,D,E,…]*hh\r\n"


    coding={
        "hhmmss.ss":"utc_time",# Real time of the measurement. The INS only considers
        "TpC":"Transponder Tp code", #Note 1
        "s":"Status",# {‘A’:data valid,‘V’:data invalid}
        "eee":"Error code",# Note 3 PHINS will not reject the USBL frame if this field is empty
        "C":"Coordinate system",# Note 4{ ‘C’: Cartesian;‘P’:Polar;‘U’:UTM;‘R’:Radians;}
        "O":"Orientation",#{‘H’:vessel Head up;‘E’: East;‘N’ = North}
        "F":"Filter",# Note 6{‘M’:Measured data;‘F’ = Filtred data;‘P’ = Predicted data}
        "x.x":"X_coordinate",# (latitude or UTM Northing)
        "y.y":"Y_coordinate",# (longitude or UTM Easting)
        "d.d":"Depth in meters",# USED
        "a.a":"Expected accuracy of the position",
        "I":"Additional information",# {‘N’ : None;‘C’ : Compass;‘I’ : Inclinometer;‘D’ = Depth;‘T’ = Time from transponder to transducer;‘V’ = Velocity}
        "A.A":"First additional",# depending on additional info Note 8
        "B.B":"Second additional",# depending on additional info N O T USED
        "D,E, …":"Potential additional fields ignored"
    }

class Giro_HEALC (NmeaManager):
    template = "$HEALC,A,B,C,D,GGG,HHH,J,K]*hh\r\n"
    element_msg = {"total_ALF": 1,
                   "sentence_number": 1,
                   "sequential_msgId":1,
                   "tot_alert":0,
                   "manu_mnemonic":"COD",
                   "alert_Id":240,
                   "alert_instance":1,
                   "rev_counter":1
                   }
    coding = [{'A':'Total number of ALF sentences Fixed to 1'},
              {'B':'Sentence number Fixed to 1'},
              {'C':'Sequential message identifier Fixed to 1'},
              {'D':'Number of alert entries 0 if no active alert, 1 if one active alert'},
              {'GGG':'Manufacturer mnemonic Empty (standardized alert identifier used)'},
              {'HHH':'Alert identifier Fixed to 240 for a gyrocompass (Note 1)'},
              {'J':'Alert instance Fixed to 1'},
              {'K':'Revision counter Starts at 1 and is incremented up to 99 after each alert status change in ALF message. Resets to 1 after 99 is used.'}
              ]

class Giro_HEALR(NmeaManager):
    template="HEALR,HHMMSS.SS,XXX,A,B,C*hh\r\n"

    element_msg={"time":"hhmmss.ssss",
                 "unique_alertID":240,
                 "alert_condition":"A",
                 "alert_ack":"V",
                 "desc":"message"
                 }

    coding =[{'HHMMSS.SS':'Time Current time (UTC time if the system is synchronized in UTC,or internal time otherwise) in hour, minute and seconds.'},
            {'XXX':'Unique Alert Identifier Fixed to 240 for a gyrocompass'},
            {'A':'Alert condition ‘A’ if alert condition is raised ‘V’ if alert condition is cleared (Note 1)'},
            {'B':'Alert acknowledge state ‘V’ if not acknowledged ‘A’ if acknowledged'},
            {'C':'Description text “System fault”'},
            ]
