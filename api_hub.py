from manageFlask import app,csrf
from flask import request,jsonify
from flask_restx import Api, Resource,Namespace, fields,Model
from forms import Tracker_control_form,Update_cst_kinematics_designation_form,Change_configuration_order_form,Servo_control_form,Designation_order_form,Integrated_Safety_Setting_form
import inspect
import json
import datetime
from utility import setup_logger
import os
import numpy as np
from manageUDP import CUSTOM_ARGS
from decoder_scg import DecodeStruct,ActionManager
from manageSCGF import *
from manageGW import *
from manageNAVS import *
from common_struct import *
from flask import Request
from enum import Enum
from werkzeug.datastructures import FileStorage
from decoder_scg import destinationSCG
from manageFlask import Change_configuration_order,Designation_order,Servo_control,Integrated_Safety_Setting,Update_cst_kinematics_designation,Tracker_control
authorizations = {
    'basicAuth': {
        'type': 'basic',
        'in': 'header',
        'name': 'Authorization'
    }
}
api = Api(title="API", version="1.0", description="Hub API",authorizations=authorizations)

logFilename=os.path.join("log","logApi_{}.log".format(datetime.datetime.strftime(datetime.datetime.now(),"%Y%m%d_%H%M%S")))
logger=setup_logger("api",logFilename)


@api.errorhandler(Exception)
@api.header('error',  'Error')
def handle_exception_with_header(error):
    '''This is a custom error'''
    logger.error(f"Error {error}" ,error)
    return {'message': error.message}, 400, {'error': f'{error}'}

ns = api.namespace('api', description='Servizi per SCGP e SCGF')
ns.logger.addHandler(logger)
   
def initSwagger(app):
    app.config.SWAGGER_UI_OPERATION_ID = True
    app.config.SWAGGER_UI_REQUEST_DURATION = True
    app.config['WTF_CSRF_ENABLED']=False
    api.init_app(app )
    #api.add_namespace(ns)
    #api.add_namespace(api_simulator)
    
@api.errorhandler(Exception)
@api.header('error',  'Error')
def handle_exception_with_header(error):
    '''This is a custom error'''
    logger.error(f"Error {error}" ,error)
    return {'message': f" error {error}"}, 400, {'error': f'{error}'}

def convert_dict2struct(type_field,values):
    obj = type_field()
    listAttr=obj.getListAttribute()
    for k in listAttr:
        if hasattr(obj,k) and k not in CUSTOM_ARGS and k in values:	
            value = None
            attribute = getattr(obj,k)
            v = values[k]
            if v is not None:
                type_field = type(attribute)
                value = type_field(v)
                setattr( obj, k, value )
    return obj
def convertRequest2Manager(action_id,cls,data):
    manager = DecodeStruct.getManager(cls)
    if manager:
        listAttr=manager.getListAttribute()
        values = data[cls]
        if hasattr(manager,"action_id"):
            values["action_id"]=action_id
        
        for k in listAttr:
            if hasattr(manager,k) and k not in CUSTOM_ARGS and k in values:
                attribute=getattr(manager,k)
                v = values[k]
                type_field = type(attribute)
                if type_field in [list]:
                    listChild=[]
                    type_field = type(attribute[0])
                    for i in range(len(attribute)):
                        if i<len(v):
                            values = v[i]
                            value = convert_dict2struct(type_field,values)
                            listChild.append(value)
                        else:
                            listChild.append(attribute[i])
                    setattr( manager, k, listChild )
                
                elif str(type_field.__module__) in ["common_struct"]:
                    value = convert_dict2struct(type_field,values)
                    setattr( manager, k, value )
                else:
                    value = None
                    if v is not None:
                        value = type_field(v)
                    setattr( manager, k, value )
    return manager

def convert_field_from_form(f, field):
    ret = None
    label = None
    if hasattr(field,"field_class"):
        field_class =field.field_class
        type_field=str(field_class.__name__)
    else:
        return None,None
    if type_field =="DateTimeLocalField":
        label=field.args[0]
        ret=fields.DateTime(required=True,attribute=f, description=label)
    elif type_field =="IntegerField":
        label=field.args[0]
        ret=fields.Integer(required=True,attribute=f, description=label)
    elif type_field =="FloatField":
        label=field.args[0]
        ret=fields.Float(required=True,attribute=f, description=label)
    elif type_field =="BooleanField":
        label=field.args[0]
        ret=fields.Boolean(required=True,attribute=f, description=label,default=False)
    elif type_field =="FieldList":
        form=field.args[0]
        field_class =form.args[0]
        list_fields=[c for c in field_class.__dict__ if not c.startswith("_") ]
        label=field_class.__name__.replace("Form_","")
        mapField={}
        for c in list_fields:
            child,label_child = convert_field_from_form(c, getattr(field_class, c))
            if child and c != "spare":
                mapField[c]=child
        ret=None
        ret=fields.Nested(api.model(label,mapField))
    elif type_field =="SelectField":
        enum=[]
        label=field.args[0]
        if 'choices' in field.kwargs:
            choices=field.kwargs['choices']
            descr="\r\n"
            for c in choices:
                enum.append(c[0])
                descr+=f"{c[0]}:{c[1]};\r\n"
        ret=fields.String(required=True,attribute=f,enum=enum,title=label,description=label+descr)
    return ret,label

