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

# قاعدة بيانات بسيطة لحفظ نقاط الإداريين في الذاكرة
staff_points = {}

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
    print("Staffbot is ready with full points and staff system!")

# ---------------------------------------------------------
# الأوامر الإدارية ونظام النقاط والعقوبات
# ---------------------------------------------------------

@bot.command(name="نقاطي", help="لعرض نقاطك الإدارية الحالية")
async def my_points(ctx):
    user_id = str(ctx.author.id)
    points = staff_points.get(user_id, 0)
    
    embed = discord.Embed(
        title="📊 رصيد نقاطك الإدارية",
        description=f"المستهدف: {ctx.author.mention}\nرصيدك الحالي هو: **{points}** نقطة.",
        color=discord.Color.green()
    )
    embed.add_field(
        name="توزيع النقاط للأعضاء:",
        value=f"🎫 إغلاق تكت: `{POINTS_CONFIG['ticket']}`\n⚠️ تحذير: `{POINTS_CONFIG['warn']}`\n🔇 ميوت/تايم أوت: `{POINTS_CONFIG['timeout']}`\n🔨 باند: `{POINTS_CONFIG['ban']}`",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name="نقاط", help="لعرض نقاط إداري معين")
@commands.has_role(ALLOWED_ROLE_ID)
async def check_points(ctx, member: discord.Member):
    user_id = str(member.id)
    points = staff_points.get(user_id, 0)
    await ctx.send(f"📊 الإداري {member.mention} لديه **{points}** نقطة في سجله الإداري.")

@bot.command(name="تحذير", help="تحذير عضو وإضافة نقاط للإداري")
@commands.has_role(ALLOWED_ROLE_ID)
async def warn_member(ctx, member: discord.Member, *, reason="بدون سبب"):
    # إضافة النقاط للإداري الذي قام بالإجراء
    admin_id = str(ctx.author.id)
    staff_points[admin_id] = staff_points.get(admin_id, 0) + POINTS_CONFIG["warn"]
    
    embed = discord.Embed(
        title="⚠️ تسجيل تحذير",
        description=f"تم تحذير العضو {member.mention} بواسطة {ctx.author.mention}",
        color=discord.Color.orange()
    )
    embed.add_field(name="السبب:", value=reason, inline=False)
    embed.add_field(name="نقاط الإداري المضافة:", value=f"+{POINTS_CONFIG['warn']} نقاط", inline=False)
    
    await ctx.send(embed=embed)
    
    # إرسال إشعار لروم الإشعارات
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

@bot.command(name="ميوت", help="اعطاء تايم أوتلعضو وإضافة نقاط للإداري")
@commands.has_role(ALLOWED_ROLE_ID)
async def timeout_member(ctx, member: discord.Member, *, reason="بدون سبب"):
    admin_id = str(ctx.author.id)
    staff_points[admin_id] = staff_points.get(admin_id, 0) + POINTS_CONFIG["timeout"]
    
    embed = discord.Embed(
        title="🔇 تسجيل ميوت (تايم أوت)",
        description=f"تم عمل تايم أوت للعضو {member.mention} بواسطة {ctx.author.mention}",
        color=discord.Color.yellow()
    )
    embed.add_field(name="السبب:", value=reason, inline=False)
    embed.add_field(name="نقاط الإداري المضافة:", value=f"+{POINTS_CONFIG['timeout']} نقاط", inline=False)
    
    await ctx.send(embed=embed)
    
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

@bot.command(name="باند", help="حظر عضو من السيرفر وإضافة نقاط للإداري")
@commands.has_role(ALLOWED_ROLE_ID)
async def ban_member(ctx, member: discord.Member, *, reason="بدون سبب"):
    admin_id = str(ctx.author.id)
    staff_points[admin_id] = staff_points.get(admin_id, 0) + POINTS_CONFIG["ban"]
    
    embed = discord.Embed(
        title="🔨 تسجيل حظر (باند)",
        description=f"تم حظر العضو {member.mention} بواسطة {ctx.author.mention}",
        color=discord.Color.red()
    )
    embed.add_field(name="السبب:", value=reason, inline=False)
    embed.add_field(name="نقاط الإداري المضافة:", value=f"+{POINTS_CONFIG['ban']} نقاط", inline=False)
    
    await ctx.send(embed=embed)
    
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

@bot.command(name="تكت", help="تسجيل إغلاق تكت وإضافة نقاط للإداري")
@commands.has_role(ALLOWED_ROLE_ID)
async def close_ticket(ctx):
    admin_id = str(ctx.author.id)
    staff_points[admin_id] = staff_points.get(admin_id, 0) + POINTS_CONFIG["ticket"]
    
    embed = discord.Embed(
        title="🎫 إغلاق تكت",
        description=f"تم تسجيل إغلاق التكت بواسطة الإداري {ctx.author.mention}",
        color=discord.Color.blue()
    )
    embed.add_field(name="نقاط الإداري المضافة:", value=f"+{POINTS_CONFIG['ticket']} نقاط", inline=False)
    
    await ctx.send(embed=embed)

# ---------------------------------------------------------
# تشغيل السيرفر المحلي ثم البوت
# ---------------------------------------------------------

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN environment variable not set.")
