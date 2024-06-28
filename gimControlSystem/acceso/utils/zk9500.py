from pyzkfp import ZKFP2
from threading import Thread

class LectorHuellasZK9500:
    def __init__(self, access_sensor=1):
        self.access_sensor = access_sensor

        self.templates = []
        self.capture = None
        self.register = False
        self.fid = 1

        self.keep_alive = True

    def initialize_sensor(self):
        self.zkfp2 = ZKFP2()
        self.zkfp2.Init()
        self.zkfp2.OpenDevice(self.access_sensor)
        self.zkfp2.Light("green")
    
    def initialize_DB(self):
        self.zkfp2.DBInit()
    
    def add_member_DB(self, member_id, template):
        self.zkfp2.DBAdd(member_id, template)

    def identify_member_DB(self, template):
        fid, score = self.zkfp2.DBIdentify(template)

        if fid:
            return fid
        else:
            return None