def convert_form(form_class)-> dict:
    ret={}
    # list_fields=[f for f in form_class.__dict__ if not f.startswith("__") ]
    attributes = inspect.getmembers( form_class, lambda a: not (inspect.isroutine( a )) )
    mapFields={a[0]:a[1] for a in attributes if not a[0].startswith("_") and a[1] and "UnboundField" in str(type(a[1]))}
    # list_fields=[f for f in attributes if hasattr(f,"field_class")]
    enum_form={}
    for f in mapFields:
        field = getattr(form_class,f)
        child,label = convert_field_from_form(f, field)
        if child and child.attribute not in ["selectDestination","action_id","seconds","microseconds"]:
            label =label or f
            field_name=child.attribute or f
            if field_name.startswith("form_"):
                s=eval(f"Struct_{label}()")
                r=repr(s).replace(",}","}")
                t=json.loads(r)
                if "spare" in t:
                    del t["spare"]
                child.example=t
                pos=int(field_name[5:])
                enum_form[pos]=label
                field_name=label
            ret[field_name] = child
    if len(enum_form)>0:
        ret["type"]=fields.String(required=True,attribute=f,enum=[enum_form[i+1] for i in range(len(enum_form))],title=label)       
    return ret

model_Change_configuration_order = api.model('Change_configuration_order', convert_form(Change_configuration_order_form))
model_Servo_control = api.model('Servo_control', convert_form(Servo_control_form))
model_Designation_order = api.model('Designation_order', convert_form(Designation_order_form))
model_Integrated_safety_settings = api.model('Integrated_safety_settings', convert_form(Integrated_Safety_Setting_form))
model_Tracker_control=api.model('Tracker_control', convert_form(Tracker_control_form))
model_Update_cst_kinematics_designation=api.model('Update_cst_kinematics_designation', convert_form(Update_cst_kinematics_designation_form))



def convert_map(mapIn):
    from config import timestamp_format
    ret={}
    mapMsg = {} 
    mapMsg.update(mapIn.copy())
    for k, v in mapMsg.items():
        if hasattr(v,"values"):
            msg = v.values(api=True)
            if v.timestamp is not None:
                msg["timestamp"] = v.timestamp.strftime( timestamp_format )
            else:
                logger.error(f"Timestamp is NONE {k} {v}" )
            ret[k] = msg
            
        else:
            ret[k] = v
    return ret

def response_msg(msg, entry):
    if entry is None:
        return ns.abort(500, status = f"Could not retrieve information {msg}", statusCode = "500")
    else:
        return jsonify(entry)
"""
parser = api.parser()
parser.add_argument("color", choices=('one', 'two'), location="uri")
parser.add_argument("param", type=int, help="Some param", location="form")
parser.add_argument("param", type=FileStorage, help="Some param", location="files")

@api.route("/with-parser", endpoint="with-parser")
class WithParserResource(Resource):
    @api.doc(parser=parser)
    def post(self,color=None):
        data=request.values
        logger.info("request.data")
        return {}
"""

@ns.route("/MsgIn")
@ns.param('msg_name', 'The msg name')
@csrf.exempt
class ListMsgIn( Resource ):

    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' },
            params={'msg_name': 'Specify the message name' })
    def get(self,msg_name=None):
        from utility import mapMsgUdpIn
        if msg_name is not None:
            return response_msg(msg_name, mapMsgUdpIn.get(msg_name))
        return convert_map(mapMsgUdpIn)

@ns.route('/MsgOut' )
@ns.param('msg_name', 'The msg name')
@csrf.exempt
class ListMsgOut( Resource ):
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' },
            params={'msg_name': 'Specify the message name' })
    def get(self,msg_name=None):
        from utility import mapMsgUdpOUT
        if msg_name is not None:
            return response_msg(msg_name, mapMsgUdpOUT.get(msg_name))
        return convert_map(mapMsgUdpOUT)


