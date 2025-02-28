from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Geçici mail oluşturma fonksiyonu (örnek)
def generate_temp_email():
    timestamp = int(time.time())
    return f"insta_{timestamp}@mail.tm"

# Rastgele Türkçe kullanıcı adı ve şifre oluştur
username = generate_turkish_username()
password = generate_password()

# Geçici email oluştur
email = generate_temp_email()

# WebDriver ayarları (ChromeDriver otomatik indirme)
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

# Doğum günü bilgilerini gir
birth_month = driver.find_element(By.XPATH, '//select[@title="Month:"]')
birth_day = driver.find_element(By.XPATH, '//select[@title="Day:"]')
birth_year = driver.find_element(By.XPATH, '//select[@title="Year:"]')

# Kullanıcının yaşını 18'den büyük olacak şekilde ayarla
birth_month.send_keys('January')
birth_day.send_keys('1')
birth_year.send_keys(str(int(time.strftime("%Y")) - 20))  # 20 yaşında yapmak için

# İleri düğmesinin tıklanabilir olmasını bekle ve tıkla
next_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, '//button[@type="button"]'))
)
next_button.click()

# Hesap oluşturmanın tamamlanmasını bekle
time.sleep(10)