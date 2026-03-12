import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["FREEE_CLIENT_ID"]
CLIENT_SECRET = os.environ["FREEE_CLIENT_SECRET"]
REDIRECT_URI = os.environ["FREEE_REDIRECT_URI"]
CODE = os.environ["FREEE_CODE"]

url = "https://accounts.secure.freee.co.jp/public_api/token"

data = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "code": CODE
}

res = requests.post(url, data=data)

print(res.status_code)
print(res.json())