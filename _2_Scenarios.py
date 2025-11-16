# _2_Scenarios.py

import pandas as pd
from _1a_Class_BrowserManager import BrowserManager
from _1b_Class_OzonScraper import OzonScraper


def process_query(scraper: OzonScraper, query: str, pages: int, max_products: int) -> pd.DataFrame:
    """
    Общая логика: получает scraper и поисковый запрос, возвращает DataFrame.
    Эта функция НЕ управляет браузером.
    """

    links = scraper.fetch_product_links(query, pages)

    if not links:
        scraper.log("Ссылки на товары не найдены.")
        return pd.DataFrame()

    all_products = []

    for i, link in enumerate(links):
        if i >= max_products:
            scraper.log(f"Достигнут лимит в {max_products} товаров.")
            break

        product_data = scraper.parse_product_page(link)
        all_products.append(product_data)

    return pd.DataFrame(all_products)


def run_scenario_by_query(query: str, pages: int, max_products: int, logger_callback=print, proxy: dict = None) -> pd.DataFrame:
    """Сценарий: поиск по запросу. Управляет жизненным циклом браузера."""

    logger_callback(f"--- ЗАПУСК СЦЕНАРИЯ: Поиск по запросу '{query}' ---")

    with BrowserManager(logger_callback=logger_callback, proxy=proxy) as driver:
        if not driver:
            logger_callback("Не удалось запустить браузер. Прерывание сценария.")
            return pd.DataFrame()
            
        scraper = OzonScraper(driver, logger_callback=logger_callback)
        results_df = process_query(scraper, query, pages, max_products)

    return results_df


def run_scenario_by_url(url: str, pages: int, max_analogs: int, logger_callback=print, proxy: dict = None) -> pd.DataFrame:
    """Сценарий: поиск аналогов по URL. Управляет жизненным циклом браузера."""

    logger_callback(f"--- ЗАПУСК СЦЕНАРИЯ: Поиск аналогов для URL '{url[:50]}...' ---")
    all_results = []

    with BrowserManager(logger_callback=logger_callback, proxy=proxy) as driver:
        if not driver:
            logger_callback("Не удалось запустить браузер. Прерывание сценария.")
            return pd.DataFrame()

        scraper = OzonScraper(driver, logger_callback=logger_callback)

        # 1. Парсинг исходного товара
        initial_data = scraper.parse_product_page(url)

        if not initial_data or not initial_data["title"]:
            logger_callback("Не удалось спарсить исходный товар. Завершение.")
            return pd.DataFrame()

        initial_data["is_initial"] = True
        all_results.append(initial_data)

        # 2. Поиск аналогов по названию
        search_query = initial_data["title"]
        analogs_df = process_query(scraper, search_query, pages, max_analogs)

        # 3. Объединение результатов
        if not analogs_df.empty:
            analogs_df["is_initial"] = False
            # Убираем исходный товар из аналогов, если он там есть
            analogs_df = analogs_df[analogs_df['url'] != url]

            initial_df = pd.DataFrame([initial_data])
            final_df = pd.concat([initial_df, analogs_df], ignore_index=True)
            return final_df

        else:
            return pd.DataFrame([initial_data])
