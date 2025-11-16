# _1a_Class_BrowserManager.py

import os
import traceback

import undetected_chromedriver as uc
from pyvirtualdisplay import Display

CHROME_BINARY_PATH = "/usr/bin/google-chrome-stable"

# Директория для хранения профиля Chrome
APP_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(APP_DIR, "chrome_profile")


class BrowserManager:
    """
    Контекстный менеджер для управления жизненным циклом драйвера Selenium.
    Гарантирует, что браузер будет всегда корректно закрыт.
    """

    def __init__(self, logger_callback=print, use_virtual_display: bool = True):
        """Инициализация менеджера."""

        self.log = logger_callback
        self.driver = None
        options = uc.ChromeOptions()
        prefs = { "profile.default_content_setting_values.geolocation": 2 }
        options.add_experimental_option("prefs", prefs)

        # Добавляем аргументы для запуска в "безголовом" режиме на сервере
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')

        self.use_virtual_display = use_virtual_display
        self.display = None

        # Явно указываем директорию для данных пользователя
        options.add_argument(f'--user-data-dir={USER_DATA_DIR}')

        self._options = options

    def __enter__(self) -> uc.Chrome | None:
        """Метод, вызываемый при входе в блок 'with'."""

        self.log("Запуск браузера...")

        try:
            if self.use_virtual_display:
                self.log("Запуск виртуального дисплея...")
                self.display = Display(visible=False, size=(1920, 1080))
                self.display.start()
                self.log(f"Виртуальный дисплей запущен на DISPLAY={self.display.display}.")

                os.environ['DISPLAY'] = f':{self.display.display}'

            self.driver = uc.Chrome(options=self._options)  # , browser_executable_path=CHROME_BINARY_PATH)
            self.log("Браузер успешно запущен.")
            return self.driver

        except Exception as e:
            print("!!! КРИТИЧЕСКАЯ ОШИБКА при запуске uc.Chrome !!!")
            print(f"Ошибка: {e}")
            print("Трассировка:")
            traceback.print_exc()
            # Важно вернуть None или возбудить исключение, чтобы не выполнять блок with
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
