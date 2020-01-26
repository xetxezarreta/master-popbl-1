from . import Session
from .models import Log


class BusinessLogic:
    __instance = None

    @staticmethod
    def getInstance():
        if BusinessLogic.__instance == None:
            BusinessLogic()
        return BusinessLogic.__instance

    def __init__(self):
        if BusinessLogic.__instance != None:
            raise Exception("This class is a singleton")
        else:
            BusinessLogic.__instance = self

    def get_logs(self):
        session = Session()
        logs = session.query(Log).all()
        session.close()
        return Log.list_as_dict(logs)

    def add_log(self,timestamp,level,service_name,msg):
        session = Session()
        new_log = Log(timestamp=timestamp,level=level,service_name=service_name,msg=msg)
        session.add(new_log)
        session.commit()
        session.close()
        return True
    
