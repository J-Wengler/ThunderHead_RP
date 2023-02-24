from thunderhead import ThunderHead
import http.client, urllib

thunder = ThunderHead("DEXCOMUSER", "DEXCOMPASS", change = -30, low = 60)
try:
    thunder.watch()
except Exception as e:
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": "PUSHOVERTOKEN",
        "user": "PUSHOVERUSER",
        "title": "ThunderHead Issue",
        "message": f"{e}",
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()
