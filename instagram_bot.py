from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import random
import string

# Türkçe karakterleri içeren rastgele kullanıcı adı oluşturma fonksiyonu
def generate_turkish_username():
    turkish_chars = 'abcdefghijklmnoprstuvyz'
    username = ''.join(random.choice(turkish_chars) for _ in range(8))
    return username

# Rastgele şifre oluşturma fonksiyonu
def generate_password(length=10):
    chars = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(chars) for _ in range(length))
    return password

# Geçici mail oluşturma fonksiyonu
def generate_temp_email():
    timestamp = int(time.time())
    return f"insta_{timestamp}@mail.tm"

try:
    # Rastgele Türkçe kullanıcı adı ve şifre oluştur
    username = generate_turkish_username()
    password = generate_password()
    
    # Geçici email oluştur
    email = generate_temp_email()
    
    # WebDriver ayarları
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    # Instagram kayıt sayfasını aç
    driver.get('https://www.instagram.com/accounts/emailsignup/')
    
    # Sayfanın yüklenmesini bekle
    time.sleep(5)
    
    # Giriş alanlarını bul ve doldur
    email_input = driver.find_element(By.NAME, 'emailOrPhone')
    full_name_input = driver.find_element(By.NAME, 'fullName')
    username_input = driver.find_element(By.NAME, 'username')
    password_input = driver.find_element(By.NAME, 'password')
    
    email_input.send_keys(email)
    full_name_input.send_keys('John Doe')  # Sabit isim (test için)
    username_input.send_keys(username)
    password_input.send_keys(password)
    
    # Gönder düğmesinin tıklanabilir olmasını bekle ve tıkla
    submit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
    )
    submit_button.click()
    
    # Doğum günü ekranının gelmesini bekle
    time.sleep(5)
    
    try:
        # Doğum tarihi seçicilerini CSS class'ı ile bul
        selects = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "select._aau-._ap32"))
        )
        
        # Seçicileri title attribute'una göre tanımla
        for select_element in selects:
            title = select_element.get_attribute('title')
            dropdown = Select(select_element)
            
            if title == 'Ay:':
                # Rastgele bir ay seç (1-12 arası)
                month_value = str(random.randint(1, 12))
                dropdown.select_by_value(month_value)
                
            elif title == 'Gün:':
                # Rastgele bir gün seç (1-28 arası)
                day_value = str(random.randint(1, 28))
                dropdown.select_by_value(day_value)
                
            elif title == 'Yıl:':
                # Rastgele bir yıl seç (1990-2000 arası)
                year_value = str(random.randint(1990, 2000))
                dropdown.select_by_value(year_value)
        
        # İleri düğmesini bul ve tıkla (Türkçe arayüz için)
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='İleri']"))
        )
        next_button.click()
        
        print(f"Hesap başarıyla oluşturuldu:")
        print(f"Email: {email}")
        print(f"Kullanıcı adı: {username}")
        print(f"Şifre: {password}")
        
    except Exception as e:
        print(f"Doğum tarihi girme hatası: {str(e)}")
        print("Hata detayı için elementin HTML'i kontrol ediliyor...")
        page_source = driver.page_source
        print(page_source)
    
    # İşlemin tamamlanmasını bekle
    time.sleep(10)

except Exception as e:
    print(f"Bir hata oluştu: {str(e)}")

finally:
    # Tarayıcıyı kapat
    driver.quit()