from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
import requests
import random
import time
from faker import Faker
import json
import os
import imaplib
import email
import re
from datetime import datetime
import string

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
    def __init__(self, gmail_address, gmail_app_password):
        """
        gmail_address: Ana Gmail adresi
        gmail_app_password: Gmail'den alınan uygulama şifresi
        """
        self.base_email = gmail_address
        self.gmail_password = gmail_app_password
        self.current_email = None
        self.fake = Faker()
        
        # Chrome ayarları
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--lang=tr-TR')
        # chrome_options.add_argument('--headless')  # Tarayıcıyı başsız modda çalıştırır
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # WebDriver kurulumu
        self.driver = uc.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

    def create_gmail_alias(self):
        """Gmail alias oluştur - Instagram uyumlu format"""
        try:
            base_name = self.base_email.split('@')[0]
            domain = self.base_email.split('@')[1]
            # Kullanıcı adınıza özel bir ön ek ekleyin
            timestamp = int(time.time())
            unique_id = f"inst{timestamp}"
            
            # base_name ve unique_id'yi birleştir
            self.current_email = f"{base_name}.{unique_id}@{domain}"
            print(f"Oluşturulan Gmail adresi: {self.current_email}")
            return self.current_email
        except Exception as e:
            print(f"Gmail adresi oluşturma hatası: {e}")
            return None
    
    def get_verification_code(self, max_attempts=30, delay=10):
        """Gmail'den doğrulama kodunu al"""
        print("\nDoğrulama kodu bekleniyor...")
        
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.base_email, self.gmail_password)
            
            for attempt in range(max_attempts):
                try:
                    mail.select("INBOX")
                    search_criteria = '(FROM "security@mail.instagram.com" UNSEEN)'
                    _, message_numbers = mail.search(None, search_criteria)
                    
                    if message_numbers[0]:
                        for num in message_numbers[0].split():
                            _, msg_data = mail.fetch(num, "(RFC822)")
                            email_body = msg_data[0][1]
                            email_message = email.message_from_bytes(email_body)
                            
                            # Mail içeriğini al
                            body = ""
                            if email_message.is_multipart():
                                for part in email_message.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                                        break
                            else:
                                body = email_message.get_payload(decode=True).decode()
                            
                            # Doğrulama kodunu bul (6 haneli)
                            code_match = re.search(r'\b\d{6}\b', body)
                            if code_match:
                                code = code_match.group(0)
                                print(f"Doğrulama kodu bulundu: {code}")
                                mail.close()
                                mail.logout()
                                return code
                            
                    print(f"Doğrulama kodu bekleniyor... Deneme {attempt + 1}/{max_attempts}")
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"Mail kontrol hatası: {e}")
                    continue
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"Mail sunucusu hatası: {e}")
        
        return None

    def wait_for_element(self, by, value, timeout=20, condition="present"):
        """Element bekle"""
        try:
            if condition == "clickable":
                return self.wait.until(EC.element_to_be_clickable((by, value)))
            else:
                return self.wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            print(f"Element bulunamadı: {value}")
            return None

    def handle_age_verification(self):
        """Yaş doğrulama formunu doldur"""
        try:
            time.sleep(2)
            # Yaş doğrulama formu kontrolü
            month_select = self.wait_for_element(By.XPATH, "//select[@title='Ay:']", timeout=5)
            if not month_select:
                return True

            print("Yaş doğrulama işlemi yapılıyor...")
            
            # Rastgele tarih oluştur (18-30 yaş arası)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            year = datetime.now().year - random.randint(18, 30)
            
            # Ay seç
            month_select.send_keys(f"{month}")
            time.sleep(random.uniform(0.5, 1.0))
            
            # Gün seç
            day_select = self.driver.find_element(By.XPATH, "//select[@title='Gün:']")
            day_select.send_keys(f"{day}")
            time.sleep(random.uniform(0.5, 1.0))
            
            # Yıl seç
            year_select = self.driver.find_element(By.XPATH, "//select[@title='Yıl:']")
            year_select.send_keys(f"{year}")
            time.sleep(random.uniform(0.5, 1.0))
            
            # İleri butonunu bul ve tıkla
            for button_text in ['İleri', 'Next']:
                try:
                    next_button = self.driver.find_element(By.XPATH, f"//button[text()='{button_text}']")
                    next_button.click()
                    print("Yaş doğrulama tamamlandı")
                    return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Yaş doğrulama hatası: {e}")
            return False

    def create_account(self):
        """Instagram hesabı oluştur"""
        try:
            # Gmail alias oluştur
            email = self.create_gmail_alias()
            if not email:
                raise Exception("Email oluşturulamadı")

            # Instagram'ı aç
            self.driver.get('https://www.instagram.com/accounts/emailsignup/')
            print("Instagram kayıt sayfası açıldı")
            time.sleep(random.uniform(2, 4))

            # Fake bilgiler oluştur
            username = f"{self.fake.user_name()}_{random.randint(100,999)}"
            password = f"Pass_{self.fake.password(length=10)}#1"
            full_name = self.fake.name()

            # Form elemanlarını bul ve doldur
            fields = {
                'emailOrPhone': email,
                'fullName': full_name,
                'username': username,
                'password': password
            }

            for field_name, value in fields.items():
                try:
                    field = self.wait_for_element(By.NAME, field_name)
                    if field:
                        field.send_keys(value)
                        time.sleep(random.uniform(0.5, 1.0))
                except Exception as e:
                    print(f"{field_name} alanı doldurma hatası: {e}")
                    raise

            # Submit butonunu bul ve tıkla
            submit_button = self.wait_for_element(By.XPATH, '//button[@type="submit"]', condition="clickable")
            if submit_button:
                submit_button.click()
                print("Form gönderildi")
                time.sleep(random.uniform(2, 4))
            else:
                raise Exception("Submit butonu bulunamadı")

            # Yaş doğrulama
            if not self.handle_age_verification():
                print("Yaş doğrulama başarısız olabilir")

            # Doğrulama kodunu bekle ve gir
            verification_code = self.get_verification_code()
            if verification_code:
                # Doğrulama kod alanını bul
                code_input = self.wait_for_element(
                    By.XPATH, 
                    "//input[@aria-label='Güvenlik Kodu' or @aria-label='Security Code']"
                )
                if code_input:
                    code_input.send_keys(verification_code)
                    time.sleep(random.uniform(1, 2))
                    
                    # Onayla butonunu bul ve tıkla
                    confirm_button = self.wait_for_element(
                        By.XPATH, 
                        "//button[contains(text(), 'Onayla') or contains(text(), 'Confirm')]",
                        condition="clickable"
                    )
                    if confirm_button:
                        confirm_button.click()
                        print("Doğrulama kodu girildi")
                    else:
                        print("Onayla butonu bulunamadı")
                else:
                    print("Doğrulama kodu giriş alanı bulunamadı")
            else:
                print("Doğrulama kodu alınamadı")

            # Hesap bilgilerini kaydet
            self.save_account_details(email, username, password)
            print("\nHesap oluşturma işlemi tamamlandı!")
            return True

        except Exception as e:
            print(f"Hesap oluşturma hatası: {e}")
            return False

    def save_account_details(self, email, username, password):
        """Hesap bilgilerini kaydet"""
        try:
            with open('hesap_kayitlari.txt', 'a', encoding='utf-8') as f:
                f.write(f"\nKayıt Zamanı: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Email: {email}\n")
                f.write(f"Kullanıcı Adı: {username}\n")
                f.write(f"Şifre: {password}\n")
                f.write("-" * 50 + "\n")
            print("\nHesap bilgileri 'hesap_kayitlari.txt' dosyasına kaydedildi")
        except Exception as e:
            print(f"Bilgi kaydetme hatası: {e}")

if __name__ == "__main__":
    # Gmail bilgilerinizi girin
    GMAIL_ADDRESS = "siyahmakalem@gmail.com"  # Gmail adresinizi girin
    GMAIL_APP_PASSWORD = "knig sptg hcgh axfw" # Gmail uygulama şifrenizi girin
    
    print("Instagram Bot başlatılıyor...")
    print("Not: CAPTCHA görünürse manuel olarak tamamlamanız gerekebilir.")
    
    bot = InstagramBot(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    success = bot.create_account()
    
    if not success:
        print("Hesap oluşturulamadı")
    
    input("\nÇıkmak için Enter'a basın...")