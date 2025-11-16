# _1b_Class_OzonScraper.py

import time
import random
import re
import os
from datetime import datetime
from typing import Any
from urllib.parse import quote

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class OzonScraper:
    """
    Класс, инкапсулирующий логику парсинга сайта Ozon.
    Принимает готовый экземпляр драйвера.
    """

    BASE_DOMAIN = "https://www.ozon.ru"
    # Папка для отладочных файлов внутри /app/static/
    DEBUG_FOLDER = "debug"

    def __init__(self, driver, logger_callback=print):
        self.driver = driver
        self.log = logger_callback

        # Создаем папку для отладки, если ее нет
        static_debug_path = os.path.join('static', self.DEBUG_FOLDER)
        os.makedirs(static_debug_path, exist_ok=True)

    @staticmethod
    def _human_delay(min_sec: int = 1, max_sec: int = 3) -> None:
        time.sleep(random.uniform(min_sec, max_sec))

    def _handle_popups(self) -> None:

        try:
            cookie_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-widget='cookieBubble'] button"))
                    )
            cookie_button.click()
            self.log("  - Окно с cookies закрыто.")
            self._human_delay()

        except Exception:
            self.log("  - Окно с cookies не найдено.")

    def fetch_product_links(self, query: str, pages: int, max_products: int) -> list[str]:
        """Собирает ссылки на товары по поисковому запросу."""

        encoded_query = quote(query)
        search_url = f"{self.BASE_DOMAIN}/search/?text={encoded_query}&from_global=true"
        print(f"Переход на страницу поиска: {search_url}")
        self.log(f"Переход на страницу поиска: {search_url}")
        self.driver.get(search_url)
        self._handle_popups()

        products_links_set = set()

        for i in range(pages):

            if len(products_links_set) >= max_products:
                self.log(f"Собрано достаточное количество ссылок ({len(products_links_set)}), прекращаем скроллинг.")
                break

            print(f"--- Сбор ссылок: итерация прокрутки {i + 1}/{pages} ---")
            self.log(f"--- Сбор ссылок: итерация прокрутки {i + 1}/{pages} ---")

            try:
                WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widget='tileGridDesktop']"))
                        )
                tile_grids = self.driver.find_elements(By.CSS_SELECTOR, "div[data-widget='tileGridDesktop']")

                for grid in tile_grids:

                    product_links_elements = grid.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")

                    for link_element in product_links_elements:
                        href = link_element.get_attribute('href')

                        if href:
                            products_links_set.add(href.split("?")[0])
                            if len(products_links_set) >= max_products:
                                break  # Выходим из внутреннего цикла по ссылкам

                    if len(products_links_set) >= max_products:
                        break  # Выходим из среднего цикла по гридам

                print(f"  - Собрано уникальных ссылок: {len(products_links_set)}")
                self.log(f"  - Собрано уникальных ссылок: {len(products_links_set)}")

                if i < pages - 1:
                    print("  - Прокрутка вниз...")
                    self.log("  - Прокрутка вниз...")
                    self.driver.execute_script("window.scrollBy(0, window.innerHeight * 1.5);")
                    self._human_delay(3, 5)

            except Exception as e:
                # === БЛОК ОТЛАДКИ ===
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                screenshot_name = f"error_{timestamp}.png"
                html_name = f"error_{timestamp}.html"

                # Пути внутри папки static
                screenshot_path_rel = os.path.join(self.DEBUG_FOLDER, screenshot_name)
                html_path_rel = os.path.join(self.DEBUG_FOLDER, html_name)

                # Абсолютные пути для сохранения
                screenshot_path_abs = os.path.join('static', screenshot_path_rel)
                html_path_abs = os.path.join('static', html_path_rel)

                print(f"!!! КРИТИЧЕСКАЯ ОШИБКА. Сохраняю отладочную информацию... !!!")
                self.log(f"!!! КРИТИЧЕСКАЯ ОШИБКА. Сохраняю отладочную информацию... !!!")
                self.driver.save_screenshot(screenshot_path_abs)

                with open(html_path_abs, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)

                self.log(f"  - Скриншот: /static/{screenshot_path_rel}")
                self.log(f"  - HTML: /static/{html_path_rel}")
                self.log(f"  - Текст ошибки: {e}. Прерываем сбор.")
                break

        return list(products_links_set)

    def parse_product_page(self, url: str) -> dict[str, Any]:
        """Парсит одну страницу товара и возвращает словарь с данными."""

        self.log(f"Парсинг страницы: {url[:60]}...")
        self.driver.get(url)
        self._human_delay(2, 4)

        product_data = { "title": None, "price": None, "rating": None, "reviews_count": None, "url": url }

        try:
            # Название
            product_data["title"] = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                    ).text

            # Цена
            price_element = self.driver.find_element(By.CSS_SELECTOR,
                                                     "div[data-widget='webPrice'] span.tsHeadline600Large"
                                                     )
            product_data["price"] = int(price_element.text.replace(' ', '').replace('₽', '').strip())

            # Рейтинг и отзывы
            rating_reviews_element = self.driver.find_element(By.CSS_SELECTOR,
                                                              "div[data-widget='webSingleProductScore'] div"
                                                              )
            parts = rating_reviews_element.text.split('•')

            if len(parts) == 2:
                product_data["rating"] = float(parts[0].strip())
                product_data["reviews_count"] = int(re.sub(r'[^0-9]', '', parts[1]))

            self.log(f"  - Успешно: {product_data['title'][:30]}...")

        except Exception as e:
            self.log(f"  - Ошибка парсинга данных на странице {url}: {e}")

        return product_data
