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
from datetime import datetime
import os
from PIL import Image
from io import BytesIO
import backoff  # New import for retries

# Logging configuration
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
        self.base_url = 'https://dropmail.me/api/graphql/web-test-2'
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, json.JSONDecodeError),
                         max_tries=3)
    def create_inbox(self):
        """Create a new temporary email inbox with improved error handling"""
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
                self.base_url,
                json={'query': query},
                timeout=30
            )
            
            # Verify response status
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {response.text}")
                raise
            
            # Validate response structure
            if 'data' not in data or 'introduceSession' not in data['data']:
                raise ValueError(f"Unexpected API response structure: {data}")
            
            session_data = data['data']['introduceSession']
            if not session_data.get('addresses'):
                raise ValueError("No email address in response")
            
            self.session_id = session_data['id']
            self.email = session_data['addresses'][0]['address']
            
            logging.info(f"Successfully created new email: {self.email}")
            return self.email
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error creating inbox: {str(e)}")
            raise
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logging.error(f"Error processing API response: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error creating inbox: {str(e)}")
            raise

    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, json.JSONDecodeError),
                         max_tries=5)
    def wait_for_verification_code(self, timeout=300):
        """Wait for Instagram verification code with improved error handling"""
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
                            headerSubject
                            html
                        }
                    }
                }
                '''
                
                variables = {'sessionId': self.session_id}
                
                response = self.session.post(
                    self.base_url,
                    json={
                        'query': query,
                        'variables': variables
                    },
                    timeout=30
                )
                
                response.raise_for_status()
                data = response.json()
                
                if 'data' not in data or 'session' not in data['data']:
                    logging.warning(f"Unexpected response structure: {data}")
                    time.sleep(5)
                    continue
                
                mails = data['data']['session'].get('mails', [])
                
                for mail in mails:
                    # Check both HTML and text content for the verification code
                    content_to_check = [
                        mail.get('text', ''),
                        mail.get('html', ''),
                        mail.get('subject', ''),
                        mail.get('headerSubject', '')
                    ]
                    
                    for content in content_to_check:
                        if not content:
                            continue
                            
                        if 'instagram' in content.lower():
                            # Look for 6-digit code
                            match = re.search(r'\b\d{6}\b', content)
                            if match:
                                code = match.group(0)
                                logging.info(f"Found verification code: {code}")
                                return code
                
                time.sleep(5)
            
            logging.warning("Timeout waiting for verification code")
            return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error getting verification code: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing API response: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error getting verification code: {str(e)}")
            raise

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.last_update = 0
        self.update_interval = 3600  # Update proxy list every hour

    def update_proxies(self):
        try:
            current_time = time.time()
            if current_time - self.last_update < self.update_interval:
                return
                
            self.last_update = current_time
            sources = [
                'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt'
            ]
            
            new_proxies = set()
            for source in sources:
                try:
                    response = requests.get(source, timeout=10)
                    response.raise_for_status()
                    proxies = response.text.strip().split('\n')
                    new_proxies.update([f'http://{proxy.strip()}' for proxy in proxies if proxy.strip()])
                except Exception as e:
                    logging.warning(f"Failed to fetch proxies from {source}: {str(e)}")
            
            self.proxies = list(new_proxies)
            logging.info(f"Updated proxy list. Total proxies: {len(self.proxies)}")
            
        except Exception as e:
            logging.error(f"Error updating proxies: {str(e)}")

    def get_proxy(self):
        if not self.proxies or time.time() - self.last_update >= self.update_interval:
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
        self.android_id = self.generate_android_device_id()
        
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
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {str(e)}")
            if proxy:
                self.proxy_manager.remove_proxy(proxy)
            raise
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in send_request: {str(e)}")
            raise

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
        try:
            # Get email from DropMail with retry
            for attempt in range(3):
                try:
                    email = self.dropmail.create_inbox()
                    if email:
                        break
                except Exception as e:
                    if attempt == 2:
                        raise
                    logging.warning(f"Retrying email creation after error: {str(e)}")
                    time.sleep(5)

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
                raise Exception(f"Account creation failed: {response}")

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
                                        # Continuing from the create_account method
                    self.save_account(email, username, password, biography)
                    logging.info("Account created and customized successfully!")
                    return True

            raise Exception("Failed to confirm email")

        except Exception as e:
            logging.error(f"Account creation error: {str(e)}")
            return False

    def save_account(self, email, username, password, biography):
        """Save created account details to a file"""
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
            raise

def main():
    """Main execution function with retry logic"""
    logging.info("Starting Instagram Account Creator...")
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        try:
            attempt += 1
            logging.info(f"Attempt {attempt} of {max_attempts}")
            
            api = InstagramAPI()
            success = api.create_account()
            
            if success:
                logging.info("Account creation and customization completed successfully")
                break
            else:
                if attempt < max_attempts:
                    wait_time = 30 * attempt  # Increasing wait time between attempts
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error("Maximum attempts reached. Failed to create account")
                    
        except Exception as e:
            logging.error(f"Unexpected error in attempt {attempt}: {str(e)}")
            if attempt < max_attempts:
                wait_time = 30 * attempt
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error("Maximum attempts reached. Terminating program")
    
    logging.info("Program terminated")

if __name__ == "__main__":
    main()