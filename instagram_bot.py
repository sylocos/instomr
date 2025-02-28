import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import string
from datetime import datetime

class InstagramBot:
    def __init__(self):
        # Configure Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        # Current year from system time
        self.current_year = datetime.now().year

    def generate_random_string(self, length=10):
        """Generate a random string for email address"""
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for i in range(length))

    def get_temp_email(self):
        """Get a temporary email address"""
        try:
            email_username = self.generate_random_string(12)
            email = f"{email_username}@temporary-mail.net"
            print(f"Oluşturulan email: {email}")
            return email
        except Exception as e:
            print(f"Email oluşturma hatası: {e}")
            return None

    def wait_for_element(self, by, value, timeout=20, condition="present"):
        """Wait for element with better error handling"""
        try:
            if condition == "clickable":
                return self.wait.until(EC.element_to_be_clickable((by, value)))
            else:
                return self.wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            print(f"Öğe bekleme zaman aşımı: {value}")
            return None
        except Exception as e:
            print(f"Öğe bekleme hatası {value}: {e}")
            return None

    def safe_send_keys(self, element, text):
        """Safely send keys to an element with random delays"""
        try:
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            time.sleep(random.uniform(0.5, 1.0))
            return True
        except Exception as e:
            print(f"Tuş gönderme hatası: {e}")
            return False

    def handle_age_verification(self):
        """Handle age verification with Turkish support"""
        try:
            # First check if age verification is present
            month_select = self.wait_for_element(By.XPATH, "//select[@title='Ay:']", timeout=5)
            if not month_select:
                print("Yaş doğrulama formu bulunamadı, devam ediliyor...")
                return True

            print("Yaş doğrulama işlemi yapılıyor...")
            
            # Turkish month names
            turkish_months = {
                1: "Ocak",
                2: "Şubat",
                3: "Mart",
                4: "Nisan",
                5: "Mayıs",
                6: "Haziran",
                7: "Temmuz",
                8: "Ağustos",
                9: "Eylül",
                10: "Ekim",
                11: "Kasım",
                12: "Aralık"
            }
            
            try:
                # Generate a birthdate for someone 18-30 years old
                month_num = random.randint(1, 12)
                day = random.randint(1, 28)
                year = random.randint(self.current_year - 30, self.current_year - 18)
                
                # Select month
                month_select = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//select[@title='Ay:']")))
                month_select.send_keys(turkish_months[month_num])
                time.sleep(random.uniform(0.5, 1.0))
                
                # Select day
                day_select = self.driver.find_element(By.XPATH, "//select[@title='Gün:']")
                day_select.send_keys(str(day))
                time.sleep(random.uniform(0.5, 1.0))
                
                # Select year
                year_select = self.driver.find_element(By.XPATH, "//select[@title='Yıl:']")
                year_select.send_keys(str(year))
                time.sleep(random.uniform(0.5, 1.0))
                
                # Try to find the Next button in both Turkish and English
                next_button = None
                for button_text in ['İleri', 'Next']:
                    try:
                        next_button = self.driver.find_element(By.XPATH, f"//button[text()='{button_text}']")
                        break
                    except NoSuchElementException:
                        continue

                if next_button:
                    next_button.click()
                    print("Yaş doğrulama başarıyla tamamlandı")
                    time.sleep(random.uniform(2, 3))
                    return True
                else:
                    print("İleri butonu bulunamadı")
                    return False
                
            except Exception as e:
                print(f"Yaş doğrulama sırasında hata: {e}")
                return False
                
        except TimeoutException:
            print("Yaş doğrulama istenmedi (zaman aşımı)")
            return True
        except Exception as e:
            print(f"Beklenmeyen yaş doğrulama hatası: {e}")
            return False

    def create_account(self):
        try:
            # Get temporary email
            email = self.get_temp_email()
            if not email:
                raise Exception("Geçici email oluşturulamadı")

            print(f"Kullanılan email: {email}")

            # Open Instagram signup page
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.get('https://www.instagram.com/accounts/emailsignup/')
            print("Instagram kayıt sayfası açıldı")
            time.sleep(random.uniform(2, 4))

            # Generate credentials
            username = f"user_{self.generate_random_string(8)}"
            password = f"Pass_{self.generate_random_string(12)}#1"

            print("Kayıt formu dolduruluyor...")
            
            # Fill form fields with better error handling
            fields = {
                'emailOrPhone': email,
                'fullName': f"John {self.generate_random_string(5)}",
                'username': username,
                'password': password
            }

            for field_name, value in fields.items():
                element = self.wait_for_element(By.NAME, field_name)
                if not element:
                    raise Exception(f"{field_name} alanı bulunamadı")
                if not self.safe_send_keys(element, value):
                    raise Exception(f"{field_name} alanı doldurulamadı")

            # Submit form
            submit_button = self.wait_for_element(By.XPATH, '//button[@type="submit"]', condition="clickable")
            if not submit_button:
                raise Exception("Gönder butonu bulunamadı")

            time.sleep(random.uniform(0.5, 1.5))
            submit_button.click()
            print("Kayıt formu gönderildi")
            time.sleep(random.uniform(2, 4))

            # Handle age verification
            if not self.handle_age_verification():
                print("Yaş doğrulama başarısız olabilir, devam ediliyor...")

            # Save account details
            self.save_account_details(email, username, password)

            print("\nHesap oluşturma işlemi tamamlandı!")
            self.print_next_steps()
            return True

        except Exception as e:
            print(f"Hesap oluşturma sırasında hata: {e}")
            return False

    def save_account_details(self, email, username, password):
        """Save account details to file"""
        try:
            with open('hesap_kayitlari.txt', 'a', encoding='utf-8') as f:
                f.write(f"\nKayıt Zamanı: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Email: {email}\n")
                f.write(f"Kullanıcı Adı: {username}\n")
                f.write(f"Şifre: {password}\n")
                f.write("-" * 50 + "\n")
            print("\nHesap bilgileri 'hesap_kayitlari.txt' dosyasına kaydedildi")
        except Exception as e:
            print(f"Hesap bilgilerini kaydetme hatası: {e}")

    def print_next_steps(self):
        """Print instructions for next steps"""
        print("\nÖNEMLİ: Sonraki adımlar:")
        print("1. Email doğrulama kodunu kontrol edin")
        print("2. CAPTCHA görünürse tamamlayın")
        print("3. Telefon doğrulaması istenirse tamamlayın")
        print("\nNot: Tarayıcı penceresi manuel doğrulama için açık kalacak")

if __name__ == "__main__":
    print("Instagram Bot başlatılıyor...")
    print("Not: CAPTCHA görünürse manuel olarak tamamlamanız gerekebilir.")
    bot = InstagramBot()
    success = bot.create_account()
    if not success:
        print("Hesap oluşturulamadı")
    print("\nÇıkmak için Ctrl+C'ye basın...")