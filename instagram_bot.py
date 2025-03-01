from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
import requests
import random
import time
from faker import Faker
import json
import os

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_proxy = None
        self.working_proxies = []  # Çalışan proxyleri sakla
        self.working_proxies_file = 'working_proxies.txt'
        self.proxy_sources = [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=yes&anonymity=all",
            "https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps"
        ]
        self.load_working_proxies()

    def load_working_proxies(self):
        """Daha önce çalışan proxyleri yükle"""
        try:
            if os.path.exists(self.working_proxies_file):
                with open(self.working_proxies_file, 'r') as f:
                    self.working_proxies = [line.strip() for line in f if line.strip()]
                print(f"{len(self.working_proxies)} adet kayıtlı proxy yüklendi")
        except:
            self.working_proxies = []

    def save_working_proxy(self, proxy):
        """Çalışan proxy'i kaydet"""
        if proxy and proxy not in self.working_proxies:
            self.working_proxies.append(proxy)
            try:
                with open(self.working_proxies_file, 'a') as f:
                    f.write(f"{proxy}\n")
            except:
                pass

    def test_proxy(self, proxy, quick=True):
        """Proxy test et"""
        try:
            timeout = 5 if quick else 10
            response = requests.get(
                'https://www.instagram.com',
                proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'},
                timeout=timeout
            )
            return response.status_code == 200
        except:
            return False

    def get_working_proxy(self):
        """Çalışan proxy bul - önce kayıtlı proxylerden dene"""
        # Önce kayıtlı proxyleri dene
        if self.working_proxies:
            random.shuffle(self.working_proxies)
            for proxy in self.working_proxies[:3]:  # İlk 3 kayıtlı proxy'i dene
                print(f"Kayıtlı proxy test ediliyor: {proxy}")
                if self.test_proxy(proxy, quick=True):
                    self.current_proxy = proxy
                    print(f"✓ Çalışan proxy bulundu: {proxy}")
                    return proxy

        # Yeni proxy listesi yükle
        for source in self.proxy_sources:
            try:
                print(f"Proxy kaynağı kontrol ediliyor: {source}")
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    if source.endswith('.txt'):
                        proxies = response.text.strip().split('\n')
                    else:  # JSON API
                        data = response.json()
                        proxies = [f"{p['ip']}:{p['port']}" for p in data.get('data', [])]
                    
                    # Her proxy'i test et
                    for proxy in proxies:
                        proxy = proxy.strip()
                        if proxy:
                            print(f"Yeni proxy test ediliyor: {proxy}")
                            if self.test_proxy(proxy):
                                self.current_proxy = proxy
                                self.save_working_proxy(proxy)
                                print(f"✓ Çalışan proxy bulundu: {proxy}")
                                return proxy
                
            except Exception as e:
                print(f"Proxy kaynağı hatası ({source}): {e}")
                continue

        return None

