import os
import django
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from asgiref.sync import sync_to_async
import aiohttp
from aiogram.fsm.context import FSMContext

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from app.models import UserProfile, ChatMessage
from django.contrib.auth.models import User

API_TOKEN = '7424564839:AAGgdtvaLz8FzW2Frb9vrMm4cM0JdBof1Fo'
SAMBANOVA_API_KEY = '9ef73b9e-0809-422e-b675-77af7d802291'
SAMBANOVA_API_URL = "https://api.sambanova.ai/v1/chat/completions"

# Initialize bot and dispatcher with storage
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
VERIFICATION_ATTEMPT = {}
VERIFIED_USERS = set()


def get_history(user_id):
    try:
        user_profile = UserProfile.objects.get(user_id=user_id)
        messages = ChatMessage.objects.filter(user_profile=user_profile).order_by('-timestamp')
        return messages, None
    except UserProfile.DoesNotExist:
        return None, "Sizning profilingiz topilmadi."
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        return None, "Yozishmalar tarixini olishda xatolik yuz berdi."


def main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛂 Passport ma'lumotlarini kiritish")],
            [KeyboardButton(text="✔️ Shaxsni tasdiqlash")],
            [KeyboardButton(text="📝 Yozishmalar tarixini ko'rish")]
        ],
        resize_keyboard=True
    )
    return keyboard


async def call_sambanova_ai(message: str, user_id: int) -> str:
    headers = {
        "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "Meta-Llama-3.1-8B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for verified users."},
            {"role": "user", "content": message}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(SAMBANOVA_API_URL, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    logger.error(f"SambaNova API error: {response.status}")
                    return "Kechirasiz, texnik nosozlik yuz berdi."
    except Exception as e:
        logger.error(f"Error calling SambaNova API: {e}")
        return "Kechirasiz, texnik nosozlik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."


@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Salom! Iltimos, quyidagi opsiyalardan birini tanlang:", reply_markup=main_menu_keyboard())


@dp.message(F.text == "🛂 Passport ma'lumotlarini kiritish")
async def request_passport(message: Message):
    VERIFICATION_ATTEMPT[message.from_user.id] = "input"
    await message.answer("Iltimos, passport ma'lumotlaringizni kiriting. Format: seriya raqami.")


@dp.message(F.text == "✔️ Shaxsni tasdiqlash")
async def request_verification(message: Message):
    if message.from_user.id in VERIFIED_USERS:
        await message.answer("Siz allaqachon tasdiqlangansiz. Menga savolingizni berishingiz mumkin.")
    else:
        VERIFICATION_ATTEMPT[message.from_user.id] = "verify"
        await message.answer("Shaxsingizni tasdiqlash uchun passport ma'lumotlarini kiriting. Format: seriya raqami.")


@dp.message(F.text == "📝 Yozishmalar tarixini ko'rish")
async def show_history(message: Message):
    user_id = message.from_user.id
    user_profile = await sync_to_async(UserProfile.objects.get)(user__id=user_id)

    # Fetch chat history in an async-safe way
    messages = await sync_to_async(list)(ChatMessage.objects.filter(user_profile=user_profile))

    if not messages:
        await message.answer("Yozishmalar tarixingiz topilmadi.")
    else:
        history = "\n".join([f"{msg.timestamp}: {msg.message_text}" for msg in messages])
        await message.answer(f"Sizning yozishmalaringiz:\n{history}")


@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id

    if user_id in VERIFIED_USERS:
        response = await call_sambanova_ai(message.text, user_id)
        await message.answer(response)
        return

    if " " not in message.text:
        await message.answer(
            "Iltimos, passport ma'lumotlaringizni to'g'ri formatda kiriting: seriya va raqam bo'sh joy bilan ajratilgan bo'lishi kerak.")
        return

    passport_info = message.text.split()

    if len(passport_info) != 2:
        await message.answer("Passport seriyasi va raqamini bo'sh joy bilan ajrating.")
        return
    elif not passport_info[0].isalpha() or len(passport_info[0]) != 2:
        await message.answer("Passport seriyasi 2 ta harfdan iborat bo'lishi kerak.")
        return
    elif not passport_info[1].isdigit() or len(passport_info[1]) != 7:
        await message.answer("Passport raqami 7 ta raqamdan iborat bo'lishi kerak.")
        return

    passport_series, passport_number = passport_info
    attempt_type = VERIFICATION_ATTEMPT.get(user_id, "input")

    try:
        if attempt_type == "verify":
            user_profile = await sync_to_async(UserProfile.objects.get)(user__id=user_id)
            if user_profile.passport_series == passport_series and user_profile.passport_number == passport_number:
                await sync_to_async(ChatMessage.objects.create)(
                    user_profile=user_profile,
                    platform='Telegram',
                    message_text="Identity verified successfully"
                )

                VERIFIED_USERS.add(user_id)

                await message.answer("✅ Shaxsingiz tasdiqlandi!")
                await message.answer("Endi men bilan suhbatlashishingiz mumkin. Qanday yordam bera olaman?")
            else:
                await sync_to_async(ChatMessage.objects.create)(
                    user_profile=user_profile,
                    platform='Telegram',
                    message_text="Failed verification attempt"
                )
                await message.answer("❌ Kiritilgan ma'lumotlar avval saqlangan ma'lumotlar bilan mos kelmadi.")
        else:
            user, _ = await sync_to_async(User.objects.get_or_create)(
                id=user_id,
                defaults={
                    'username': str(user_id),
                    'password': 'sanjar1425'
                }
            )

            user_profile, created = await sync_to_async(UserProfile.objects.get_or_create)(
                user=user,
                defaults={
                    'passport_series': passport_series,
                    'passport_number': passport_number
                }
            )

            if not created:
                user_profile.passport_series = passport_series
                user_profile.passport_number = passport_number
                await sync_to_async(user_profile.save)()

            await sync_to_async(ChatMessage.objects.create)(
                user_profile=user_profile,
                platform='Telegram',
                message_text=f"Passport ma'lumotlari yangilandi: Seriya: {passport_series}, Raqam: {passport_number}"
            )

            await message.answer("✅ Ma'lumotlaringiz saqlandi!")

    except UserProfile.DoesNotExist:
        await message.answer("Sizning ma'lumotlaringiz topilmadi. Iltimos, avval passport ma'lumotlarini kiriting.")
    except Exception as e:
        logger.error(f"Passport ma'lumotlarini qayta ishlashda xatolik: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
    finally:
        VERIFICATION_ATTEMPT.pop(user_id, None)


async def main():
    try:
        logger.info("Bot ishga tushmoqda...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
