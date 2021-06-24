import numpy as np
import datetime

import utility


class BaseStruct:
    listTypes=None
        
    def replaceBracket(self,value:str):
        return "{"+value[1:-1]+"}"
    
    def __repr__(self):
        names=self.getListAttribute()
        val=[getattr(self,k) for k in names]
        descr=""
        for i in range(len(names)):
            if type(val[i]) in [float,int]:
                descr+=f' "{names[i]}":{val[i]},'
            else:
                descr+=f' "{names[i]}": "{val[i]}",'
        return "{"+descr+"}"
    
    @property
    def formato_payload(self):

        names=self.getListAttribute()
        if self.listTypes is None:
            types=[type(getattr(self,k)) for k in names]
            values={k:getattr(self,k) for k in names}
            self.listTypes={"types":types,"values":values}
        else:
            types=self.listTypes["types"]
            values=self.listTypes["values"]
        formatUnpack, calculate_len = utility.getType( types, names ,values)
        return formatUnpack

    def getTypes(self):
        names = self.getListAttribute()
        types = [type( getattr( self, k ) ) for k in names]
        return {names[i]:types[i] for i in range(len(names)) }


class Struct_time_of_validity(BaseStruct):#=0#	30	8	1
    seconds=np.uint(0)#	30	4	1	uint
    microseconds=np.uint(0)#	34	4	1	uint

    def getListAttribute(self):
        return ["seconds","microseconds"]

    def __repr__(self):
        unixtimestamp = self.seconds
        if unixtimestamp>0:
            time_of_validity = datetime.datetime.fromtimestamp(unixtimestamp).strftime('%Y-%m-%d %H:%M:%S')
            return self.replaceBracket(f'( "s": \"{time_of_validity}\", "micros": {self.microseconds} )')
        return self.replaceBracket( f'( "s": 0, "micros": "0" )' )

class Struct_3d_cartesian_kinematics(BaseStruct):#	40	26	1	struct
    spare=0 #	40	2	1	padding
    x=0.0 #	42	4	1	float
    y=0.0 #	46	4	1	float
    z=0.0 #50	4	1	float
    vx=0.0#	54	4	1	float
    vy=0.0#	58	4	1	float
    vz=0.0#	62	4	1	float
  
    #def __repr__(self):
    #    return self.replaceBracket(f"( x: {self.x}, y: {self.y},  z: {self.z},  vx: {self.vx},  vy: {self.vy}, vz: {self.vz})")

    def getListAttribute(self):
        return ["spare","x","y","z","vx","vy","vz"]

class Struct_3d_cartesian_position(BaseStruct):#	40	14	1	struct
    spare=0#	40	2	1	padding
    x=0.0#	42	4	1	float
    y=0.0#	46	4	1	float
    z=0.0#	50	4	1	float


    #def __repr__(self):
    #    return self.replaceBracket(f"( x: {self.x}, y: {self.y},  z: {self.z})")

    def getListAttribute(self):
        return ["spare","x","y","z"]

class Struct_2d_cartesian(BaseStruct):#	kinematics	40	18	1
    spare=0#	40	2	1	padding
    x=0.0#	42	4	1	float
    y=0.0#	46	4	1	float
    vx=0.0#	50	4	1	float
    vy=0.0#	54	4	1	float


    #def __repr__(self):
    #    return self.replaceBracket(f"( x: {self.x}, y: {self.y},  vx: {self.vx},  vy: {self.vy})")

    def getListAttribute(self):
        return ["spare","x","y","vx","vy"]

class Struct_2d_cartesian_position(BaseStruct):#	40	10	1	struct
    spare=0#	40	2	1	padding
    x=0.0#	42	4	1	float
    y=0.0#	46	4	1	float


    #def __repr__(self):
    #    return self.replaceBracket(f"( x: {self.x}, y: {self.y})")

    def getListAttribute(self):
        return ["spare","x","y"]

class Struct_2d_polar_kinematics(BaseStruct):#	40	18	1	struct
    spare=0#	40	2	1	padding
    true_bearing=0.0#	42	4	1	float
    angle_of_sight=0.0#	46	4	1	float
    true_bearing_rate=0.0#50	4	1	float
    angle_of_sight_rate=0.0#	54	4	1	float


    def getListAttribute(self):
        return ["spare","true_bearing","angle_of_sight","true_bearing_rate","angle_of_sight_rate"]

    #def __repr__(self):
    #    return self.replaceBracket(f"( true_bearing: {self.true_bearing}, angle_of_sight: {self.angle_of_sight},  " \
    #           f"true_bearing_rate: {self.true_bearing_rate},  angle_of_sight_rate: {self.angle_of_sight_rate})")

