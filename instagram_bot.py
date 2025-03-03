from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select  # Bunu ekledik
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
        
        # Chrome options güncellemeleri
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--lang=en-US')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--start-maximized')  # Pencereyi tam boyut yap
        chrome_options.add_argument('--disable-extensions')  # Eklentileri devre dışı bırak
        chrome_options.add_argument('--disable-popup-blocking')  # Pop-up engelleyiciyi devre dışı bırak
        chrome_options.add_argument('--disable-gpu')  # GPU kullanımını devre dışı bırak
        
        # User agent ekle
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = uc.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
        except Exception as e:
            print(f"Chrome başlatma hatası: {str(e)}")
            raise
    
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

    def click_next_button(self):
        """Next butonunu bulmak ve tıklamak için geliştirilmiş fonksiyon"""
        button_found = False
        
        # Updated selectors specifically for the collectNameNext button
        selectors = [
            # Most specific selector targeting the exact button structure
            (By.CSS_SELECTOR, "#collectNameNext button.VfPpkd-LgbsSe"),
            (By.CSS_SELECTOR, "div.XjS9D.TrZEUc button"),
            (By.XPATH, "//div[@id='collectNameNext']//button"),
            (By.XPATH, "//button[.//span[contains(@jsname, 'V67aGc')][text()='Next']]"),
            # Fallback selectors
            (By.CSS_SELECTOR, "button.VfPpkd-LgbsSe.VfPpkd-LgbsSe-OWXEXe-k8QpJ"),
            (By.CSS_SELECTOR, "button[jsname='LgbsSe']"),
        ]
        
        print("Next butonu aranıyor...")
        
        for by, selector in selectors:
            try:
                print(f"Denenen selektör: {selector}")
                
                # Ensure page is loaded and wait for any animations
                time.sleep(2)
                
                # Wait for button presence
                button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                
                # Wait for button to be clickable
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((by, selector))
                )
                
                # Remove overlay elements and potential blockers
                self.driver.execute_script("""
                    // Remove overlay elements
                    var overlays = document.querySelectorAll('.VfPpkd-Jh9lGc, .VfPpkd-J1Ukfc-LhBDec, .VfPpkd-RLmnJb');
                    overlays.forEach(function(el) { el.remove(); });
                    
                    // Ensure button container is visible
                    var container = document.querySelector('#collectNameNext');
                    if(container) {
                        container.style.opacity = '1';
                        container.style.visibility = 'visible';
                    }
                    
                    // Remove any pointer-events: none
                    arguments[0].style.pointerEvents = 'auto';
                    
                    // Ensure button is visible and clickable
                    arguments[0].style.opacity = '1';
                    arguments[0].style.visibility = 'visible';
                    arguments[0].style.display = 'block';
                """, button)
                
                # Scroll to ensure button is in view
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", 
                    button
                )
                time.sleep(1)
                
                # Try multiple click methods
                click_methods = [
                    # Method 1: Direct JavaScript click with event dispatch
                    lambda: self.driver.execute_script("""
                        arguments[0].click();
                        arguments[0].dispatchEvent(new MouseEvent('click', {
                            'view': window,
                            'bubbles': true,
                            'cancelable': true,
                            'buttons': 1
                        }));
                    """, button),
                    
                    # Method 2: JavaScript click on parent container
                    lambda: self.driver.execute_script("""
                        var container = document.querySelector('#collectNameNext');
                        if(container) {
                            container.querySelector('button').click();
                        }
                    """),
                    
                    # Method 3: Standard Selenium click
                    lambda: button.click(),
                    
                    # Method 4: ActionChains click
                    lambda: ActionChains(self.driver).move_to_element(button).click().perform(),
                    
                    # Method 5: JavaScript click with focus
                    lambda: self.driver.execute_script("""
                        arguments[0].focus();
                        arguments[0].click();
                    """, button)
                ]
                
                for i, click_method in enumerate(click_methods, 1):
                    try:
                        print(f"Tıklama yöntemi {i} deneniyor...")
                        click_method()
                        time.sleep(1)
                        
                        # Check if click was successful
                        if self.check_button_clicked():
                            button_found = True
                            print(f"Buton {i}. yöntem ile başarıyla tıklandı!")
                            break
                    except Exception as click_error:
                        print(f"{i}. tıklama yöntemi hatası: {click_error}")
                        continue
                
                if button_found:
                    break
                    
            except Exception as e:
                print(f"Selektör hatası: {e}")
                continue
        
        if not button_found:
            # Save debug information
            try:
                self.driver.save_screenshot("button_error.png")
                with open("page_source.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print("Debug bilgileri kaydedildi: button_error.png ve page_source.html")
            except:
                pass
            
            raise Exception("Next butonu bulunamadı veya tıklanamadı!")
        
        # Wait for page transition
        time.sleep(3)
        return button_found
        
    def check_button_clicked(self):
        """Butonun tıklanıp tıklanmadığını kontrol et"""
        try:
            # Try multiple methods to verify if click was successful
            
            # Method 1: Check if button is no longer visible
            try:
                WebDriverWait(self.driver, 2).until_not(
                    EC.visibility_of_element_located((By.ID, "collectNameNext"))
                )
                return True
            except:
                pass
            
            # Method 2: Check if URL changed
            current_url = self.driver.current_url
            time.sleep(1)
            if current_url != self.driver.current_url:
                return True
            
            # Method 3: Check for loading indicators
            try:
                loading = self.driver.find_element(By.CSS_SELECTOR, ".loading-indicator")
                return loading.is_displayed()
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"Click verification error: {e}")
            return False        
    def create_gmail_account(self):
        try:
            self.driver.get('https://accounts.google.com/signup')
            print("Gmail kayıt sayfası açıldı")
            time.sleep(3)
    
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(1000, 9999)}"
            password = f"{self.fake.password(length=15)}#1"
    
            # İlk sayfa için sadece isim ve soyisim
            first_page_fields = [
                ('firstName', first_name),
                ('lastName', last_name)
            ]
    
            # İlk sayfadaki alanları doldur
            for field_name, value in first_page_fields:
                try:
                    field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.NAME, field_name))
                    )
                    if field:
                        field.clear()
                        for char in value:
                            field.send_keys(char)
                            time.sleep(random.uniform(0.1, 0.3))
                        time.sleep(random.uniform(0.5, 1.0))
                        print(f"{field_name} alanı dolduruldu")
                except Exception as e:
                    print(f"{field_name} alanı doldurma hatası: {str(e)}")
                    self.driver.save_screenshot(f"error_{field_name}.png")
                    raise
    
            # İlk next butonuna tıkla
            print("İlk sayfadaki next butonuna tıklanıyor...")
            if not self.click_next_button():
                raise Exception("İsim sayfasındaki Next butonuna tıklanamadı")
    
            time.sleep(2)  # Sayfa geçişini bekle
    
            # İkinci sayfa için doğum tarihi ve cinsiyet
            try:
                # Doğum günü seçimi
                day_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "day"))
                )
                day = str(random.randint(1, 28))
                day_input.clear()
                day_input.send_keys(day)
                print("Doğum günü girildi")
    
                # Ay seçimi
                month_select = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "month"))
                )
                month_select = Select(month_select)
                month_select.select_by_value(str(random.randint(1, 12)))
                print("Doğum ayı seçildi")
    
                # Yıl seçimi
                year_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "year"))
                )
                # 18-35 yaş arası
                year = str(datetime.now().year - random.randint(18, 35))
                year_input.clear()
                year_input.send_keys(year)
                print("Doğum yılı girildi")
    
                # Cinsiyet seçimi
                gender_select = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "gender"))
                )
                gender_select = Select(gender_select)
                gender_select.select_by_value(str(random.randint(1, 2)))  # 1: Male, 2: Female
                print("Cinsiyet seçildi")
    
                time.sleep(1)
    
                # İkinci next butonuna tıkla
                print("İkinci sayfadaki next butonuna tıklanıyor...")
                if not self.click_next_button():
                    raise Exception("Doğum tarihi sayfasındaki Next butonuna tıklanamadı")
    
                time.sleep(2)  # Sayfa geçişini bekle
    
            except Exception as e:
                print(f"Doğum tarihi ve cinsiyet girme hatası: {str(e)}")
                self.driver.save_screenshot("error_birthday_gender.png")
                raise
    
            # Üçüncü sayfa - Gmail adresi oluşturma
            try:
                time.sleep(2)  # Sayfa yüklenmesini bekle
                
                username_taken = True
                max_attempts = 5  # Maximum deneme sayısı
                attempt = 0
    
                while username_taken and attempt < max_attempts:
                    if attempt > 0:
                        # Yeni bir username oluştur
                        username = f"{first_name.lower()}{last_name.lower()}{random.randint(1000, 9999)}"
                        print(f"Yeni username deneniyor: {username}")
    
                    try:
                        # "Create your own Gmail address" butonu var mı kontrol et
                        try:
                            create_gmail_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//div[@id='selectionc3'][contains(text(), 'Create your own Gmail address')]"))
                            )
                            # Buton varsa tıkla
                            try:
                                create_gmail_button.click()
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", create_gmail_button)
                                except:
                                    ActionChains(self.driver).move_to_element(create_gmail_button).click().perform()
                            print("'Create your own Gmail address' butonuna tıklandı")
                            time.sleep(2)
                            
                            # Alt sekmede açılan input'u bul
                            email_input = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Create a Gmail address']"))
                            )
                        except:
                            # Buton yoksa direkt input'u bul
                            print("'Create your own Gmail address' butonu bulunamadı, direkt input aranıyor...")
                            email_input = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Username' or @name='Username']"))
                            )
                        
                        # Email input alanını temizle ve yeni username'i gir
                        email_input.clear()
                        for char in username:
                            email_input.send_keys(char)
                            time.sleep(random.uniform(0.1, 0.3))
                        print(f"Email kullanıcı adı girildi: {username}")
                        time.sleep(1)
    
                        # Next butonuna tıkla
                        print("Email girişi sonrası next butonuna tıklanıyor...")
                        if not self.click_next_button():
                            raise Exception("Email sayfasındaki Next butonuna tıklanamadı")
    
                        time.sleep(2)  # Next butonuna tıkladıktan sonra bekle
    
                        # Username kullanılıyor mu kontrol et
                        try:
                            error_message = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'That username is taken')]"))
                            )
                            print(f"Bu username kullanımda: {username}")
                            attempt += 1
                            continue  # While döngüsüne devam et
                        except:
                            # Hata mesajı bulunamadı, username kullanılabilir
                            username_taken = False
                            print(f"Username kullanılabilir: {username}")
                            break  # While döngüsünden çık
    
                    except Exception as e:
                        print(f"Email girişi hatası: {str(e)}")
                        self.driver.save_screenshot(f"error_email_input_attempt_{attempt}.png")
                        attempt += 1
    
                if username_taken:
                    raise Exception(f"Kullanılabilir bir username bulunamadı {max_attempts} denemeden sonra")
    
            except Exception as e:
                print(f"Email oluşturma hatası: {str(e)}")
                self.driver.save_screenshot("error_email_creation.png")
                raise
    
            # Dördüncü sayfa - Şifre girişi
            try:
                print("Şifre girişi sayfası bekleniyor...")
                time.sleep(2)
    
                # Şifre alanlarını doldur
                password_fields = [
                    ('Passwd', password),  # İlk şifre alanı
                    ('PasswdAgain', password)  # Şifre onay alanı
                ]
    
                for field_name, value in password_fields:
                    try:
                        # Şifre alanını bul
                        password_field = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.NAME, field_name))
                        )
                        password_field.clear()
                        # Şifreyi yavaşça gir
                        for char in value:
                            password_field.send_keys(char)
                            time.sleep(random.uniform(0.1, 0.3))
                        print(f"{field_name} alanına şifre girildi")
                        time.sleep(random.uniform(0.5, 1.0))
                    except Exception as e:
                        print(f"Şifre alanı doldurma hatası ({field_name}): {str(e)}")
                        self.driver.save_screenshot(f"error_password_{field_name}.png")
                        raise
    
                # Next butonuna tıkla
                print("Şifre girişi sonrası next butonuna tıklanıyor...")
                next_button_clicked = False
                
                # Farklı next buton selektörleri
                next_button_selectors = [
                    (By.XPATH, "//button[.//span[contains(text(), 'Next')]]"),
                    (By.XPATH, "//button[contains(@class, 'VfPpkd-LgbsSe')]"),
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.XPATH, "//div[contains(@class, 'VfPpkd-dgl2Hf-ppHlrf-sM5MNb')]//button")
                ]
    
                for by, selector in next_button_selectors:
                    try:
                        next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        # Farklı tıklama yöntemlerini dene
                        try:
                            next_button.click()
                        except:
                            try:
                                self.driver.execute_script("arguments[0].click();", next_button)
                            except:
                                ActionChains(self.driver).move_to_element(next_button).click().perform()
                        
                        next_button_clicked = True
                        print(f"Şifre sayfasındaki next butonuna tıklandı (selector: {selector})")
                        break
                    except:
                        continue
    
                if not next_button_clicked:
                    raise Exception("Şifre sayfasındaki next butonuna tıklanamadı")
    
                time.sleep(2)  # Next butonuna tıkladıktan sonra bekle
    
            except Exception as e:
                print(f"Şifre girişi hatası: {str(e)}")
                self.driver.save_screenshot("error_password_page.png")
                raise
    
            # CAPTCHA kontrolü ve çözümü
            try:
                captcha_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'g-recaptcha'))
                )
                if captcha_element:
                    site_key = captcha_element.get_attribute('data-sitekey')
                    captcha_solution = self.solve_captcha(site_key, self.driver.current_url)
                    if captcha_solution:
                        self.driver.execute_script(
                            f'document.getElementById("g-recaptcha-response").innerHTML = "{captcha_solution}"'
                        )
                        submit_button = self.driver.find_element(By.ID, 'submit')
                        submit_button.click()
                        print("CAPTCHA çözüldü ve form gönderildi")
                    else:
                        print("CAPTCHA çözülemedi, manuel müdahale gerekebilir")
            except:
                print("CAPTCHA elementi bulunamadı, devam ediliyor...")
    
            # Hesap oluşturma başarılı mı kontrol et
            try:
                success_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Welcome')]"))
                )
                if success_element:
                    print("Hesap başarıyla oluşturuldu!")
                    return {
                        'email': f"{username}@gmail.com",
                        'password': password
                    }
            except:
                print("Hesap oluşturma durumu belirsiz")
                return None
    
        except Exception as e:
            print(f"Hesap oluşturma hatası: {str(e)}")
            self.driver.save_screenshot("error_account_creation.png")
            return None
    
        finally:
            try:
                self.driver.save_screenshot("gmail_son_durum.png")
                print("Son durum ekran görüntüsü kaydedildi: gmail_son_durum.png")
            except:
                pass
    
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass
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
                return None
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