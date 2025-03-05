import requests
import json
import time
import random
import string
import uuid
import hashlib
import hmac
import logging
import re
import warnings
import urllib3
import concurrent.futures
from faker import Faker
from datetime import datetime
from urllib.parse import urlencode
import os
from PIL import Image
from io import BytesIO

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Logging ayarları
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

    def create_inbox(self):
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
            
            response = self.session.post(
                'https://dropmail.me/api/graphql/web-test-2',
                json={'query': query}
            )
            
            data = response.json()
            self.session_id = data['data']['introduceSession']['id']
            self.email = data['data']['introduceSession']['addresses'][0]['address']
            
            logging.info(f"Created new email: {self.email}")
            return self.email
            
        except Exception as e:
            logging.error(f"Error creating inbox: {str(e)}")
            return None

    def wait_for_verification_code(self, timeout=300):
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                query = '''
                query($sessionId: ID!) {
                    session(id: $sessionId) {
                        mails {
                            fromAddr
                            subject
                            text
                        }
                    }
                }
                '''
                
                variables = {'sessionId': self.session_id}
                
                response = self.session.post(
                    'https://dropmail.me/api/graphql/web-test-2',
                    json={
                        'query': query,
                        'variables': variables
                    }
                )
                
                data = response.json()
                mails = data['data']['session']['mails']
                
                for mail in mails:
                    if 'instagram' in mail['fromAddr'].lower():
                        match = re.search(r'\b\d{6}\b', mail['text'])
                        if match:
                            code = match.group(0)
                            logging.info(f"Found verification code: {code}")
                            return code
                
                time.sleep(5)
            
            logging.warning("Timeout waiting for verification code")
            return None
            
        except Exception as e:
            logging.error(f"Error getting verification code: {str(e)}")
            return None

