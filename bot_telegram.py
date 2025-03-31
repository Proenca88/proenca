import os
import logging
import asyncio
import gspread
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configurações do Telegram
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://proenca.onrender.com/"

# Configurações do Google Sheets
GOOGLE_SHEETS_CREDENTIALS = "google_credentials.json"
SHEET_NAME = "MinhaPlanilha"

def get_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

# Configuração do Flask
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def home():
    return "Bot Telegram rodando!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    asyncio.run(application.process_update(update))
    return "OK"

# Função para buscar dados do Google Sheets
async def get_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = get_google_sheet()
    data = sheet.get_all_values()
    message = "\n".join([" - ".join(row) for row in data])
    await update.message.reply_text(f"Dados da Planilha:\n{message}")

# Função para exibir botões interativos
async def show_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Opção 1", callback_data='1')],
                [InlineKeyboardButton("Opção 2", callback_data='2')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha uma opção:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Você escolheu a opção {query.data}")

# Configuração do bot
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("dados", get_data))
application.add_handler(CommandHandler("opcoes", show_buttons))
application.add_handler(CallbackQueryHandler(button_handler))

async def set_webhook():
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}{TOKEN}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=8080)
