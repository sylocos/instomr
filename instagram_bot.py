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
        # Multiple backup URLs
        self.base_urls = [
            "https://dropmail.me/api/graphql/web-test",
            "https://dropmail.me/api/graphql/test1",
            "https://dropmail.me/api/graphql/test2",
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
        
        # Updated headers
        self.session.headers.update({
            'Host': 'dropmail.me',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'accept': '*/*',
            'content-type': 'application/json',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Origin': 'https://dropmail.me',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://dropmail.me/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9'
        })

    def _get_next_base_url(self):
        """Rotate through available base URLs"""
        self.current_url_index = (self.current_url_index + 1) % len(self.base_urls)
        return self.base_urls[self.current_url_index]

    def _make_request(self, query, variables=None, timeout=(5, 10)):
        """Make a GraphQL request with enhanced error handling and retry logic"""
        last_exception = None
        
        # Try each available URL
        for _ in range(len(self.base_urls)):
            current_url = self.base_urls[self.current_url_index]
            try:
                payload = {'query': query}
                if variables:
                    payload['variables'] = variables
                
                logging.debug(f"Attempting request to {current_url}")
                
                response = self.session.post(
                    current_url,
                    json=payload,
                    timeout=timeout,
                    verify=True
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.warning(f"Request failed with status {response.status_code}")
                    self._get_next_base_url()
                    
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logging.warning(f"Connection failed for {current_url}: {str(e)}")
                last_exception = e
                self._get_next_base_url()
                continue
                
            except Exception as e:
                logging.error(f"Unexpected error with {current_url}: {str(e)}")
                last_exception = e
                self._get_next_base_url()
                continue
        
        if last_exception:
            raise last_exception
        raise Exception("All URLs failed")

    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, json.JSONDecodeError),
                         max_tries=5,
                         max_time=120)
    def create_inbox(self):
        """Create a new email inbox with improved error handling"""
        try:
            query = '''
            mutation {
                introduceSession {
                    id
                    expiresAt
                    addresses {
                        address
                    }
                }
            }
            '''
            
            # Try with shorter timeout first
            data = self._make_request(query, timeout=(3, 7))
            
            if 'errors' in data:
                logging.error(f"GraphQL errors: {data['errors']}")
                raise Exception(f"GraphQL error: {data['errors']}")
            
            if 'data' not in data or 'introduceSession' not in data['data']:
                logging.error(f"Invalid response structure: {data}")
                raise Exception("Invalid API response structure")
            
            session_data = data['data']['introduceSession']
            if not session_data.get('addresses'):
                logging.error(f"No addresses in session data: {session_data}")
                raise Exception("No email addresses provided")
            
            self.session_id = session_data['id']
            self.email = session_data['addresses'][0]['address']
            
            logging.info(f"Successfully created email: {self.email}")
            return self.email
                
        except Exception as e:
            logging.error(f"Error creating inbox: {str(e)}")
            raise

    @backoff.on_exception(backoff.expo,
                         (requests.exceptions.RequestException, json.JSONDecodeError),
                         max_tries=5,
                         max_time=180)
    def wait_for_verification_code(self, timeout=300):
        """Wait for and extract Instagram verification code from emails"""
        try:
            start_time = time.time()
            check_interval = 5  # seconds between checks
            
            while time.time() - start_time < timeout:
                query = '''
                query GetMails($sessionId: ID!) {
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
                    # Use shorter timeout for mail checks
                    data = self._make_request(query, variables, timeout=(3, 7))
                    
                    if data and 'data' in data and 'session' in data['data']:
                        session = data['data']['session']
                        if session and 'mails' in session:
                            mails = session['mails']
                            
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
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    logging.warning(f"Error checking mail: {str(e)}")
                    time.sleep(1)  # Short sleep before retry
                    continue
            
            logging.warning("Timeout waiting for verification code")
            return None
            
        except Exception as e:
            logging.error(f"Error in verification code check: {str(e)}")
            return None

def test_dropmail():
    """Test the DropMail functionality"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        client = DropMailClient()
        print("Creating new email inbox...")
        
        email = client.create_inbox()
        print(f"Created email: {email}")
        return True
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_dropmail()
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    if test_dropmail():
        print("DropMail test completed successfully!")
    else:
        print("DropMail test failed!")


    @backoff.on_exception(backoff.expo,
                         (requests.exceptions.RequestException, json.JSONDecodeError),
                         max_tries=5,
                         max_time=180)
    def wait_for_verification_code(self, timeout=300):
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                query = '''
                query GetSessionMails($sessionId: ID!) {
                    session(id: $sessionId) {
                        mails {
                            fromAddr
                            subject
                            text
                            html
                        }
                    }
                }
                '''
                
                # Updated request structure
                payload = {
                    'operationName': 'GetSessionMails',
                    'query': query,
                    'variables': {
                        'sessionId': self.session_id
                    }
                }
                
                try:
                    response = self.session.post(
                        self.base_urls[self.current_url_index],
                        json=payload,
                        timeout=15
                    )
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'data' in data and 'session' in data['data']:
                        mails = data['data']['session'].get('mails', [])
                        
                        for mail in mails:
                            content_to_check = [
                                mail.get('text', ''),
                                mail.get('html', ''),
                                mail.get('subject', '')
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
                    self.get_next_base_url()
                    time.sleep(5)
            
            return None
            
        except Exception as e:
            logging.error(f"Error in verification code check: {str(e)}")
            return None

    @backoff.on_exception(backoff.expo,
                         (requests.exceptions.RequestException, json.JSONDecodeError),
                         max_tries=5,
                         max_time=180)
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
                            html
                        }
                    }
                }
                '''
                
                variables = {'sessionId': self.session_id}
                
                try:
                    response = self.session.post(
                        self.base_urls[self.current_url_index],
                        json={'query': query, 'variables': variables},
                        timeout=15
                    )
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'data' in data and 'session' in data['data']:
                        mails = data['data']['session'].get('mails', [])
                        
                        for mail in mails:
                            content_to_check = [
                                mail.get('text', ''),
                                mail.get('html', ''),
                                mail.get('subject', '')
                            ]
                            
                            for content in content_to_check:
                                if content and 'instagram' in content.lower():
                                    match = re.search(r'\b\d{6}\b', content)
                                    if match:
                                        return match.group(0)
                    
                    time.sleep(5)
                    
                except Exception as e:
                    logging.warning(f"Error checking mail: {str(e)}")
                    self.get_next_base_url()
                    time.sleep(5)
            
            return None
            
        except Exception as e:
            logging.error(f"Error in verification code check: {str(e)}")
            return None

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.last_update = 0
        self.update_interval = 3600

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
                    if response.status_code == 200:
                        proxies = response.text.strip().split('\n')
                        new_proxies.update([f'http://{proxy.strip()}' for proxy in proxies if proxy.strip()])
                except Exception as e:
                    logging.warning(f"Failed to fetch proxies from {source}: {str(e)}")
            
            self.proxies = list(new_proxies)
            
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
            
        except Exception as e:
            if proxy:
                self.proxy_manager.remove_proxy(proxy)
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
            for attempt in range(3):
                try:
                    email = self.dropmail.create_inbox()
                    if email:
                        break
                except Exception as e:
                    if attempt == 2:
                        raise
                    logging.warning(f"Retrying email creation: {str(e)}")
                    time.sleep(5)

            username = f"{self.fake.user_name()}_{random.randint(100,999)}"
            password = f"Pass_{self.fake.password(length=10)}#1"
            full_name = self.fake.name()

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
                'device_timestamp': self.timestamp
            }

            response = self.send_request('accounts/create/', account_data)
            if not response or 'account_created' not in response:
                raise Exception(f"Account creation failed: {response}")

            verification_code = self.dropmail.wait_for_verification_code()
            if not verification_code:
                raise Exception("Failed to get verification code")

            confirm_data = {
                'code': verification_code,
                'device_id': self.device_id,
                'email': email,
            }

            response = self.send_request('accounts/confirm_email/', confirm_data)
            if response and response.get('status') == 'ok':
                biography = self.generate_random_bio()
                if self.update_profile(biography):
                    self.save_account(email, username, password, biography)
                    return True
            
            raise Exception("Account creation or customization failed")

        except Exception as e:
            logging.error(f"Account creation error: {str(e)}")
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