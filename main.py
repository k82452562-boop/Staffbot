import discord
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread

# --- سيرفر HTTP بسيط لإبقاء Render حياً ---
app = Flask('')

@app.route('/')
def home():
    return "Staffbot is Running 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ---------------------------------------------------------
# إعدادات البوت والتوكن والبادئة والمساعدين
# ---------------------------------------------------------

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "."

# الرتبة المسموح لها استخدام النوايا
ALLOWED_ROLE_ID = 154552063939624006

# روم الإشعارات الخاص بالتثبيتات عامة
NOTIFICATION_CHANNEL_ID = 1553848524205072474

# توزيع النقاط حسب العقوبات
POINTS_CONFIG = {
    "ticket": 10,   # إغلاق تكت (10 نقاط)
    "warn": 10,     # تحذير (10 نقاط)
    "timeout": 10,  # تايم أوت / ميوت (10 نقاط)
    "ban": 10       # باند / حظر (10 نقاط)
}

# جدول ترقيات الرتب (PROMOTION_MILESTONES)
PROMOTION_MILESTONES = {
    # يمكنك وضع قيمك هنا كما كانت في ملفك الأصلي
}

# ---------------------------------------------------------
# إعدادات ديسكورد وبدء التشغيل
# ---------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Bot is ready and running!")

# ---------------------------------------------------------
# تشغيل السيرفر المحلي ثم البوت
# ---------------------------------------------------------

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN environment variable not set.")
