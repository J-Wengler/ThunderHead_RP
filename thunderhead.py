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
    def __init__(self, username: str, password: str, change, low):
        self.username = username
        self.password = password
        self.conn = None
        self.dexcom = None
        self.bgvs = []
        self.slopes = []
        self.change = change
        self.low = low
        self.time_passed = 0
        # Create new dexcom object
        self.create_dexcom()

    # Uses the pydexcom package to create a new dexcom object
    def create_dexcom(self):
        new_dexcom = Dexcom(self.username, self.password)
        self.dexcom = new_dexcom
        #self.set_up_database()

    # Uses the current dexcom object to get the current blood glucose
    def get_current_blood_sugar(self):
        bg = self.dexcom.get_current_glucose_reading()
        print(bg.value)

    # Uses the Pushover API to send a message
    def send_message(self, message = "DEFAULT MESSAGE", title = "Thunderhead Notification"):
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": "a7hxahk94ajn8tyt5y13wnq4dwia1t",
            "user": "u39yretpf7kpu775jm8djwey42t8jh",
            "title": title,
            "message": f"{message}",
        }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()

    # Gets a blood sugar reading every 5 minutes and checks to see if an alert is warranted
    def watch(self):
        self.send_message(message = "Starting watch...", title = "ThunderHead Notification")
        # reset stored blood glucose levels 
        self.bgvs = []
        # get the initial blood sugar reading
        initial_bg = self.dexcom.get_current_glucose_reading()
        if initial_bg is None:
            self.send_message("No Blood Glucose Value")
            time.sleep(300)
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
                time.sleep(300)
            else:
                next_bg = next_bg.value
                self.bgvs.append(next_bg)
                self.send_update()
            # add next blood glucose to stored values
            ##self.bgvs.append(next_bg)
            #print(next_bg)
            # check if an alert is warranted
            ##self.send_update()
            # wait 5 minutes
            time.sleep(300)

    # checks if a change or low warrants an alert
    # this is where the heart of the dynamic monitoring will occur
    # I need to whiteboard the situations in which I want the alerts to happen
    # the goal is to have code that can monitor blood sugar and dynamically alter it's threshold 
    def check(self, bg, change):
        if bg <= self.low or change <= self.change:
            return True
        if change > -10 and change < 0:
            estimated_change = change * 3
            estimated_bg = bg + estimated_change
            if estimated_bg <= self.low:
                return True
            else:
                return False 
        if change < -10:
            estimated_change = change * 4
            estimated_bg = bg + estimated_change
            if estimated_bg <= self.low:
                return True
            else:
                return False
        return False
            
    def make_message(self):
        bg_len = len(self.bgvs)
        slope_len = len(self.slopes)
        cur_slope = self.slopes[slope_len - 1]
        old_slope = self.slopes[slope_len - 2]
        # new bg
        cur_bg = self.bgvs[bg_len - 1]
        # old bg
        old_bg = self.bgvs[bg_len - 2]
        estimated_bg = cur_bg + cur_slope
        old_estimation = old_bg + old_slope
        change_in_slope = cur_slope - old_slope
        message = f"Blood Glucose: {cur_bg} (estimated to be {estimated_bg} in 5 minutes)\nCurrent Change: {cur_slope} \n Slope Trend: {change_in_slope} \n Current sugar ({cur_bg}) was estimated to be {old_estimation}"
        return message
        

    # gets the current bg and old blood glucose to calculate change in order to potentially send an alert
    def send_update(self):
        bg_len = len(self.bgvs)
        # current bg
        new_bg = self.bgvs[bg_len - 1]
        # old bg
        old_bg = self.bgvs[bg_len - 2]
        # Sets sign="+" if the change is positive and "-" if negative
        # if sign="#" then something has happened that I did not anticipate
        # sign = "#"
        # if new_bg >= old_bg:
        #     sign = "+"
        # else:
        #     sign = "-"
        change = new_bg - old_bg
        self.slopes.append(change)
        if self.time_passed < 60:
            self.time_passed += 5
        else:
            self.send_message("ThunderHead is still active")
            self.time_passed = 0
        # checks to see if the change or current bg warrant an alert
        # the else statement is just to debug so you get an alert everytime regardless
        if self.check(new_bg, change):
            message = self.make_message()
            print(message)
            print()
            self.send_message(message, "LOW ANTICIPATED")
        # else:
        #     message = self.make_message()
        #     print(message)
        #     print()
        #     self.send_message(message)
        
    # Not working yet
    # Potential plan is to create a database to get a summary notification each day
    # Talk to mom about how best to set up the database
    def set_up_database(self):
        #FIXME
        conn = sqlite3.connect('dexcom_database') 
        self.conn = conn
        c = self.conn.cursor()
        #FIXME
        # The below command needs to be changed to create the proper database
        c.execute('''
          CREATE TABLE IF NOT EXISTS dexcom
          ([product_id] INTEGER PRIMARY KEY, [product_name] TEXT)
          ''')
        #c.execute(''' DROP TABLE bgv''')
        
