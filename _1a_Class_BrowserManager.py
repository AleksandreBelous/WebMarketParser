# _1a_Class_BrowserManager.py

import os
import traceback
import zipfile

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
    Поддерживает работу через прокси с аутентификацией.
    """

    def __init__(self, logger_callback=print, use_virtual_display: bool = True, proxy: dict = None):
        """
        Инициализация менеджера.
        :param logger_callback: Функция для логирования.
        :param use_virtual_display: Использовать ли виртуальный дисплей (для серверов).
        :param proxy: Словарь с настройками прокси, например:
                      {
                          "host": "proxy.example.com",
                          "port": 8080,
                          "user": "proxy_user",
                          "pass": "proxy_password"
                      }
        """
        self.log = logger_callback
        self.driver = None
        self.proxy = proxy
        self._options = self._create_chrome_options()
        self.use_virtual_display = use_virtual_display
        self.display = None

    def _create_chrome_options(self) -> uc.ChromeOptions:
        """Создает и настраивает опции для Chrome."""
        options = uc.ChromeOptions()
        prefs = {
            "profile.default_content_setting_values.geolocation": 2,  # Запретить геолокацию
            "credentials_enable_service": False,  # Отключить менеджер паролей
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option("prefs", prefs)

        # Стандартные аргументы для стабильности
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-blink-features=AutomationControlled") # Дополнительная маскировка
        options.add_argument(f'--user-data-dir={USER_DATA_DIR}') # Явно указываем директорию для данных пользователя
        options.add_argument("--start-maximized") # Запуск в максимальном окне

        # Установка прокси, если он предоставлен
        if self.proxy:
            self.log(f"Настройка прокси: {self.proxy['host']}:{self.proxy['port']}")
            proxy_extension = self._create_proxy_extension()
            options.add_extension(proxy_extension)

        return options

    def _create_proxy_extension(self) -> str:
        """Создает временное расширение для Chrome для аутентификации на прокси."""
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            }
        }
        """
        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{self.proxy['host']}",
                    port: parseInt({self.proxy['port']})
                }},
                bypassList: ["localhost"]
            }}
        }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{self.proxy['user']}",
                    password: "{self.proxy['pass']}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """
        proxy_dir = os.path.join(APP_DIR, 'proxy_extension')
        os.makedirs(proxy_dir, exist_ok=True)

        manifest_path = os.path.join(proxy_dir, 'manifest.json')
        with open(manifest_path, 'w') as f:
            f.write(manifest_json)

        background_path = os.path.join(proxy_dir, 'background.js')
        with open(background_path, 'w') as f:
            f.write(background_js)
        
        # Запаковываем расширение в zip-архив, который будет добавлен в Chrome
        zip_path = os.path.join(APP_DIR, 'proxy.zip')
        with zipfile.ZipFile(zip_path, 'w') as zp:
            zp.write(manifest_path, 'manifest.json')
            zp.write(background_path, 'background.js')

        return zip_path

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

            self.driver = uc.Chrome(options=self._options)
            self.log("Браузер успешно запущен.")
            return self.driver

        except Exception as e:
            self.log("!!! КРИТИЧЕСКАЯ ОШИБКА при запуске uc.Chrome !!!")
            self.log(f"Ошибка: {e}")
            self.log("Трассировка:")
            self.log(traceback.format_exc())
            # Важно вернуть None или возбудить исключение, чтобы не выполнять блок with
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

        # Удаляем временные файлы прокси-расширения
        proxy_zip = os.path.join(APP_DIR, 'proxy.zip')
        if os.path.exists(proxy_zip):
            os.remove(proxy_zip)
        
        proxy_dir = os.path.join(APP_DIR, 'proxy_extension')
        if os.path.exists(proxy_dir):
            # os.rmdir(proxy_dir) # This will fail if not empty, good enough for now
            import shutil
            shutil.rmtree(proxy_dir)
        
        self.log("Браузер закрыт.")
