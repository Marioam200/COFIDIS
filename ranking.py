from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

class ProCyclingStatsScraper:
    def __init__(self, team_name: str):
        self.team_name = team_name
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.maximize_window()
        self.base_url = "https://www.procyclingstats.com/"
        self.wait = WebDriverWait(self.driver, 15)
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
        self.driver.get(self.base_url + "rankings.php")
        time.sleep(2)
        try:
            cookies_accept = self.wait.until(EC.element_to_be_clickable((By.ID, "cmpbntyestxt")))
            cookies_accept.click()
        except Exception:
            self.resolver_captcha()

    def extract_full_ranking(self, file_name="ranking_completo_2025.csv"):
        try:
            self.driver.get(self.base_url + "rankings.php")
            
            # 1. Obtener la lista de valores (0, 100, 200...) antes de empezar el bucle
            self.wait.until(EC.presence_of_element_located((By.NAME, "offset")))
            select_element = Select(self.driver.find_element(By.NAME, "offset"))
            offsets = [opt.get_attribute("value") for opt in select_element.options]
            
            all_riders_data = []

            # 2. Bucle para recorrer cada rango
            for val in offsets:
                # Re-localizar el select en cada iteración porque la página se refresca
                select_elem = self.wait.until(EC.presence_of_element_located((By.NAME, "offset")))
                select_obj = Select(select_elem)
                select_obj.select_by_value(val)
                
                # Clic en filtrar
                self.driver.find_element(By.NAME, "filter").click()
                
                # Espera obligatoria para que la tabla cambie de datos
                time.sleep(5)
                
                # 3. Extraer los datos de la tabla actual
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                table = soup.find('table', class_='basic')
                rows = table.find('tbody').find_all('tr')

                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 7:
                        all_riders_data.append({
                            'Rank': cols[0].get_text(strip=True),
                            'Rider': cols[4].get_text(strip=True).replace('H2H', '').strip(),
                            'Team': cols[5].get_text(strip=True),
                            'Points': cols[6].get_text(strip=True)
                        })

            # 4. Guardar todos los datos acumulados (deberían ser ~2523 filas)
            df = pd.DataFrame(all_riders_data)
            path_final = os.path.join('data', file_name)
            df.to_csv(path_final, index=False, encoding='utf-8-sig')
            return df
            
        except Exception:
            return None

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = ProCyclingStatsScraper(team_name="General")
    try:
        scraper.accept_cookies()
        scraper.extract_full_ranking("PCS_Ranking_Completo.csv")
    finally:
        scraper.close()