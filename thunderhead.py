from hashlib import new
from pydexcom import Dexcom
import sqlite3
import pandas as pd
import time
import http.client, urllib
from yeelight import Bulb

FIRSTWEIGHT = .25
SECONDWEIGHT = .25
THIRDWEIGHT = .50

PINK = [168, 50, 164] # No Blood sugar
RED = [255, 0 , 0] # Low
BLUE = [0,255,0] # High
WHITE = [0,0,0] # Normal

class ThunderHead: 
    # username = dexcom username
    # password = dexcom password
    # change = the threshold for change between concurrent blood glucose levels that you want to prompt an alert
    # low = the low threshold below which you want to be alerted
    def __init__(self, username: str, password: str, change, low, high):
        self.username = username
        self.password = password
        self.conn = None
        self.dexcom = None
        self.bgvs = []
        self.slopes = []
        self.change = change
        self.low = low
        self.high = high
        self.time_passed = 0
        self.bulb = None
        # Create new dexcom object
        self.create_objects()

    # Uses the pydexcom package to create a new dexcom object
    def create_objects(self):
        new_dexcom = Dexcom(self.username, self.password)
        self.dexcom = new_dexcom
        new_bulb = Bulb("192.168.1.64")
        self.bulb = new_bulb
        #self.set_up_database()

    # Uses the current dexcom object to get the current blood glucose
    def get_current_blood_sugar(self):
        bg = self.dexcom.get_current_glucose_reading()
        print(bg.value)

    # Uses the Pushover API to send a message
    def send_message(self, message = "DEFAULT MESSAGE", title = "Test"):
        print(message)
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": "a7hxahk94ajn8tyt5y13wnq4dwia1t",
            "user": "u39yretpf7kpu775jm8djwey42t8jh",
            "title": title,
            "message": f"{message}",
        }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()

    def change_bulb(self, val):
        try:
            if val == 'h':
                self.bulb.set_rgb(0,255,0)
            elif val == 'l':
                self.bulb.set_rgb(255, 0 , 0)
            elif val == 'n':
                self.bulb.set_rgb(255,255,255)
            elif val == 'm':
                self.bulb.set_rgb(168, 50, 164)
        except Exception as e:
            t = time.localtime()
            current_time = time.strftime("%H:%M:%S", t)
            error_str = f"ERROR: {e} TIME: {current_time}"

            print(error_str)

    def watch_efficient(self):
        self.send_message(message = "Starting (test) watch...", title = "ThunderHead Test")
        #Start infinite loop
        while True:
            bgvs = self.dexcom.get_glucose_readings(minutes=20, max_count=4)
            self.check_once(bgvs)
            quit(1)

    def check_once(self, bgvs):
        can_check = True
        for bg in bgvs:
            if bg == None:
                can_check = False

        if can_check:
            #self.print_bgvs(bgvs)
            data_1 = bgvs[3].value
            data_2 = bgvs[2].value
            data_3 = bgvs[1].value
            data_4 = bgvs[0].value

            first_slope = data_2 - data_1
            second_slope = data_3 - data_2 
            third_slope = data_4 - data_3
            average_slope = (first_slope * FIRSTWEIGHT) + (second_slope * SECONDWEIGHT) + (third_slope * THIRDWEIGHT)
            cur_bg = data_4
            self.check(cur_bg, average_slope)
        else:
            self.send_message("Insufficient data to run algorithm", title = "ALGORITHM ERROR")






    def print_bgvs(self, bgvs):
        n = 1
        for bg in bgvs:
            if bg is None:
                print(f"BG #{n} is Empty")
            else:
                print(f"BG #{n} is {bg.value}")   
            n = n + 1
        print()    
    

    # Gets a blood sugar reading every 5 minutes and checks to see if an alert is warranted
    def watch(self):
        self.send_message(message = "Starting (test) watch...", title = "ThunderHead Test")
        # reset stored blood glucose levels 
        self.bgvs = []
        # get the initial blood sugar reading
        initial_bg = self.dexcom.get_current_glucose_reading()
        if initial_bg is None:
            self.send_message("No Blood Glucose Value")
            self.bgvs.append(-99)
        else:
            initial_bg = initial_bg.value
            self.bgvs.append(initial_bg)
        # add the initial value to stored values
        ##self.bgvs.append(initial_bg)
        # wait 5 minutes
        time.sleep(300)
        while True:
            # get next blood glucose

            next_bg = self.dexcom.get_current_glucose_reading()
            if next_bg is None:
                self.send_message("No Blood Glucose Value")
                self.bgvs.append(-99)
                self.change_bulb('m')
                #self.calc_slopes()
                #time.sleep(300)
            else:
                next_bg = next_bg.value
                self.bgvs.append(next_bg)
                self.calc_slopes()
            # add next blood glucose to stored values
            ##self.bgvs.append(next_bg)
            #print(next_bg)
            # check if an alert is warranted
            ##self.send_update()
            # wait 5 minutes
            time.sleep(300)

    
    def check(self, current_bg, slope):
        predicted_bg = current_bg + (slope * 3)
        #past_bg = self.bgvs[len(self.bgvs) - 2]
        #print(f"Current Glucose: {current_bg} -> Predicted Glucose {predicted_bg}")
        if predicted_bg <= self.low:
            message = f"Current Glucose: {current_bg} \nPredicted Glucose (15mins): {predicted_bg}\nAverage Fall: {slope}"
            self.send_message(message=message, title= "LOW PREDICTED")
            self.change_bulb('l')
        elif predicted_bg >= self.high:
            message = f"Current Glucose: {current_bg} \nPredicted Glucose (15mins): {predicted_bg}\nAverage Rise: {slope}"
            self.send_message(message=message, title= "HIGH PREDICTED")
            self.change_bulb('h')
        else:
            self.change_bulb('n')


    # gets the current bg and old blood glucose to calculate change in order to potentially send an alert
    def calc_slopes(self):
        bg_len = len(self.bgvs)
        if bg_len < 4:
            self.send_message("Insufficient data to run algorithm", title = "ALGORITHM ERROR")
        else:
            data_1 = self.bgvs[bg_len - 4]
            data_2 = self.bgvs[bg_len - 3]
            data_3 = self.bgvs[bg_len - 2]
            data_4 = self.bgvs[bg_len - 1]
            if data_1 == -99 or data_2 == -99 or data_3 == -99 or data_4 == -99:
                message = f"Could not run predictive algorithm. One of these values ({data_1}, {data_2}, {data_3}, {data_4}) was -99"
                self.send_message(message = message, title = "ALGORITHM ERROR")
            else:
                first_slope = data_2 - data_1
                second_slope = data_3 - data_2 
                third_slope = data_4 - data_3
                average_slope = (first_slope * FIRSTWEIGHT) + (second_slope * SECONDWEIGHT) + (third_slope * THIRDWEIGHT)
                cur_bg = data_4
                self.check(cur_bg, average_slope)
