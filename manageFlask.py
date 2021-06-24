import datetime
import inspect
import json
import os
import numpy
from flask import request, render_template, Response, flash
from flask_restful import Api, Resource
from flask_socketio import SocketIO, emit
import logging
from logging.handlers import RotatingFileHandler
import common_struct
from Hub import app
from decoder_scg import ActionManager
from forms import Tracker_control_form,Update_cst_kinematics_designation_form,Change_configuration_order_form, Designation_order_form, Servo_control_form,Integrated_Safety_Setting_form
from gevent.pywsgi import WSGIServer
from flask_wtf import CSRFProtect
from flask_fontawesome import FontAwesome
from flask_bootstrap import Bootstrap
from config import conf
from time import time

logger = logging.getLogger( __name__ )
api = Api( app )
sock = SocketIO()
csrf = CSRFProtect()


def initServer():
    from api_hub import initSwagger
    from utility import setup_logger
    LOG_FILENAME=os.path.join("log","logFlask_{}.log".format(datetime.datetime.strftime(datetime.datetime.now(),"%Y%m%d_%H%M%S")))
    setup_logger("flask", LOG_FILENAME,log=app.logger)
    fa = FontAwesome(app)
    Bootstrap( app )
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    SECRET_KEY = os.urandom( 32 )
    app.config['SECRET_KEY'] = SECRET_KEY
    csrf.init_app(app )
    sock.init_app(app)
    logging.getLogger('socketio').setLevel(logging.ERROR)
    logging.getLogger('engineio').setLevel(logging.ERROR)
    
    if conf.enable_swagger:
        initSwagger(app)
    initRoute()
    server = WSGIServer( (conf.http_server, conf.http_port), app ,log=app.logger)
    logger.info(f"init server {conf.http_server}:{conf.http_port}")
    logging.getLogger('pywsgi').setLevel(logging.ERROR)
    return server 

#@app.errorhandler(CSRFError)
def handle_error(e):
    logger.error(f"ERROR CSRFError", e )
    return render_template('error.html', reason=e.description), 400

def initRoute():
    api.add_resource( Home, '/home' if conf.enable_swagger else '/')
    api.add_resource( Change_configuration_order, '/change_configuration_order' )
    api.add_resource( Designation_order, '/designation_order' )
    api.add_resource( Servo_control, '/servo_control_form' )

