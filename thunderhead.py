from hashlib import new
from pydexcom import Dexcom
import sqlite3
import pandas as pd
import time
import http.client, urllib

class ThunderHead: 
    # username = dexcom username
    # password = dexcom password
    # change = the threshold for change between concurrent blood glucose levels that you want to prompt an alert
    # low = the low threshold below which you want to be alerted
    def __init__(self, username: str, password: str, low, high):
        self.username = username
        self.password = password
        self.conn = None
        self.dexcom = None
        self.bgvs = []
        self.slopes = []
        self.low = low
        self.high = high
        self.time_passed = 0
        self.fw = .25
        self.sw = .25
        self.tw = .50
        # Create new dexcom object
        self.create_dexcom()

    # Uses the pydexcom package to create a new dexcom object
    def create_dexcom(self):
        new_dexcom = Dexcom(self.username, self.password)
        self.dexcom = new_dexcom
        #self.set_up_database()

    # Uses the Pushover API to send a message
    def send_message(self, message = "DEFAULT MESSAGE", title = "Thunderhead Notification"):
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": "PUSHOVERTOKER",
            "user": "PUSHOVERUSER",
            "title": title,
            "message": f"{message}",
        }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()

    # Gets a blood sugar reading every 5 minutes and checks to see if an alert is warranted
    def watch(self):
        self.send_message(message = "ThunderHead_RP Server Started", title = "ThunderHead_RP Notification")
        time_passed = 0
        while True:
            self.check()
            time.sleep(300)
            time_passed = time_passed + 5
            if time_passed >= 180:
                self.send_message("ThunderHead_RP is running", title="ThunderHead_RP Status")
                time_passed = 0

    def check(self):
        bgvs = self.dexcom.get_glucose_readings(minutes=20, max_count= 4)
        if len(bgvs) < 4:
            self.send_message("Can't get 4 data points", title = "Algorithm Error")
        if self.check_bgvs(bgvs):
            #Check the bg
            self.calc_slopes(bgvs)
        else:
            bg_string = []
            for bg in bgvs:
                if bg == None:
                    bg_string.append("Missing")
                else:
                    bg.append(str(bg.value))
            to_return = f"No continous data: {bg_string}"
            self.send_message(to_return, title = "Algorithm Error")
        
    def check_bgvs(self, bgvs):
        can_check = True
        for bg in bgvs:
            if bg == None:
                can_check = False
        return can_check

    def calc_slopes(self, bgvs):
        data_1 = bgvs[3].value
        data_2 = bgvs[2].value
        data_3 = bgvs[1].value
        data_4 = bgvs[0].value

        first_slope = data_2 - data_1
        second_slope = data_3 - data_2 
        third_slope = data_4 - data_3
        # Calculate the weighted average of the three slopes
        average_slope = (first_slope * self.fw) + (second_slope * self.sw) + (third_slope * self.tw)
        last_bg = data_3
        cur_bg = data_4
        self.evaluate_threshold(cur_bg, last_bg, average_slope)

    def evaluate_threshold(self, cur_bg, last_bg, slope):
        pred_bg = cur_bg + (slope * 3)
        if pred_bg <= self.low:
            message_str = f"Current bg: {cur_bg}\nPredicted bg: {pred_bg}\nLast bg: {last_bg}\nWeighted Fall: {slope}"
            print(message_str) 
            self.send_message(message=message_str, title="LOW ALERT")
        elif pred_bg >= self.high:
            message_str = f"Current bg: {cur_bg}\nPredicted bg: {pred_bg}\nLast bg: {last_bg}\nWeighted Rise: {slope}"
            print(message_str) 
            self.send_message(message=message_str, title="HIGH ALERT")
        else:
            print(f"Stable BG ({cur_bg})")