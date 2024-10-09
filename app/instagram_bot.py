import os
import django
import logging
import json
import pickle
import time
import requests
import codecs
from instagram_private_api import Client, ClientCookieExpiredError, ClientLoginRequiredError, \
    ClientCheckpointRequiredError

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# Import models after Django is set up
from app.models import UserProfile, ChatMessage, InstagramProfile

# Configuration
INSTAGRAM_USERNAME = 'sanjarbek__1401'
INSTAGRAM_PASSWORD = 'sanjar1425'
SAMBANOVA_API_KEY = '9ef73b9e-0809-422e-b675-77af7d802291'
SAMBANOVA_API_URL = "https://api.sambanova.ai/v1/chat/completions"
COOKIES_FILE = 'instagram_cookies.json'

MAX_LOGIN_ATTEMPTS = 3
LOGIN_COOLDOWN = 300

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


class InstagramSupportBot:
    def __init__(self):
        self.api = None
        self.processed_messages = set()
        self.login_attempts = 0

    def save_cookies(self, api):
        """Save API cookies to a file"""
        try:
            cookies = api.settings
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f, default=to_json)
            logger.info("Cookies saved successfully")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def load_cookies(self):
        """Load cookies from file"""
        try:
            if os.path.exists(COOKIES_FILE):
                with open(COOKIES_FILE, 'r') as f:
                    cached_settings = json.load(f, object_hook=from_json)
                    return cached_settings
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
        return None

    def login(self):
        """Attempt to log in to Instagram with improved error handling"""
        if self.login_attempts >= MAX_LOGIN_ATTEMPTS:
            logger.error(
                f"Maximum login attempts ({MAX_LOGIN_ATTEMPTS}) reached. Waiting for {LOGIN_COOLDOWN} seconds.")
            time.sleep(LOGIN_COOLDOWN)
            self.login_attempts = 0

        try:
            cached_settings = self.load_cookies()
            if cached_settings:
                try:
                    self.api = Client(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, settings=cached_settings)
                    logger.info("Successfully logged in using saved cookies")
                    self.login_attempts = 0
                    return True
                except (ClientCookieExpiredError, ClientLoginRequiredError):
                    logger.warning("Saved cookies expired, attempting fresh login")
                    if os.path.exists(COOKIES_FILE):
                        os.remove(COOKIES_FILE)

            try:
                self.api = Client(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                self.save_cookies(self.api)
                logger.info("Successfully logged in directly")
                self.login_attempts = 0
                return True
            except ClientCheckpointRequiredError:
                logger.error("Checkpoint challenge required. Manual intervention needed.")
                self.handle_checkpoint_challenge()
                return False
            except Exception as e:
                logger.error(f"Login failed: {e}")
                self.login_attempts += 1
                return False

        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            self.login_attempts += 1
            return False

    def handle_checkpoint_challenge(self):
        """
        Method to handle checkpoint challenge
        This is a placeholder - actual implementation would depend on your needs
        """
        logger.info("Checkpoint challenge detected. Please complete the following steps:")
        logger.info("1. Log in to Instagram manually using a web browser")
        logger.info("2. Complete any security challenges")
        logger.info("3. Once completed, delete the cookies file and restart the bot")

        # You might want to send a notification to the admin here
        self.notify_admin_of_checkpoint()

    def notify_admin_of_checkpoint(self):
        """Send notification to admin about checkpoint challenge"""
        # Implement your notification logic here
        logger.info("Admin notification sent about checkpoint challenge")

    def handle_message(self, thread_id: str, user_id: int, message: str):
        message_identifier = f"{thread_id}:{message}"

        if message_identifier in self.processed_messages:
            return

        try:
            response = self.generate_support_response(message)
            self.api.direct_v2_send(text=response, thread_ids=[thread_id])
            self.processed_messages.add(message_identifier)

            # Save the chat message to the database
            user_profile = UserProfile.objects.get(user_id=user_id)
            ChatMessage.objects.create(user_profile=user_profile, platform='instagram', message_text=message)

            logger.info(f"Processed message from user {user_id}: {message[:50]}...")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def generate_support_response(self, user_message: str) -> str:
        headers = {
            "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
            "Content-Type": "application/json"
        }

        system_prompt = """You are a helpful customer support assistant for our product. 
        Provide clear, concise, and helpful responses to customer inquiries. 
        If you don't know something, say so and offer to escalate to a human agent. 
        Always maintain a professional and friendly tone."""

        payload = {
            "model": "Meta-Llama-3.1-8B-Instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }

        try:
            response = requests.post(SAMBANOVA_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Error generating support response: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later or contact our support team directly."

    def run(self):
        consecutive_errors = 0
        while True:
            try:
                if not self.api:
                    if not self.login():
                        time.sleep(60)
                        continue

                inbox = self.api.direct_v2_inbox()
                threads = inbox['inbox']['threads']

                for thread in threads:
                    if thread['items']:
                        latest_item = thread['items'][0]
                        if latest_item['item_type'] == 'text':
                            thread_id = thread['thread_id']
                            user_id = thread['users'][0]['pk']
                            message = latest_item['text']
                            self.handle_message(thread_id, user_id, message)

                consecutive_errors = 0
                time.sleep(5)

            except (ClientCookieExpiredError, ClientLoginRequiredError):
                logger.warning("Session expired, attempting to login again")
                self.api = None
            except Exception as e:
                consecutive_errors += 1
                wait_time = min(60 * consecutive_errors, 3600)
                logger.error(f"Error in main loop: {e}. Waiting {wait_time} seconds before retry.")
                time.sleep(wait_time)


def main():
    bot = InstagramSupportBot()
    try:
        logger.info("Starting Instagram Support Bot")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        if os.path.exists(COOKIES_FILE):
            os.remove(COOKIES_FILE)
            logger.info("Deleted cookies file due to error")


if __name__ == '__main__':
    main()