@ns.route('/MsgNmea' )
@ns.param('source_id', 'The source id')
@csrf.exempt
class ListMsgNmea( Resource ):
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' },
            params={'msg_name': 'Specify the message name','source_id': 'Specify the source id' })
    def get(self,msg_name=None,source_id=None):
        from utility import mapMsg
        if msg_name is not None:
            return response_msg(msg_name, mapMsg.get(msg_name))
        return convert_map(mapMsg)

@ns.route('/MsgSended' )
@ns.param('action_id', 'The action id')
@csrf.exempt
class ListMsgPending( Resource ):
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' },
            params={'action_id': 'Specify the action_id' })
    def get(self,ation_id=None):
        from decoder_scg import ActionManager
        return convert_map(ActionManager.mapMsgPending)

@ns.route('/MsgWithAck' )
@ns.param('action_id', 'The action id')
class ListMsgWithAck( Resource ):
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' },
            params={'action_id': 'Specify the action_id' })
    def get(self,ation_id=None):
        from decoder_scg import ActionManager
        return convert_map(ActionManager.mapMsgReceived)

def set_internal_struct(self,attribute,variables):
        from manageUDP import CUSTOM_ARGS
        values={}
        types=attribute.getTypes()
        for k in attribute.getListAttribute():
            if hasattr( attribute, k ) and k not in CUSTOM_ARGS and k in variables:
                v = variables[k]
                if k=="seconds":
                    v=int(datetime.datetime.timestamp(v))
                if k in types:
                    type_f=types[k]
                else:
                    type_f = type( getattr(attribute,k ))
                values[k] = type_f( v )
                setattr( attribute, k, type_f( v ) )
        return values

def send_UDP_from(resource, req):
        from manageUDP import CUSTOM_ARGS
        import utility as ut
        from config import MAX_RETRY,MAX_TIME_TO_SEND,SIMULATOR_RESPONSE
        from time import time,sleep
        import json
        d=req.args["destination"]
        action_id=int(req.args["action_id"])
        destination=resource.out_msg_classes[destinationSCG.index(d)]
        cls=ut.getManagerClass(destination)
        obj = cls()
        
        values=req.get_json(force=True)
        
        for k in obj.getListAttribute():
            attribute=getattr(obj,k)
            if hasattr(obj,k) and k not in CUSTOM_ARGS and k in values:
                v=values[k]
                type_f=type(attribute)
                #values[k]=type_f(v)
                setattr( obj, k, type_f(v) )
            if k.endswith("type") and "type" in values and values["type"] in values:
                c=values["type"]
                s=eval(f"Struct_{c}")
                variables=values[c]
                child=s()
                for j in child.getListAttribute():
                    attribute=getattr(child,j)
                    type_f=type(attribute)
                    v=variables.get(j)
                    if v is not None:
                        setattr( child, j, type_f(v) )
                if hasattr(obj,"kinematics"):
                    obj.kinematics=child
            if k.endswith( "time_of_validity"):
                t="%.6f" % time()
                attribute=getattr(obj,k)
                timeunix=t.split(".")
                attribute.seconds=int(timeunix[0])
                attribute.microseconds=int(timeunix[1])
                
        msg_name = obj.__class__.__name__
        response_class = resource.resp_msg_classes[destinationSCG.index(d)]
        ret={"result":-1,"description":f"{response_class} not received"}
        for t in range(MAX_RETRY):
            if hasattr(obj,"action_id"):
                obj.action_id=action_id
            else:
                logger.error(f"obj without action id attribute {destination}")
            obj.sendUDP( msg_name,action_id)
            sleep(MAX_TIME_TO_SEND)
            if hasattr(obj, "kinematics_time_of_validity"):
                t="%.6f" % time()
                attribute=getattr(obj,"kinematics_time_of_validity")
                timeunix=t.split(".")
                attribute.seconds=int(timeunix[0])
                attribute.microseconds=int(timeunix[1])
            if SIMULATOR_RESPONSE:
                destination=resource.resp_msg_classes[destinationSCG.index(d)]
                cls=ut.getManagerClass(destination)
                obj_resp = cls()
                if hasattr(obj_resp,"reported_action_id"):
                     obj_resp.reported_action_id=action_id
                resp=repr(obj_resp).replace(":b'",":'").replace(",}","}").replace("'","\"")
                logger.debug( "Risposta simulata {} {}".format( action_id,resp ) )
                obj_resp=json.loads(resp)
                ret = response_msg(destination,obj_resp)
                break
            if action_id in ActionManager.mapMsgReceived:
                obj_resp = ActionManager.mapMsgReceived[action_id]
                resp=repr(obj_resp).replace(":b'",":'").replace(",}","}")
                logger.debug( "Risposta ricevuta {} {}".format( action_id,resp ) )
                print("Risposta ricevuta {} {}".format( action_id,resp ))
                ret = response_msg(destination,resp)
                break
            else:
                destination = resource.resp_msg_classes[destinationSCG.index( d )]
                if destination in ActionManager.mapMsgIn:
                    obj_resp = ActionManager.mapMsgIn[destination]
                    resp = repr( obj_resp ).replace( ":b'", ":'" ).replace( ",}", "}" )
                    logger.debug( "Risposta ricevuta {} {}".format( action_id, resp ) )
                    print( "Risposta ricevuta {} {}".format( action_id, resp ) )
                    ret = response_msg( destination, resp )
                    break

        return ret

