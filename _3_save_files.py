# _3_save_files.py

import os
from datetime import datetime

import pandas as pd


def save_parsing_results(df: pd.DataFrame, input_data: str, is_url: bool, directory: str, logger_callback=print
                         ) -> dict:
    """
    Сохраняет DataFrame в CSV файл и возвращает путь к файлу и его содержимое.
    Эта функция повторяет логику сохранения из app.py.

    :param df: DataFrame для сохранения.
    :param input_data: Исходные данные (URL или поисковый запрос).
    :param is_url: Флаг, указывающий, является ли input_data URL.
    :param directory: Директория для сохранения файлов.
    :param logger_callback: Функция для логирования сообщений.
    :return: Словарь с 'filepath' и 'csv_content', или пустой словарь в случае ошибки/отсутствия данных.
    """

    if df is None or df.empty:
        logger_callback("Нет данных для сохранения.")
        return { }

    os.makedirs(directory, exist_ok=True)

    filename_prefix = "analogs" if is_url else f"query_{input_data.replace(' ', '_')[:20]}"
    filename = f"{filename_prefix}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
    filepath = os.path.join(directory, filename)

    try:
        df.to_csv(filepath, sep=';', index=False, encoding='utf-8')
        logger_callback(f"Результаты сохранены в файл: {filename}")

        with open(filepath, 'r', encoding='utf-8') as f:
            csv_content = f.read()

        return { 'filepath': filepath, 'csv_content': csv_content }

    except IOError as e:
        logger_callback(f"Ошибка сохранения CSV файла {filepath}: {e}")
        return { }
    except Exception as e:
        logger_callback(f"Неизвестная ошибка при сохранении CSV: {e}")
        return { }
