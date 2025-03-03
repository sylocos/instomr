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
        self.proxy_auth_file = 'proxy_auth.txt'
        self.proxy_auth = {}
        self.load_working_proxies()
        self.load_proxy_auth()

    def load_working_proxies(self):
        """Çalışan proxyleri dosyadan yükle"""
        try:
            if os.path.exists(self.working_proxies_file):
                with open(self.working_proxies_file, 'r') as f:
                    self.working_proxies = [line.strip() for line in f if line.strip()]
                print(f"{len(self.working_proxies)} adet kayıtlı proxy yüklendi")
        except Exception as e:
            print(f"Proxy yükleme hatası: {e}")
            self.working_proxies = []

    def load_proxy_auth(self):
        """Proxy kimlik bilgilerini yükle"""
        try:
            if os.path.exists(self.proxy_auth_file):
                with open(self.proxy_auth_file, 'r') as f:
                    for line in f:
                        if '|' in line:
                            proxy, auth = line.strip().split('|')
                            if ':' in auth:
                                username, password = auth.split(':')
                                self.proxy_auth[proxy] = {
                                    'username': username,
                                    'password': password
                                }
        except Exception as e:
            print(f"Proxy kimlik bilgileri yükleme hatası: {e}")

    def save_proxy_auth(self, proxy, username, password):
        """Proxy kimlik bilgilerini kaydet"""
        try:
            with open(self.proxy_auth_file, 'a') as f:
                f.write(f"{proxy}|{username}:{password}\n")
            self.proxy_auth[proxy] = {'username': username, 'password': password}
            print(f"Proxy kimlik bilgileri kaydedildi: {proxy}")
        except Exception as e:
            print(f"Proxy kimlik bilgileri kaydetme hatası: {e}")

    def get_working_proxy(self):
        """Çalışan bir proxy döndür"""
        if not self.working_proxies:
            print("Kayıtlı çalışan proxy bulunamadı!")
            return None

        for proxy in self.working_proxies:
            print(f"Kayıtlı proxy test ediliyor: {proxy}")
            if self.test_proxy(proxy):
                self.current_proxy = proxy
                return proxy

        print("Çalışan proxy bulunamadı!")
        return None

    def test_proxy(self, proxy):
        """Proxy'yi test et"""
        try:
            test_url = 'https://www.google.com'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            # Proxy kimlik bilgilerini kontrol et
            if proxy in self.proxy_auth:
                auth = self.proxy_auth[proxy]
                proxy_url = f"http://{auth['username']}:{auth['password']}@{proxy}"
            else:
                proxy_url = f"http://{proxy}"

            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }

            response = requests.get(
                test_url,
                proxies=proxies,
                headers=headers,
                timeout=10,
                verify=False
            )

            if response.status_code == 200:
                print(f"✓ Çalışan proxy bulundu: {proxy}")
                return True

        except requests.exceptions.ProxyError as e:
            if '407' in str(e):
                print(f"Proxy kimlik doğrulama gerekiyor: {proxy}")
                username = input(f"Proxy {proxy} için kullanıcı adı: ")
                password = input(f"Proxy {proxy} için şifre: ")
                self.save_proxy_auth(proxy, username, password)
                return self.test_proxy(proxy)  # Yeni kimlik bilgileriyle tekrar dene
            print(f"Proxy bağlantı hatası: {e}")
        except Exception as e:
            print(f"Proxy test hatası: {e}")
        return False

    def remove_dead_proxy(self, proxy):
        """Çalışmayan proxy'i listeden kaldır"""
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            try:
                with open(self.working_proxies_file, 'w') as f:
                    for p in self.working_proxies:
                        f.write(f"{p}\n")
                print(f"Çalışmayan proxy kaldırıldı: {proxy}")
            except Exception as e:
                print(f"Proxy kaldırma hatası: {e}")
