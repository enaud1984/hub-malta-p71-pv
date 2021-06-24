from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, IntegerField, FloatField, FieldList, FormField
from wtforms.validators import DataRequired

from wtforms.fields.html5 import DateTimeLocalField


choiceDestination=[("SCGF","SCGF - Prua(centrale=Foward)"),("SCGP","SCGP - Babordo (lato sx=port)"),("SCGS","SCGS - Dritta (lato dx=starboard)")]
choiceConfiguration_request=[(0, 'Local'), (1, 'Autonomous'),(2, 'Integrated')]
choicedesignation_type=[(1, 'CST'), (2, 'Position')]
choiceFiring_authorization=[(0, 'firing not authorised'),(1, 'firing authorised')]
choiceKinematics_type=[(1,"3D CARTESIAN KINEMATICS"),
                       (2,"3D CARTESIAN POSITION"),
                       (3,"2D CARTESIAN KINEMATICS"),
                       (4,"2D CARTESIAN POSITION"),
                       (5,"2D POLAR KINEMATICS"),
                       (6,"2D POLAR SURFACE KINEMATICS"),
                       (7,"2D POLAR POSITION"),
                       (8,"2D POLAR SURFACE POSITION"),
                       (9,"1D POLAR POSITION"),
                       (10,"EW 1D POLAR POSITION"),
                       (11,"EW 2D POLAR POSITION")]

choiceServo=[(0,"No change"),(1,"Not Authorised;"),(2,"Authorised")]
FireEnable=[(0,"No change"),(1,"Firing Disabled"),(2,"Firing Enabled")]
FireWithoutTracking=[(0,"No change"),(1,"Not Authorised;"),(2,"Authorised")]
enabled=[(1,"OFF"),(2,"ON")]
algorithm=[(1,"Correlation"),(2,"Contrast")]
state=[(0,"Not tracking"),(1,"Tracking"),(2,"Memory")]
window_resize=[(0,"No change (Not Used)"),(1,"Window Size Decreased"),(2,"Window Size Increased")]

class Form_3d_cartesian_kinematics(FlaskForm):#	40	26	1	struct
    x = FloatField("x")   #	42	4	1	float
    y = FloatField("y")   #	46	4	1	float
    z = FloatField("z")   #50	4	1	float
    vx = FloatField("vx")  #	54	4	1	float
    vy = FloatField("vy")  #	58	4	1	float
    vz = FloatField("vz")  #	62	4	1	float


class Form_3d_cartesian_position(FlaskForm):#	40	14	1	struct
    x = FloatField("x")  #	42	4	1	float
    y = FloatField("y")  #	46	4	1	float
    z = FloatField("z")  #	50	4	1	float


class Form_2d_cartesian(FlaskForm):#	kinematics	40	18	1
    x = FloatField("x")#	42	4	1	float
    y = FloatField("y")#	46	4	1	float
    vx = FloatField("vx")#	50	4	1	float
    vy = FloatField("vy")#	54	4	1	float


class Form_2d_cartesian_position(FlaskForm):#	40	10	1	struct
    x = FloatField("x")#	42	4	1	float
    y = FloatField("y")#	46	4	1	float


class Form_2d_polar_kinematics(FlaskForm):#	40	18	1	struct
    true_bearing    = FloatField("True bearing")  #	42	4	1	float
    angle_of_sight  = FloatField("Angle of sight")  #	46	4	1	float
    true_bearing_rate = FloatField("True bearing rate")  #50	4	1	float
    angle_of_sight_rate = FloatField("Angle of sight rate")  #	54	4	1	float


class Form_2d_polar_surface(FlaskForm):#	kinematics	40	18	1
    spare = 0#	40	2	1	padding
    true_bearing = FloatField("True bearing")  #	42	4	1	float
    range_2d = FloatField("Range 2d")  #	46	4	1	float
    true_bearing_rate = FloatField("True bearing rate")  #	50	4	1	float
    range_rate = FloatField("Range rate")  #	54	4	1	float


class Form_2d_polar_position(FlaskForm):#	40	10	1	struct
    spare=0#	40	2	1	padding
    true_bearing   = FloatField("True bearing")  #	42	4	1	float
    angle_of_sight =FloatField("Angle of sight")  #	46	4	1	float


class Form_2d_polar_surface_position(FlaskForm):#	40	10	1
    spare=0#	40	2	1	shortInt
    padding_range = FloatField("padding range")  #	42	4	1 float
    true_bearing  = FloatField("True bearing")  #46	4	1	float


class Form_1d_polar_position(FlaskForm):#	40	6	1	struct
    spare = 0#	40	2	1	padding
    true_bearing = FloatField("True bearing")  #	42	4	1	float


class Form_ew_1d_polar_position(FlaskForm):#	40	14	1	struct
    spare = 0  # 40	2	1	padding
    true_bearing = FloatField( "True bearing" )  # 42	4	1	float
    origin_Latitude = FloatField("Origin_Latitude")  #	46	4	1	Float	deg	[-90..+90]
    origin_Longitude = FloatField("Origin Longitude")  #	50	4	1	Float	deg	[-180..+180]


class Form_ew_2d_polar_position(FlaskForm):#	40	18	1	struct		
    spare=0#	40	2	1	padding		
    true_bearing = FloatField("True bearing")  #	42	4	1	float	rad	[0..2_*_pi]
    angle_of_sight = FloatField("Angle of sight")  #	46	4	1	float	rad	[-pi/2..pi/2]
    origin_latitude = FloatField("Origin Latitude")  #	46	4	1	float	deg	[-90..+90]
    origin_longitude = FloatField("Origin Longitude")  #	50	4	1	float	deg	[-180..+180]


