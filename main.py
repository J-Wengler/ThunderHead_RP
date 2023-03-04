from thunderhead import ThunderHead
import http.client, urllib

thunder = ThunderHead("DEXCOMUSER", "DEXCOMPASS", low = 60, high = 260)
try:
    thunder.watch()
except Exception as e:
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": "PUSHOVERTOKER",
        "user": "PUSHOVERUSER",
        "title": "ThunderHead_RP Server Issue",
        "message": f"Failed with error -> {e}",
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()
