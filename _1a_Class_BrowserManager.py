# _1a_Class_BrowserManager.py

import undetected_chromedriver as uc


class BrowserManager:
    """
    Контекстный менеджер для управления жизненным циклом драйвера Selenium.
    Гарантирует, что браузер будет всегда корректно закрыт.
    """

    def __init__(self) -> None:
        """Инициализация менеджера."""

        self.driver = None
        options = uc.ChromeOptions()
        prefs = { "profile.default_content_setting_values.geolocation": 2 }
        options.add_experimental_option("prefs", prefs)
        self._options = options

    def __enter__(self) -> uc.Chrome:
        """Метод, вызываемый при входе в блок 'with'."""

        print("Запуск браузера...")
        self.driver = uc.Chrome(options=self._options)
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Метод, вызываемый при выходе из блока 'with' (даже при ошибках)."""

        if self.driver:
            print("Закрытие браузера...")
            self.driver.quit()
        print("Браузер закрыт.")
