from thunderhead import ThunderHead
import http.client, urllib
from yeelight import Bulb

# BULB TESTING
#new_bulb = Bulb("BULB_IP")
#new_bulb.turn_off()
#new_bulb.turn_on()
thunder = ThunderHead("DEXCOMUSER", "DEXCOMPASS", change = -30, low = 60, high = 275)
try:
    thunder.watch_efficient()
except Exception as e:
    print(e)
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": "PUSHOVERTOKEN",
        "user": "PUSHOVERUSER",
        "title": "ThunderHead Issue",
        "message": f"TEST SERVER FAILED WITH ERROR: {e}",
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()