class Server( Resource ):
    def get(self):
        #se browser ritorna FORM else ritorna il json del messaggio se esiste altrimenti errore 400
        return self.manageGet(request)

    def post(self):
        return self.managePost(request)

    def manageGet(self,request):
        try:
            from utility import mapMsgUdpOUT
            #se browser ritorna FORM else ritorna il json del messaggio se esiste altrimenti errore 400
            if self.is_browser(request):
                form =self.getForm(request)
                if hasattr(form,"action_id"):
                    form.action_id.default=ActionManager.current_action_id+1

                kinematics_type=request.args.get('kinematics_type')
                if kinematics_type is not None:
                    form.kinematics_type.default = int(kinematics_type)
                    form.kinematics=getattr(form,"form_"+kinematics_type)
                    #form.kinematics.name=form.kinematics_type.choices[int(kinematics_type)-1][1]
                    form.kinematics.short_name = form.kinematics_type.choices[int( kinematics_type ) - 1][1]
                form.process()

                return Response(render_template(self.template , form=form), mimetype='text/html' )
            elif self.msg in mapMsgUdpOUT:

                return json.dumps( mapMsgUdpOUT[self.msg] )
            else:
                return "not found", 404
        except Exception as e:
            logger.error(f"ERROR DETAIL: {self.__class__.__name__}", e )


    def getForm(self,req):
        return self.form_class(req.form)

    def is_browser(self,req):
        userAgent=req.headers.get('User-Agent')
        contentType= req.content_type
        return "Mozilla" in req.headers.get('User-Agent')

    def sendUDPfromForm(self, cls, form,req):
        from manageUDP import CUSTOM_ARGS
        obj = cls()
        variables={}
        values={}
        if hasattr(obj,"setValues") and hasattr(form,"kinematics_type"): #obj.__class__.__name__=="GW_SCGP_designation_order_INS":
            index_choice=int(form.kinematics_type.data)-1
            variables={"kinematics_type":index_choice}
            for k in req.form:
                if form.kinematics_type.choices[index_choice][1] in k:
                    variables[k.split("-")[-1]]=req.form[k]  #passare pure le variabili?
            obj.setValues(variables)
        variables.update( form.data )

        for k in obj.getListAttribute():
            attribute=getattr(obj,k)
            if "STRUCT" in f"{type(attribute)}".upper():
                v=self.setInternalStruct(attribute,variables)
                values.update(v)
                continue
            if hasattr(obj,k) and k not in CUSTOM_ARGS and k in form.data:
                v=form.data[k]
                type_f=type(attribute)
                values[k]=type_f(v)
                setattr( obj, k, type_f(v) )
            if k.endswith( "time_of_validity"):
                t="%.6f" % time()
                attribute=getattr(obj,k)
                timeunix=t.split(".")
                attribute.seconds=int(timeunix[0])
                attribute.microseconds=int(timeunix[1])
            
        msg_name = obj.__class__.__name__
        obj.sendUDP( msg_name,obj.action_id)
        return obj

    def setInternalStruct(self,attribute,variables):
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


    def sendUDP(self, cls, req_data ):
        from manageUDP import CUSTOM_ARGS
        obj = cls()
        for k, v in req_data.items():
            if hasattr(obj,k) and k not in CUSTOM_ARGS:
                setattr( obj, k, v )
        obj.sendUDP( obj.__class__.__name__, obj.action_id)
        return obj

    out_msg_classes=[]
    

    def getDestination(self,form=None,request=None):
        import utility as ut
        from decoder_scg import destinationSCG
        if form is not None:
            if form.selectDestination.data in destinationSCG:
                destination=self.out_msg_classes[destinationSCG.index(form.selectDestination.data)]
            else:
                destination=self.out_msg_classes[0]
        else:
            if request.data["selectDestination"] in destinationSCG:
                destination = self.out_msg_classes[destinationSCG.index(request.data["selectDestination"])]
            else:
                destination = self.out_msg_classes[0]
        return ut.getManagerClass(destination)

    def removeSubForms(self,form):
        try:
            for i in range( 15 ):
                k = "form_" + str( i + 1 )
                if k in form._fields:
                    del form._fields[k]
            return form
        except Exception:
            logger.error( "error on del form " + str( i + 1 ) )
    
    def managePost(self,request):
        if self.is_browser(request):
            form = self.getForm(request)
            self.manageChange(request,form)
            destination=self.getDestination(form)
            if form.validate():
                #req_data={"configuration_request":form.configuration_request.data}
                obj = self.sendUDPfromForm( destination, form ,request)
                msg =f'Message  {self.__class__.__name__} Sended...{obj.values()}'
                flash( msg )
                logger.info(msg)
                self.applyChangeForm(request,form)
                return Response( render_template( self.template, form=form, msg="Messaggio Inviato..." ), mimetype='text/html' )
            else:
                flash( form.errors )
                return Response( render_template( self.template, form=form ), mimetype='text/html' )
        else:
            destination=self.getDestination(None,request)
            obj = self.sendUDP( destination, request.data)
            msg =f'Message  {self.__class__.__name__} Sended...{obj.values()}'
            flash( msg )
            logger.info(msg)
            data = {"response":f"OK {destination}"} # Your data in JSON-serializable type
            response = app.response_class(response=json.dumps(data),
                                        status=200,
                                        mimetype='application/json')
            return response

    def manageChange(self,request,form):
        if request.args.get("change"):
            self.applyChangeForm(request,form)
            return Response( render_template( self.template, form=form ), mimetype='text/html' )
        self.removeSubForms( form )

    def applyChangeForm(self,request,form):
        pass



class Change_configuration_order( Server ):
    form_class = Change_configuration_order_form
    msg="GW_SCGP_change_configuration_order_INS"
    template='change_configuration_order_form.html'
    out_msg_classes=["GW_SCGP_change_configuration_order_INS","GW_SCGF_change_configuration_order_INS","GW_SCGS_change_configuration_order_INS"]
    