class Struct_2d_polar_surface(BaseStruct):#	kinematics	40	18	1
    spare=0#	40	2	1	padding
    true_bearing=0.0#	42	4	1	float
    range_2d=0.0#	46	4	1	float
    true_bearing_rate=0.0#	50	4	1	float
    range_rate=0.0#	54	4	1	float


    def getListAttribute(self):
        return ["spare","true_bearing","range_2d","true_bearing_rate","range_rate"]

    #def __repr__(self):
    #    return self.replaceBracket(f"( true_bearing: {self.true_bearing}, range_2d: {self.range_2d},  " \
    #           f"true_bearing_rate: {self.true_bearing_rate},  range_rate: {self.range_rate})")

class Struct_2d_polar_position(BaseStruct):#	40	10	1	struct
    spare=0#	40	2	1	padding
    true_bearing=0.0#	42	4	1	float
    angle_of_sight=0.0#	46	4	1	float


    def getListAttribute(self):
        return ["spare","true_bearing", "angle_of_sight"]

    #def __repr__(self):
    #    return self.replaceBracket(f"( true_bearing: {self.true_bearing}, angle_of_sight: {self.angle_of_sight})")

class Struct_2d_polar_surface_position(BaseStruct):#	40	10	1
    spare=0#	40	2	1	shortInt
    padding_range=0.0#	42	4	1 float
    true_bearing=0.0#46	4	1	float

    def getListAttribute(self):
        return ["spare","padding_range", "true_bearing"]

    #def __repr__(self):
    #    return self.replaceBracket(f"( padding_range: {self.padding_range}, true_bearing: {self.true_bearing})")


class Struct_1d_polar_position(BaseStruct):#	40	6	1	struct
    spare=0#	40	2	1	padding
    true_bearing=0.0#	42	4	1	float

    #def __repr__(self):
    #    return self.replaceBracket(f"(true_bearing: {self.true_bearing})")

    def getListAttribute(self):
        return ["spare","true_bearing"]

class Struct_ew_1d_polar_position(BaseStruct):#	40	14	1	struct
    spare = 0  # 40	2	1	padding
    true_bearing = 0.0  # 42	4	1	float
    origin_Latitude=0.0#	46	4	1	Float	deg	[-90..+90]
    origin_Longitude=0.0#	50	4	1	Float	deg	[-180..+180]

    #def __repr__(self):
    #    return self.replaceBracket(f"( origin_Latitude: {self.origin_Latitude}, origin_Longitude: {self.origin_Longitude})")

    def getListAttribute(self):
        return ["spare","true_bearing","origin_Latitude","origin_Longitude"]

class Struct_ew_2d_polar_position(BaseStruct):#	40	18	1	struct
    spare=0#	40	2	1	padding		
    true_bearing=0.0#	42	4	1	float	rad	[0..2_*_pi]
    angle_of_sight=0.0#	46	4	1	float	rad	[-pi/2..pi/2]
    origin_latitude=0.0#	46	4	1	float	deg	[-90..+90]
    origin_longitude=0.0#	50	4	1	float	deg	[-180..+180]

    def getListAttribute(self):
        return ["spare","true_bearing","angle_of_sight","origin_latitude","origin_longitude"]


    #def __repr__(self):
    #    return self.replaceBracket(f"( true_bearing: {self.true_bearing},angle_of_sight: {self.angle_of_sight},origin_Latitude: {self.origin_latitude}, origin_Longitude: {self.origin_longitude})")

