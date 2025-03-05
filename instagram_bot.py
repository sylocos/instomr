import requests
import json
import time
import random
import string
import uuid
import hmac
import hashlib
import logging
import re
from faker import Faker
from datetime import datetime, timezone
import os
from PIL import Image
from io import BytesIO
import backoff
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Logging configuration with UTC time
logging.Formatter.converter = time.gmtime
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_creator.log'),
        logging.StreamHandler()
    ]
)

class DropMailClient:
    def __init__(self):
        self.session = requests.Session()
        self.email = None
        self.session_id = None
        # API endpoints
        self.base_urls = [
            'https://dropmail.me/api/graphql/web-test-2',
            'https://dropmail.me/api/graphql/web-test',
            f"https://dropmail.me/api/graphql/web-test-{datetime.now(timezone.utc).strftime('%Y%m%d')}e6Jet"
        ]
        self.current_url_index = 0
        
        # Configure session with retry mechanism
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy, pool_maxsize=10)
        self.session.mount("https://", adapter)
        
        # Headers
        self.session.headers.update({
            'Host': 'dropmail.me',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Origin': 'https://dropmail.me',
            'Referer': 'https://dropmail.me/',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        })

    def _get_next_base_url(self):
        """Rotate through available base URLs"""
        self.current_url_index = (self.current_url_index + 1) % len(self.base_urls)
        return self.base_urls[self.current_url_index]

    def create_inbox(self):
        """Create a new temporary email inbox"""
        try:
            query = '''
            mutation {
                introduceSession {
                    id
                    addresses {
                        address
                    }
                    expiresAt
                }
            }
            '''
            
            # Try each URL until one works
            for _ in range(len(self.base_urls)):
                try:
                    response = self.session.post(
                        self.base_urls[self.current_url_index],
                        json={'query': query},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and 'introduceSession' in data['data']:
                            self.session_id = data['data']['introduceSession']['id']
                            self.email = data['data']['introduceSession']['addresses'][0]['address']
                            logging.info(f"Successfully created email: {self.email}")
                            return self.email
                    
                    self._get_next_base_url()
                    
                except Exception as e:
                    logging.warning(f"Error with endpoint {self.base_urls[self.current_url_index]}: {str(e)}")
                    self._get_next_base_url()
                    continue
            
            raise Exception("All endpoints failed")
            
        except Exception as e:
            logging.error(f"Error creating inbox: {str(e)}")
            return None

    def wait_for_verification_code(self, timeout=300):
        """Wait for Instagram verification code"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                query = '''
                query($sessionId: ID!) {
                    session(id: $sessionId) {
                        mails {
                            fromAddr
                            text
                            html
                            headerSubject
                        }
                    }
                }
                '''
                
                variables = {'sessionId': self.session_id}
                
                try:
                    response = self.session.post(
                        self.base_urls[self.current_url_index],
                        json={
                            'query': query,
                            'variables': variables
                        },
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and 'session' in data['data']:
                            mails = data['data']['session'].get('mails', [])
                            
                            for mail in mails:
                                content_to_check = [
                                    mail.get('text', ''),
                                    mail.get('html', ''),
                                    mail.get('headerSubject', ''),
                                    mail.get('fromAddr', '')
                                ]
                                
                                for content in content_to_check:
                                    if content and 'instagram' in content.lower():
                                        match = re.search(r'\b\d{6}\b', content)
                                        if match:
                                            code = match.group(0)
                                            logging.info(f"Found verification code: {code}")
                                            return code
                    
                    time.sleep(5)
                    
                except Exception as e:
                    logging.warning(f"Error checking mail: {str(e)}")
                    self._get_next_base_url()
                    time.sleep(5)
                    continue
            
            logging.warning("Timeout waiting for verification code")
            return None
            
        except Exception as e:
            logging.error(f"Error in verification code check: {str(e)}")
            return None
class ProxyManager:
    def __init__(self):
        self.working_proxies = []
        self.current_index = 0
        self.last_update = 0
        self.update_interval = 180
        self.min_working_proxies = 5
        
        # Güvenilir ve ücretsiz proxy listesi
        self.base_proxies = [
            'http://51.159.115.233:3128',
            'http://163.172.31.44:80',
            'http://51.158.154.73:3128',
            'http://195.154.255.118:3128',
            'http://51.158.68.133:8811',
            'http://51.158.172.165:8811',
            'http://163.172.157.142:3128',
            'http://51.15.242.202:3128',
            'http://51.15.242.202:8080',
            'http://51.158.172.165:8761',
            'http://149.202.181.48:5566',
            'http://51.158.172.165:8089',
            'http://51.158.98.121:8811',
            'http://163.172.189.32:8811',
            'http://178.32.129.31:3128',
            'http://151.80.196.163:8811',
            'http://151.80.196.163:8118',
            'http://163.172.157.142:8089',
            'http://51.158.68.68:8761',
            'http://51.158.106.54:8811'
        ]

    def update_proxies(self):
        """Update working proxy list"""
        try:
            if time.time() - self.last_update < self.update_interval and len(self.working_proxies) >= self.min_working_proxies:
                return

            self.last_update = time.time()
            self.working_proxies = []

            # Test base proxies
            for proxy in self.base_proxies:
                if self.test_proxy(proxy):
                    self.working_proxies.append(proxy)
                    if len(self.working_proxies) >= 10:  # En az 10 çalışan proxy bul
                        break

            if self.working_proxies:
                logging.info(f"Updated proxy list. Working proxies: {len(self.working_proxies)}")
            else:
                logging.warning("No working proxies found!")

        except Exception as e:
            logging.error(f"Error updating proxies: {str(e)}")

    def test_proxy(self, proxy):
        """Test single proxy"""
        try:
            session = requests.Session()
            session.verify = False
            session.headers.update({
                'User-Agent': 'Instagram 269.0.0.18.75 Android',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            })

            # Test URLs
            test_urls = [
                'https://www.instagram.com/',
                'https://i.instagram.com/api/v1/si/fetch_headers/'
            ]

            for url in test_urls:
                try:
                    response = session.get(
                        url,
                        proxies={'http': proxy, 'https': proxy},
                        timeout=5
                    )
                    if response.status_code < 400:
                        return True
                except:
                    continue

            return False
            
        except:
            return False

    def get_proxy(self):
        """Get a working proxy"""
        if len(self.working_proxies) < self.min_working_proxies:
            self.update_proxies()
        
        if not self.working_proxies:
            return None
        
        # Rastgele proxy seç
        return random.choice(self.working_proxies)

    def remove_proxy(self, proxy):
        """Remove failed proxy"""
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            logging.info(f"Removed bad proxy. Remaining working proxies: {len(self.working_proxies)}")
        
        if len(self.working_proxies) < self.min_working_proxies:
            self.update_proxies()
    def get_random_proxy(self):
        """Get a random working proxy"""
        if len(self.working_proxies) < self.min_working_proxies:
            self.update_proxies()
        return random.choice(self.working_proxies) if self.working_proxies else None
class InstagramAPI:
    def __init__(self):
        self.session = requests.Session()
        self.fake = Faker('tr_TR')
        self.proxy_manager = ProxyManager()
        self.dropmail = DropMailClient()
        
        self.device_id = self.generate_device_id()
        self.phone_id = self.generate_uuid()
        self.uuid = self.generate_uuid()
        self.waterfall_id = self.generate_uuid()
        self.advertising_id = self.generate_uuid()
        self.android_id = self.generate_android_device_id()
        
        # Current UTC timestamp in milliseconds
        self.timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        self.bio_templates = [
            "🌟 {} | Hayatın tadını çıkar ✨",
            "💫 {} | Pozitif enerji 🌈",
            "🌺 {} | Kendini sev 💝",
            "✨ {} | Hayat güzel 🌟",
            "🎯 {} | Hedeflerine odaklan 💪",
            "🌈 {} | Her an yeni bir başlangıç 🎊",
            "💫 {} | Yaşamak güzel 🌸",
            "🍀 {} | Şansını kendin yarat ⭐",
            "🎨 {} | Hayatı renklendir 🎭",
            "🌙 {} | Yeni ufuklara 🌅"
        ]
        
        self.headers = {
            'User-Agent': f'Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; ONEPLUS A3003; OnePlus3; qcom; tr_TR; {random.randint(300000000, 400000000)})',
            'Accept': '*/*',
            'Accept-Language': 'tr-TR',
            'Accept-Encoding': 'gzip, deflate',
            'X-IG-App-ID': '936619743392459',
            'X-IG-Device-ID': self.device_id,
            'X-IG-Android-ID': self.android_id,
            'X-IG-Connection-Type': 'WIFI',
            'X-IG-Capabilities': '3brTvw==',
            'X-IG-App-Locale': 'tr_TR',
        }
        
        self.session.headers.update(self.headers)

    def generate_device_id(self):
        return 'android-' + ''.join(random.choice(string.hexdigits) for _ in range(16))

    def generate_uuid(self):
        return str(uuid.uuid4())

    def generate_android_device_id(self):
        return 'android-' + ''.join(random.choice(string.hexdigits) for _ in range(8))

    def generate_signature(self, data):
        sig_key = '4f8732eb9ba7d1c8e8897a75d6474d4eb3f5279137431b2aafb71fafe2abe178'
        return hmac.new(
            sig_key.encode('utf-8'),
            str(data).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    @backoff.on_exception(backoff.expo,
                         (requests.exceptions.RequestException, json.JSONDecodeError),
                         max_tries=3)
    def send_request(self, endpoint, data=None, params=None):
        url = f'https://i.instagram.com/api/v1/{endpoint}'
        max_retries = 5
        retry_count = 0
        retry_delay = 3
        
        while retry_count < max_retries:
            proxy = self.proxy_manager.get_proxy()
            if not proxy:
                logging.warning("No working proxies available. Waiting...")
                time.sleep(retry_delay)
                retry_count += 1
                continue
                
            try:
                # Request data preparation
                if data:
                    data['device_timestamp'] = str(int(time.time() * 1000))
                    json_data = json.dumps(data)
                    signature = self.generate_signature(json_data)
                    params = {
                        'ig_sig_key_version': '4',
                        'signed_body': f'{signature}.{json_data}'
                    }
                
                # Setup session
                session = requests.Session()
                session.verify = False
                session.headers.update(self.headers)
                
                # Additional headers
                extra_headers = {
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-IG-Connection-Speed': f'{random.randint(1000, 3000)}kbps',
                    'X-IG-Bandwidth-Speed-KBPS': '-1.000',
                    'X-IG-Bandwidth-TotalBytes-B': '0',
                    'X-IG-Bandwidth-TotalTime-MS': '0',
                }
                session.headers.update(extra_headers)
                
                # Make request
                response = session.post(
                    url,
                    data=data,
                    params=params,
                    proxies={'http': proxy, 'https': proxy},
                    timeout=15
                )
                
                if response.status_code == 200:
                    try:
                        json_response = response.json()
                        if 'status' in json_response and json_response['status'] == 'fail':
                            if 'message' in json_response:
                                logging.warning(f"Instagram error: {json_response['message']}")
                            self.proxy_manager.remove_proxy(proxy)
                            continue
                        return json_response
                    except json.JSONDecodeError:
                        logging.warning(f"Invalid JSON response: {response.text[:100]}")
                        self.proxy_manager.remove_proxy(proxy)
                elif response.status_code == 429:
                    logging.warning("Rate limited. Waiting...")
                    time.sleep(30)
                    continue
                else:
                    logging.warning(f"Request failed with status {response.status_code}")
                    self.proxy_manager.remove_proxy(proxy)
                    
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request error with proxy {proxy}: {str(e)}")
                self.proxy_manager.remove_proxy(proxy)
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
            
            retry_count += 1
            time.sleep(retry_delay)
        
        raise Exception(f"Failed to send request to {endpoint} after {max_retries} attempts")
    def generate_random_bio(self):
        template = random.choice(self.bio_templates)
        words = [self.fake.word() for _ in range(2)]
        return template.format(" ".join(words))

    def update_profile(self, biography):
        try:
            bio_data = {
                'raw_text': biography,
                'device_id': self.device_id,
            }
            bio_response = self.send_request('accounts/set_biography/', bio_data)
            
            if not bio_response or bio_response.get('status') != 'ok':
                raise Exception(f"Failed to update biography: {bio_response}")

            logging.info("Profile updated successfully")
            return True

        except Exception as e:
            logging.error(f"Error updating profile: {str(e)}")
            return False

    @backoff.on_exception(backoff.expo,
                         Exception,
                         max_tries=3)
    def create_account(self):
        max_attempts = 3
        current_attempt = 0
        
        while current_attempt < max_attempts:
            try:
                # Get email from DropMail
                email = self.dropmail.create_inbox()
                if not email:
                    raise Exception("Failed to create email inbox")
    
                # Generate account details
                username = f"{self.fake.user_name()}_{random.randint(100,999)}"
                password = f"Pass_{self.fake.password(length=10)}#1"
                full_name = self.fake.name()
    
                # Account data
                account_data = {
                    'device_id': self.device_id,
                    'email': email,
                    'username': username,
                    'password': password,
                    'first_name': full_name,
                    'client_id': self.device_id,
                    'seamless_login_enabled': '1',
                    'force_sign_up_code': '',
                    'waterfall_id': self.waterfall_id,
                    'qs_stamp': '',
                    'phone_id': self.phone_id,
                    'guid': self.uuid,
                    'advertising_id': self.advertising_id,
                }
    
                # Create account
                response = self.send_request('accounts/create/', account_data)
                
                if not response:
                    raise Exception("No response from Instagram")
                    
                if 'account_created' not in response:
                    error_msg = response.get('message', 'Unknown error')
                    raise Exception(f"Account creation failed: {error_msg}")
    
                # Wait for verification code
                verification_code = self.dropmail.wait_for_verification_code()
                if not verification_code:
                    raise Exception("Failed to get verification code")
    
                # Confirm email
                confirm_data = {
                    'code': verification_code,
                    'device_id': self.device_id,
                    'email': email,
                }
    
                response = self.send_request('accounts/confirm_email/', confirm_data)
                if response and response.get('status') == 'ok':
                    # Update profile
                    biography = self.generate_random_bio()
                    if self.update_profile(biography):
                        self.save_account(email, username, password, biography)
                        logging.info("Account created and customized successfully!")
                        return True
                
                raise Exception("Account creation or customization failed")
    
            except Exception as e:
                logging.error(f"Account creation error: {str(e)}")
                current_attempt += 1
                if current_attempt < max_attempts:
                    wait_time = 10
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                
        return False
    
    def save_account(self, email, username, password, biography):
        try:
            # UTC zaman damgası oluştur
            current_time = datetime.now(timezone.utc)
            
            # Dosya adını tarihle oluştur
            filename = f'instagram_accounts_{current_time.strftime("%Y%m%d")}.txt'
            
            # Hesap bilgilerini kaydet
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Registration Time (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
                f.write(f"Email: {email}\n")
                f.write(f"Username: {username}\n")
                f.write(f"Password: {password}\n")
                f.write(f"Biography: {biography}\n")
                f.write(f"{'='*50}\n")
            
            # Ayrıca başarılı hesapları ayrı dosyada sakla
            with open('successful_accounts.txt', 'a', encoding='utf-8') as f:
                f.write(f"{username}:{password}:{email}\n")
                
            logging.info(f"Account details saved successfully to {filename}")
            
        except Exception as e:
            logging.error(f"Error saving account details: {str(e)}")
            raise

def main():
    """Main execution function with improved retry logic and error handling"""
    logging.info("Starting Instagram Account Creator...")
    
    max_attempts = 3
    attempt = 0
    wait_time_base = 10
    
    while attempt < max_attempts:
        try:
            attempt += 1
            logging.info(f"Attempt {attempt} of {max_attempts}")
            
            # Instagram API instance oluştur
            api = InstagramAPI()
            
            # Hesap oluşturma işlemini başlat
            success = api.create_account()
            
            if success:
                logging.info("Account creation and customization completed successfully")
                break
            else:
                if attempt < max_attempts:
                    wait_time = wait_time_base * (2 ** (attempt - 1))  # Exponential backoff
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error("Maximum attempts reached. Failed to create account")
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error in attempt {attempt}: {str(e)}")
            if attempt < max_attempts:
                wait_time = wait_time_base * (2 ** (attempt - 1))
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error in attempt {attempt}: {str(e)}")
            if attempt < max_attempts:
                wait_time = wait_time_base * (2 ** (attempt - 1))
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
        except Exception as e:
            logging.error(f"Unexpected error in attempt {attempt}: {str(e)}")
            if attempt < max_attempts:
                wait_time = wait_time_base * (2 ** (attempt - 1))
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error("Maximum attempts reached. Terminating program")
                break
    
    logging.info("Program terminated")

if __name__ == "__main__":
    try:
        # Set process title if possible
        try:
            import setproctitle
            setproctitle.setproctitle('instagram_bot')
        except ImportError:
            pass
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Start the main process
        main()
        
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Critical error: {str(e)}")
        sys.exit(1)