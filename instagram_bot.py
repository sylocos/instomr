from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
from faker import Faker
import re
from datetime import datetime

class InstagramBot:
    def __init__(self):
        self.fake = Faker('tr_TR')
        
        # Chrome ayarlarını yapılandır
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--lang=tr-TR')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        
        # User agent ekle
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        # Deneysel özellikler
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'})
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
            # İlk sekmeyi aç - temp-mail.io
            self.driver.get('https://temp-mail.io/tr')
            print("Temp-mail.io açıldı")
            time.sleep(5)
    
            # Email elementini bul ve değeri al
            email_element = self.wait_for_element(By.ID, "email")
            if not email_element:
                raise Exception("Email elementi bulunamadı")
            
            email = email_element.get_attribute("value")
            print(f"Email alındı: {email}")
    
            # İlk sekmenin handle'ını kaydet
            temp_mail_tab = self.driver.current_window_handle
    
            # Yeni sekme aç ve Instagram'a git
            print("Instagram için yeni sekme açılıyor...")
            self.driver.execute_script("window.open('about:blank', '_blank')")
            
            # Yeni sekmeye geç
            windows = self.driver.window_handles
            instagram_tab = windows[-1]
            self.driver.switch_to.window(instagram_tab)
            
            # Instagram'ı aç
            try:
                self.driver.get("https://www.instagram.com/accounts/emailsignup/")
                time.sleep(5)
                print("Instagram kayıt sayfası açıldı")
            except Exception as e:
                print(f"Instagram sayfası açılamadı: {str(e)}")
                raise
    
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
                time.sleep(3)
            else:
                raise Exception("Kayıt butonu bulunamadı")
    
            # Yaş doğrulama
            self.handle_age_verification()
    
            # Temp-mail sekmesine geri dön ve onay kodunu al
            print("Temp-mail sekmesine dönülüyor...")
            self.driver.switch_to.window(temp_mail_tab)
            verification_code = self.get_verification_code()
    
            if verification_code:
                # Instagram sekmesine geri dön
                print("Instagram sekmesine dönülüyor...")
                self.driver.switch_to.window(instagram_tab)
                time.sleep(2)
                
                # Kodu gir
                try:
                    # Doğrulama kodu input alanını bul
                    code_input = self.wait_for_element(By.NAME, "email_confirmation_code")
                    if code_input:
                        # Input alanını temizle
                        code_input.clear()
                        time.sleep(0.5)
                        
                        # Kodu yavaşça gir
                        for digit in verification_code:
                            code_input.send_keys(digit)
                            time.sleep(random.uniform(0.1, 0.3))
                        
                        print("Doğrulama kodu girildi")
                        time.sleep(2)  # Biraz daha bekle
    
                        # İleri butonu için JavaScript yaklaşımı
                        try:
                            # JavaScript ile butonu bul ve tıkla
                            js_click = """
                            function clickNextButton() {
                                // Tüm buton elementlerini kontrol et
                                const elements = document.querySelectorAll('div[role="button"]');
                                for (const el of elements) {
                                    if (el.textContent.trim() === 'İleri') {
                                        // Butonu görünür yap
                                        el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                        // Tıklama olayını tetikle
                                        el.click();
                                        return true;
                                    }
                                }
                                return false;
                            }
                            return clickNextButton();
                            """
                            
                            # JavaScript kodunu çalıştır
                            result = self.driver.execute_script(js_click)
                            if result:
                                print("İleri butonuna JavaScript ile tıklandı")
                                time.sleep(2)
                            else:
                                print("JavaScript ile tıklama başarısız, alternatif yöntem deneniyor...")
                                
                                # Enter tuşu ile dene
                                code_input.send_keys(Keys.RETURN)
                                time.sleep(1)
                                print("Enter tuşu gönderildi")
                                
                                # Form submit dene
                                self.driver.execute_script("""
                                    const form = document.querySelector('form');
                                    if(form) form.submit();
                                """)
                                time.sleep(1)
                                print("Form submit denendi")
                                
                                # Son çare: Sayfayı yenile ve tekrar dene
                                self.driver.refresh()
                                time.sleep(5)
                                print("Sayfa yenilendi, tekrar deneniyor...")
                                
                                # Yeniden JavaScript ile tıklamayı dene
                                result = self.driver.execute_script(js_click)
                                if result:
                                    print("Sayfa yenileme sonrası tıklama başarılı")
                                else:
                                    print("Tüm tıklama denemeleri başarısız")
                                    self.save_screenshot("ileri_butonu_hatasi")
                        
                        except Exception as e:
                            print(f"İleri butonuna tıklama hatası: {str(e)}")
                            self.save_screenshot("ileri_butonu_hatasi")
                    else:
                        print("Kod giriş alanı bulunamadı!")
                        self.save_screenshot("kod_input_hatasi")
                        
                except Exception as e:
                    print(f"Kod girişi sırasında hata: {str(e)}")
                    self.save_screenshot("kod_girisi_hatasi")
    
            # Hesap bilgilerini kaydet
            self.save_account_details(email, username, password)
            return True
    
        except Exception as e:
            print(f"Hesap oluşturma hatası: {str(e)}")
            self.save_screenshot("hata")
            return False
    def get_verification_code(self, max_attempts=30, delay=10):
        print("\nDoğrulama kodu bekleniyor...")
        
        for attempt in range(max_attempts):
            try:
                # Yenile butonunu bul ve tıkla
                refresh_button = self.wait_for_element(
                    By.CSS_SELECTOR,
                    "button[data-qa='refresh-button']",
                    timeout=5,
                    condition="clickable"
                )
                
                if refresh_button:
                    print("Yenileme butonu tıklanıyor...")
                    refresh_button.click()
                    time.sleep(2)
                else:
                    print("Yenileme butonu bulunamadı, sayfa yenileniyor...")
                    self.driver.refresh()
                    time.sleep(2)
                
                # Instagram mesajını ara
                messages = self.wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".message__subject[data-qa='message-subject']")
                ))
                
                for message in messages:
                    try:
                        subject = message.get_attribute("title")
                        if "Instagram kodunuz" in subject:
                            code_match = re.search(r'\b\d{6}\b', subject)
                            if code_match:
                                code = code_match.group(0)
                                print(f"Doğrulama kodu bulundu: {code}")
                                return code
                    except:
                        continue
                
                print(f"Deneme {attempt + 1}/{max_attempts}: Kod bekleniyor...")
                time.sleep(delay)
                
            except TimeoutException:
                print(f"Timeout - deneme {attempt + 1}")
                continue
                
        print("Doğrulama kodu bulunamadı!")
        return None

    def handle_age_verification(self):
        try:
            time.sleep(2)
            month_select = self.wait_for_element(By.XPATH, "//select[@title='Ay:']", timeout=5)
            if not month_select:
                return True

            print("Yaş doğrulama yapılıyor...")
            
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
            print(f"Yaş doğrulama hatası: {str(e)}")
            return False

    def get_new_email(self):
        try:
            # Mevcut sekmeyi hatırla
            current_tab = self.driver.current_window_handle
            
            # Temp-mail sekmesini bul ve geç
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if "temp-mail.io" in self.driver.current_url:
                    break
            
            # Yeni email butonu
            random_button = self.wait_for_element(
                By.CSS_SELECTOR,
                "button[data-qa='random-button']",
                condition="clickable"
            )
            
            if random_button:
                random_button.click()
                time.sleep(3)
                
                email_element = self.wait_for_element(By.ID, "email")
                if email_element:
                    email = email_element.get_attribute("value")
                    print(f"Yeni email alındı: {email}")
                    
                    # Önceki sekmeye geri dön
                    self.driver.switch_to.window(current_tab)
                    return email
            
            # Önceki sekmeye geri dön
            self.driver.switch_to.window(current_tab)
            return None
            
        except Exception as e:
            print(f"Yeni email alma hatası: {str(e)}")
            # Hata durumunda da önceki sekmeye dön
            self.driver.switch_to.window(current_tab)
            return None

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