class BaseForm(FlaskForm):
    from decoder_scg import ActionManager
    action_id=IntegerField("action_id",default=ActionManager.current_action_id+1)
    selectDestination = SelectField( "Select Destination", choices=choiceDestination, validators=[DataRequired()] )

class Designation_order_form(BaseForm):
    designation_type = SelectField('Designation Type', choices=choicedesignation_type,
                                        validators=[DataRequired()])

    threat_key = BooleanField("Threat Key")  # 22	1	1	Bool
    designation_control_pause = BooleanField("Designation Control Pause")  # 23	1	1	bool
    firing_authorization = SelectField('Firing Authorization', choices=choiceFiring_authorization,
                                        validators=[DataRequired()])
    cstn =IntegerField("CSTN (Numero CST della traccia inviata)")  # 26	4	1	int
    #kinematics_time_of_validity	30	36	1	struct
    seconds =  DateTimeLocalField("Kinematics Time of validity (date)", format='%Y-%m-%dT%H:%M:%S',)
    #time = TimeField("Kinematics Time of validity (time)")
    microseconds= IntegerField("Microsendi passati da Kinematics Time of validity",validators=[DataRequired()])
    kinematics_type = SelectField("Kinematics Type",choices=choiceKinematics_type,
                                  validators=[DataRequired()])
    kinematics=None
    form_1=FieldList(FormField(Form_3d_cartesian_kinematics),min_entries=1)
    form_2=FieldList(FormField(Form_3d_cartesian_position),min_entries=1)
    form_3=FieldList(FormField(Form_2d_cartesian),min_entries=1)
    form_4=FieldList(FormField(Form_2d_cartesian_position),min_entries=1)
    form_5=FieldList(FormField(Form_2d_polar_kinematics),min_entries=1)
    form_6=FieldList(FormField(Form_2d_polar_surface),min_entries=1)
    form_7=FieldList(FormField(Form_2d_polar_position),min_entries=1)
    form_8=FieldList(FormField(Form_2d_polar_surface_position),min_entries=1)
    form_9=FieldList(FormField(Form_1d_polar_position),min_entries=1)
    form_10=FieldList(FormField(Form_ew_1d_polar_position),min_entries=1)
    form_11=FieldList(FormField(Form_ew_2d_polar_position),min_entries=1)

class Change_configuration_order_form(BaseForm):
    configuration_request = SelectField('Configuration Request', choices=choiceConfiguration_request,
                                        validators=[DataRequired()])

class Servo_control_form(BaseForm):
    gun_servo=SelectField('Gun Servo', choices=choiceServo,
                                        validators=[DataRequired()])
    stabilization = SelectField( 'Stabilization', choices=choiceServo,
                            validators=[DataRequired()] )
    manual_control = SelectField( 'Manual Control', choices=choiceServo,
                            validators=[DataRequired()] )
    parking_position=BooleanField("Parking Position")
    left_loading_position=BooleanField("Left Loading Position")
    right_loading_position=BooleanField("Right Loading Position")
    drift_compensation=SelectField( 'Drift Compensation', choices=choiceServo,
                            validators=[DataRequired()] )

class Integrated_Safety_Setting_form(BaseForm):
    fire_enable_state=SelectField('Fire Enable', choices=FireEnable,
                                        validators=[DataRequired()])
    fire_without_tracking_state = SelectField( 'Fire without tracking', choices=FireWithoutTracking,
                            validators=[DataRequired()] )
    free_engagement_authorisation_state = SelectField( 'Free engagement authorisation', choices=FireWithoutTracking,
                            validators=[DataRequired()] )

class Tracker_control_form(BaseForm):
    enabled=SelectField('enabled', choices=enabled,
                                        validators=[DataRequired()])
    algorithm=SelectField('algorithm', choices=algorithm,
                                        validators=[DataRequired()])
    state=SelectField('state', choices=state,
                                        validators=[DataRequired()])
    window_resize=SelectField('window_resize', choices=window_resize,
                                        validators=[DataRequired()])

class Update_cst_kinematics_designation_form(BaseForm):

    cstn = IntegerField( "CSTN (Numero CST della traccia inviata)" )  # 16	4	1	int
    #kinematics_time_of_validity	20	8	1	struct
    seconds =  DateTimeLocalField("Kinematics Time of validity (date)", format='%Y-%m-%dT%H:%M:%S',)
    microseconds= IntegerField("Microsendi passati da Kinematics Time of validity",validators=[DataRequired()])

    kinematics_type = SelectField("Kinematics Type",choices=choiceKinematics_type,
                                  validators=[DataRequired()]) #28 2 1 int
    kinematics=None
    form_1=FieldList(FormField(Form_3d_cartesian_kinematics),min_entries=1)
    form_2=FieldList(FormField(Form_3d_cartesian_position),min_entries=1)
    form_3=FieldList(FormField(Form_2d_cartesian),min_entries=1)
    form_4=FieldList(FormField(Form_2d_cartesian_position),min_entries=1)
    form_5=FieldList(FormField(Form_2d_polar_kinematics),min_entries=1)
    form_6=FieldList(FormField(Form_2d_polar_surface),min_entries=1)
    form_7=FieldList(FormField(Form_2d_polar_position),min_entries=1)
    form_8=FieldList(FormField(Form_2d_polar_surface_position),min_entries=1)
    form_9=FieldList(FormField(Form_1d_polar_position),min_entries=1)
    form_10=FieldList(FormField(Form_ew_1d_polar_position),min_entries=1)
    form_11=FieldList(FormField(Form_ew_2d_polar_position),min_entries=1)