class Designation_order(Server):
    form_class = Designation_order_form
    msg="GW_SCGP_designation_order_INS"
    template='designation_order_form.html'
    out_msg_classes=["GW_SCGP_designation_order_INS","GW_SCGF_designation_order_INS","GW_SCGS_designation_order_INS"]
    
    def applyChangeForm(self,request,form):
        kinematics_type = request.args.get( 'kinematics_type' )
        if kinematics_type is not None:
            form.kinematics_type.default = int( kinematics_type )
            form.kinematics = getattr( form, "form_" + kinematics_type )
            # form.kinematics.name=form.kinematics_type.choices[int(kinematics_type)-1][1]
            form.kinematics.short_name = form.kinematics_type.choices[int( kinematics_type ) - 1][1]
            form.kinematics.min_entries=1
            form.process()
    

class Servo_control(Server):
    form_class = Servo_control_form
    msg = "GW_SCGP_servo_control_INS"
    template = 'servo_control_form.html'
    out_msg_classes=["GW_SCGP_servo_control_INS","GW_SCGF_servo_control_INS","GW_SCGS_servo_control_INS"]


class Integrated_Safety_Setting( Server ):
    form_class = Integrated_Safety_Setting_form
    msg = "GW_SCGP_integrated_safety_settings_INS"
    template = 'integrated_safety_setting_form.html'
    out_msg_classes = ["GW_SCGP_integrated_safety_settings_INS", "GW_SCGF_integrated_safety_settings_INS",
                       "GW_SCGS_integrated_safety_settings_INS"]

class Tracker_control(Server):
    form_class = Tracker_control_form
    msg = "SCGP_CS_tracker_control_INS"
    template = 'tracker_control_form.html'
    out_msg_classes = ["GW_SCGP_tracker_control_INS", "GW_SCGF_tracker_control_INS",
                       "GW_SCGS_tracker_control_INS"]

class Update_cst_kinematics_designation(Server):
    form_class = Update_cst_kinematics_designation_form
    msg = "GW_SCGP_update_cst_kinematics_designation_INS"
    template = 'update_cst_kinematics_designation_form.html'
    out_msg_classes = ["SCGP_GW_designation_report_INS", "SCGF_GW_designation_report_INS",
                       "SCGS_GW_designation_report_INS"]

class Home( Resource ):
    def get(self):
        from utility import mapMsgUdpIn
        return Response( render_template( 'index.html' ), mimetype='text/html' )


def sendMessageMapUDP_IN(message):
    sock.emit( 'mapMsgIN', {'data': str( message )}, namespace="/test" )

def sendMessageMapUDP_OUT(message):
    sock.emit( 'mapMsgOUT', {'data': str( message )}, namespace="/test" )


def sendMessageMapSerial(message):
    sock.emit( 'mapMsgSerial', {'data': str( message )}, namespace="/test" )


def sendMessageActionReceived(message):
    sock.emit( 'ActionReceived', {'data': str( message )}, namespace="/test" )

def sendMessageActionPending(message):
    sock.emit( 'ActionPending', {'data': str( message )}, namespace="/test" )

def sendMessageErrors(error):
    sock.emit( 'Error', {'data': str( repr(error) )}, namespace="/test" )

@sock.on( "connectHandler" ,namespace='/test')
def connectHandler(msg):
    logger.info("Connesso Utente...")

    from decoder_scg import ActionManager
    from utility import listErrors
    for k, v in ActionManager.mapMsgReceived.items():
        msg = v.values()
        # sock.emit( 'ActionReceived', {'data': msg}, namespace="/test" )
        sendMessageActionReceived( msg )

    for k, v in ActionManager.mapMsgPending.items():
        msg = v.values()
        # sock.emit( 'ActionPending', {'data': msg}, namespace="/test" )
        sendMessageActionPending( msg )
    
    for err in listErrors:
        sendMessageErrors(err)
        

@sock.on( "disconnect" )
def disconnectHandler():
    from decoder_scg import ActionManager
    ActionManager.CleanObjResp()




