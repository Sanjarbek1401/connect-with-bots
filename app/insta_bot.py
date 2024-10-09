from instabot import Bot
import time

bot = Bot()

try:
    bot.login(username="sanjarbek__1401", password="sanjar1425")
except Exception as e:
    print(f"Login failed: {e}")
    # Handle checkpoint challenge
    if "challenge_required" in str(e):
        print("A challenge is required. Please verify your account manually.")
        # You can also add code here to wait for user input or handle re-tries
    else:
        print("An unknown error occurred during login.")

# Continue with follow action if logged in
try:
    bot.follow("munisarizaeva")
except Exception as e:
    print(f"Error following user: {e}")
