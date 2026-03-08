import os
import requests
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

def query_notion():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    payload = {
        "filter": {
            "and": [
                {"property": "Paid At", "date": {"is_empty": True}},
                {"property": "Reminder Sent", "checkbox": {"equals": False}}
            ]
        }
    }
    res = requests.post(url, headers=headers, json=payload, timeout=30)
    res.raise_for_status()
    return res.json()["results"]

def get_title(page):
    return "".join([x["plain_text"] for x in page["properties"]["Title"]["title"]])

def get_due_date(page):
    value = page["properties"]["Due Date"]["date"]
    if not value:
        return None
    return datetime.fromisoformat(value["start"]).date()

def get_amount(page):
    return page["properties"]["Amount"]["number"]

def send_slack(text):
    res = requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    res.raise_for_status()

def update_reminded(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": {
            "Reminder Sent": {"checkbox": True},
            "Reminded At": {"date": {"start": datetime.now().isoformat()}}
        }
    }
    res = requests.patch(url, headers=headers, json=payload, timeout=30)
    res.raise_for_status()

def main():
    today = date.today()
    pages = query_notion()

    for page in pages:
        due_date = get_due_date(page)
        if not due_date:
            continue

        diff = (due_date - today).days
        if diff not in [2, 3]:
            continue

        title = get_title(page)
        amount = get_amount(page)

        text = f"⚠️ 支払期限リマインド\n{title}\n期限: {due_date}\n残り: {diff}日\n金額: {amount}"
        send_slack(text)
        update_reminded(page["id"])

if __name__ == "__main__":
    main()