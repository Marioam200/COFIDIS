from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

class ProCyclingStatsScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.maximize_window()
        self.base_url = "https://www.procyclingstats.com/"
        self.wait = WebDriverWait(self.driver, 15) # Espera explícita
        
        if not os.path.exists('data'):
            os.makedirs('data')

    def resolver_captcha(self):
        try:
            time.sleep(3)
            iframe = self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
            self.driver.switch_to.frame(iframe)
            checkbox = self.driver.find_element(By.ID, "recaptcha-anchor")
            checkbox.click()
            self.driver.switch_to.default_content()
            time.sleep(5) 
        except Exception:
            self.driver.switch_to.default_content()

    def accept_cookies(self):
        self.driver.get(self.base_url + "races.php")
        time.sleep(2)
        try:
            # Uso de espera explícita como en tu segundo código
            cookies_accept = self.wait.until(EC.element_to_be_clickable((By.ID, "cmpbntyestxt")))
            cookies_accept.click()
        except Exception:
            self.resolver_captcha()

    def search_C25(self):
        self.driver.get(self.base_url + "races.php")
        
        try:
            self.wait.until(EC.presence_of_element_located((By.NAME, "year")))
            select_year = Select(self.driver.find_element(By.NAME, "year"))
            select_year.select_by_value("2025")
            
            self.wait.until(EC.presence_of_element_located((By.NAME, "circuit")))
            select_circuit = Select(self.driver.find_element(By.NAME, "circuit"))
            select_circuit.select_by_value("") # El valor "" corresponde a '-' (Todos)
            
            boton_filter = self.wait.until(EC.element_to_be_clickable((By.NAME, "filter")))
            boton_filter.click()
            
            time.sleep(5) 
            
        except Exception as e:
            print(f"❌ Error al aplicar filtros: {e}")

    def extract_calendar_to_csv(self, file_name="calendario_uci_2025.csv"):
        path_final = os.path.join('data', file_name)
        
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.basic")))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            table_body = soup.find('table', class_='basic').find('tbody')
            
            if not table_body:
                print("No se encontró el cuerpo de la tabla.")
                return None
                
            data = []
            rows = table_body.find_all('tr')
            for row in rows:
                cols = row.find_all('td')

                if len(cols) >= 5:
                    data.append({
                        'Date': cols[0].get_text(strip=True),
                        'Race': cols[2].get_text(strip=True),
                        'Winner': cols[3].get_text(strip=True),
                        'Class': cols[4].get_text(strip=True)
                    })
            
            df = pd.DataFrame(data)
            df.to_csv(path_final, index=False, encoding='utf-8-sig')
            print(f" Calendario exportado con {len(df)} carreras: {path_final}")
            return df

        except Exception as e:
            print(f" Error extrayendo la tabla: {e}")
            return None

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = ProCyclingStatsScraper() 
    try:
        scraper.accept_cookies()
        scraper.search_C25()
        scraper.extract_calendar_to_csv("calendario_uci_2025.csv")
    finally:
        scraper.close()