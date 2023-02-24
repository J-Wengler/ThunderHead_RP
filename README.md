# ThunderHead_RP
Implementation of the ThunderHead algorithm for use in a headless raspberry pi environment combined with the pushover API. 

To run, clone the repo onto your raspberry pi, and edit main.py with your dexcom username/password and Pushover Token/User values. Then run "python3 main.py" in the main folder. I suggest using the linux screen utility to ensure the code runs in the background.

To connect a yeelight bulb, change the BULB_IP variable to reflect the IP of your specific bulb. MAKE SURE LAN CONTROL IS ENABLED IN THE YEELIGHT APP. I suggest setting the bulb up manually using the yeelight app becuase it will allow you to set up LAN Control easily. 