class InstagramBot:
    def __init__(self):
        self.fake = Faker('tr_TR')
        self.proxy_manager = ProxyManager()
        self.driver = None
        self.wait = None
        self.log_file = 'instagram_bot.log'
        self.account_file = 'instagram_accounts.txt'

    def log(self, message):
        """Log kaydı tut"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"{timestamp} - {message}\n"
        print(message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message)

    def setup_driver(self):
        """Tarayıcıyı proxy ile başlat"""
        try:
            if self.driver:
                self.driver.quit()

            proxy = self.proxy_manager.get_working_proxy()
            if not proxy:
                raise Exception("Çalışan proxy bulunamadı!")

            options = uc.ChromeOptions()
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument(f'--proxy-server=http://{proxy}')
            options.add_argument('--lang=tr-TR')
            
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 20)
            return True

        except Exception as e:
            self.log(f"Tarayıcı hatası: {e}")
            return False

    def find_element_with_wait(self, by, value, timeout=10, condition="presence"):
        """Element bekleyerek bul"""
        try:
            if condition == "clickable":
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
            else:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            return element
        except TimeoutException:
            self.log(f"Element bulunamadı: {value}")
            return None

    def human_type(self, element, text):
        """İnsan gibi yaz"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.5, 1.0))

    def handle_verification(self):
        """Yaş doğrulama formunu doldur"""
        try:
            # Ay seçimi
            month_select = self.find_element_with_wait(
                By.CSS_SELECTOR, 
                'select[title="Ay:"]'
            )
            if month_select:
                month = random.randint(1, 12)
                month_select.send_keys(str(month))
                time.sleep(random.uniform(0.5, 1.0))

                # Gün seçimi
                day_select = self.find_element_with_wait(
                    By.CSS_SELECTOR, 
                    'select[title="Gün:"]'
                )
                if day_select:
                    day = random.randint(1, 28)
                    day_select.send_keys(str(day))
                    time.sleep(random.uniform(0.5, 1.0))

                # Yıl seçimi
                year_select = self.find_element_with_wait(
                    By.CSS_SELECTOR, 
                    'select[title="Yıl:"]'
                )
                if year_select:
                    year = random.randint(1985, 2000)
                    year_select.send_keys(str(year))
                    time.sleep(random.uniform(0.5, 1.0))

                # İleri butonu
                next_button = self.find_element_with_wait(
                    By.XPATH,
                    "//button[text()='İleri']",
                    condition="clickable"
                )
                if next_button:
                    next_button.click()
                    time.sleep(random.uniform(2, 3))
                    return True

        except Exception as e:
            self.log(f"Yaş doğrulama hatası: {e}")
        return False

    def create_account(self):
        """Instagram hesabı oluştur"""
        try:
            if not self.setup_driver():
                return False

            self.log("Instagram kayıt sayfası açılıyor...")
            self.driver.get('https://www.instagram.com/accounts/emailsignup/')
            time.sleep(random.uniform(2, 4))

            # Hesap bilgileri oluştur
            email = self.fake.email()
            full_name = self.fake.name()
            username = f"tr_{self.fake.user_name()}_{random.randint(100,999)}"
            password = f"Tr{self.fake.password(length=10)}#1"

            # Form doldur
            fields = {
                'emailOrPhone': (email, 'Email'),
                'fullName': (full_name, 'Ad Soyad'),
                'username': (username, 'Kullanıcı Adı'),
                'password': (password, 'Şifre')
            }

            for field_name, (value, field_type) in fields.items():
                element = self.find_element_with_wait(By.NAME, field_name)
                if not element:
                    raise Exception(f"{field_type} alanı bulunamadı")
                self.human_type(element, value)

            # Kayıt ol butonu
            submit_button = self.find_element_with_wait(
                By.XPATH,
                '//button[@type="submit"]',
                condition="clickable"
            )
            if submit_button:
                submit_button.click()
                time.sleep(random.uniform(3, 5))
            else:
                raise Exception("Kayıt butonu bulunamadı")

            # Yaş doğrulama
            if not self.handle_verification():
                self.log("Yaş doğrulama tamamlanamadı")

            # Hesap bilgilerini kaydet
            account_info = {
                "tarih": time.strftime('%Y-%m-%d %H:%M:%S'),
                "email": email,
                "kullanici_adi": username,
                "sifre": password,
                "proxy": self.proxy_manager.current_proxy
            }

            with open(self.account_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(account_info, ensure_ascii=False) + '\n')
                f.write('-' * 50 + '\n')

            self.log("Hesap bilgileri kaydedildi!")
            
            # CAPTCHA kontrolü
            input("\nCAPTCHA varsa tamamlayın ve Enter'a basın...")
            return True

        except Exception as e:
            self.log(f"Hesap oluşturma hatası: {e}")
            return False

        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("""
    Instagram Hesap Oluşturucu v2.0
    -------------------------------
    - Proxy rotasyonu aktif
    - İnsan benzeri davranış
    - Otomatik yaş doğrulama
    - Log kaydı
    - Hesap bilgileri JSON formatında
    """)

    bot = InstagramBot()
    
    while True:
        bot.create_account()
        choice = input("\nYeni hesap oluşturulsun mu? (E/H): ").lower()
        if choice != 'e':
            break

if __name__ == "__main__":
    main()