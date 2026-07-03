"""Vercel serverless function that handles Telegram webhook updates (Flask WSGI)."""

import json
import os
import sys
import traceback

# Add project root to path so `lib` imports work on Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
import telegram
from telegram import Update

from lib.parser import parse_expense
from lib.sheets import append_row


app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.environ.get("TELEGRAM_ALLOWED_USER_ID")


def _log(msg):
    print(f"[expense-bot] {msg}", flush=True)


def _allowed_ids():
    """Return set of allowed Telegram user IDs."""
    raw = os.environ.get("TELEGRAM_ALLOWED_USER_IDS", ALLOWED_USER_ID or "")
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


def _send_message(chat_id: int, text: str):
    bot = telegram.Bot(token=BOT_TOKEN)
    return bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")


@app.route("/", methods=["GET"])
def health():
    """Simple health check."""
    return jsonify({"ok": True, "bot": bool(BOT_TOKEN), "sheet": bool(os.environ.get("GOOGLE_SHEET_ID"))}), 200


@app.route("/api/webhook", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates."""
    _log(f"Received request: {request.method}")
    try:
        body = request.get_json(force=True)
        _log(f"Update body: {json.dumps(body)}")

        update = Update.de_json(body, None)

        if not update.message or not update.message.text:
            _log("No message text in update")
            return jsonify({"ok": True}), 200

        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        text = update.message.text.strip()
        _log(f"Message from {user_id}: {text}")

        # Auth check
        allowed = _allowed_ids()
        _log(f"Allowed IDs: {allowed}")
        if user_id not in allowed:
            _log(f"Unauthorized user: {user_id}")
            _send_message(chat_id, "⛔ You're not authorized to use this bot.")
            return jsonify({"ok": True}), 200

        # Help / start
        if text.lower() in ("/start", "/help"):
            _send_message(
                chat_id,
                "💸 *Expense Bot*\n\nSend me expenses like:\n"
                "• `Lunch 5000`\n"
                "• `Data 2000 yesterday`\n"
                "• `Transport 1500 on July 1`\n\n"
                "I'll add them to your Google Sheet.",
            )
            return jsonify({"ok": True}), 200

        # Parse and append
        try:
            parsed = parse_expense(text)
            _log(f"Parsed: {parsed}")
            append_row(
                parsed["date"],
                parsed["description"],
                parsed["amount"],
            )
            _log("Row appended successfully")
            _send_message(
                chat_id,
                f"✅ Added to sheet:\n"
                f"*{parsed['description']}* — {parsed['currency']}{parsed['amount']:,.2f}\n"
                f"📅 {parsed['date']}",
            )
        except ValueError as exc:
            _log(f"Parse error: {exc}")
            _send_message(
                chat_id,
                f"⚠️ Could not parse: {exc}\n\nTry: `Lunch 5000`",
            )
        except Exception as exc:
            _log(f"Sheet error: {traceback.format_exc()}")
            _send_message(
                chat_id,
                f"❌ Failed to save to sheet. Please try again.\n_{str(exc)}_",
            )

        return jsonify({"ok": True}), 200

    except Exception as exc:
        _log(f"Webhook error: {traceback.format_exc()}")
        return jsonify({"error": str(exc)}), 500
