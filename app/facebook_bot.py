import os
import asyncio
import logging
from typing import Optional, Dict, Any
import aiohttp
from aiohttp import web
import json

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
FACEBOOK_ACCESS_TOKEN = 'EAAL4JX8G4VoBOxl05GgN9cZCQcFASZAD8qsy5lcuvSDinjTZBFrHtx7BjJS0kMe3PZB1UEhWjWrBtziG9BJOEO28I6ZByDZAVN45zhHrQ4B6AfZBgr6vFPiyDllo4Uvy16ZAXne6mQ70sGby7bJZAwAm8UJbc6ZA2XemlyxciOPrtkgRxB27IFwYSVruljtDJV8J5IYt7ZC1XdyVWShX85Rk2p8bDwSyOkZD'
VERIFY_TOKEN = 'EAAL4JX8G4VoBOxl05GgN9cZCQcFASZAD8qsy5lcuvSDinjTZBFrHtx7BjJS0kMe3PZB1UEhWjWrBtziG9BJOEO28I6ZByDZAVN45zhHrQ4B6AfZBgr6vFPiyDllo4Uvy16ZAXne6mQ70sGby7bJZAwAm8UJbc6ZA2XemlyxciOPrtkgRxB27IFwYSVruljtDJV8J5IYt7ZC1XdyVWShX85Rk2p8bDwSyOkZD'
SAMBANOVA_API_URL = 'https://api.sambanova.ai/v1/chat/completions'
SAMBANOVA_API_KEY = '55ae919a-eac8-4164-ba70-7c2472688b34'

# Constants
API_VERSION = 'v17.0'
REQUEST_TIMEOUT = 30  # seconds


class FacebookBot:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.app = web.Application()
        self.setup_routes()
        self.debug_messages = []

    def setup_routes(self):
        self.app.router.add_get('/', self.handle_home)
        self.app.router.add_get('/webhook', self.verify_webhook)
        self.app.router.add_post('/webhook', self.handle_webhook)
        self.app.router.add_get('/debug', self.handle_debug)

    async def handle_home(self, request: web.Request) -> web.Response:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Facebook Messenger Bot</title>
        </head>
        <body>
            <h1>Facebook Messenger Bot</h1>
            <p>Status: Running</p>
            <ul>
                <li><a href="/debug">View Debug Information</a></li>
                <li><a href="/webhook">Webhook Endpoint</a></li>
            </ul>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')

    async def handle_debug(self, request: web.Request) -> web.Response:
        debug_info = {
            'status': 'running',
            'recent_messages': self.debug_messages[-10:],  # Last 10 messages
            'webhook_url': str(request.url).replace('/debug', '/webhook'),
            'verify_token': VERIFY_TOKEN
        }
        return web.json_response(debug_info)

    async def start(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT))
        return self

    async def stop(self):
        if self.session:
            await self.session.close()

    async def verify_webhook(self, request: web.Request) -> web.Response:
        """Verify webhook with Facebook."""
        if request.query.get('hub.mode') == 'subscribe' and request.query.get('hub.verify_token') == VERIFY_TOKEN:
            challenge = request.query.get('hub.challenge', '')
            logger.info(f"Webhook verified successfully")
            return web.Response(text=challenge)
        logger.warning(f"Webhook verification failed")
        return web.Response(text='Invalid verification token', status=403)

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming webhook events from Facebook."""
        try:
            data = await request.json()
            self.debug_messages.append({
                'timestamp': asyncio.get_event_loop().time(),
                'data': data
            })

            if data.get('object') == 'page':
                for entry in data.get('entry', []):
                    for messaging_event in entry.get('messaging', []):
                        sender_id = messaging_event.get('sender', {}).get('id')
                        message_text = messaging_event.get('message', {}).get('text')

                        if sender_id and message_text:
                            asyncio.create_task(self.handle_message(sender_id, message_text))

                return web.Response(text='EVENT_RECEIVED')
            return web.Response(text='NOT_A_PAGE_EVENT')
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return web.Response(text=f'ERROR: {str(e)}', status=500)

    async def handle_message(self, sender_id: str, message_text: str) -> None:
        """Handle an incoming message."""
        try:
            logger.info(f"Handling message from {sender_id}: {message_text}")
            response = await self.process_with_sambanova(message_text)
            if response:
                await self.send_message(sender_id, response)
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    async def send_message(self, recipient_id: str, message_text: str) -> bool:
        """Send a message to a specific recipient."""
        url = f"https://graph.facebook.com/{API_VERSION}/me/messages"
        payload = {
            'recipient': {'id': recipient_id},
            'message': {'text': message_text}
        }
        params = {'access_token': FACEBOOK_ACCESS_TOKEN}

        try:
            async with self.session.post(url, json=payload, params=params) as response:
                if response.status == 200:
                    logger.info(f"Message sent to {recipient_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send message: {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False

    async def process_with_sambanova(self, message_text: str) -> Optional[str]:
        """Process a message using the SambaNova API."""
        headers = {
            'Authorization': f'Bearer {SAMBANOVA_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {'input': message_text}

        try:
            async with self.session.post(SAMBANOVA_API_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('output')
                else:
                    error_text = await response.text()
                    logger.error(f"SambaNova API error: {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Error calling SambaNova API: {str(e)}")
            return None


async def main():
    bot = FacebookBot()
    await bot.start()

    runner = web.AppRunner(bot.app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)

    try:
        await site.start()
        logger.info("Server started at http://localhost:8080")
        logger.info(f"Webhook URL: http://localhost:8080/webhook")
        logger.info(f"Debug URL: http://localhost:8080/debug")

        # Keep the server running
        while True:
            await asyncio.sleep(3600)
    finally:
        await bot.stop()
        await runner.cleanup()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")