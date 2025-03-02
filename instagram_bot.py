from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
import requests
import random
import time
from faker import Faker
import csv
import os
import imaplib
import email
import re
from datetime import datetime

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_proxy = None
        self.working_proxies = []
        self.working_proxies_file = 'working_proxies.txt'
        self.proxy_sources = [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=yes&anonymity=all",
            "https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps"
        ]
        self.load_working_proxies()

    def load_working_proxies(self):
        try:
            if os.path.exists(self.working_proxies_file):
                with open(self.working_proxies_file, 'r') as f:
                    self.working_proxies = [line.strip() for line in f if line.strip()]
                print(f"{len(self.working_proxies)} adet kayıtlı proxy yüklendi")
        except:
            self.working_proxies = []

    def save_working_proxy(self, proxy):
        if proxy and proxy not in self.working_proxies:
            self.working_proxies.append(proxy)
            try:
                with open(self.working_proxies_file, 'a') as f:
                    f.write(f"{proxy}\n")
            except:
                pass

    def test_proxy(self, proxy, quick=True):
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
        if self.working_proxies:
            random.shuffle(self.working_proxies)
            for proxy in self.working_proxies[:3]:
                print(f"Kayıtlı proxy test ediliyor: {proxy}")
                if self.test_proxy(proxy, quick=True):
                    self.current_proxy = proxy
                    print(f"✓ Çalışan proxy bulundu: {proxy}")
                    return proxy

        for source in self.proxy_sources:
            try:
                print(f"Proxy kaynağı kontrol ediliyor: {source}")
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    if source.endswith('.txt'):
                        proxies = response.text.strip().split('\n')
                    else:
                        data = response.json()
                        proxies = [f"{p['ip']}:{p['port']}" for p in data.get('data', [])]
                    
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

class GmailAccountCreator:
    def __init__(self):
        self.fake = Faker()
        self.proxy_manager = ProxyManager()
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--lang=en-US')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = uc.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

    def solve_captcha(self, site_key, url):
        api_key = 'your_2captcha_api_key'  # 2Captcha API anahtarınızı buraya ekleyin
        try:
            # CAPTCHA çözme isteği gönder
            captcha_id = requests.post(
                'http://2captcha.com/in.php',
                data={'key': api_key, 'method': 'userrecaptcha', 'googlekey': site_key, 'pageurl': url}
            ).text.split('|')[1]

            # CAPTCHA çözümünü bekle
            recaptcha_answer = requests.get(
                f"http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}"
            ).text

            while 'CAPCHA_NOT_READY' in recaptcha_answer:
                time.sleep(5)
                recaptcha_answer = requests.get(
                    f"http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}"
                ).text

            recaptcha_answer = recaptcha_answer.split('|')[1]
            return recaptcha_answer

        except Exception as e:
            print(f"CAPTCHA çözme hatası: {e}")
            return None

    def create_gmail_account(self):
        try:
            self.driver.get('https://accounts.google.com/signup')
            print("Gmail kayıt sayfası açıldı")
            time.sleep(random.uniform(2, 4))

            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(1000, 9999)}"
            password = f"{self.fake.password(length=15)}#1"

            fields = {
                'firstName': first_name,
                'lastName': last_name,
                'Username': username,
                'Passwd': password,
                'ConfirmPasswd': password
            }

            for field_name, value in fields.items():
                try:
                    field = self.wait.until(EC.presence_of_element_located((By.NAME, field_name)))
                    if field:
                        for char in value:
                            field.send_keys(char)
                            time.sleep(random.uniform(0.1, 0.3))
                        time.sleep(random.uniform(0.5, 1.0))
                except Exception as e:
                    print(f"{field_name} alanı doldurma hatası: {e}")
                    raise

            next_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="accountDetailsNext"]/div/button')))
            if next_button:
                next_button.click()
                print("Form gönderildi")
                time.sleep(random.uniform(2, 4))
            else:
                raise Exception("Next butonu bulunamadı")

            # CAPTCHA çözme
            site_key = self.driver.find_element(By.CLASS_NAME, 'g-recaptcha').get_attribute('data-sitekey')
            captcha_solution = self.solve_captcha(site_key, self.driver.current_url)

            if captcha_solution:
                self.driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML = "{captcha_solution}"')
                self.driver.find_element(By.ID, 'submit').click()
                print("CAPTCHA çözüldü ve form gönderildi")
            else:
                raise Exception("CAPTCHA çözülemedi")

            return {
                'email': f"{username}@gmail.com",
                'password': password
            }

        except Exception as e:
            print(f"Hesap oluşturma hatası: {e}")
            return None

        finally:
            try:
                self.driver.save_screenshot("gmail_son_durum.png")
                print("Son durum ekran görüntüsü kaydedildi: gmail_son_durum.png")
            except:
                pass

            if self.driver:
                self.driver.quit()

