# _3_save_files.py

import os
from datetime import datetime

import pandas as pd


def save_results(df: pd.DataFrame, base_filename: str, directory: str) -> dict:
    """
    Сохраняет DataFrame в форматах CSV и XLSX.

    :param df: DataFrame для сохранения.
    :param base_filename: Базовое имя файла (без расширения и даты).
    :param directory: Директория для сохранения файлов.
    :return: Словарь с путями к сохраненным файлам.
    """
    if df is None or df.empty:
        return { }

    os.makedirs(directory, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    full_base_filename = f"{base_filename}_{timestamp}"

    saved_files = { }

    # --- Сохранение в CSV ---
    csv_filename = f"{full_base_filename}.csv"
    csv_filepath = os.path.join(directory, csv_filename)
    df.to_csv(csv_filepath, sep=';', index=False, encoding='utf-8')
    saved_files['csv'] = {
            'filename': csv_filename,
            'filepath': csv_filepath
            }

    # --- Сохранение в XLSX ---
    try:
        xlsx_filename = f"{full_base_filename}.xlsx"
        xlsx_filepath = os.path.join(directory, xlsx_filename)
        df.to_excel(xlsx_filepath, index=False, engine='openpyxl')
        saved_files['xlsx'] = {
                'filename': xlsx_filename,
                'filepath': xlsx_filepath
                }
    except ImportError:
        print("Для сохранения в .xlsx установите библиотеку: pip install openpyxl")
    except Exception as e:
        print(f"Ошибка при сохранении в .xlsx: {e}")

    return saved_files
