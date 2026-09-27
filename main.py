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

# رقم الرتبة المسموح لها باستخدام الأوامر
ALLOWED_ROLE_ID = 154552063939624006

# روم الإشعارات الخاص بالتثبيتات والنقاط
NOTIFICATION_CHANNEL_ID = 1553848524205072474

# توزيع النقاط حسب الإجراءات والعقوبات
POINTS_CONFIG = {
    "ticket": 10,   
    "warn": 10,     
    "timeout": 10,  
    "ban": 10       
}

# قاعدة بيانات بسيطة لحفظ نقاط الإداريين في الذاكرة
staff_points = {}

# دالة للتحقق مما إذا كان المستخدم لديه صلاحية الأدمن أو الرتبة المطلوبة
def is_admin_or_has_role():
    async def predicate(ctx):
        # التحقق إذا كان صاحب الرسالة هو صاحب السيرفر
        if ctx.guild.owner == ctx.author:
            return True
        # التحقق من صلاحية الأدمن (Administrator)
        if ctx.author.guild_permissions.administrator:
            return True
        # التحقق من وجود الرتبة المحددة
        if any(role.id == ALLOWED_ROLE_ID for role in ctx.author.roles):
            return True
        return False
    return commands.check(predicate)

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
    print("Staffbot is ready with secure permissions!")

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
    await ctx.send(embed=embed)

@bot.command(name="تحذير", help="تحذير عضو وإضافة نقاط للإداري")
@is_admin_or_has_role()
async def warn_member(ctx, member: discord.Member, *, reason="بدون سبب"):
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

@bot.command(name="ميوت", help="اعطاء تايم أوت لعضو وإضافة نقاط للإداري")
@is_admin_or_has_role()
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

@bot.command(name="باند", help="حظر عضو من السيرفر وإضافة نقاط للإداري")
@is_admin_or_has_role()
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

@bot.command(name="تكت", help="تسجيل إغلاق تكت وإضافة نقاط للإداري")
@is_admin_or_has_role()
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
