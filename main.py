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
# الإعدادات العامة للبوت
# ---------------------------------------------------------

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "."

# رتبة الإدارة المسموح لها باستخدام الأوامر
ALLOWED_ROLE_ID = 154552063939624006

# روم الإشعارات الخاص بالتثبيتات والنقاط
NOTIFICATION_CHANNEL_ID = 1553848524205072474

# توزيع النقاط حسب الإجراءات والعقوبات
POINTS_CONFIG = {
    "ticket": 10,   # إغلاق تكت (10 نقاط)
    "warn": 10,     # تحذير (10 نقاط)
    "timeout": 10,  # تايم أوت / ميوت (10 نقاط)
    "ban": 10       # باند / حظر (10 نقاط)
}

# ---------------------------------------------------------
# إعدادات ديسكورد وبدء التشغيل
# ---------------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Staffbot is ready and running with full Arabic system!")

# ---------------------------------------------------------
# أوامر البوت الإدارية والنقاط (بالعربي)
# ---------------------------------------------------------

@bot.command(name="نقاطي", help="لعرض نقاطك الإدارية الحالية")
async def my_points(ctx):
    embed = discord.Embed(
        title="📊 نظام نقاط الإدارة",
        description=f"مرحباً بك {ctx.author.mention}\nإليك تفاصيل نقاط الإجراءات والعقوبات المسجلة:",
        color=discord.Color.green()
    )
    embed.add_field(
        name="قيمة النقاط لكل إجراء:",
        value=f"🎫 إغلاق تكت: `{POINTS_CONFIG['ticket']}` نقاط\n⚠️ تحذير: `{POINTS_CONFIG['warn']}` نقاط\n🔇 تايم أوت: `{POINTS_CONFIG['timeout']}` نقاط\n🔨 باند: `{POINTS_CONFIG['ban']}` نقاط",
        inline=False
    )
    await ctx.send(embed=embed)


@bot.command(name="إعطاء_نقاط", help="إضافة نقاط لإداري معين")
@commands.has_role(ALLOWED_ROLE_ID)
async def add_points(ctx, member: discord.Member, amount: int, *, reason=None):
    embed = discord.Embed(
        title="✅ تم إضافة النقاط بنجاح",
        description=f"تمت إضافة {amount} نقطة إلى الإداري {member.mention}",
        color=discord.Color.blue()
    )
    if reason:
        embed.add_field(name="السبب:", value=reason, inline=False)
    
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
    
    await ctx.send(embed=embed)


@bot.command(name="رتبة", help="منح رتبة إدارية أو إزالة رتبة")
@commands.has_role(ALLOWED_ROLE_ID)
async def manage_role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"❌ تم إزالة الرتبة {role.name} من {member.mention}")
    else:
        await member.add_roles(role)
        await ctx.send(f"✅ تم إعطاء الرتبة {role.name} إلى {member.mention}")

# ---------------------------------------------------------
# تشغيل السيرفر المحلي ثم البوت
# ---------------------------------------------------------

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN environment variable not set.")
