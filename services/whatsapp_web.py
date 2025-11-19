from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep

class WhatsAppWeb:
    def __init__(self):
        self.driver = None

    def start(self):
        self.driver = webdriver.Chrome()
        self.driver.get("https://web.whatsapp.com")
        input("Após escanear o QR Code, pressione ENTER...")

    def send(self, number, message):
        try:
            url = f"https://web.whatsapp.com/send?phone={number}&text={message}"
            self.driver.get(url)
            sleep(7)

            box = self.driver.find_element(By.XPATH, "//div[@title='Mensagem']")
            box.send_keys(Keys.ENTER)
            return True, "Sent"

        except Exception as e:
            return False, str(e)

    def close(self):
        if self.driver:
            self.driver.quit()
