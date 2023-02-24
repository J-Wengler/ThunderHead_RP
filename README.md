# ThunderHead_RP
Implementation of the ThunderHead algorithm for use in a headless raspberry pi environment combined with the pushover API. 

To run, clone the repo onto your raspberry pi, and edit main.py with your dexcom username/password and Pushover Token/User values. Then run "python3 main.py" in the main folder. I suggest using the linux screen utility to ensure the code runs in the background.

FIXME:
 1. Change to reflect the current ThunderHead algorithm (no data storage, pulls 4 bgvs every 5 mins)
