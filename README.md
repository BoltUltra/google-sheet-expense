# Expense Telegram Bot → Google Sheets

Text your expenses to a Telegram bot and they automatically appear in your Google Sheets expense tracker.

## How it works

- Send a message like `Lunch 5000`
- The bot parses the amount, description, and date
- A new row is appended to your Google Sheet

## Example messages

```
Lunch 5000
Bought data 2000 yesterday
Transport 1500 on July 1
Salary 300000
```

## Setup

### 1. Create a Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the prompts
3. Copy the **API token**

### 2. Get your Telegram user ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy the numeric ID

### 3. Set up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Google Sheets API**
4. Go to **IAM & Admin → Service Accounts**
5. Create a service account
6. Create a **JSON key** and download it
7. Open the JSON file and copy the entire contents
8. **Share your Google Sheet** with the service-account email address (give it **Editor** access)
9. Copy your sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/THIS_IS_THE_SHEET_ID/edit
   ```

### 4. Environment variables

Copy `.env.example` to `.env` and fill in:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALLOWED_USER_ID=your_telegram_user_id
GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account",...}
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_SHEET_RANGE=Sheet1!A:C
```

> For Vercel, paste the entire service-account JSON into the `GOOGLE_SHEETS_CREDENTIALS_JSON` environment variable.

### 5. Deploy to Vercel

1. Push this repo to GitHub
2. Import the repo in [Vercel](https://vercel.com/)
3. Add all the environment variables in the Vercel dashboard
4. Deploy
5. Copy your Vercel domain, e.g. `https://expense-bot.vercel.app`

### 6. Set the Telegram webhook

Run this in your terminal (replace the values):

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://<YOUR_VERCEL_DOMAIN>/api/webhook"}'
```

Or just open this URL in your browser:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://<YOUR_VERCEL_DOMAIN>/api/webhook
```

### 7. Test

Send `Lunch 5000` to your bot on Telegram. ✅

## Local testing

Install dependencies:

```bash
pip install -r requirements.txt
```

Test the parser:

```bash
python -c "from lib.parser import parse_expense; print(parse_expense('Lunch 5000 yesterday'))"
```

## Project structure

```
.
├── api/webhook.py       # Vercel serverless entry point
├── lib/parser.py        # Expense message parser
├── lib/sheets.py        # Google Sheets API helper
├── requirements.txt     # Python dependencies
├── vercel.json          # Vercel configuration
└── .env.example         # Environment variable template
```

## Troubleshooting

- **Bot doesn't reply:** Check that the webhook is set and Vercel logs show no errors.
- **Sheet not updating:** Make sure the service account email has **Editor** access to the sheet.
- **Wrong date format:** The sheet column should be plain text or a date format that accepts `YYYY-MM-DD`.

## License

MIT