class InstagramBot:
    def __init__(self, gmail_address, gmail_app_password):
        self.base_email = gmail_address
        self.gmail_password = gmail_app_password
        self.current_email = None
        self.fake = Faker('tr_TR')
        self.proxy_manager = ProxyManager()
        
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--lang=tr-TR')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        self.driver = uc.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

    def create_gmail_alias(self):
        try:
            base_name = self.base_email.split('@')[0]
            domain = self.base_email.split('@')[1]
            timestamp = int(time.time())
            unique_id = f"inst{timestamp}"
            self.current_email = f"{base_name}.{unique_id}@{domain}"
            print(f"Oluşturulan Gmail adresi: {self.current_email}")
            return self.current_email
        except Exception as e:
            print(f"Gmail adresi oluşturma hatası: {e}")
            return None

    def get_verification_code(self, max_attempts=30, delay=10):
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
                            
                            body = ""
                            if email_message.is_multipart():
                                for part in email_message.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                                        break
                            else:
                                body = email_message.get_payload(decode=True).decode()
                            
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
        try:
            print(f"Aranan element: {value}")
            if condition == "clickable":
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
            else:
                element = self.wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            print(f"Element bulunamadı: {value}")
            try:
                with open("page_source.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print("Sayfa kaynağı 'page_source.html' dosyasına kaydedildi")
            except:
                pass
            return None

    def handle_age_verification(self):
        try:
            time.sleep(2)
            month_select = self.wait_for_element(By.XPATH, "//select[@title='Ay:']", timeout=5)
            if not month_select:
                return True

            print("Yaş doğrulama işlemi yapılıyor...")
            
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            year = datetime.now().year - random.randint(18, 30)
            
            month_select.send_keys(f"{month}")
            time.sleep(random.uniform(0.5, 1.0))
            
            day_select = self.driver.find_element(By.XPATH, "//select[@title='Gün:']")
            day_select.send_keys(f"{day}")
            time.sleep(random.uniform(0.5, 1.0))
            
            year_select = self.driver.find_element(By.XPATH, "//select[@title='Yıl:']")
            year_select.send_keys(f"{year}")
            time.sleep(random.uniform(0.5, 1.0))
            
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

    def enter_verification_code(self, code):
        try:
            code_input_selectors = [
                "//input[@aria-label='Güvenlik Kodu' or @aria-label='Security Code']",
                "//input[@name='email_confirmation_code']",
                "//input[@id='email_confirmation_code']",
                "//input[@placeholder='Güvenlik Kodu' or @placeholder='Security Code']",
                "//input[@type='text' and @inputmode='numeric']",
                "//input[contains(@class, 'confirmation')]",
                "//input[@autocomplete='one-time-code']"
            ]

            code_input = None
            for selector in code_input_selectors:
                try:
                    code_input = self.wait_for_element(By.XPATH, selector, timeout=5)
                    if code_input:
                        print(f"Kod giriş alanı bulundu: {selector}")
                        break
                except:
                    continue

            if code_input:
                for digit in code:
                    code_input.send_keys(digit)
                    time.sleep(random.uniform(0.1, 0.3))
                time.sleep(1)

                confirm_button_selectors = [
                    "//button[contains(text(), 'Onayla')]",
                    "//button[contains(text(), 'Confirm')]",
                    "//button[@type='submit']",
                    "//div[contains(@role, 'button')]//*[contains(text(), 'Onayla')]",
                    "//div[contains(@role, 'button')]//*[contains(text(), 'Confirm')]",
                    "//button[contains(@class, 'submit')]",
                    "//div[@role='button'][text()='İleri']"
                ]

                for selector in confirm_button_selectors:
                    try:
                        confirm_button = self.wait_for_element(
                            By.XPATH,
                            selector,
                            timeout=5,
                            condition="clickable"
                        )
                        if confirm_button:
                            confirm_button.click()
                            print("Doğrulama kodu gönderildi")
                            return True
                    except:
                        continue

                print("Onay butonu bulunamadı")
                return False
            else:
                print("Doğrulama kodu giriş alanı bulunamadı")
                return False

        except Exception as e:
            print(f"Kod girişi hatası: {e}")
            return False

    def create_account(self):
        try:
            email = self.create_gmail_alias()
            if not email:
                raise Exception("Email oluşturulamadı")

            self.driver.get('https://www.instagram.com/accounts/emailsignup/')
            print("Instagram kayıt sayfası açıldı")
            time.sleep(random.uniform(2, 4))

            username = f"{self.fake.user_name()}_{random.randint(100,999)}"
            password = f"Pass_{self.fake.password(length=10)}#1"
            full_name = self.fake.name()

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
                        for char in value:
                            field.send_keys(char)
                            time.sleep(random.uniform(0.1, 0.3))
                        time.sleep(random.uniform(0.5, 1.0))
                except Exception as e:
                    print(f"{field_name} alanı doldurma hatası: {e}")
                    raise

            submit_button = self.wait_for_element(
                By.XPATH, 
                '//button[@type="submit"]', 
                condition="clickable"
            )
            if submit_button:
                submit_button.click()
                print("Form gönderildi")
                time.sleep(random.uniform(2, 4))
            else:
                raise Exception("Submit butonu bulunamadı")

            if not self.handle_age_verification():
                print("Yaş doğrulama başarısız olabilir")

            verification_code = self.get_verification_code()
            if verification_code:
                if self.enter_verification_code(verification_code):
                    print("Kod girişi başarılı!")
                else:
                    print("Kod girişi başarısız")
            else:
                print("Doğrulama kodu alınamadı")

            self.save_account_details(email, username, password)
            return True

        except Exception as e:
            print(f"Hesap oluşturma hatası: {e}")
            return False

        finally:
            try:
                self.driver.save_screenshot("son_durum.png")
                print("Son durum ekran görüntüsü kaydedildi: son_durum.png")
            except:
                pass

            if self.driver:
                self.driver.quit()

    def save_account_details(self, email, username, password):
        try:
            with open('hesap_kayitlari.csv', 'a', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), email, username, password])
            print("\nHesap bilgileri 'hesap_kayitlari.csv' dosyasına kaydedildi")
        except Exception as e:
            print(f"Bilgi kaydetme hatası: {e}")

if __name__ == "__main__":
    print("Instagram Bot başlatılıyor...")
    print("Not: CAPTCHA görünürse manuel olarak tamamlamanız gerekebilir.")
    
    gmail_creator = GmailAccountCreator()
    gmail_account = gmail_creator.create_gmail_account()
    
    if gmail_account:
        instagram_bot = InstagramBot(gmail_account['email'], gmail_account['password'])
        if instagram_bot.create_account():
            print("Instagram hesabı başarıyla oluşturuldu")
        else:
            print("Instagram hesabı oluşturulamadı")
    else:
        print("Gmail hesabı oluşturulamadı")