class Struct_Ship_Attitude(BaseStruct):
    heading = 0.0 #Heading	60	4	1	Float	rad
    relative_roll = 0.0 #Relative roll	64	4	1	Float	rad
    absolute_pitch = 0.0 #Absolute pitch	68	4	1	Float	rad
    heading_rate = 0.0 #Heading rate	72	4	1	Float	rad/s
    relative_roll_rate = 0.0 #Relative Roll rate	76	4	1	Float	rad/s
    absolute_pitch_rate = 0.0 #Absolute Pitch rate	80	4	1	Float	rad/s
    north_velocity = 0.0 #North velocity	84	4	1	Float	m/s
    east_velocity = 0.0 #East velocity	88	4	1	Float	m/s
    vertical_velocity = 0.0 #Vertical velocity	92	4	1	Float	m/s


    def getListAttribute(self):
        return ["heading","relative_roll","absolute_pitch","heading_rate","relative_roll_rate","absolute_pitch_rate",
                "north_velocity","east_velocity","vertical_velocity"]

    #def __repr__(self):
    #    return self.replaceBracket(f"( heading: {self.heading},relative_roll: {self.relative_roll},absolute_pitch: {self.absolute_pitch}, " \
    #           f"heading_rate: {self.heading_rate},relative_roll_rate: {self.relative_roll_rate},absolute_pitch_rate: {self.absolute_pitch_rate}, " \
    #           f"north_velocity: {self.north_velocity},east_velocity: {self.east_velocity},vertical_velocity: {self.vertical_velocity})")

class Struct_Ship_Position(BaseStruct):
    latitude=0.0#Latitude	24	4	1	Float	deg
    longitude=0.0#Longitude	28	4	1	Float	deg
    log_speed=0.0#Log speed	32	4	1	Float	m/s
    course_made_good=0.0#Course made good	36	4	1	Float	rad
    speed_over_ground=0.0#Speed over ground	40	4	1	Float	m/s
    set=0.0#Set	44	4	1	Float	rad
    drift=0.0#Drift	48	4	1	Float	m/s
    latitude_accuracy=0.0#Latitude Accuracy	52	4	1	Float	Nm
    longitude_accuracy=0.0#Longitude Accuracy	56	4	1	Float	Nm

    def getListAttribute(self):
        return ["latitude","longitude","log_speed","course_made_good","speed_over_ground","set",
                "drift","latitude_accuracy","longitude_accuracy"]

    #def __repr__(self):
    #    return self.replaceBracket(f"( latitude: {self.latitude},longitude: {self.longitude},log_speed: {self.log_speed}, " \
    #          f"course_made_good: {self.course_made_good},speed_over_ground: {self.speed_over_ground}," \
    #           f"set: {self.set}, drift: {self.drift}," \
    #           f"latitude_accuracy: {self.latitude_accuracy},longitude_accuracy: {self.longitude_accuracy})")

class Struct_WarningCode(BaseStruct):
    failure_byte_01 = b'Ox0'  # 22	1	1	Bit-Struct
    failure_byte_02 = b'Ox0'  # 23	1	1	Bit-Struct
    failure_byte_03 = b'Ox0'  # 24	1	1	Bit-Struct
    failure_byte_04 = b'Ox0'  # 25	1	1	Bit-Struct
    failure_byte_05 = b'Ox0'  # 26	1	1	Bit-Struct
    failure_byte_06 = b'Ox0'  # 27	1	1	Bit-Struct
    failure_byte_07 = b'Ox0'  # 28	1	1	Bit-Struct
    failure_byte_08 = b'Ox0'  # 29	1	1	Bit-Struct
    failure_byte_09 = b'Ox0'  # 30	1	1	Bit-Struct
    failure_byte_10 = b'Ox0'  # 31	1	1	Bit-Struct
    failure_byte_11 = b'Ox0'  # 32	1	1	Bit-Struct
    failure_byte_12 = b'Ox0'  # 33	1	1	Bit-Struct
    failure_byte_13 = b'Ox0'  # 34	1	1	Bit-Struct
    failure_byte_14 = b'Ox0'  # 35	1	1	Bit-Struct
    failure_byte_15 = b'Ox0'  # 36	1	1	Bit-Struct
    failure_byte_16 = b'Ox0'  # 37	1	1	Bit-Struct
   
    def getListAttribute(self):
        return ["failure_byte_01","failure_byte_02","failure_byte_03","failure_byte_04",
                "failure_byte_05","failure_byte_06","failure_byte_07","failure_byte_08",
                "failure_byte_09","failure_byte_10","failure_byte_11","failure_byte_12",
                "failure_byte_13","failure_byte_14","failure_byte_15","failure_byte_16"]

    def __repr__(self):
        return self.decode()
        
    def decode(self):
        from decoder_scg import decoder
        descr=""
        for i in range(16):
            field_name=f"failure_byte_{i+1:02}"
            value=decoder.decodeValueFailure("SCGP_Multi_health_status_INS",field_name,getattr(self,field_name))
            v = getattr(self,field_name)
            if not isinstance(v, int):
                v = int.from_bytes(v, 'big')
            descr+=f'\'{field_name}\':{v},'
            #descr+=f'\'{field_name}\':"{value}",'
        return self.replaceBracket(f"({descr[:-1]})")

