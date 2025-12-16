import os
import telebot
import requests
import json
import logging
from flask import Flask, request

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
YANDEX_API_KEY = os.environ.get('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.environ.get('YANDEX_FOLDER_ID')
YANDEX_MODEL = "yandexgpt-lite"

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

def ask_yandex_gpt(user_message, system_prompt="Ты полезный и вежливый ассистент."):
    """
    Отправляет запрос к YandexGPT API и возвращает текстовый ответ.
    """
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }
    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 1500
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_message}
        ]
    }

    # === ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ЗАПРОСА ===
    logger.info(f"🔍 Отправляю запрос к YandexGPT на URL: {url}")
    logger.info(f"🔍 Использую Folder ID: {YANDEX_FOLDER_ID}")
    logger.info(f"🔍 Заголовок Authorization начинается с: {YANDEX_API_KEY[:15]}...")
    logger.info(f"🔍 Тело запроса (data): {json.dumps(data, ensure_ascii=False)[:500]}...")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        logger.info(f"📡 Получен HTTP статус от YandexGPT: {response.status_code}")
        logger.info(f"📡 Заголовки ответа: {dict(response.headers)}")

        # Пытаемся залогировать тело ответа
        try:
            response_body = response.text[:1000]
            logger.info(f"📦 Тело ответа: {response_body}")
        except:
            logger.info("📦 Не удалось прочитать тело ответа для логирования")

        response.raise_for_status()
        result_json = response.json()
        answer_text = result_json['result']['alternatives'][0]['message']['text']
        logger.info(f"✅ Успешно получили ответ от AI")
        return answer_text.strip()

    except requests.exceptions.Timeout:
        logger.error("⏱ Таймаут запроса к YandexGPT (30 сек)")
        return "Извините, AI-сервис не ответил вовремя."
    except requests.exceptions.ConnectionError as e:
        logger.error(f"🔌 Ошибка соединения с YandexGPT: {e}")
        return "Извините, не удалось установить соединение с AI-сервисом."
    except requests.exceptions.HTTPError as e:
        logger.error(f"🚨 Ошибка HTTP от YandexGPT: {e}")
        logger.error(f"Код статуса: {response.status_code if 'response' in locals() else 'N/A'}")
        
        if response.status_code == 403:
            return "Ошибка доступа (403). Проверьте API-ключ и права доступа каталога."
        elif response.status_code == 404:
            return "Ресурс не найден (404). Проверьте правильность Folder ID и имя модели."
        elif response.status_code == 429:
            return "Слишком много запросов (429). Превышен лимит. Попробуйте позже."
        else:
            return f"Ошибка сервера AI (код {response.status_code})."
    except (KeyError, ValueError) as e:
        logger.error(f"📊 Ошибка разбора JSON-ответа от YandexGPT: {e}")
        return "Извините, AI-сервис вернул неожиданный ответ."
    except Exception as e:
        logger.error(f"💥 Неизвестная ошибка при запросе к YandexGPT: {type(e).__name__}: {e}")
        return "Извините, произошла непредвиденная ошибка."

# --- TELEGRAM ОБРАБОТЧИКИ ---
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
    bot.send_chat_action(message.chat.id, 'typing')
    answer = ask_yandex_gpt(message.text)
    bot.reply_to(message, answer)

# --- FLASK ЭНДПОИНТЫ ---
@app.route('/')
def home():
    return "🤖 Telegram Bot with YandexGPT is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Bad Request', 400

# --- ЗАПУСК ---
if __name__ == '__main__':
    # Проверка переменных при запуске
    if not TELEGRAM_TOKEN:
        logger.error("CRITICAL: Переменная TELEGRAM_TOKEN не задана.")
    if not YANDEX_API_KEY:
        logger.error("CRITICAL: Переменная YANDEX_API_KEY не задана.")
    if not YANDEX_FOLDER_ID:
        logger.error("CRITICAL: Переменная YANDEX_FOLDER_ID не задана.")

    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Запуск бота на порту {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
