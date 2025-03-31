import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from datetime import datetime
import os
from flask import Flask, jsonify
from threading import Thread

# Configuração do logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credenciais.json"  # Caminho para o JSON de credenciais
SPREADSHEET_NAME = "MateriaisBot"  # Nome exato da sua planilha no Google Sheets

# Função para conectar ao Google Sheets
def connect_google_sheets():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1  # Ajuste se necessário

# Criando um servidor Flask para escutar a porta 8080
app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify(status="OK")

# Definindo os estados da conversa
DATA_RECECAO, GUIA_REMESSA, FORNECEDOR, TIPO_MATERIAL, MATERIAL, OBSERVACOES_MATERIAL, LOTE, QUANTIDADE, CHEFE_PROJETO, OBSERVACOES, HANDLING_UNIT = range(11)

# Função que irá processar a mensagem inicial
def process_message(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Bem-vindo ao bot! Vamos começar?')
    return DATA_RECECAO  # Defina o estado inicial da conversa

# Função para processar a data de recepção
def input_data_rececao(update: Update, context: CallbackContext) -> int:
    data_rececao = update.message.text
    try:
        datetime.strptime(data_rececao, '%d/%m/%Y')  # Verificar se a data está no formato correto
        update.message.reply_text(f'Data de recepção escolhida: {data_rececao}')
        return GUIA_REMESSA  # Proseguir para o próximo passo
    except ValueError:
        update.message.reply_text('Data inválida. Por favor, insira a data no formato DD/MM/AAAA.')
        return DATA_RECECAO  # Solicitar novamente a data

# Função para solicitar a guia de remessa
def guia_remessa(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Por favor, insira a guia de remessa.')
    return FORNECEDOR  # Próximo passo

# Função para inserir fornecedor
def fornecedor(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Insira o nome do fornecedor:')
    return TIPO_MATERIAL  # Próximo passo

# Função para selecionar o tipo de material
def tipo_material(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Material A", callback_data='material_a')],
        [InlineKeyboardButton("Material B", callback_data='material_b')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Escolha o tipo de material:', reply_markup=reply_markup)
    return MATERIAL  # Aguardar resposta sobre o material

# Função para processar o material selecionado
def material(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    material_selecionado = query.data
    query.edit_message_text(f'Material selecionado: {material_selecionado}')
    return OBSERVACOES_MATERIAL  # Proseguir para o próximo passo

# Função para inserir observações sobre o material
def observacoes_material(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Por favor, insira as observações sobre o material.')
    return LOTE  # Próximo passo

# Função para inserir o lote
def lote(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Por favor, insira o lote:')
    return QUANTIDADE  # Próximo passo

# Função para inserir a quantidade
def quantidade(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Por favor, insira a quantidade:')
    return CHEFE_PROJETO  # Próximo passo

# Função para inserir o chefe de projeto
def chefe_projeto(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Por favor, insira o nome do chefe de projeto:')
    return OBSERVACOES  # Próximo passo

# Função para inserir observações gerais
def observacoes(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Por favor, insira observações gerais:')
    return HANDLING_UNIT  # Próximo passo

# Função para inserir unidade de manuseio
def handling_unit(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Por favor, insira a unidade de manuseio:')
    return ConversationHandler.END  # Fim da conversa

# Função principal para configurar o bot
def start_bot():
    TOKEN = "YOUR_BOT_TOKEN"  # Substitua pelo seu token do BotFather
    application = Application.builder().token(TOKEN).build()

    # Configurar a conversação
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, process_message)],  # Aqui o bot vai iniciar com qualquer mensagem
        states={
            DATA_RECECAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_data_rececao)],
            GUIA_REMESSA: [MessageHandler(filters.TEXT & ~filters.COMMAND, guia_remessa)],
            FORNECEDOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, fornecedor)],
            TIPO_MATERIAL: [CallbackQueryHandler(tipo_material)],
            MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, material)],
            OBSERVACOES_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, observacoes_material)],
            LOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lote)],
            QUANTIDADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantidade)],
            CHEFE_PROJETO: [MessageHandler(filters.TEXT & ~filters.COMMAND, chefe_projeto)],
            OBSERVACOES: [MessageHandler(filters.TEXT & ~filters.COMMAND, observacoes)],
            HANDLING_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handling_unit)],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, process_message)],  # Caso o usuário digite "Cancelar"
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# Função para rodar ambos (Flask e Bot)
def run():
    # Rodar o bot em uma thread separada
    bot_thread = Thread(target=start_bot)
    bot_thread.start()

    # Rodar o Flask na porta 8080
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    run()
