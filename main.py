# telegram_expense_bot/main.py

import os
import logging
import pytesseract
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# OpenAI or local LLM handler
import openai  # comment this if using local model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Load environment variables ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERVICE_ACCOUNT_FILE = "creds.json"  # Google Sheet credentials

# === Helper functions ===
def extract_text_from_image(image_path):
    return pytesseract.image_to_string(Image.open(image_path))

def extract_expense_info(text):
    openai.api_key = OPENAI_API_KEY
    prompt = f"""
    Extract date, merchant, amount, and category from the following:
    {text}
    Format output as JSON with keys: date, merchant, amount, category.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return eval(response.choices[0].message['content'])

def write_to_google_sheet(data):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    values = [[data['date'], data['merchant'], data['amount'], data['category']]]
    sheet.values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body={'values': values}
    ).execute()

# === Telegram Handler ===
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    file_path = await file.download_to_drive()
    logger.info(f"Downloaded photo to {file_path}")

    text = extract_text_from_image(file_path)
    logger.info(f"OCR extracted text: {text}")

    expense = extract_expense_info(text)
    logger.info(f"Parsed expense: {expense}")

    write_to_google_sheet(expense)
    await update.message.reply_text("Expense recorded successfully!")

# === Main app ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)
    app.add_handler(photo_handler)
    logger.info("Bot is polling...")
    app.run_polling()
