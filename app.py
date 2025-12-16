import os
import telebot
import requests
import logging
from flask import Flask, request

# --- Конфигурация ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
YANDEX_API_KEY = os.environ.get('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.environ.get('YANDEX_FOLDER_ID')
# Модель: "yandexgpt-lite" (быстрая, для чата) или "yandexgpt" (Pro, для сложных задач)[citation:2][citation:7]
YANDEX_MODEL = "yandexgpt-lite"

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

def ask_yandex_gpt(user_message, system_prompt="Ты полезный и вежливый ассистент."):
    """
    Отправляет запрос к YandexGPT API и возвращает текстовый ответ.
    Структура запроса соответствует официальной документации[citation:3][citation:4].
    """
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"  # Аутентификация по API-ключу[citation:3]
    }
    # Формирование промпта с учетом ролей system, user, assistant[citation:3]
    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,  # Параметр "творчества" от 0 до 1
            "maxTokens": 1500
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_message}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()  # Проверка на ошибки HTTP
        result_json = response.json()
        # Извлечение текста ответа из структуры JSON[citation:3]
        answer_text = result_json['result']['alternatives'][0]['message']['text']
        return answer_text.strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при запросе к YandexGPT: {e}")
        return "Извините, произошла ошибка соединения с AI."
    except (KeyError, ValueError) as e:
        logger.error(f"Ошибка разбора ответа от YandexGPT: {e}")
        return "Извините, не удалось обработать ответ от AI."

# --- Обработчики команд Telegram ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот, работающий на YandexGPT.\n"
        "Просто напишите мне сообщение, и я постараюсь вам помочь.\n"
        "Команды:\n"
        "/start или /help - это сообщение\n"
        "/status - проверить статус подключения"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['status'])
def send_status(message):
    status = "✅ Бот активен. "
    if YANDEX_API_KEY and YANDEX_FOLDER_ID:
        status += "Ключ YandexGPT найден."
    else:
        status += "⚠️ Внимание: Ключ или ID каталога YandexGPT не заданы в настройках."
    bot.reply_to(message, status)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    logger.info(f"Получено сообщение от {message.from_user.id}: {message.text}")
    # Показываем пользователю, что бот "печатает"
    bot.send_chat_action(message.chat.id, 'typing')
    # Получаем ответ от YandexGPT
    answer = ask_yandex_gpt(message.text)
    # Отправляем ответ пользователю
    bot.reply_to(message, answer)

# --- Flask эндпоинты для вебхука ---
@app.route('/')
def home():
    return "🤖 Telegram Bot with YandexGPT is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Конечная точка, куда Telegram отправляет обновления."""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Bad Request', 400

if __name__ == '__main__':
    # Проверка обязательных переменных окружения
    if not TELEGRAM_TOKEN:
        logger.error("CRITICAL: Переменная окружения TELEGRAM_TOKEN не задана.")
    if not YANDEX_API_KEY:
        logger.error("CRITICAL: Переменная окружения YANDEX_API_KEY не задана.")
    if not YANDEX_FOLDER_ID:
        logger.error("CRITICAL: Переменная окружения YANDEX_FOLDER_ID не задана.")

    # Запуск Flask-сервера (Render сам устанавливает переменную PORT)
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Запуск бота на порту {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
