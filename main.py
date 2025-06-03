# telegram_expense_bot/main.py

import os
import logging
import pytesseract
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Load environment variables ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SERVICE_ACCOUNT_FILE = "creds.json"  # Google Sheet credentials

# === Helper functions ===
def extract_text_from_image(image_path):
    return pytesseract.image_to_string(Image.open(image_path))

def extract_expense_info(text):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "mistral",
        "prompt": f"""
You are a structured financial document parser. From the following text, extract all financial transactions.

Each transaction should be a JSON object with the following keys:
- date: format as YYYY-MM-DD if possible
- merchant: clean and readable merchant name only (no time, no location tags)
- amount: convert to numeric float, exclude currency symbols (e.g., 27.60)
- category: one of [Housing, Utilities, Cleaning, Loan & Credit, Investment, Insurance, Health & Fitness, Subscription, Shopping, Online Purchases, Public Transport, Private Transport, Travel, Dining & Drinks, Entertainment, Leisure & Fun, Charity & Donations, Tax & Government Fees, Others]

Rules:
- If date is ambiguous, infer best estimate and use YYYY-MM-DD.
- If any field is missing, use null (not empty string).
- Return a JSON array of consistent objects, with no markdown, comments, or explanation.

Input text:
{text}
""",
        "stream": False
    })

    try:
        content = response.json()["response"]
        logger.info(f"Ollama response: {content}")

        # Extract actual JSON from markdown-wrapped response
        start = content.find("[")
        end = content.rfind("]") + 1
        if start != -1 and end != -1:
            json_data = content[start:end]
            return json.loads(json_data)
        else:
            raise ValueError("No valid JSON array found in response.")

    except Exception as e:
        logger.error(f"Failed to parse Ollama response: {e}")
        raise

def write_multiple_to_google_sheet(data):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    values = []
    for entry in data:
        date = entry.get('date', '')
        merchant = entry.get('merchant', '')
        amount = entry.get('amount', '')
        category = entry.get('category', '')
        values.append([date, merchant, amount, category])

    sheet.values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body={'values': values}
    ).execute()

# === Telegram Handler ===
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 Received 1 image. Processing...")

    image_folder = "images"
    os.makedirs(image_folder, exist_ok=True)

    file = await update.message.photo[-1].get_file()
    image_filename = os.path.join(image_folder, f"{file.file_id}.jpg")
    await file.download_to_drive(custom_path=image_filename)
    logger.info(f"Downloaded photo to {image_filename}")

    text = extract_text_from_image(image_filename)
    logger.info(f"OCR extracted text: {text}")

    expense_data = extract_expense_info(text)
    logger.info(f"Parsed expense: {expense_data}")

    write_multiple_to_google_sheet(expense_data)

    # Format summary message
    rows = []
    for i, entry in enumerate(expense_data):
        date = entry.get('date', '')
        merchant = entry.get('merchant', '')
        amount = entry.get('amount', '')
        category = entry.get('category', '')
        rows.append(f"{i+1}. `{date}` | `{merchant}` | `{amount}` | `{category}`")

    message = "📋 *Expense Summary*\n" + "\n".join(rows)
    await update.message.reply_text(message, parse_mode='Markdown')

# === Main app ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)
    app.add_handler(photo_handler)
    logger.info("Bot is polling...")
    app.run_polling()
