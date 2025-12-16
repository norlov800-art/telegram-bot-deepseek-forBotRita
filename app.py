import os
from flask import Flask, request
import telebot
import requests

# ========== КОНФИГУРАЦИЯ ==========
TELEGRAM_TOKEN = os.environ.get("8504373078:AAEINBhCSq7yBC42A5Ucf14Z-UmK95WEqXI")
DEEPSEEK_API_KEY = os.environ.get("sk-3baac25d30784da9acb6d5c9a067bc8b")

if not TELEGRAM_TOKEN:
    print("❌ ОШИБКА: TELEGRAM_TOKEN не найден!")
    TELEGRAM_TOKEN = "8504373078:AAEINBhCSq7yBC42A5Ucf14Z-UmK95WEqXI"  # временно для теста

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = telebot.TeleBot(TELEGRAM_TOKEN)  # ← ТОКЕН В КАВЫЧКАХ!
app = Flask(__name__)

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
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": message.text}]
            }
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                json=data,
                headers=headers,
                timeout=30
            )
            answer = response.json()["choices"][0]["message"]["content"]
            bot.reply_to(message, answer[:4000])
        else:
            bot.reply_to(message, f"Вы сказали: {message.text}")
            
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)[:200]}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🚀 Запуск Telegram бота...")
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
