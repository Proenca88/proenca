# Usa uma imagem oficial do Python
FROM python:3.10

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia todos os arquivos do seu bot para o contêiner
COPY . /app

# Instala as dependências do bot
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta 8080 (necessário para o Cloud Run)
EXPOSE 8080

# Comando para rodar o bot
CMD ["python", "bot_telegram.py"]