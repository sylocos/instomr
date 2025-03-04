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
from faker import Faker
from datetime import datetime
from urllib.parse import urlencode
import os
from PIL import Image
from io import BytesIO

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
        """Wait for Instagram verification code"""
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
        self.proxies = []
        self.current_index = 0

    def update_proxies(self):
        try:
            sources = [
                'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt'
            ]
            
            for source in sources:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\n')
                    self.proxies.extend([f'http://{proxy.strip()}' for proxy in proxies if proxy.strip()])
            
            self.proxies = list(set(self.proxies))
            logging.info(f"Updated proxy list. Total proxies: {len(self.proxies)}")
            
        except Exception as e:
            logging.error(f"Error updating proxies: {str(e)}")

    def get_proxy(self):
        if not self.proxies:
            self.update_proxies()
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

    def remove_proxy(self, proxy):
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logging.info(f"Removed bad proxy. Remaining: {len(self.proxies)}")

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
        
        # Biyografi şablonları
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
            'User-Agent': 'Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; ONEPLUS A3003; OnePlus3; qcom; tr_TR; 314665256)',
            'Accept': '*/*',
            'Accept-Language': 'tr-TR',
            'Accept-Encoding': 'gzip, deflate',
            'X-IG-App-ID': '936619743392459',
            'X-IG-Device-ID': self.device_id,
            'X-IG-Android-ID': self.generate_android_device_id(),
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

    def send_request(self, endpoint, data=None, params=None):
        url = f'https://i.instagram.com/api/v1/{endpoint}'
        proxy = self.proxy_manager.get_proxy()
        
        try:
            if data:
                json_data = json.dumps(data)
                signature = self.generate_signature(json_data)
                
                params = {
                    'ig_sig_key_version': '4',
                    'signed_body': f'{signature}.{json_data}'
                }
            
            response = self.session.post(
                url,
                data=data,
                params=params,
                proxies={'http': proxy, 'https': proxy} if proxy else None,
                timeout=30
            )
            
            return response.json()
            
        except Exception as e:
            logging.error(f"Request error: {str(e)}")
            if proxy:
                self.proxy_manager.remove_proxy(proxy)
            return None

    def generate_random_bio(self):
        template = random.choice(self.bio_templates)
        words = [self.fake.word() for _ in range(2)]
        return template.format(" ".join(words))

    def update_profile(self, biography):
        try:
            # Biyografi güncelle
            bio_data = {
                'raw_text': biography,
                'device_id': self.device_id,
            }
            bio_response = self.send_request('accounts/set_biography/', bio_data)
            if not bio_response or bio_response.get('status') != 'ok':
                raise Exception("Failed to update biography")

            logging.info("Profile updated successfully")
            return True

        except Exception as e:
            logging.error(f"Error updating profile: {str(e)}")
            return False

    def create_account(self):
        try:
            # Get email from DropMail
            email = self.dropmail.create_inbox()
            if not email:
                raise Exception("Failed to create email inbox")

            # Generate account details
            username = f"{self.fake.user_name()}_{random.randint(100,999)}"
            password = f"Pass_{self.fake.password(length=10)}#1"
            full_name = self.fake.name()

            # Create account data
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
            if not response or 'account_created' not in response:
                raise Exception("Account creation failed")

            # Wait for and enter verification code
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
                # Generate and set random bio
                biography = self.generate_random_bio()
                
                # Update profile with bio
                if self.update_profile(biography):
                    self.save_account(email, username, password, biography)
                    logging.info("Account created and customized successfully!")
                    return True
                
            raise Exception("Account creation or customization failed")

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
        success = api.create_account()
        
        if success:
            logging.info("Account creation and customization completed successfully")
        else:
            logging.error("Failed to create or customize account")
            
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
    finally:
        logging.info("Program terminated")

if __name__ == "__main__":
    main()