class Struct_NoPointingZone(BaseStruct):#22	17	10	Struct			Definisce un settore volumetrico di No Pointing
    validity=False#22	1	1	Bool			Specifica se la zona è in uso
    no_pointing_zone_start_azimuth=0.0  #23	4	1	Float	gradi	[0..360]	Valore iniziale in azimuth della zona di No Pointing
    no_pointing_zone_end_azimuth=0.0    #27	4	1	Float	gradi	[0..360]	Valore finale in azimuth della zona di No Pointing
    no_pointing_zone_start_elevation=0.0#31	4	1	Float	gradi	[-90..90]	Valore iniziale in elevazione della zona di No Pointing
    no_pointing_zone_end_elevation=0.0  #35	4	1	Float	gradi	[-90..90]	Valore finale in elevazione della zona di No Pointing
    def getListAttribute(self):
        return ["validity","no_pointing_zone_start_azimuth","no_pointing_zone_end_azimuth","no_pointing_zone_start_elevation","no_pointing_zone_end_elevation"]

class Struct_NoFiringZone(BaseStruct):#192	17	10	Struct			Definisce un settore volumetrico di No Firing
    validity=False                           #192	1	1	Bool			Specifica se la zona è in uso
    no_firing_zone_start_azimuth = 0.0      #193	4	1	Float	gradi	[0..360]	Valore iniziale in azimuth della zona di No Firing
    no_firing_zone_end_azimuth = 0.0        #197	4	1	Float	gradi	[0..360]	Valore finale in azimuth della zona di No Firing
    no_firing_zone_start_elevation = 0.0    #201	4	1	Float	gradi	[-90..90]	Valore iniziale in elevazione della zona di No Firing
    no_firing_zone_end_elevation = 0.0      #205	4	1	Float	gradi	[-90..90]	Valore finale in elevazione della zona di No Firing
    start_azimuth_limit = 0.0               #362	4	1	Float	gradi	[0..360]	Fine corsa sinistro di brandeggio (riferimento asse chiglia)
    end_azimuth_limit = 0.0                 #366	4	1	Float	gradi	[0..360]	Fine corsa destro in brandeggio (riferimento asse chiglia)
    start_elevation_limit = 0.0             #370	4	1	Float	gradi	[-90..0]	Fine corsa di depressione
    end_elevation_limit = 0.0               #374	4	1	Float	gradi	[0..90]	Fine corsa di elevazione 

    def getListAttribute(self):
        return ["validity","no_firing_zone_start_azimuth","no_firing_zone_end_azimuth", \
                "no_firing_zone_start_elevation","no_firing_zone_end_elevation", \
                "start_azimuth_limit","end_azimuth_limit", \
                "start_elevation_limit","end_elevation_limit"]

   
class Struct_CRP_relative_mounting_position(BaseStruct):#	378	12	1	Struct			Struttura contenente le coordinate della posizione relativa dell'affusto della SCG rispetto al CRP nave.
    x_position=np.intc(0) #	378	4	1	Int	mm	[-250000..250000]	Coordinata X del sistema di riferimento: origine CRP, asse X positivo verso EST, asse Y positivo verso NORD, asse Z positivo verso l’ALTO.
    y_position=np.intc(0) #	382	4	1	Int	mm	[-250000..250000]	Coordinata Y del sistema di riferimento: origine CRP,asse X positivo verso EST, asse Y positivo verso NORD, asse Z positivo verso l’ALTO.
    z_position=np.intc(0) #	386	4	1	Int	mm	[-50000..50000]	Coordinata Z del sistema di riferimento: origine CRP, asse X positivo verso EST, asse Y positivo verso NORD, asse Z positivo verso l’ALTO.

    def getListAttribute(self):
        return ["x_position","y_position","z_position"]






