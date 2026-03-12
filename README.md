# Invoice Reminder & freee Sync

Notionで管理している請求・支払い情報を元に

- 未払いのリマインド通知
- 支払い済みのfreee自動登録

を行う自動化ツールです。

GitHub Actionsで定期実行されます。

---

# 全体構成

```
Notion DB
   ↓
GitHub Actions
   ↓
Python Script

① reminder.py
未払いリマインド通知

② sync_freee.py
支払い済みデータを freee に登録
```

---

# 機能

## 未払いリマインド

Notion DB を確認し

```
Status = OPEN
Reminder Sent = false
Due Date ≤ today + 3
```

の条件のものを Slack に通知します。

通知後

```
Reminder Sent = true
```

に更新します。

---

## freee連携

Notion DB を確認し

```
Status = PAID
freee Deal ID = empty
```

のものを freee API に登録します。

登録成功後

```
freee Deal ID
freee Sync Status = done
```

を Notion に更新します。

---

# Notion Database

最低限必要なカラム

| Property | Type | 用途 |
|--------|------|------|
| Title | Title | 請求名 |
| Amount | Number | 金額 |
| Due Date | Date | 支払期限 |
| Paid At | Date | 支払日 |
| Status | Status | OPEN / PAID |
| Reminder Sent | Checkbox | 通知済みフラグ |
| freee Deal ID | Text | freee登録ID |
| freee Sync Status | Status | sync結果 |

---

# 使用技術

| 技術 | 用途 |
|----|----|
| Python | スクリプト |
| Notion API | DB取得 / 更新 |
| freee API | 会計登録 |
| Slack Webhook | 通知 |
| GitHub Actions | 定期実行 |
| PyNaCl | GitHub Secret更新 |

---

# ディレクトリ構成

```
invoice-reminder
│
├ reminder.py
├ sync_freee.py
├ get_freee_token.py
├ requirements.txt
│
└ .github
    └ workflows
        ├ reminder.yml
        └ sync_freee.yml
```

---

# セットアップ

## 1. clone

```bash
git clone https://github.com/<user>/invoice-reminder.git
cd invoice-reminder
```

---

## 2. Python環境

```bash
pip install -r requirements.txt
```

---

## 3. .env 作成

```bash
touch .env
```

.env に以下を設定

```env
NOTION_TOKEN=
NOTION_DATABASE_ID=

FREEE_CLIENT_ID=
FREEE_CLIENT_SECRET=
FREEE_REFRESH_TOKEN=

FREEE_COMPANY_ID=
FREEE_WALLETABLE_ID=
FREEE_WALLETABLE_TYPE=
FREEE_ACCOUNT_ITEM_ID=
FREEE_TAX_CODE=

GH_REPO_OWNER=
GH_REPO_NAME=
GH_SECRET_PAT=

SLACK_WEBHOOK_URL=
```

---

# freee 初期設定

初回のみ実行

```bash
python get_freee_token.py
```

実行して `refresh_token` を取得し `.env` または GitHub Secrets に保存します。

※通常運用ではこのスクリプトは使用しません。

---

# GitHub Secrets

GitHub

```
Settings
↓
Secrets and variables
↓
Actions
```

に以下を登録

```
NOTION_TOKEN
NOTION_DATABASE_ID

FREEE_CLIENT_ID
FREEE_CLIENT_SECRET
FREEE_REFRESH_TOKEN

FREEE_COMPANY_ID
FREEE_WALLETABLE_ID
FREEE_WALLETABLE_TYPE
FREEE_ACCOUNT_ITEM_ID
FREEE_TAX_CODE

GH_REPO_OWNER
GH_REPO_NAME
GH_SECRET_PAT

SLACK_WEBHOOK_URL
```

---

# GitHub Actions

## reminder.yml

未払い通知

```
毎日実行
```

---

## sync_freee.yml

freee連携

```
毎時実行
```

処理フロー

```
Notion確認
↓
対象なし → 終了
↓
対象あり → freee token refresh
↓
freee登録
↓
Notion更新
↓
refresh token 更新
↓
GitHub Secret 更新
```

---

# ローカル実行

## reminder

```bash
python reminder.py
```

## freee sync

```bash
python sync_freee.py
```

---

# トラブルシューティング

## freee token error

```
invalid_grant
```

原因

- refresh_token失効
- redirect URI mismatch

対処

```bash
python get_freee_token.py
```

---

## GitHub Secret更新エラー

```
401 Bad credentials
```

確認

- GH_SECRET_PAT
- Secrets write permission

---

# 今後の改善案

- Slack通知のBlockKit化
- freee登録失敗の再試行
- logging導入
- エラーレポート
- Notion webhook対応