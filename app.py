# app.py

import os
import re
import threading
from datetime import datetime
from dotenv import load_dotenv

from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
import pandas as pd

# Импортируем наши модули
from _1a_Class_BrowserManager import BrowserManager
from _1b_Class_OzonScraper import OzonScraper
from _2_scenarios import run_scenario_by_query, run_scenario_by_url  # Импортируем сценарии
from _3_save_files import save_parsing_results

load_dotenv()

# --- Настройка Flask ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 # Не кешировать статические файлы

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS")
DOWNLOAD_FOLDER = 'downloads'

socketio = SocketIO(app, async_mode='threading', cors_allowed_origins=[CORS_ALLOWED_ORIGINS, "http://127.0.0.1:5000"])


# browser_manager = BrowserManager()


# --- Маршруты Flask ---
@app.route('/')
def index():
    return render_template('index.html')


# Маршрут для скачивания файлов из папки downloads
@app.route('/downloads/<path:filename>')
def static_files(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


# --- Обработчики SocketIO ---
@socketio.on('connect')
def handle_connect():
    print(f"Клиент подключился: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"Клиент отключился: {request.sid}")


@socketio.on('start_parsing')
def handle_start_parsing(data):
    session_id = request.sid
    print(f"Получен запрос на парсинг от {session_id} с данными: {data}")

    def socket_logger(message):
        socketio.emit('log_message', { 'data': str(message) }, room=session_id)

    def parsing_thread_function(task_data):
        """
        Основная функция, выполняющая парсинг.
        Определяет, это URL или поисковый запрос, и запускает нужный сценарий.
        """
        input_data = task_data.get('input_data', '').strip()
        pages = task_data.get('pages', 1)
        max_items = task_data.get('max_items', 5)

        df_results = None

        # Определяем, URL это или поисковый запрос
        is_url = input_data.startswith('http') and 'ozon.ru' in input_data

        try:

            if is_url:
                df_results = run_scenario_by_url(input_data, pages, max_items, logger_callback=socket_logger)
            else:
                df_results = run_scenario_by_query(input_data, pages, max_items, logger_callback=socket_logger)

            if df_results is not None and not df_results.empty:
                # Используем централизованную функцию для сохранения
                saved_info = save_parsing_results(
                        df=df_results,
                        input_data=input_data,
                        is_url=is_url,
                        directory=DOWNLOAD_FOLDER,
                        logger_callback=socket_logger
                        )

                if saved_info and 'filepath' in saved_info and 'csv_content' in saved_info:
                    # Отправляем клиенту ссылку на скачивание и содержимое файла
                    result_filename = os.path.basename(saved_info['filepath'])
                    socketio.emit('parsing_finished', {
                            'result_url': f'/{DOWNLOAD_FOLDER}/{result_filename}',
                            'csv_data'  : saved_info['csv_content']
                            }, room=session_id
                                  )

                else:
                    socket_logger("Ошибка при сохранении результатов парсинга.")
                    socketio.emit('parsing_finished', { }, room=session_id)

            else:
                socket_logger("Парсинг завершился безрезультатно.")
                socketio.emit('parsing_finished', { }, room=session_id)  # Завершаем без ссылки

        except Exception as e:
            socket_logger(f"--- КРИТИЧЕСКАЯ ОШИБКА ---")
            socket_logger(str(e))
            socketio.emit('parsing_finished', { }, room=session_id)

    thread = threading.Thread(target=parsing_thread_function, args=(data,))
    thread.start()

    socketio.emit('task_started', { 'data': 'Задача парсинга запущена...' }, room=session_id)


# --- Запуск приложения ---
if __name__ == '__main__':
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