class ProxyManager:
    def __init__(self):
        self.working_proxies = []
        self.current_index = 0
        self.last_update = 0
        self.update_interval = 180
        self.min_working_proxies = 5

    def update_proxies(self):
        try:
            if time.time() - self.last_update < self.update_interval and len(self.working_proxies) >= self.min_working_proxies:
                return

            self.last_update = time.time()
            new_proxies = set()

            # Güvenilir proxy listesi
            trusted_proxies = [
                'http://51.159.115.233:3128',
                'http://163.172.31.44:80',
                'http://51.158.154.73:3128',
                'http://195.154.255.118:3128',
                'http://51.158.68.133:8811',
                'http://51.158.172.165:8811',
                'http://163.172.157.142:3128',
                'http://51.15.242.202:3128',
                'http://51.15.242.202:8080',
                'http://51.158.172.165:8761'
            ]
            new_proxies.update(trusted_proxies)

            # Test proxies
            self.working_proxies = []
            for proxy in new_proxies:
                if self.test_proxy(proxy):
                    self.working_proxies.append(proxy)
                    if len(self.working_proxies) >= 10:
                        break

            if self.working_proxies:
                logging.info(f"Updated proxy list. Working proxies: {len(self.working_proxies)}")
            else:
                logging.warning("No working proxies found!")

        except Exception as e:
            logging.error(f"Error updating proxies: {str(e)}")

    def test_proxy(self, proxy):
        try:
            session = requests.Session()
            session.verify = False
            session.headers.update({
                'User-Agent': 'Instagram 269.0.0.18.75 Android',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            })

            proxies = {
                'http': proxy,
                'https': proxy
            }

            test_urls = [
                'https://i.instagram.com/api/v1/si/fetch_headers/',
                'https://www.instagram.com/'
            ]

            for url in test_urls:
                try:
                    response = session.get(
                        url,
                        proxies=proxies,
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
        """Get a working proxy or return None for direct connection"""
        if len(self.working_proxies) < self.min_working_proxies:
            self.update_proxies()
        
        if not self.working_proxies:
            logging.warning("No working proxies available, will try direct connection")
            return None
    
        return random.choice(self.working_proxies)
        
        return random.choice(self.working_proxies)

    def remove_proxy(self, proxy):
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            logging.info(f"Removed bad proxy. Remaining working proxies: {len(self.working_proxies)}")
        
        if len(self.working_proxies) < self.min_working_proxies:
            self.update_proxies()

class InstagramAPI:
    def __init__(self):
        self.session = requests.Session()
        self.fake = Faker('tr_TR')
        self.proxy_manager = ProxyManager()
        self.dropmail = DropMailClient()
        
        # Generate unique identifiers
        self.device_id = self.generate_device_id()
        self.phone_id = self.generate_uuid()
        self.uuid = self.generate_uuid()
        self.waterfall_id = self.generate_uuid()
        self.advertising_id = self.generate_uuid()
        self.android_id = self.generate_android_device_id()
        
        # API URLs
        self.api_url = 'https://i.instagram.com/api/v1/'
        self.sig_key_version = '4'
        self.sig_key = '4f8732eb9ba7d1c8e8897a75d6474d4eb3f5279137431b2aafb71fafe2abe178'
        
        # Device info
        self.device_settings = {
            'app_version': '269.0.0.18.75',
            'android_version': 26,
            'android_release': '8.0.0',
            'dpi': '480',
            'resolution': '1080x1920',
            'manufacturer': 'OnePlus',
            'device': 'ONEPLUS A3003',
            'model': 'OnePlus3',
            'cpu': 'qcom',
            'version_code': '314665256'
        }

        # Headers
        self.headers = {
            'User-Agent': f"Instagram {self.device_settings['app_version']} Android ({self.device_settings['android_version']}/{self.device_settings['android_release']}; {self.device_settings['dpi']}dpi; {self.device_settings['resolution']}; {self.device_settings['manufacturer']}; {self.device_settings['device']}; {self.device_settings['model']}; {self.device_settings['cpu']}; tr_TR; {self.device_settings['version_code']})",
            'Accept': '*/*',
            'Accept-Language': 'tr-TR',
            'Accept-Encoding': 'gzip, deflate',
            'X-IG-Capabilities': '3brTvw==',
            'X-IG-Connection-Type': 'WIFI',
            'X-IG-App-ID': '936619743392459',
            'X-IG-App-Locale': 'tr_TR',
            'X-IG-Device-ID': self.device_id,
            'X-IG-Android-ID': self.android_id,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        self.session.headers.update(self.headers)

    def generate_device_id(self):
        """Generate a random device ID"""
        return 'android-' + ''.join(random.choice(string.hexdigits) for _ in range(16))

    def generate_android_device_id(self):
        """Generate a random Android device ID"""
        # Android device ID format: APA91b{16 chars}
        return 'APA91b' + ''.join(random.choice(string.hexdigits) for _ in range(16))

    def generate_uuid(self):
        """Generate a random UUID"""
        return str(uuid.uuid4())

    def generate_phone_id(self):
        """Generate a random phone ID"""
        return self.generate_uuid()

    def generate_waterfall_id(self):
        """Generate a random waterfall ID"""
        return self.generate_uuid()

    def generate_adid(self):
        """Generate a random advertising ID"""
        return self.generate_uuid()

    def generate_signature(self, data):
        return hmac.new(
            self.sig_key.encode('utf-8'),
            str(data).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def send_request(self, endpoint, data=None, params=None):
        url = self.api_url + endpoint
        max_retries = 5
        retry_count = 0
        retry_delay = 3
        
        while retry_count < max_retries:
            proxy = self.proxy_manager.get_proxy()
            
            try:
                if data:
                    # Temel veriyi hazırla
                    data.update({
                        'device_id': self.device_id,
                        '_uuid': self.uuid,
                        '_uid': self.device_id,
                        'guid': self.uuid,
                        'phone_id': self.phone_id,
                        '_csrftoken': 'missing',
                        'device_timestamp': str(int(time.time()))
                    })
                    
                    # JSON string oluştur ve imzala
                    json_data = json.dumps(data)
                    signature = self.generate_signature(json_data)
                    
                    # POST verisi hazırla
                    signed_body = f'{signature}.{json_data}'
                    post_data = {
                        'signed_body': signed_body,
                        'ig_sig_key_version': self.sig_key_version
                    }
                else:
                    post_data = None
                
                # Session oluştur
                session = requests.Session()
                session.headers.update(self.headers)
                session.verify = False
                
                if proxy:
                    logging.info(f"Trying with proxy: {proxy}")
                    proxies = {'http': proxy, 'https': proxy}
                else:
                    logging.info("Trying with direct connection...")
                    proxies = None
                
                # İsteği gönder
                response = session.post(
                    url,
                    data=post_data,
                    proxies=proxies,
                    timeout=30 if not proxy else 15
                )
                
                logging.info(f"Response status: {response.status_code}")
                logging.info(f"Response headers: {dict(response.headers)}")
                logging.info(f"Response content: {response.text[:500]}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 400:
                    error_response = response.json()
                    error_msg = error_response.get('message', 'Unknown error')
                    logging.error(f"Bad request error: {error_msg}")
                    if 'challenge' in error_response:
                        logging.error("Challenge required")
                    raise Exception(f"Bad request: {error_msg}")
                elif response.status_code == 429:
                    wait_time = int(response.headers.get('Retry-After', 60))
                    logging.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {str(e)}")
            except Exception as e:
                logging.error(f"Request error: {str(e)}")
            
            if proxy:
                self.proxy_manager.remove_proxy(proxy)
            
            retry_count += 1
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
        
        raise Exception(f"Failed to send request to {endpoint} after {max_retries} attempts")

    def create_account(self):
        try:
            # Email oluştur
            email = self.dropmail.create_inbox()
            if not email:
                raise Exception("Failed to create email inbox")

            # Hesap bilgileri
            username = f"{self.fake.user_name()}_{random.randint(100,999)}".lower()
            password = f"Pass_{self.fake.password(length=10)}#1"
            first_name = self.fake.first_name()

            # Account creation data
            signup_data = {
                'allow_contacts_sync': 'true',
                'sn_result': 'GOOGLE_PLAY_UNAVAILABLE',
                'username': username,
                'first_name': first_name,
                'adid': self.advertising_id,
                'device_id': self.device_id,
                'email': email,
                'password': password,
                'login_attempt_count': '0',
                'phone_id': self.phone_id,
                'guid': self.uuid,
                'force_sign_up_code': '',
                'waterfall_id': self.waterfall_id,
                'qs_stamp': '',
                'has_sms_consent': 'true',
            }

            # Hesap oluşturma isteği
            response = self.send_request('accounts/create/', signup_data)
            
            if not response:
                raise Exception("No response from server")
            
            if 'account_created' not in response:
                error_msg = response.get('message', 'Unknown error')
                raise Exception(f"Account creation failed: {error_msg}")

            # Doğrulama kodu bekle
            verification_code = self.dropmail.wait_for_verification_code()
            if not verification_code:
                raise Exception("Failed to get verification code")

            # Email doğrulama
            confirm_data = {
                'code': verification_code,
                'device_id': self.device_id,
                'email': email,
            }

            response = self.send_request('accounts/confirm_email/', confirm_data)
            
            if response and response.get('status') == 'ok':
                # Biyografi güncelle
                biography = self.generate_random_bio()
                if self.update_profile(biography):
                    self.save_account(email, username, password, biography)
                    logging.info("Account created successfully!")
                    return True
            
            raise Exception("Account creation failed at confirmation stage")

        except Exception as e:
            logging.error(f"Account creation error: {str(e)}")
            return False
    def save_account(self, email, username, password, biography):
        try:
            with open('instagram_accounts.txt', 'a', encoding='utf-8') as f:
                f.write(f"\nRegistration Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Email: {email}\n")
                f.write(f"Username: {username}\n")
                f.write(f"Password: {password}\n")
                f.write(f"Biography: {biography}\n")
                f.write("-" * 50 + "\n")
            logging.info("Account details saved successfully")
        except Exception as e:
            logging.error(f"Error saving account details: {str(e)}")

def main():
    logging.info("Starting Instagram Account Creator...")
    
    try:
        api = InstagramAPI()
        max_attempts = 3
        current_attempt = 0
        
        while current_attempt < max_attempts:
            logging.info(f"Attempt {current_attempt + 1} of {max_attempts}")
            
            try:
                if api.create_account():
                    logging.info("Account creation successful!")
                    break
                else:
                    current_attempt += 1
                    if current_attempt < max_attempts:
                        wait_time = random.randint(30, 60)  # Random bekleme süresi
                        logging.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        # Proxy listesini yenile
                        api.proxy_manager.update_proxies()
            except Exception as e:
                logging.error(f"Error during attempt {current_attempt + 1}: {str(e)}")
                current_attempt += 1
                if current_attempt < max_attempts:
                    wait_time = random.randint(60, 120)  # Hata durumunda daha uzun bekle
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
    finally:
        logging.info("Program terminated")

if __name__ == "__main__":
    main()