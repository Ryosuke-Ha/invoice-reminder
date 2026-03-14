# Invoice Reminder & freee Sync

An automation tool that uses invoice/payment information managed in Notion to:

- Send reminders for unpaid invoices
- Automatically register paid transactions in freee

The workflows run periodically using GitHub Actions.

---

# Architecture

```
Notion DB
   ↓
GitHub Actions
   ↓
Python Scripts

① reminder.py
Send reminders for unpaid invoices

② sync_freee.py
Register paid transactions to freee
```

---

# Features

## Unpaid Invoice Reminder

The system checks the Notion database and sends a Slack notification when:

```
Status = OPEN
Due Date ≤ today + 3
```

After sending the notification, the following field is updated:

```
Reminder Sent = true
```

---

## freee Integration

The system checks the Notion database and registers records to the freee API when:

```
Status = PAID
freee Deal ID = empty
```

After successful registration:

```
freee Deal ID
freee Sync Status = done
```

are updated in Notion.

---

# Notion Database

Minimum required properties:

| Property | Type | Purpose |
|--------|------|------|
| Title | Title | Invoice title |
| Amount | Number | Amount |
| Due Date | Date | Payment due date |
| Paid At | Date | Payment date |
| Status | Status | OPEN / PAID |
| Reminder Sent | Checkbox | Reminder flag |
| freee Deal ID | Text | freee transaction ID |
| freee Sync Status | Status | Sync result |
| freee Company ID | Number | ID |
| freee Acccount Item ID | Number | ID |
| freee Tax Code | Number | Code |

---

# Technologies

| Technology | Purpose |
|----|----|
| Python | Automation scripts |
| Notion API | Fetch and update database records |
| freee API | Register accounting transactions |
| Slack Webhook | Notifications |
| GitHub Actions | Scheduled execution |
| PyNaCl | GitHub secret encryption |

---

# Directory Structure

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

# Setup

## 1. Clone repository

```bash
git clone https://github.com/<user>/invoice-reminder.git
cd invoice-reminder
```

---

## 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Create `.env`

```bash
touch .env
```

Add the following configuration:

```env
NOTION_TOKEN=
NOTION_DATABASE_ID=

FREEE_CLIENT_ID=
FREEE_CLIENT_SECRET=
FREEE_REFRESH_TOKEN=

FREEE_WALLETABLE_ID=
FREEE_WALLETABLE_TYPE=

GH_REPO_OWNER=
GH_REPO_NAME=
GH_SECRET_PAT=

SLACK_WEBHOOK_URL=
```

---

# freee Initial Setup

Run this **only once** during the initial setup:

```bash
python get_freee_token.py
```

This script retrieves a `refresh_token`.

Store the token in `.env` or GitHub Secrets.

This script is **not required during normal operation**.

---

# GitHub Secrets

In GitHub:

```
Settings
↓
Secrets and variables
↓
Actions
```

Register the following secrets:

```
NOTION_TOKEN
NOTION_DATABASE_ID

FREEE_CLIENT_ID
FREEE_CLIENT_SECRET
FREEE_REFRESH_TOKEN

FREEE_WALLETABLE_ID
FREEE_WALLETABLE_TYPE

GH_REPO_OWNER
GH_REPO_NAME
GH_SECRET_PAT

SLACK_WEBHOOK_URL
```

---

# GitHub Actions

## reminder.yml

Handles unpaid invoice reminders.

```
Runs daily
```

---

## sync_freee.yml

Handles freee synchronization.

```
Runs daily
```

Processing flow:

```
Check Notion
↓
No target → exit
↓
Target exists → refresh freee token
↓
Register transaction in freee
↓
Update Notion
↓
Update refresh token
↓
Update GitHub Secret
```

---

# Local Execution

## Run reminder

```bash
python reminder.py
```

## Run freee sync

```bash
python sync_freee.py
```

---

# Troubleshooting

## freee token error

```
invalid_grant
```

Possible causes:

- expired refresh token
- redirect URI mismatch

Solution:

```bash
python get_freee_token.py
```

---

## GitHub Secret update error

```
401 Bad credentials
```

Check:

- `GH_SECRET_PAT`
- repository Secrets write permission