class GmailAccountCreator:
    def __init__(self):
        """Gmail hesap oluşturucu başlatıcı"""
        self.fake = Faker()
        self.proxy_manager = ProxyManager()
        
        try:
            # Chrome options güncellemeleri
            chrome_options = uc.ChromeOptions()
            
            # Pencere boyutu ve pozisyonu
            window_sizes = [
                (1366, 768),
                (1920, 1080),
                (1536, 864),
                (1440, 900),
                (1600, 900)
            ]
            window_size = random.choice(window_sizes)
            pos_x = random.randint(0, 100)
            pos_y = random.randint(0, 100)
            
            chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
            chrome_options.add_argument(f"--window-position={pos_x},{pos_y}")
            
            # User Agent listesi - Chrome 133 için güncellenmiş
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.142 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.140 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.130 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.100 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
            ]
            self.user_agent = random.choice(user_agents)
            chrome_options.add_argument(f'--user-agent={self.user_agent}')
            
            # Temel Chrome argümanları
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-automation')
            chrome_options.add_argument('--disable-blink-features')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Performans ve güvenlik ayarları
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-translate')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--no-default-browser-check')
            
            # Gizlilik ayarları
            chrome_options.add_argument('--incognito')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-save-password-bubble')
            chrome_options.add_argument('--disable-single-click-autofill')
            chrome_options.add_argument('--disable-autofill-keyboard-accessory-view')
            
            # Dil ve bölge ayarları
            chrome_options.add_argument('--lang=en-US')
            chrome_options.add_argument('--accept-lang=en-US,en;q=0.9')
            
            # WebRTC ayarları
            chrome_options.add_argument('--use-fake-ui-for-media-stream')
            chrome_options.add_argument('--use-fake-device-for-media-stream')
            
            print("Chrome başlatılıyor...")
            
            # Chrome driver'ı başlat - Chrome 133 için güncellendi
            self.driver = uc.Chrome(
                options=chrome_options,
                use_subprocess=True,
                version_main=133,  # Chrome 133 için güncellendi
                driver_executable_path=None,
                headless=False
            )
            
            # CDP Commands ile WebDriver özelliklerini gizle
            print("WebDriver özellikleri gizleniyor...")
            
            # User Agent override
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self.user_agent,
                "platform": "Windows",
                "acceptLanguage": "en-US,en;q=0.9"
            })
            
            # WebDriver gizleme scripti
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                "source": """
                    // WebDriver özelliğini gizle
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Chrome runtime
                    window.chrome = {
                        runtime: {},
                        app: {},
                        loadTimes: function(){},
                        csi: function(){},
                        loadTimes: function(){}
                    };
                    
                    // Plugin ve mimari bilgilerini gizle
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [
                            {
                                0: {type: "application/x-google-chrome-pdf"},
                                description: "Portable Document Format",
                                filename: "internal-pdf-viewer",
                                length: 1,
                                name: "Chrome PDF Plugin"
                            }
                        ]
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'Win32'
                    });
                    
                    // Permission API'yi modifiye et
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // WebGL vendor ve renderer bilgilerini gizle
                    const getParameter = WebGLRenderingContext.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter(parameter);
                    };
                """
            })
            
            # Network ayarları
            print("Network ayarları yapılandırılıyor...")
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'DNT': '1',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1'
                }
            })
            
            # WebDriverWait nesnesini oluştur
            self.wait = WebDriverWait(self.driver, 20)
            print("Chrome başlatıldı ve konfigürasyon tamamlandı")
            
        except Exception as e:
            print(f"Chrome başlatma hatası: {str(e)}")
            if hasattr(self, 'driver'):
                try:
                    self.driver.quit()
                except:
                    pass
            raise
        
    def simulate_human_behavior(self):
        """6. İnsan davranışı simülasyonu"""
        try:
            # Mouse hareketleri
            actions = ActionChains(self.driver)
            for _ in range(random.randint(3, 6)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                actions.move_by_offset(x_offset, y_offset)
                actions.pause(random.uniform(0.1, 0.3))
            actions.perform()
            
            # Sayfa scroll
            scroll_amount = random.randint(100, 300)
            self.driver.execute_script(f"window.scrollTo(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Rastgele bekleme
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"İnsan davranışı simülasyon hatası: {e}")
    
    def prepare_browser(self):
        """9. Google üzerinden doğal navigasyon"""
        try:
            print("Tarayıcı hazırlanıyor...")
            
            # Google'a git
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            # İnsan davranışı simüle et
            self.simulate_human_behavior()
            
            # Google'da arama yap
            search_queries = [
                "create gmail account",
                "gmail sign up",
                "how to create google account",
                "make new gmail"
            ]
            
            search_box = self.wait.until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            search_query = random.choice(search_queries)
            for char in search_query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
                
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(2, 4))
            
            # Sayfada biraz gezin
            self.simulate_human_behavior()
            
            return True
            
        except Exception as e:
            print(f"Tarayıcı hazırlama hatası: {e}")
            return False
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
    def inject_instagram_evasion_scripts(self):
        """Instagram için bot tespitini engelleyici JavaScript kodlarını enjekte eder"""
        evasion_scripts = """
            // Instagram'ın bot tespitini bypass et
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Instagram'ın otomasyon kontrollerini atla
            const originalFunction = window.Function.prototype.toString;
            window.Function.prototype.toString = function() {
                if (this === window.navigator.permissions.query) {
                    return 'function query() { [native code] }';
                }
                return originalFunction.apply(this, arguments);
            };
            
            // Instagram için özel zamanlama simülasyonu
            const rand = (min, max) => Math.floor(Math.random() * (max - min) + min);
            const delay = rand(50, 150);
            
            const originalDate = Date.now;
            Date.now = function() {
                return originalDate() + delay;
            };
        """
        try:
            self.driver.execute_script(evasion_scripts)
        except Exception as e:
            print(f"Instagram script enjeksiyon hatası: {e}")
    
    def simulate_instagram_human_behavior(self):
        """Instagram'da insan davranışlarını simüle eder"""
        actions = [
            lambda: time.sleep(random.uniform(0.8, 2.0)),  # Instagram için optimal bekleme
            lambda: self.driver.execute_script(
                f"window.scrollBy(0, {random.randint(-200, 200)});"
            ),  # Instagram feed scroll simülasyonu
            lambda: ActionChains(self.driver).move_by_offset(
                random.randint(-40, 40), 
                random.randint(-40, 40)
            ).move_by_offset(
                random.randint(-10, 10), 
                random.randint(-10, 10)
            ).perform(),  # İki aşamalı fare hareketi
            lambda: ActionChains(self.driver).pause(
                random.uniform(0.2, 0.4)
            ).send_keys(Keys.TAB if random.random() < 0.2 else Keys.ESCAPE).perform(),
            lambda: self.add_random_cursor_movement()  # Özel cursor hareketi
        ]
        
        # Instagram için daha doğal davranış döngüsü
        for _ in range(random.randint(2, 4)):
            try:
                random.choice(actions)()
                if random.random() < 0.4:  # %40 ihtimalle ekstra hareket
                    time.sleep(random.uniform(0.3, 0.7))
                    random.choice(actions)()
            except:
                continue
    
    def add_random_cursor_movement(self):
        """Instagram için özel imza niteliğinde fare hareketi oluşturur"""
        try:
            action = ActionChains(self.driver)
            # Benzersiz hareket paterni
            points = [(random.randint(-60, 60), random.randint(-60, 60)) for _ in range(3)]
            
            for x, y in points:
                action.move_by_offset(x, y)
                action.pause(random.uniform(0.1, 0.3))
            
            action.perform()
        except:
            pass            
    def create_gmail_account(self):
        try:
            if not self.first_page():
                return False
                
            if not self.second_page():
                return False
                
            if not self.third_page():
                return False
                
            if not self.fourth_page():
                return False
                
            return True
                
        except Exception as e:
            print(f"Gmail hesabı oluşturma hatası: {e}")
            self.driver.save_screenshot("gmail_error.png")
            return False
    
    def first_page(self):
        """İlk sayfa - İsim ve Soyisim"""
        try:
            print("Gmail kayıt sayfası açılıyor...")
            self.driver.get('https://accounts.google.com/signup')
            time.sleep(5)
            
            # İsim ve soyisim için fake data oluştur
            self.first_name = self.fake.first_name()
            self.last_name = self.fake.last_name()
            
            # İsim alanı için selektörler
            first_name_selectors = [
                (By.ID, "firstName"),
                (By.NAME, "firstName"),
                (By.CSS_SELECTOR, "input[aria-label='First name']"),
                (By.CSS_SELECTOR, "input.whsOnd.zHQkBf[name='firstName']"),
                (By.XPATH, "//input[@jsname='YPqjbf'][@name='firstName']")
            ]
            
            # Soyisim alanı için selektörler
            last_name_selectors = [
                (By.ID, "lastName"),
                (By.NAME, "lastName"),
                (By.CSS_SELECTOR, "input[aria-label='Last name (optional)']"),
                (By.CSS_SELECTOR, "input.whsOnd.zHQkBf[name='lastName']"),
                (By.XPATH, "//input[@jsname='YPqjbf'][@name='lastName']")
            ]
            
            # İsim alanını doldur
            first_name_input = None
            for by, selector in first_name_selectors:
                try:
                    print(f"İsim alanı deneniyor: {selector}")
                    first_name_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    if first_name_input:
                        break
                except:
                    continue
            
            if first_name_input:
                # JavaScript ile değeri ayarla ve event tetikle
                self.driver.execute_script("""
                    arguments[0].value = arguments[1];
                    arguments[0].dispatchEvent(new Event('change'));
                    arguments[0].dispatchEvent(new Event('input'));
                """, first_name_input, self.first_name)
                
                # Yedek yöntem olarak normal input da gönder
                first_name_input.clear()
                for char in self.first_name:
                    first_name_input.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                print(f"İsim girildi: {self.first_name}")
            else:
                print("İsim alanı bulunamadı!")
                self.driver.save_screenshot("error_firstname.png")
                return False
                
            time.sleep(random.uniform(0.5, 1.0))
            
            # Soyisim alanını doldur
            last_name_input = None
            for by, selector in last_name_selectors:
                try:
                    print(f"Soyisim alanı deneniyor: {selector}")
                    last_name_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    if last_name_input:
                        break
                except:
                    continue
                    
            if last_name_input:
                # JavaScript ile değeri ayarla ve event tetikle
                self.driver.execute_script("""
                    arguments[0].value = arguments[1];
                    arguments[0].dispatchEvent(new Event('change'));
                    arguments[0].dispatchEvent(new Event('input'));
                """, last_name_input, self.last_name)
                
                # Yedek yöntem olarak normal input da gönder
                last_name_input.clear()
                for char in self.last_name:
                    last_name_input.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                print(f"Soyisim girildi: {self.last_name}")
            else:
                print("Soyisim alanı bulunamadı!")
                self.driver.save_screenshot("error_lastname.png")
                return False
                
            time.sleep(random.uniform(0.5, 1.0))
            
            # İnsan davranışını taklit et
            self.add_random_cursor_movement()
            
            # İleri butonuna tıkla
            next_buttons = [
                "//span[contains(text(), 'Next')]",
                "//span[contains(text(), 'İleri')]",
                "//button[@type='button']//span[contains(text(), 'Next')]",
                "//button[@type='button']//span[contains(text(), 'İleri')]",
                "//button[contains(@class, 'VfPpkd-LgbsSe')]",
                "//div[contains(@class, 'VfPpkd-RLmnJb')]"
            ]
            
            next_clicked = False
            for next_xpath in next_buttons:
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, next_xpath))
                    )
                    next_button.click()
                    next_clicked = True
                    print("İleri butonuna tıklandı")
                    time.sleep(2)
                    break
                except:
                    continue
                    
            if not next_clicked:
                print("İleri butonu bulunamadı!")
                self.driver.save_screenshot("error_next_button.png")
                return False
                
            return True
            
        except Exception as e:
            print(f"İlk sayfa hatası: {e}")
            self.driver.save_screenshot("gmail_first_page_error.png")
            return False
        
    def second_page(self):
        """İkinci sayfa - Doğum tarihi ve cinsiyet"""
        try:
            print("Doğum tarihi ve cinsiyet sayfası...")
            
            # Doğum tarihi alanlarının yüklenmesini bekle
            try:
                self.wait.until(EC.presence_of_element_located((By.NAME, "day")))
            except:
                print("Doğum tarihi sayfası yüklenemedi!")
                return False
                
            # Gün gir
            try:
                day = str(random.randint(1, 28))
                day_input = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "day"))
                )
                day_input.clear()
                day_input.send_keys(day)
                print(f"Gün girildi: {day}")
            except:
                print("Gün alanı bulunamadı!")
                return False
                
            time.sleep(random.uniform(0.5, 1.0))
            
            # Ay seç
            try:
                month = str(random.randint(1, 12))
                month_select = Select(self.wait.until(
                    EC.presence_of_element_located((By.ID, "month"))
                ))
                month_select.select_by_value(month)
                print(f"Ay seçildi: {month}")
            except:
                print("Ay alanı bulunamadı!")
                return False
                
            time.sleep(random.uniform(0.5, 1.0))
            
            # Yıl gir
            try:
                # 18-35 yaş arası
                year = str(datetime.now().year - random.randint(18, 35))
                year_input = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "year"))
                )
                year_input.clear()
                year_input.send_keys(year)
                print(f"Yıl girildi: {year}")
            except:
                print("Yıl alanı bulunamadı!")
                return False
                
            time.sleep(random.uniform(0.5, 1.0))
            
            # Cinsiyet seç
            try:
                gender_select = Select(self.wait.until(
                    EC.presence_of_element_located((By.ID, "gender"))
                ))
                gender = random.choice(['1', '2'])  # 1: Male, 2: Female
                gender_select.select_by_value(gender)
                print(f"Cinsiyet seçildi: {'Erkek' if gender=='1' else 'Kadın'}")
            except:
                print("Cinsiyet alanı bulunamadı!")
                return False
                
            time.sleep(random.uniform(0.5, 1.0))
            
            # İleri butonuna tıkla
            next_buttons = [
                "//span[contains(text(), 'Next')]",
                "//span[contains(text(), 'İleri')]",
                "//button[@type='button']//span[contains(text(), 'Next')]",
                "//button[@type='button']//span[contains(text(), 'İleri')]"
            ]
            
            next_clicked = False
            for next_xpath in next_buttons:
                try:
                    next_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, next_xpath))
                    )
                    next_button.click()
                    next_clicked = True
                    print("İkinci sayfa - İleri butonuna tıklandı")
                    time.sleep(2)
                    break
                except:
                    continue
                    
            if not next_clicked:
                print("İkinci sayfa - İleri butonu bulunamadı!")
                self.driver.save_screenshot("error_second_page_next.png")
                return False
                
            return True
            
        except Exception as e:
            print(f"İkinci sayfa hatası: {e}")
            self.driver.save_screenshot("gmail_second_page_error.png")
            return False
    
    def third_page(self):
        """Üçüncü sayfa - Gmail adresi"""
        try:
            print("Gmail adresi oluşturma sayfası...")
            time.sleep(2)
            
            # Kullanıcı adı oluştur
            username = f"{self.first_name.lower()}{self.last_name.lower()}{random.randint(1000, 9999)}"
            username = ''.join(e for e in username if e.isalnum())
            
            username_taken = True
            max_attempts = 5
            attempt = 0
            
            while username_taken and attempt < max_attempts:
                if attempt > 0:
                    username = f"{self.first_name.lower()}{self.last_name.lower()}{random.randint(1000, 9999)}"
                    username = ''.join(e for e in username if e.isalnum())
                    print(f"Yeni username deneniyor: {username}")
                    
                try:
                    # "Create your own Gmail address" butonu var mı kontrol et
                    try:
                        create_gmail_button = self.wait.until(
                            EC.element_to_be_clickable(
                                (By.XPATH, "//div[contains(text(), 'Create your own Gmail address')]")
                            )
                        )
                        create_gmail_button.click()
                        print("'Create your own Gmail address' butonuna tıklandı")
                        time.sleep(2)
                    except:
                        print("'Create your own Gmail address' butonu bulunamadı")
                    
                    # Email input alanını bul
                    email_input = None
                    try:
                        email_input = self.wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//input[@aria-label='Create a Gmail address']")
                            )
                        )
                    except:
                        try:
                            email_input = self.wait.until(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//input[@aria-label='Username' or @name='Username']")
                                )
                            )
                        except:
                            print("Email input alanı bulunamadı!")
                            return False
                    
                    if email_input:
                        email_input.clear()
                        for char in username:
                            email_input.send_keys(char)
                            time.sleep(random.uniform(0.1, 0.3))
                        print(f"Email kullanıcı adı girildi: {username}")
                        
                    time.sleep(1)
                    
                    # İleri butonuna tıkla
                    next_buttons = [
                        "//span[contains(text(), 'Next')]",
                        "//span[contains(text(), 'İleri')]",
                        "//button[@type='button']//span[contains(text(), 'Next')]",
                        "//button[@type='button']//span[contains(text(), 'İleri')]"
                    ]
                    
                    next_clicked = False
                    for next_xpath in next_buttons:
                        try:
                            next_button = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, next_xpath))
                            )
                            next_button.click()
                            next_clicked = True
                            print("Üçüncü sayfa - İleri butonuna tıklandı")
                            time.sleep(2)
                            break
                        except:
                            continue
                            
                    if not next_clicked:
                        print("Üçüncü sayfa - İleri butonu bulunamadı!")
                        return False
                    
                    # Username kullanılıyor mu kontrol et
                    try:
                        error_message = self.wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[contains(text(), 'That username is taken')]")
                            )
                        )
                        print(f"Bu username kullanımda: {username}")
                        attempt += 1
                        continue
                    except:
                        username_taken = False
                        self.username = username  # Başarılı username'i kaydet
                        print(f"Username kullanılabilir: {username}")
                        break
                        
                except Exception as e:
                    print(f"Email girişi hatası: {e}")
                    attempt += 1
                    
            if username_taken:
                print("Kullanılabilir username bulunamadı!")
                return False
                
            return True
            
        except Exception as e:
            print(f"Üçüncü sayfa hatası: {e}")
            self.driver.save_screenshot("gmail_third_page_error.png")
            return False
    
    def fourth_page(self):
        """Dördüncü sayfa - Şifre"""
        try:
            print("Şifre oluşturma sayfası...")
            time.sleep(2)
            
            # Şifre oluştur
            self.password = f"{self.fake.word()}{random.randint(100, 999)}!{random.choice(['@','#','$'])}"
            
            # Şifre alanlarını doldur
            password_fields = [
                ('Passwd', self.password),
                ('PasswdAgain', self.password)
            ]
            
            for field_name, value in password_fields:
                try:
                    password_field = self.wait.until(
                        EC.presence_of_element_located((By.NAME, field_name))
                    )
                    password_field.clear()
                    for char in value:
                        password_field.send_keys(char)
                        time.sleep(random.uniform(0.1, 0.3))
                    print(f"{field_name} alanına şifre girildi")
                    time.sleep(random.uniform(0.5, 1.0))
                except:
                    print(f"Şifre alanı bulunamadı: {field_name}")
                    return False
            
            # İleri butonuna tıkla
            next_button_selectors = [
                (By.XPATH, "//button[.//span[contains(text(), 'Next')]]"),
                (By.XPATH, "//button[contains(@class, 'VfPpkd-LgbsSe')]"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//div[contains(@class, 'VfPpkd-dgl2Hf-ppHlrf-sM5MNb')]//button"),
                (By.XPATH, "//span[contains(text(), 'Next')]"),
                (By.XPATH, "//span[contains(text(), 'İleri')]")
            ]
            
            next_clicked = False
            for by, selector in next_button_selectors:
                try:
                    next_button = self.wait.until(
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
                    
                    next_clicked = True
                    print(f"Dördüncü sayfa - İleri butonuna tıklandı (selector: {selector})")
                    time.sleep(2)
                    break
                except:
                    continue
            
            if not next_clicked:
                print("Dördüncü sayfa - İleri butonu tıklanamadı!")
                self.driver.save_screenshot("error_fourth_page_next.png")
                return False
                
            # CAPTCHA kontrolü
            try:
                captcha_element = self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'g-recaptcha'))
                )
                if captcha_element:
                    print("CAPTCHA tespit edildi!")
                    site_key = captcha_element.get_attribute('data-sitekey')
                    if hasattr(self, 'solve_captcha'):
                        captcha_solution = self.solve_captcha(site_key, self.driver.current_url)
                        if captcha_solution:
                            self.driver.execute_script(
                                f'document.getElementById("g-recaptcha-response").innerHTML = "{captcha_solution}"'
                            )
                            print("CAPTCHA çözüldü")
                        else:
                            print("CAPTCHA çözülemedi!")
                            return False
                    else:
                        print("CAPTCHA çözme fonksiyonu bulunamadı!")
                        return False
            except:
                print("CAPTCHA bulunamadı, devam ediliyor...")
                
            # Hesap oluşturma başarılı mı kontrol et
            try:
                success_element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Welcome')]"))
                )
                if success_element:
                    print("Gmail hesabı başarıyla oluşturuldu!")
                    # Hesap bilgilerini kaydet
                    with open("gmail_accounts.txt", "a") as f:
                        f.write(f"{self.username}@gmail.com:{self.password}\n")
                    return True
            except:
                print("Hesap oluşturma durumu belirsiz")
                self.driver.save_screenshot("account_creation_final.png")
                return False
                
            return True
            
        except Exception as e:
            print(f"Dördüncü sayfa hatası: {e}")
            self.driver.save_screenshot("gmail_fourth_page_error.png")
            return False
        
        finally:
            try:
                # Son durumu kaydet
                self.driver.save_screenshot("gmail_son_durum.png")
                print("Son durum ekran görüntüsü kaydedildi: gmail_son_durum.png")
            except:
                pass
                        
    def complete_registration(self, username, password):
        """Kayıt işlemini tamamla"""
        try:
            # Next/İleri butonları için olası seçiciler
            next_button_selectors = [
                "//span[contains(text(), 'Next')]/parent::button",
                "//span[contains(text(), 'İleri')]/parent::button",
                "//button[@type='submit']",
                "//div[@role='button'][contains(., 'Next')]",
                "//div[@role='button'][contains(., 'İleri')]"
            ]
            
            for selector in next_button_selectors:
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    next_button.click()
                    print("İleri butonuna tıklandı")
                    time.sleep(2)
                    break
                except:
                    continue
            
            # Hesap oluşturma başarılı mı kontrol et
            success_indicators = [
                "//span[contains(text(), 'Welcome')]",
                "//span[contains(text(), 'Hoş geldiniz')]",
                "//div[contains(text(), 'Account created')]",
                "//div[contains(text(), 'Hesap oluşturuldu')]"
            ]
            
            for indicator in success_indicators:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, indicator))
                    )
                    print("Hesap başarıyla oluşturuldu!")
                    return {
                        'email': f"{username}@gmail.com",
                        'password': password
                    }
                except:
                    continue
            
            print("Hesap oluşturma durumu belirsiz, devam ediliyor...")
            return {
                'email': f"{username}@gmail.com",
                'password': password
            }
            
        except Exception as e:
            print(f"Kayıt tamamlama hatası: {e}")
            return None   
    


   # Yeni eklenecek sınıf