@ns.param('destination', 'The destination',enum=destinationSCG,help='Bad choice: {error_msg}')
@ns.param('action_id','Specify the action Id associated to message',type=int)
@csrf.exempt
class BaseOrder(Resource):
    out_msg_classes=[]
    resp_msg_classes=[]

@ns.route("/change_configuration_order")
class ChangeConfigurationOrder(BaseOrder):
    out_msg_classes=Change_configuration_order.out_msg_classes
    resp_msg_classes=["SCGP_GW_acknowledgment_INS","SCGF_GW_acknowledgment_INS","SCGS_GW_acknowledgment_INS"]
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' })
    @api.expect(model_Change_configuration_order)
    def post(self):
        return send_UDP_from(self,request)

@ns.route("/servo_control")
class ServoControl(BaseOrder):
    out_msg_classes=Servo_control.out_msg_classes
    resp_msg_classes=["SCGP_GW_servo_report_INS","SCGF_GW_servo_report_INS","SCGS_GW_servo_report_INS"]
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' })
    @api.expect(model_Servo_control)
    def post(self):
        return send_UDP_from(self,request)

@ns.route("/designation_order")
class DesignationOrder(BaseOrder):
    out_msg_classes=Designation_order.out_msg_classes
    resp_msg_classes=["SCGP_GW_acknowledgment_INS","SCGF_GW_acknowledgment_INS","SCGS_GW_acknowledgment_INS",]
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' })
    @api.expect(model_Designation_order)
    def post(self):
        return send_UDP_from(self,request)

@ns.route("/integrated_safety_setting")
class IntegratedSafetySetting(BaseOrder):
    out_msg_classes=Integrated_Safety_Setting.out_msg_classes
    resp_msg_classes = ["SCGP_CS_integrated_safety_settings_report_INS", "SCGF_CS_integrated_safety_settings_report_INS",
                       "SCGS_CS_integrated_safety_settings_report_INS"]
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' })
    @api.expect(model_Integrated_safety_settings)
    def post(self):
        return send_UDP_from(self,request)

@ns.route("/tracker_control")
class TrackerControl(BaseOrder):
    out_msg_classes=Tracker_control.out_msg_classes
    resp_msg_classes=["SCGP_CS_tracker_report_INS","SCGF_CS_tracker_report_INS","SCGS_CS_tracker_report_INS"]
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' })
    @api.expect(model_Tracker_control)
    def post(self):
        return send_UDP_from(self,request)

@ns.route("/update_cst_kinematics_designation")
class UpdateCstKinematicsDesignation(BaseOrder):
    out_msg_classes=Update_cst_kinematics_designation.out_msg_classes
    resp_msg_classes=["SCGP_GW_designation_report_INS","SCGF_GW_designation_report_INS","SCGS_GW_designation_report_INS"]
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' })
    @api.expect(model_Update_cst_kinematics_designation)
    def post(self):
        return send_UDP_from(self,request)

def get_map_struct(type_field):
    obj = type_field()
    list_fields = [c for c in obj.getListAttribute() ]
    label = type_field.__name__
    mapField = {}
    for c in list_fields:
        child,label_child = convert_field_from_udp(c, obj, getattr(obj, c))
        if child :
            mapField[c]=child
    return mapField

