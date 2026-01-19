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
        """
        Selecciona el año 2025 y el circuito 'All' para obtener el calendario completo.
        """
        print("🔍 Configurando filtros para el calendario 2025...")
        self.driver.get(self.base_url + "races.php")
        
        try:
            # 1. Esperar y seleccionar AÑO 2025
            self.wait.until(EC.presence_of_element_located((By.NAME, "year")))
            select_year = Select(self.driver.find_element(By.NAME, "year"))
            select_year.select_by_value("2025")
            
            # 2. Esperar y seleccionar CIRCUITO (Vacío = All)
            self.wait.until(EC.presence_of_element_located((By.NAME, "circuit")))
            select_circuit = Select(self.driver.find_element(By.NAME, "circuit"))
            select_circuit.select_by_value("") # El valor "" corresponde a '-' (Todos)
            
            # 3. Pulsar botón Filter
            boton_filter = self.wait.until(EC.element_to_be_clickable((By.NAME, "filter")))
            boton_filter.click()
            
            # Espera a que la URL cambie o la tabla se refresque
            time.sleep(5) 
            print("✅ Filtros aplicados correctamente.")
            
        except Exception as e:
            print(f"❌ Error al aplicar filtros: {e}")

    def extract_calendar_to_csv(self, file_name="calendario_uci_2025.csv"):
        print("📊 Extrayendo tabla de carreras...")
        path_final = os.path.join('data', file_name)
        
        try:
            # Esperar a que la tabla aparezca después del filtrado
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
                # Filtramos filas que no son de carreras (algunas filas son separadores de meses)
                if len(cols) >= 5:
                    data.append({
                        'Date': cols[0].get_text(strip=True),
                        'Race': cols[2].get_text(strip=True),
                        'Winner': cols[3].get_text(strip=True),
                        'Class': cols[4].get_text(strip=True)
                    })
            
            df = pd.DataFrame(data)
            df.to_csv(path_final, index=False, encoding='utf-8-sig')
            print(f"✅ Calendario exportado con {len(df)} carreras: {path_final}")
            return df

        except Exception as e:
            print(f"❌ Error extrayendo la tabla: {e}")
            return None

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = ProCyclingStatsScraper("General") 
    try:
        scraper.accept_cookies()
        scraper.search_C25()
        scraper.extract_calendar_to_csv("calendario_uci_2025.csv")
    finally:
        scraper.close()