class BrowserFingerprint:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.viewport_sizes = [
            (1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720)
        ]
        
        self.languages = ["tr-TR,tr;q=0.9,en;q=0.8", "en-US,en;q=0.9", "en-GB,en;q=0.9"]
        
    def generate_fingerprint(self):
        return {
            "user_agent": random.choice(self.user_agents),
            "viewport": random.choice(self.viewport_sizes),
            "language": random.choice(self.languages),
            "platform": random.choice(["Windows", "Macintosh", "Linux"]),
            "webgl_vendor": random.choice(["Google Inc.", "Apple Inc."]),
            "renderer": random.choice([
                "ANGLE (AMD Radeon)", 
                "ANGLE (Intel(R) UHD Graphics)",
                "ANGLE (NVIDIA GeForce)"
            ])
        }            
class InstagramBot:
    def __init__(self, gmail_address, gmail_app_password):
        self.base_email = gmail_address
        self.gmail_password = gmail_app_password
        self.current_email = None
        self.fake = Faker('tr_TR')
        self.proxy_manager = ProxyManager()
        
        # Chrome profil yolu
        chrome_profile_path = os.path.join(os.path.expanduser('~'), 'chrome_profiles', 'instagram_bot')
        os.makedirs(chrome_profile_path, exist_ok=True)
        
        # Chrome options ayarları
        chrome_options = uc.ChromeOptions()
        
        # Temel Chrome argümanları
        chrome_arguments = [
            '--disable-blink-features=AutomationControlled',
            '--disable-notifications',
            '--ignore-certificate-errors',
            '--ignore-ssl-errors',
            '--disable-infobars',
            '--lang=tr-TR',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            f'--user-data-dir={chrome_profile_path}',
            '--window-size=1920,1080',
            f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Argümanları ekle
        for arg in chrome_arguments:
            chrome_options.add_argument(arg)
        
        # WebRTC ve WebGL ayarları için preferences
        prefs = {
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "profile.password_manager_enabled": False,
            "profile.managed_default_content_settings.images": 1,
            "credentials_enable_service": False
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Proxy ayarları
        if self.proxy_manager:
            proxy = self.proxy_manager.get_working_proxy()
            if proxy:
                chrome_options.add_argument(f'--proxy-server=http://{proxy}')
        
        try:
            self.driver = uc.Chrome(options=chrome_options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            self.wait = WebDriverWait(self.driver, 20)
        except Exception as e:
            print(f"Chrome başlatma hatası: {str(e)}")
            raise
    def inject_instagram_evasion_scripts(self):
        """Instagram için bot tespitini engelleyici JavaScript kodlarını enjekte eder"""
        evasion_scripts = """
            // Instagram'ın bot tespitini bypass et
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Instagram'ın otomasyon kontrollerini atla
            const originalFunction = window.Function.prototype.toString;
            window.Function.prototype.toString = function() {
                if (this === window.navigator.permissions.query) {
                    return 'function query() { [native code] }';
                }
                return originalFunction.apply(this, arguments);
            };
            
            // Instagram için özel zamanlama simülasyonu
            const rand = (min, max) => Math.floor(Math.random() * (max - min) + min);
            const delay = rand(50, 150);
            
            const originalDate = Date.now;
            Date.now = function() {
                return originalDate() + delay;
            };
        """
        try:
            self.driver.execute_script(evasion_scripts)
        except Exception as e:
            print(f"Instagram script enjeksiyon hatası: {e}")
    
    def simulate_instagram_human_behavior(self):
        """Instagram'da insan davranışlarını simüle eder"""
        actions = [
            lambda: time.sleep(random.uniform(0.8, 2.0)),  # Instagram için optimal bekleme
            lambda: self.driver.execute_script(
                f"window.scrollBy(0, {random.randint(-200, 200)});"
            ),  # Instagram feed scroll simülasyonu
            lambda: ActionChains(self.driver).move_by_offset(
                random.randint(-40, 40), 
                random.randint(-40, 40)
            ).move_by_offset(
                random.randint(-10, 10), 
                random.randint(-10, 10)
            ).perform(),  # İki aşamalı fare hareketi
            lambda: ActionChains(self.driver).pause(
                random.uniform(0.2, 0.4)
            ).send_keys(Keys.TAB if random.random() < 0.2 else Keys.ESCAPE).perform(),
            lambda: self.add_random_cursor_movement()  # Özel cursor hareketi
        ]
        
        # Instagram için daha doğal davranış döngüsü
        for _ in range(random.randint(2, 4)):
            try:
                random.choice(actions)()
                if random.random() < 0.4:  # %40 ihtimalle ekstra hareket
                    time.sleep(random.uniform(0.3, 0.7))
                    random.choice(actions)()
            except:
                continue
    
    def add_random_cursor_movement(self):
        """Instagram için özel imza niteliğinde fare hareketi oluşturur"""
        try:
            action = ActionChains(self.driver)
            # Benzersiz hareket paterni
            points = [(random.randint(-60, 60), random.randint(-60, 60)) for _ in range(3)]
            
            for x, y in points:
                action.move_by_offset(x, y)
                action.pause(random.uniform(0.1, 0.3))
            
            action.perform()
        except:
            pass
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