import os
import django
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from asgiref.sync import sync_to_async

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from app.models import UserProfile, ChatMessage
from django.contrib.auth.models import User

API_TOKEN = '7424564839:AAGgdtvaLz8FzW2Frb9vrMm4cM0JdBof1Fo'

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Constants
VERIFICATION_ATTEMPT = {}

# Reply keyboard for main options
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

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Salom! Iltimos, quyidagi opsiyalardan birini tanlang:", reply_markup=main_menu_keyboard())

@dp.message(F.text == "🛂 Passport ma'lumotlarini kiritish")
async def request_passport(message: Message):
    VERIFICATION_ATTEMPT[message.from_user.id] = "input"
    await message.answer("Iltimos, passport ma'lumotlaringizni kiriting. Format: seriya raqami.")

@dp.message(F.text == "✔️ Shaxsni tasdiqlash")
async def request_verification(message: Message):
    VERIFICATION_ATTEMPT[message.from_user.id] = "verify"
    await message.answer("Shaxsingizni tasdiqlash uchun passport ma'lumotlarini kiriting. Format: seriya raqami.")

@dp.message(F.text == "📝 Yozishmalar tarixini ko'rish")
async def show_history(message: Message):
    await history_handler(message)

@dp.message()
async def handle_passport_data(message: Message):
    if " " not in message.text:
        return

    passport_info = message.text.split()
    if len(passport_info) != 2 or not passport_info[0].isalpha() or len(passport_info[0]) != 2 or not passport_info[1].isdigit() or len(passport_info[1]) != 7:
        await message.answer("Iltimos, passport ma'lumotlaringizni to'g'ri formatda kiriting. Seriya 2 harf, raqam 7 raqamdan iborat bo'lishi kerak.")
        return

    passport_series, passport_number = passport_info
    attempt_type = VERIFICATION_ATTEMPT.get(message.from_user.id, "input")

    try:
        if attempt_type == "verify":
            await verify_identity(message, passport_series, passport_number)
        else:
            await save_passport_data(message, passport_series, passport_number)
    except Exception as e:
        print(f"Error processing passport data: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
    finally:
        VERIFICATION_ATTEMPT.pop(message.from_user.id, None)

# Passport ma'lumotlarini tekshirish va olish
async def verify_identity(message: Message, passport_series: str, passport_number: str):
    user_profile = await sync_to_async(lambda: UserProfile.objects.filter(user_id=message.from_user.id).first())()

    if not user_profile:
        await message.answer("Sizning ma'lumotlaringiz topilmadi. Iltimos, avval passport ma'lumotlarini kiriting.")
        return

    if user_profile.passport_series == passport_series and user_profile.passport_number == passport_number:
        chat_message = ChatMessage(
            user_profile=user_profile,
            platform='Telegram',
            message_text="Identity verified successfully"
        )
        await sync_to_async(chat_message.save)()

        await message.answer("✅ Shaxsingiz tasdiqlandi!")
    else:
        chat_message = ChatMessage(
            user_profile=user_profile,
            platform='Telegram',
            message_text="Failed verification attempt"
        )
        await sync_to_async(chat_message.save)()

        await message.answer("❌ Kiritilgan ma'lumotlar avval saqlangan ma'lumotlar bilan mos kelmadi.")

# Passport ma'lumotlarini saqlash
async def save_passport_data(message: Message, passport_series: str, passport_number: str):
    user, created = await sync_to_async(User.objects.get_or_create)(
        id=message.from_user.id,
        defaults={
            'username': str(message.from_user.id),
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

    chat_message = ChatMessage(
        user_profile=user_profile,
        platform='Telegram',
        message_text=f"Passport data updated: Series: {passport_series}, Number: {passport_number}"
    )
    await sync_to_async(chat_message.save)()

    await message.answer("✅ Ma'lumotlaringiz saqlandi!")

async def history_handler(message: Message):
    user_profile = await sync_to_async(lambda: UserProfile.objects.filter(user_id=message.from_user.id).first())()

    if not user_profile:
        await message.answer("Sizning profilingiz topilmadi.")
        return

    messages = await sync_to_async(list)(ChatMessage.objects.filter(user_profile=user_profile))
    if not messages:
        await message.answer("Hech qanday yozishma topilmadi.")
        return

    response = "\n".join([f"{msg.timestamp}: {msg.platform} - {msg.message_text}" for msg in messages])
    await message.answer(response)

async def main():
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
