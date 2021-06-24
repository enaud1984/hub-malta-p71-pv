import logging
import os
import csv


destinationSCG=["SCGP","SCGF","SCGS"]
logger = logging.getLogger(__name__)



class DecodeStruct:
    mapFailure = {}
    mapEnum={}
    decoder = None

    def __init__(self):
        self.initFailure()
        self.initEnum()

    
    @staticmethod
    def getManager(manager_class):
        import manageSCGP as scgp
        import manageSCGF as scgf
        import manageSCGS as scgs
        import manageNAVS as navs
        import manageGW as gw
        if manager_class.startswith("NAVS"):
            obj = eval( "navs."+manager_class + "()")
        elif manager_class.startswith("SCGP_"):
            #obj_pointer=getattr( module, manager ) #<class 'manageSCGP.SCGP_MULTI_health_status_INS'>
            #obj=obj_pointer()
            obj = eval( "scgp." + manager_class + "()")
        elif manager_class.startswith( "SCGF_" ):
            obj = eval( "scgf." + manager_class  + "()")
        elif manager_class.startswith( "SCGS_" ):
            obj = eval( "scgs." + manager_class  + "()")
        elif manager_class.startswith( "GW" ):
            obj = eval( "gw." + manager_class  + "()")
        else:
            obj=None
        return obj

    def initFailure(self):
        try:
            from config import failureCsvFile
            i = 0
            with open( failureCsvFile, newline='\r\n' ) as csvfile:
                reader = csv.reader( csvfile, delimiter='\t' )
                i = 0
                for row in reader:
                    if i == 0:
                        header = row  # NOME_BIT	POSIZIONE	MESSAGGIO	FIELD_NAME	tipo	Descrizione
                    else:
                        manager = row[2]  # nome_classe
                        listField = {}
                        obj=self.getManager(manager)
                        if obj is None:
                            logger.error(f"Errore Caricamento failure non trovato manager {manager}")
                            continue
                        if manager not in self.mapFailure:
                            self.mapFailure[manager] = listField
                        else:
                            listField = self.mapFailure[manager]
                        field_name = row[3]
                        listBit = []
                        if field_name not in listField:
                            listField[field_name] = listBit
                        else:
                            listBit = listField[field_name]
                        listBit.append( {header[i]: row[i] for i in range( len( row ) )} )
                    i += 1
                logger.info("Caricato Failure.csv {}".format(i))
        except Exception as e:
            logger.error(f"Errore Caricamento FAILURE.csv alla riga {i}", e)

    def initEnum(self):
        try:
            from config import enumCsvFile
            i = 0
            with open( enumCsvFile, newline='\r\n' ) as csvfile:
                reader = csv.reader( csvfile, delimiter='\t' )
                i = 0
                for row in reader:
                    if i == 0:
                        header = row  # MESSAGGIO	NOME_BIT	POSIZIONE	ENUM
                    else:
                        manager = row[0]  # nome_classe
                        listField = {}
                        obj=self.getManager(manager)
                        if obj is None:
                            logger.error(f"Errore Caricamento enum_udp non trovato manager {manager}")
                            continue
                        if manager not in self.mapEnum:
                            self.mapEnum[manager] = listField
                        else:
                            listField = self.mapEnum[manager]
                        if " " in row[1]:
                            field_name = row[1].lower().replace(" ","_")
                        else:
                            field_name=row[1]
                        if not hasattr(obj,field_name) and hasattr(obj,field_name.lower()):
                            field_name = field_name.lower()
                        
                        listValue = {"row": {header[i]: row[i] for i in range( len( row ) )}}
                        if field_name not in listField:
                            listField[field_name] = listValue
                        else:
                            listValue = listField[field_name]
                        if not hasattr(obj,field_name):
                            logger.error(f"Errore Caricamento enum_udp non trovato attributo {field_name} su manager {manager}")

                        enumList=row[3]
                        if "." in enumList:
                            values=row[3].split(".")
                        elif ";" in enumList:
                            values=row[3].split(";")
                        for v in values:
                            l=v.split(":")
                            if len(l)>1:
                                listValue[int(l[0])]=l[1]
                    i += 1
            logger.info("Caricato enum_udp.csv {}".format(i))
        except Exception as e:
            logger.error(f"Errore Caricamento enum_udp.csv alla riga {i}", e)

    def decodeValueEnum(self,obj,field_name,value):
        cls=obj.__class__.__name__
        if cls in self.mapEnum:
            if field_name in self.mapEnum[cls]:
                descr=self.mapEnum[cls][field_name].get(value)
                if descr is not None:
                    descr=str(value)+":"+str(descr)
                return descr or value
        return value
    
    @staticmethod
    def choices(obj,field_name):
        cls=obj.__class__.__name__
        mapEnum = decoder.mapEnum
        if cls in mapEnum:
            if field_name in mapEnum[cls]:
                return mapEnum[cls][field_name]
        return None

    def decodeValueFailure(self,cls,field_name,value):
        if cls in self.mapFailure:
            if field_name in self.mapFailure[cls]:
                listBit= self.mapFailure[cls][field_name]
                desc=""
                for i in range(len(listBit)):
                    """
                    if type(value)==int:
                        value=value
                    else:
                        value=value[0]
                    """
                    if type(value) in [int]:
                        if value&(1<<i):
                            desc+=listBit[i]["Descrizione"]+","
                    else:
                        desc=f"{value}"
                        break
                return desc
        return value

decoder=DecodeStruct()

class ActionManager:
    current_action_id=0
    mapMsgPending={}
    mapMsgReceived={}

    @staticmethod
    def NextActionId(obj_req,action_id):
        from manageFlask import sendMessageActionPending
        if action_id is None:
            ActionManager.current_action_id+=1
            obj_req.action_id=ActionManager.current_action_id
            ActionManager.mapMsgPending[ActionManager.current_action_id]=obj_req
        else:
            ActionManager.mapMsgPending[action_id] = obj_req
            ActionManager.current_action_id = action_id+1
        sendMessageActionPending( obj_req )
        return ActionManager.current_action_id,obj_req

    @staticmethod
    def AckObj(obj_resp):
        from manageFlask import sendMessageActionReceived
        try:
            action_id=None
            if hasattr(obj_resp,"action_id"):
                action_id=obj_resp.action_id
            elif hasattr(obj_resp,"reported_action_id"):
                action_id = obj_resp.reported_action_id
            if action_id is not None and action_id in ActionManager.mapMsgPending:
                obj_req=ActionManager.mapMsgPending[action_id]
                s="action_id" if hasattr(obj_resp,"action_id") else "reported_action_id"
                mapObj={s:action_id,"class_req":obj_req.__class__.__name__,"request":obj_req.values(), "response":obj_resp.values(), "readed":False}
                ActionManager.mapMsgReceived[action_id]=mapObj
                del ActionManager.mapMsgPending[action_id]
                sendMessageActionReceived(mapObj )
        except Exception as e:
            logger.error(f"Errore AckObj {obj_resp} ", e)
    @staticmethod
    def CleanObjResp():
        deleted=[]
        mapReaded={}
        for k,v in ActionManager.mapMsgReceived.items():
            cls=v["class_req"]
            if cls not in mapReaded:
                mapReaded[cls]=k
            else:
                deleted.append(mapReaded[cls])
                mapReaded[cls]=k
        for d in deleted:
            del ActionManager.mapMsgReceived[d]
