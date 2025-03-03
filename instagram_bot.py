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
import re
from datetime import datetime
import string

class TempMailIO:
    def __init__(self):
        self.api_url = "https://api.internal.temp-mail.io/api/v4/email"
        self.current_email = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def create_email(self):
        try:
            print("Geçici email oluşturuluyor...")
            username = ''.join(random.choices(string.ascii_lowercase, k=10))
            domain = "unigeol.com"  # temp-mail.io'nun stabil domaini
            self.current_email = f"{username}@{domain}"
            
            response = requests.post(
                f"{self.api_url}/new",
                json={"email": self.current_email},
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                print(f"Email başarıyla oluşturuldu: {self.current_email}")
                return self.current_email
            else:
                print(f"Email oluşturma yanıt kodu: {response.status_code}")
                return self.current_email  # Yine de emaili döndür
                
        except Exception as e:
            print(f"Email oluşturma hatası: {str(e)}")
            return None

    def get_messages(self):
        try:
            if not self.current_email:
                return []
                
            response = requests.get(
                f"{self.api_url}/{self.current_email}/messages",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            return []
            
        except Exception as e:
            print(f"Mesaj alma hatası: {str(e)}")
            return []

    def get_verification_code(self, max_attempts=30, delay=10):
        print(f"\nDoğrulama kodu bekleniyor: {self.current_email}")
        
        for attempt in range(max_attempts):
            try:
                messages = self.get_messages()
                
                for message in messages:
                    subject = message.get('subject', '').lower()
                    body = message.get('body_text', message.get('body_html', ''))
                    
                    if 'instagram' in subject or 'instagram' in body.lower():
                        # Önce subject'te ara
                        code_match = re.search(r'\b\d{6}\b', subject)
                        if not code_match:
                            # Sonra body'de ara
                            code_match = re.search(r'\b\d{6}\b', body)
                            
                        if code_match:
                            code = code_match.group(0)
                            print(f"Doğrulama kodu bulundu: {code}")
                            return code
                
                print(f"Deneme {attempt + 1}/{max_attempts}: Kod bekleniyor...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"Kod kontrol hatası: {str(e)}")
                time.sleep(delay)
                
        print("Doğrulama kodu bulunamadı!")
        return None

class InstagramBot:
    def __init__(self):
        self.temp_mail = TempMailIO()
        self.fake = Faker('tr_TR')
        
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--lang=tr-TR')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = uc.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            print("Chrome başarıyla başlatıldı")
        except Exception as e:
            print(f"Chrome başlatma hatası: {str(e)}")
            raise

    def wait_for_element(self, by, value, timeout=20, condition="present"):
        try:
            if condition == "clickable":
                element = self.wait.until(EC.element_to_be_clickable((by, value)))
            else:
                element = self.wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            print(f"Element bulunamadı: {value}")
            return None
        except Exception as e:
            print(f"Element beklenirken hata: {str(e)}")
            return None

    def create_account(self):
        try:
            # Instagram'ı aç
            self.driver.get('https://www.instagram.com/accounts/emailsignup/')
            print("Instagram kayıt sayfası açıldı")
            time.sleep(random.uniform(3, 5))

            # Geçici email oluştur
            email = self.temp_mail.create_email()
            if not email:
                raise Exception("Email oluşturulamadı")

            # Fake bilgiler oluştur
            username = f"{self.fake.user_name()}_{random.randint(100,999)}"
            password = f"Pass_{self.fake.password(length=10)}#1"
            full_name = self.fake.name()

            # Form doldur
            fields = {
                'emailOrPhone': email,
                'fullName': full_name,
                'username': username,
                'password': password
            }

            for field_name, value in fields.items():
                field = self.wait_for_element(By.NAME, field_name)
                if not field:
                    raise Exception(f"{field_name} alanı bulunamadı")
                    
                field.clear()
                for char in value:
                    field.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                time.sleep(random.uniform(0.5, 1))

            # Kayıt ol butonuna tıkla
            submit_button = self.wait_for_element(By.XPATH, '//button[@type="submit"]', condition="clickable")
            if submit_button:
                submit_button.click()
                print("Kayıt formu gönderildi")
                time.sleep(random.uniform(3, 5))
            else:
                raise Exception("Kayıt butonu bulunamadı")

            # Yaş doğrulama
            self.handle_age_verification()

            # Doğrulama kodunu bekle
            verification_code = self.temp_mail.get_verification_code()
            if verification_code:
                # Kodu gir
                code_input = self.wait_for_element(
                    By.XPATH, 
                    "//input[@aria-label='Güvenlik Kodu' or @aria-label='Security Code']"
                )
                if code_input:
                    for digit in verification_code:
                        code_input.send_keys(digit)
                        time.sleep(random.uniform(0.1, 0.3))
                    
                    # Onayla butonuna tıkla
                    confirm_button = self.wait_for_element(
                        By.XPATH, 
                        "//button[contains(text(), 'Onayla') or contains(text(), 'Confirm')]",
                        condition="clickable"
                    )
                    if confirm_button:
                        confirm_button.click()
                        print("Doğrulama kodu onaylandı")
                        time.sleep(3)
                    else:
                        print("Onay butonu bulunamadı")
                else:
                    print("Kod giriş alanı bulunamadı")

            # Hesap bilgilerini kaydet
            self.save_account_details(email, username, password)
            return True

        except Exception as e:
            print(f"Hesap oluşturma hatası: {str(e)}")
            self.save_screenshot("hata")
            return False

    def handle_age_verification(self):
        try:
            time.sleep(2)
            month_select = self.wait_for_element(By.XPATH, "//select[@title='Ay:']", timeout=5)
            if not month_select:
                return True

            print("Yaş doğrulama yapılıyor...")
            
            # 18-30 yaş arası rastgele tarih
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
            
            # İleri butonuna tıkla
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
            print(f"Yaş doğrulama hatası: {str(e)}")
            return False

    def save_account_details(self, email, username, password):
        try:
            with open('hesap_kayitlari.txt', 'a', encoding='utf-8') as f:
                f.write(f"\nKayıt Zamanı: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Email: {email}\n")
                f.write(f"Kullanıcı Adı: {username}\n")
                f.write(f"Şifre: {password}\n")
                f.write("-" * 50 + "\n")
            print("\nHesap bilgileri kaydedildi")
        except Exception as e:
            print(f"Bilgi kaydetme hatası: {str(e)}")

    def save_screenshot(self, prefix="ekran"):
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            print(f"Ekran görüntüsü: {filename}")
        except Exception as e:
            print(f"Ekran görüntüsü hatası: {str(e)}")

    def __del__(self):
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except:
            pass

if __name__ == "__main__":
    print("Instagram Bot başlatılıyor...")
    print("Not: CAPTCHA görünürse manuel olarak tamamlamanız gerekebilir.")
    
    try:
        bot = InstagramBot()
        success = bot.create_account()
        
        if not success:
            print("Hesap oluşturulamadı")
        
    except Exception as e:
        print(f"Bot hatası: {str(e)}")
    
    finally:
        input("\nÇıkmak için Enter'a basın...")