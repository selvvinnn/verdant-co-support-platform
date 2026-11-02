import hashlib
import hmac
import json
import urllib.request
import urllib.error

SECRET = b"verdant-demo-secret-2026"

payload = {
    "event_id": "evt_absdkjadsa23",
    "type": "message.received",
    "brand_id": "verdant-co",
    "timestamp": "2026-11-03T10:15:22Z",
    "customer": {
        "id": "cust_1042",
        "name": "Aisha Khan",
        "phone": "+919800000001",
    },
    "message": {
        "id": "msg_812371893",
        "type": "text",
        "text": (
            "Hi, my order #44233 hasn't arrived yet. "
            "Can I change the delivery address?"
        ),
    },
}

raw_body = json.dumps(
    payload,
    separators=(",", ":"),
).encode("utf-8")

digest = hmac.new(
    SECRET,
    raw_body,
    hashlib.sha256,
).hexdigest()

request = urllib.request.Request(
    "http://127.0.0.1:8000/webhooks/messages",
    data=raw_body,
    headers={
        "Content-Type": "application/json",
        "X-Signature": f"sha256={digest}",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request) as response:
        print("HTTP:", response.status)
        print("Response:", response.read().decode())

except urllib.error.HTTPError as error:
    print("HTTP:", error.code)
    print("Response:", error.read().decode())