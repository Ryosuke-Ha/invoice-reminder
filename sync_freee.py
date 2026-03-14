import os
import base64
from datetime import datetime

import requests
from nacl import encoding, public
from dotenv import load_dotenv

load_dotenv()

# ----------------------------
# Env
# ----------------------------
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

FREEE_CLIENT_ID = os.environ["FREEE_CLIENT_ID"]
FREEE_CLIENT_SECRET = os.environ["FREEE_CLIENT_SECRET"]
FREEE_REFRESH_TOKEN = os.environ["FREEE_REFRESH_TOKEN"]

FREEE_WALLETABLE_ID = int(os.environ["FREEE_WALLETABLE_ID"])
FREEE_WALLETABLE_TYPE = os.environ["FREEE_WALLETABLE_TYPE"]

GH_REPO_OWNER = os.environ["GH_REPO_OWNER"]
GH_REPO_NAME = os.environ["GH_REPO_NAME"]
GH_SECRET_PAT = os.environ["GH_SECRET_PAT"]

NOTION_VERSION = "2022-06-28"

# ----------------------------
# Notion helpers
# ----------------------------
def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

def query_notion():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Status", "status": {"equals": "PAID"}},
                {"property": "freee Deal ID", "rich_text": {"is_empty": True}},
            ]
        }
    }
    res = requests.post(url, headers=notion_headers(), json=payload, timeout=30)
    print("notion query status:", res.status_code)
    print("notion query body:", res.text[:1000])
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

def get_freee_company_id(page):
    return int(page["properties"]["freee Company ID"]["number"] or 0)

def get_freee_account_item_id(page):
    return int(page["properties"]["freee Account Item ID"]["number"] or 0)

def get_freee_tax_code(page):
    return int(page["properties"]["freee Tax Code"]["number"] or 0)

def update_success(page_id, deal_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
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
    res = requests.patch(url, headers=notion_headers(), json=payload, timeout=30)
    print("notion success update:", res.status_code, res.text[:500])
    res.raise_for_status()

def update_error(page_id, error_message):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "freee Sync Status": {
                "select": {"name": "error"}
            }
        }
    }

    # Error Message列がある場合だけ使う想定
    if error_message:
        payload["properties"]["Error Message"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": error_message[:1800]}
                }
            ]
        }

    res = requests.patch(url, headers=notion_headers(), json=payload, timeout=30)
    print("notion error update:", res.status_code, res.text[:500])
    res.raise_for_status()

# ----------------------------
# freee token refresh
# ----------------------------
def refresh_freee_token():
    url = "https://accounts.secure.freee.co.jp/public_api/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": FREEE_CLIENT_ID,
        "client_secret": FREEE_CLIENT_SECRET,
        "refresh_token": FREEE_REFRESH_TOKEN,
    }
    res = requests.post(url, data=data, timeout=30)
    print("freee token refresh status:", res.status_code)
    print("freee token refresh body:", res.text[:1000])
    res.raise_for_status()

    data = res.json()
    access_token = data["access_token"]
    new_refresh_token = data["refresh_token"]
    return access_token, new_refresh_token

# ----------------------------
# GitHub secret update
# ----------------------------
def github_headers():
    return {
        "Authorization": f"Bearer {GH_SECRET_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def get_repo_public_key():
    url = f"https://api.github.com/repos/{GH_REPO_OWNER}/{GH_REPO_NAME}/actions/secrets/public-key"
    res = requests.get(url, headers=github_headers(), timeout=30)
    print("github public key status:", res.status_code)
    print("github public key body:", res.text[:500])
    res.raise_for_status()
    return res.json()

def encrypt_secret(public_key_str, secret_value):
    public_key_obj = public.PublicKey(
        public_key_str.encode("utf-8"),
        encoding.Base64Encoder()
    )
    sealed_box = public.SealedBox(public_key_obj)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def update_github_secret(secret_name, secret_value):
    key_info = get_repo_public_key()
    encrypted_value = encrypt_secret(key_info["key"], secret_value)

    url = f"https://api.github.com/repos/{GH_REPO_OWNER}/{GH_REPO_NAME}/actions/secrets/{secret_name}"
    payload = {
        "encrypted_value": encrypted_value,
        "key_id": key_info["key_id"]
    }
    res = requests.put(url, headers=github_headers(), json=payload, timeout=30)
    print(f"github secret update [{secret_name}] status:", res.status_code)
    print(f"github secret update [{secret_name}] body:", res.text[:500])
    res.raise_for_status()

# ----------------------------
# freee deal
# ----------------------------
def create_freee_deal(access_token, title, amount, paid_at, company_id, account_item_id, tax_code):
    url = "https://api.freee.co.jp/api/1/deals"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "company_id": company_id,
        "issue_date": paid_at,
        "type": "expense",
        "details": [
            {
                "account_item_id": account_item_id,
                "tax_code": tax_code,
                "amount": amount,
                "description": title,
            }
        ],
        "payments": [
            {
                "date": paid_at,
                "from_walletable_type": FREEE_WALLETABLE_TYPE,
                "from_walletable_id": FREEE_WALLETABLE_ID,
                "amount": amount,
            }
        ]
    }

    print("=== freee payload ===")
    print(payload)

    res = requests.post(url, headers=headers, json=payload, timeout=30)
    print("=== freee status ===")
    print(res.status_code)
    print("=== freee response ===")
    print(res.text[:2000])
    res.raise_for_status()
    return res.json()

# ----------------------------
# main
# ----------------------------
def main():
    # 1. 先にNotionから対象取得
    pages = query_notion()
    print("pages:", len(pages))

    # 2. 対象がなければ終了
    if len(pages) == 0:
        print("No target pages. Skip freee token refresh.")
        return

    # 3. 対象がある時だけトークン更新
    access_token, new_refresh_token = refresh_freee_token()

    # 4. refresh token を GitHub Secrets に保存
    update_github_secret("FREEE_REFRESH_TOKEN", new_refresh_token)

    # 5. freee連携
    for page in pages:
        title = get_title(page)
        amount = get_amount(page)
        paid_at = get_paid_at(page)

        company_id = get_freee_company_id(page)
        account_item_id = get_freee_account_item_id(page)
        tax_code = get_freee_tax_code(page)

        if not paid_at or amount <= 0:
            print("skip invalid row:", title, paid_at, amount)
            continue

        if company_id <= 0 or account_item_id <= 0:
            print("skip invalid freee master:", title, company_id, account_item_id, tax_code)
            update_error(page["id"], "Missing freee Company ID or freee Account Item ID")
            continue

        try:
            result = create_freee_deal(
                access_token=access_token,
                title=title,
                amount=amount,
                paid_at=paid_at,
                company_id=company_id,
                account_item_id=account_item_id,
                tax_code=tax_code,
            )

            deal_id = result.get("deal", {}).get("id") or result.get("id")
            if not deal_id:
                raise Exception(f"deal_id not found: {result}")

            update_success(page["id"], deal_id)
            print(f"done: {title} -> deal_id={deal_id}")

        except Exception as e:
            print("freee sync error:", str(e))
            update_error(page["id"], str(e))

if __name__ == "__main__":
    main()