def convert_field_from_udp(f, obj, field)->(fields.Raw,str):
    ret: fields.Raw = None
    label = f
    type_field = type(field)
    if type_field == list and len(field)>0 and type(field[0]).__name__.startswith("Struct"):
        type_field = type(field[0])
        mapField = get_map_struct(type_field)
        model = api.model(label,mapField)
        ret = fields.List(fields.Nested(model))
    elif type_field in [np.uint]:  # "action_id", "seconds", "microseconds"
        ret = fields.Integer(required=True, description=label)
    elif type_field in [np.intc]:
        ret = fields.Integer(required=True, description=label)
    elif type_field in [float]:
        ret = fields.Float(description=label)
    elif type_field in [bool]:
        ret = fields.Boolean(required=True, description=label,default=False)
    elif type_field in [int]:
        choices=DecodeStruct.choices(obj,f)
        if choices:
            enum=[]
            descr="\r\n"
            for c in choices:
                enum.append(c)
                descr += f"{c}:{choices[c]};\r\n"
            ret=fields.String(required=True, enum=enum, description=label+descr)
        else:
            ret = fields.Integer(readonly=True, description=label)
    elif type_field in [str]:
        ret=fields.String(required=True, description=label)
    elif type_field in [bytes]:
        ret=fields.Integer(required=True, description=label)
    elif str(type_field.__module__) in ["common_struct"]:
        mapField = get_map_struct(type_field)
        ret = fields.Nested(api.model(label, mapField))
    return ret,label


def convertUdp(cls):
    obj=cls()
    fields = obj.getListAttribute()
    conf={}
    for f in fields:
        child,label_child = convert_field_from_udp(f, obj, getattr(obj, f))
        if child :
            conf[f] = child
    if len(fields)!=len(conf):
        diff = {k:type(getattr(obj,k)) for k in fields if k not in conf and getattr(obj,k)}
        #for k in diff: 
        #    child,label_child = convert_field_from_udp(f, obj, getattr(obj, f))
        if len(diff)>0:
            logger.error(f"Errore analisi attributi {cls.__name__} mancanti {diff} {conf}")
        else:
            logger.info(f"analisi attributi {cls.__name__} mancanti {diff}")
    return api.model(cls.__name__,conf)


def getModelsSCG():
    from config import listUDP_IN 
    mapModels={}
    for c in listUDP_IN:
        mapModels[str(c.__name__)] = fields.Nested(convertUdp(c),allow_null=True,skip_none=True)
    return mapModels

modelSCG=api.model('SCG', getModelsSCG())

def getModelsGW():
    import manageGW as gw
    list_manager=dir(gw)
    list_manager = [m for m in list_manager if m.startswith("GW_") or m.startswith("CS_")]
    cls=[eval(m) for m in list_manager]
    mapModels={}
    for c in cls:
        mapModels[str(c.__name__)] = fields.Nested(convertUdp(c),allow_null=True,skip_none=True)
    return mapModels

modelGW=api.model('GW', getModelsGW())

def getModelsNav():
    import manageNAVS as nav
    list_manager=dir(nav)
    list_manager = [m for m in list_manager if m.startswith("NAVS_") ]
    cls=[eval(m) for m in list_manager]
    mapModels={}
    for c in cls:
        mapModels[str(c.__name__)] = fields.Nested(convertUdp(c),allow_null=True,skip_none=True)
    return mapModels

modelNAV=api.model('NAV', getModelsNav())

@ns.route("/SCG")
@ns.route("/SCG/<int:action_id>")
@csrf.exempt
class SendMsgResponse(Resource):

    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, 
             params={ 'action_id': 'Specify the action Id associated to message' })
    @api.expect(modelSCG)
    def post(self, action_id:int=None,*args,**kwargs):
        try:
            
            data=request.json
            logger.info(f"action_id {action_id} request:{data}")
            list_manager=[]
            for msg in data:
                manager = convertRequest2Manager(action_id,msg,data)
                ActionManager.AckObj(manager)
                list_manager.append(manager.values())		
            # list_of_names[id] = request.json['name']
            return {
                "status": "New message added",
                "list":list_manager
            }
        except KeyError as e:
            ns.abort(500, e.__doc__, status = "Could not save information", statusCode = "500")
        except Exception as e:
            ns.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")


@ns.route("/GW")
@csrf.exempt
class MsgResponseGW(Resource):
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 404: 'Not Found' }, 
             params={ 'action_id': 'Specify the action Id associated to message' })
    @ns.response(200, "successfully fetched health details", modelGW)
    def get(self,*args,**kwargs):
        pass

@ns.route("/NAV")
@csrf.exempt
class MsgResponseNAV(Resource):
    @api.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 404: 'Not Found' }, 
             params={ 'action_id': 'Specify the action Id associated to message' })
    @ns.response(200, "successfully fetched health details", modelNAV)
    def get(self,*args,**kwargs):
        pass
