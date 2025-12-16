import os
import telebot
import requests
from flask import Flask

# Конфигурация
TELEGRAM_TOKEN = os.environ.get('8504373078:AAEINBhCSq7yBC42A5Ucf14Z-UmK95WEqXI')
DEEPSEEK_API_KEY = os.environ.get('sk-3baac25d30784da9acb6d5c9a067bc8b')
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

bot = telebot.TeleBot(8504373078:AAEINBhCSq7yBC42A5Ucf14Z-UmK95WEqXI)
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает! ✅"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        headers = {
            "Authorization": f"Bearer {sk-3baac25d30784da9acb6d5c9a067bc8b}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": message.text}],
            "stream": False
        }
        
        response = requests.post(DEEPSEEK_API_URL, json=data, headers=headers)
        response_data = response.json()
        
        answer = response_data["choices"][0]["message"]["content"]
        bot.reply_to(message, answer[:4096])
        
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

def start_bot():
    print("Бот запущен...")
    bot.remove_webhook()
    bot.polling(none_stop=True)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=10000)
