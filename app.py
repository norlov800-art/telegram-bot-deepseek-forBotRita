import os
from flask import Flask, request
import telebot
import requests

# ========== КОНФИГУРАЦИЯ ==========
TELEGRAM_TOKEN = os.environ.get('8504373078:AAEINBhCSq7yBC42A5Ucf14Z-UmK95WEqXI')
DEEPSEEK_API_KEY = os.environ.get('sk-3baac25d30784da9acb6d5c9a067bc8b')

if not TELEGRAM_TOKEN:
    print("❌ ОШИБКА: TELEGRAM_TOKEN не найден!")

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)  # ← ВАЖНО: переменная 'app'

# ========== FLASK РОУТЫ ==========
@app.route('/')
def home():
    return "✅ Бот работает! Отправьте /start в Telegram"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return 'OK', 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'Error', 500

# ========== TELEGRAM ОБРАБОТЧИКИ ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Привет! Я бот с DeepSeek API на Render!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        if DEEPSEEK_API_KEY:
            headers = {
                "Authorization": f"Bearer {sk-3baac25d30784da9acb6d5c9a067bc8b}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": message.text}],
                "stream": False,
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                json=data,
                headers=headers,
                timeout=30
            )
            response_data = response.json()
            answer = response_data["choices"][0]["message"]["content"]
            bot.reply_to(message, answer[:4000])
        else:
            bot.reply_to(message, f"Вы сказали: {message.text}")
            
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            bot.reply_to(message, "⚠️ Лимит запросов к API. Попробуйте позже.")
        else:
            bot.reply_to(message, f"Ошибка: {error_msg[:200]}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🚀 Запуск Telegram бота...")
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
