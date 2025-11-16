# _1a_Class_BrowserManager.py

import os
import traceback

# Используем стандартный Selenium и его помощников
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

from pyvirtualdisplay import Display

CHROME_BINARY_PATH = "/usr/bin/google-chrome-stable"

# Директория для хранения профиля Chrome.
# Используем новую папку, чтобы избежать конфликтов со старыми профилями.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(APP_DIR, "chrome_profile_stealth")


class BrowserManager:
    """
    Контекстный менеджер для управления жизненным циклом драйвера Selenium.
    Использует selenium-stealth для маскировки от обнаружения.
    Гарантирует, что браузер будет всегда корректно закрыт.
    """

    def __init__(self, logger_callback=print, use_virtual_display: bool = True):
        """Инициализация менеджера."""

        self.log = logger_callback
        self.driver = None

        options = webdriver.ChromeOptions()
        # Отключаем флаги, которые могут выдавать автоматизацию
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # ВАЖНО: Добавляем headless режим
        options.add_argument('--headless=new')  # Используйте 'new' для современных версий Chrome

        # Стандартные аргументы для стабильности
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f'--user-data-dir={USER_DATA_DIR}')

        self.use_virtual_display = use_virtual_display
        self.display = None
        self._options = options

    def __enter__(self) -> webdriver.Chrome | None:
        """Метод, вызываемый при входе в блок 'with'."""

        self.log("Запуск браузера с selenium-stealth...")

        try:
            if self.use_virtual_display:
                self.log("Запуск виртуального дисплея...")
                self.display = Display(visible=False, size=(1920, 1080))
                self.display.start()
                self.log(f"Виртуальный дисплей запущен на DISPLAY={self.display.display}.")
                os.environ['DISPLAY'] = f':{self.display.display}'

            # webdriver-manager автоматически скачает и установит подходящий chromedriver
            self.log("Установка/поиск chromedriver...")
            service = ChromeService(ChromeDriverManager().install())
            self.log("Запуск webdriver.Chrome...")
            self.driver = webdriver.Chrome(service=service, options=self._options)
            self.log("Применение stealth-патчей...")

            # Применяем stealth-патчи для маскировки
            stealth(self.driver,
                    languages=["ru-RU", "ru"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )

            self.log("Браузер и selenium-stealth успешно запущены.")
            return self.driver

        except Exception as e:
            self.log("!!! КРИТИЧЕСКАЯ ОШИБКА при запуске браузера со stealth !!!")
            self.log(f"Ошибка: {e}")
            self.log("Трассировка:")
            self.log(traceback.format_exc())
            if self.display:
                self.display.stop()
            return None

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Метод, вызываемый при выходе из блока 'with' (даже при ошибках)."""

        if self.driver:
            self.log("Закрытие браузера...")
            self.driver.quit()

        if self.display:
            self.log("Остановка виртуального дисплея...")
            self.display.stop()

        self.log("Браузер закрыт.")
