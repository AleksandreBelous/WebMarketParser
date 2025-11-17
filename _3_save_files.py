# _3_save_files.py

import os
from datetime import datetime

import pandas as pd


def save_parsing_results(df: pd.DataFrame, input_data: str, is_url: bool, directory: str, logger_callback=print
                         ) -> dict:
    """
    Сохраняет DataFrame в CSV и XLSX файлы и возвращает пути к файлам и содержимое CSV.

    :param df: DataFrame для сохранения.
    :param input_data: Исходные данные (URL или поисковый запрос).
    :param is_url: Флаг, указывающий, является ли input_data URL.
    :param directory: Директория для сохранения файлов.
    :param logger_callback: Функция для логирования сообщений.
    :return: Словарь с 'csv_filepath', 'csv_content', 'xlsx_filepath' (опционально)
             или пустой словарь в случае ошибки/отсутствия данных.
    """

    if df is None or df.empty:
        logger_callback("Нет данных для сохранения.")
        return { }

    os.makedirs(directory, exist_ok=True)

    filename_prefix = "analogs" if is_url else f"query_{input_data.replace(' ', '_')[:20]}"
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    full_base_filename = f"{filename_prefix}_{timestamp}"

    saved_info = { }

    # --- Сохранение в CSV ---
    try:
        csv_filename = f"{full_base_filename}.csv"
        csv_filepath = os.path.join(directory, csv_filename)
        df.to_csv(csv_filepath, sep=';', index=False, encoding='utf-8')
        saved_info['csv_filepath'] = csv_filepath
        logger_callback(f"Результаты сохранены в CSV: {csv_filepath}")

        # Читаем содержимое CSV для возврата
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        saved_info['csv_content'] = csv_content

    except IOError as e:
        logger_callback(f"Ошибка сохранения CSV файла {csv_filepath}: {e}")
    except Exception as e:
        logger_callback(f"Неизвестная ошибка при сохранении CSV: {e}")

    # --- Сохранение в XLSX ---
    try:
        xlsx_filename = f"{full_base_filename}.xlsx"
        xlsx_filepath = os.path.join(directory, xlsx_filename)
        df.to_excel(xlsx_filepath, index=False, engine='openpyxl')
        saved_info['xlsx_filepath'] = xlsx_filepath
        logger_callback(f"Результаты сохранены в XLSX: {xlsx_filepath}")
    except IOError as e:
        logger_callback(f"Ошибка сохранения XLSX файла {xlsx_filepath}: {e}")
    except Exception as e:
        logger_callback(f"Неизвестная ошибка при сохранении XLSX: {e}")

    return saved_info
