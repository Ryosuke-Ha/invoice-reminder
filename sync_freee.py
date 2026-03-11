import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

FREEE_ACCESS_TOKEN = os.environ["FREEE_ACCESS_TOKEN"]
FREEE_COMPANY_ID = int(os.environ["FREEE_COMPANY_ID"])
FREEE_WALLETABLE_ID = int(os.environ["FREEE_WALLETABLE_ID"])
FREEE_ACCOUNT_ITEM_ID = int(os.environ["FREEE_ACCOUNT_ITEM_ID"])
FREEE_TAX_CODE = int(os.environ["FREEE_TAX_CODE"])

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
                {"property": "Paid At", "date": {"is_not_empty": True}},
                {"property": "freee Deal ID", "rich_text": {"is_empty": True}}
            ]
        }
    }
    res = requests.post(url, headers=headers, json=payload, timeout=30)
    res.raise_for_status()
    return res.json()["results"]

def get_title(page):
    items = page["properties"]["Title"]["title"]
    return "".join([x["plain_text"] for x in items]) if items else "(no title)"

def get_amount(page):
    return int(page["properties"]["Amount"]["number"] or 0)

def get_paid_at(page):
    value = page["properties"]["Paid At"]["date"]
    if not value:
        return None
    return datetime.fromisoformat(value["start"]).date().isoformat()

def create_freee_deal(title, amount, paid_at):
    url = "https://api.freee.co.jp/api/1/deals"
    headers = {
        "Authorization": f"Bearer {FREEE_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "company_id": FREEE_COMPANY_ID,
        "issue_date": paid_at,
        "type": "expense",
        "details": [
            {
                "account_item_id": FREEE_ACCOUNT_ITEM_ID,
                "tax_code": FREEE_TAX_CODE,
                "amount": amount,
                "description": title
            }
        ],
        "payments": [
            {
                "date": paid_at,
                "from_walletable_type": "wallet",
                "from_walletable_id": FREEE_WALLETABLE_ID,
                "amount": amount
            }
        ]
    }
    
    print("=== freee payload ===")
    print(payload)

    res = requests.post(url, headers=headers, json=payload, timeout=30)

    print("=== freee status ===")
    print(res.status_code)
    print("=== freee response ===")
    print(res.text)

    res.raise_for_status()
    return res.json()

def update_notion(page_id, deal_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": {
            "freee Deal ID": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": str(deal_id)}
                    }
                ]
            },
            "freee Sync Status": {
                "select": {"name": "done"}
            }
        }
    }
    res = requests.patch(url, headers=headers, json=payload, timeout=30)
    res.raise_for_status()

def update_error(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    payload = {
        "properties": {
            "freee Sync Status": {
                "select": {"name": "error"}
            }
        }
    }
    res = requests.patch(url, headers=headers, json=payload, timeout=30)
    res.raise_for_status()

def main():
    pages = query_notion()

    for page in pages:
        title = get_title(page)
        amount = get_amount(page)
        paid_at = get_paid_at(page)

        if not paid_at or amount <= 0:
            continue

        try:
            result = create_freee_deal(title, amount, paid_at)

            deal_id = result.get("deal", {}).get("id")
            if not deal_id:
                deal_id = result.get("id")

            if not deal_id:
                raise Exception(f"deal_id not found: {result}")

            update_notion(page["id"], deal_id)

        except Exception as e:
            print("freee sync error:", e)
            update_error(page["id"])

if __name__ == "__main__":
    main()