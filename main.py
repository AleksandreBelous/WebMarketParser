# main.py

import os
import json
import pandas as pd
from datetime import datetime

# Импортируем наши модули
from _2_Scenarios import run_scenario_by_query, run_scenario_by_url


def load_settings(filepath="settings.json"):
    """Загружает настройки из JSON файла."""

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    except FileNotFoundError:
        print(f"Ошибка: Файл настроек '{filepath}' не найден.")
        return None

    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла '{filepath}'.")
        return None


def save_results(df: pd.DataFrame, filename_prefix: str):
    """Сохраняет DataFrame в CSV."""

    if df is None or df.empty:
        print("Нет данных для сохранения.")
        return

    dirname = "results"
    os.makedirs(dirname, exist_ok=True)

    filename = f"{filename_prefix}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
    filepath = os.path.join(dirname, filename)
    df.to_csv(filepath, index=False, encoding='utf-8')

    print(f"--- РАБОТА ЗАВЕРШЕНА ---")
    print(f"Результаты ({len(df)} строк) сохранены в файл: {filename}")


def main():
    settings = load_settings()

    if settings:
        mode = settings.get("run_mode")
        parse_conf = settings.get("parse_settings", { })
        pages = parse_conf.get("pages_to_parse", 1)
        max_items = parse_conf.get("max_analogs_or_products", 5)

        df_results = None

        if mode == "query":
            query = settings.get("input_query")

            if not query:
                print("Ошибка: в 'settings.json' не указан 'input_query' для режима 'query'.")
            else:
                df_results = run_scenario_by_query(query, pages=pages, max_products=max_items)
                save_results(df_results, f"ozon_query_{query.replace(' ', '_')}")

        elif mode == "url":
            url = settings.get("input_url")

            if not url:
                print("Ошибка: в 'settings.json' не указан 'input_url' для режима 'url'.")
            else:
                df_results = run_scenario_by_url(url, pages=pages, max_analogs=max_items)
                save_results(df_results, "ozon_analogs")

        else:
            print(f"Ошибка: Неизвестный режим работы '{mode}' в 'settings.json'. Доступные режимы: 'query', 'url'.")


if __name__ == '__main__':
    main()
