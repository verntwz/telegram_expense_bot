# Telegram Expense Tracker Bot

This project sets up a Telegram bot that accepts receipt or bank statement screenshots, extracts expense information using OCR and an LLM (OpenAI or local), and logs the details into a Google Sheet.

---

## 🚀 Features
- OCR receipt/bank statement screenshots
- LLM to extract: **date, amount, merchant, category**
- Google Sheets integration for tracking expenses

---

## 🧰 Requirements
- Python 3.9+
- Telegram Bot Token ([@BotFather](https://t.me/botfather))
- Google Cloud service account JSON (`creds.json`)
- OpenAI API Key (or local LLM)

---

## 📦 Setup Instructions

### 1. Clone this repo or set up a new project folder
If you're starting a new project:
```bash
mkdir telegram-expense-bot
cd telegram-expense-bot

git init
# Replace with your actual GitHub repo URL
git remote add origin https://github.com/verntwz/telegram_expense_bot.git
git pull origin main  # or "master" depending on your default branch
```
Or if cloning:
```bash
git clone https://github.com/yourusername/telegram-expense-bot.git
cd telegram-expense-bot
```

### 2. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file:
```
TELEGRAM_BOT_TOKEN=your_telegram_token
GOOGLE_SHEET_ID=your_google_sheet_id
OPENAI_API_KEY=your_openai_api_key
```

Or set them in terminal before running.

### 4. Enable Google Sheets API
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Enable **Google Sheets API**
- Create service account credentials and download `creds.json`
- Share your Google Sheet with the service account email

### 5. Run the bot
```bash
python main.py
```

---

## 🤖 Local LLM (Optional)
If you prefer a self-hosted model:

### Install Ollama
```bash
brew install ollama  # macOS
```
Or on Windows, download the installer from: https://ollama.com/download

Then run:
```bash
ollama run mistral
```

### Modify the `extract_expense_info` function in `main.py`:
```python
import requests

def extract_expense_info(text):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "mistral",
        "prompt": f"Extract date, merchant, amount, and category from the following text: {text}. Output in JSON."
    })
    return eval(response.json()["response"])
```

---

## 📈 Google Sheets Format
| Date       | Merchant        | Amount | Category  |
|------------|------------------|--------|-----------|
| 2025-06-03 | Starbucks Orchard| 5.60   | Beverage  |

---

## 🧪 Future Ideas
- Classify transactions by confidence level
- Add category learning (ML-based)
- Auto-tagging recurring vendors

---

## License
MIT
