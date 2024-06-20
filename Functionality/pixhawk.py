import socket
import time

from MAVProxy.modules.lib import mp_module

class suav_location(mp_module.MPModule):
    def __init__(self, mpstate):
        """Initialise module"""
        super(suav_location, self).__init__(mpstate, "suav_location", "SUAV location extraction")
        self.emit_interval = 0.1
        self.last_emitted = time.time()
        self.sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

        self.lat = 0
        self.lon = 0
        self.rel_alt = 0
        self.alt = 0

        self.pitch = 0
        self.yaw = 0
        self.roll = 0

        self.dlat = 0
        self.dlon = 0
        self.dalt = 0
        self.heading = 0

    def idle_task(self):
        '''called rapidly by mavproxy'''
        now = time.time()
        if now-self.last_emitted > self.emit_interval:
            self.last_emitted = now

            if self.lat != 0:
                #print("Current GPS Position: Lat={}, Lon={}, Relative Alt={}m".format(self.lat, self.lon, self.rel_alt))
                #print("Current Attitude: Roll={}, Pitch={}, Yaw={}".format(self.roll, self.pitch, self.yaw))
                self.send_data()

    def mavlink_packet(self, m):
        '''handle mavlink packets'''
        if self.settings.target_system == 0 or self.settings.target_system == m.get_srcSystem():
            if m.get_type() == 'GLOBAL_POSITION_INT':
                (lat, lon, alt, relative_alt, dlat, dlon, dalt, heading) = (m.lat*1.0e-7, m.lon*1.0e-7, m.alt/1000,
                                                                            m.relative_alt/1000, m.vx/100, m.vy/100, m.vz/100, m.hdg/100)
                self.lat = lat
                self.lon = lon
                self.alt = alt
                self.rel_alt = relative_alt
                self.dlat = dlat
                self.dlon = dlon
                self.dalt = dalt
                self.heading = heading
            elif m.get_type() == 'ATTITUDE':
                (roll, pitch, yaw) = (m.roll, m.pitch, m.yaw)
                self.roll = roll
                self.pitch = pitch
                self.yaw = yaw

    def send_data(self):
        t = time.time()
        # send to 5005 for image labeller
        image_data = (t, self.lon, self.lat, self.rel_alt, self.alt, self.roll, self.pitch, self.yaw, self.dlat, self.dlon, self.dalt, self.heading)
        image_message = f"{image_data}".encode()
        self.sock.sendto(image_message, ("127.0.0.1", 5005))

        # send to 5007 for drop system
        # items = [self.lon, self.lat, self.rel_alt, self.dlat, self.dlon, self.dalt, self.heading, t]
        # self.sock.sendto(self.encode_message(items), ("127.0.0.1", 5007))

    def encode_message(self, items):
        message = ""
        for index, item in enumerate(items):
            message += str(item)
            if index != len(items) - 1:
                message += ","
        return message.encode()

def init(mpstate):
    '''initialise module'''
    return suav_location(mpstate)