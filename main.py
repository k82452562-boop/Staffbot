import discord
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread

# ----------------------------------------------------
# سيرفر Flask لإبقاء البوت نشطاً على Render
# ----------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ----------------------------------------------------
# 1. إعدادات البوت والتوكن والبادئة والصلاحيات
# ----------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "."  # البادئة الخاصة بالأوامر

# الأيدي المسموح لها استخدام البوت
ALLOWED_ROLE_IDS = [
    1545520633939624006,  # الرتبة الأساسية المحددة
    1545520950064316516,  # رتبة الإدارة الصغرى / العليا
    1540838084151877714   # رتبة الإدارة الوسطى
]

NOTIFICATION_CHANNEL_ID = 1553848524205072474

POINTS_CONFIG = {
    "ticket": 10,
    "warn": 10,
    "timeout": 10,
    "ban": 10
}

PROMOTION_MILESTONES = {
    400: {"title": "الإدارة الصغرى", "role_id": 1545520950064316516},
    700: {"title": "الإدارة الوسطى", "role_id": 1540838084151877714},
    1000: {"title": "الإدارة العليا", "role_id": 1545520950064316516}
}

# ----------------------------------------------------
# 2. تهيئة البوت وقاعدة البيانات
# ----------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)
DATA_FILE = "points.json"

# فحص الصلاحيات المبسط والواضح
@bot.check
async def check_permissions(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    has_role = any(role.id in ALLOWED_ROLE_IDS for role in getattr(ctx.author, 'roles', []))
    if has_role:
        return True
    
    await ctx.send("❌ **عذرًا:** ليس لديك الصلاحية لاستخدام هذا الأمر!")
    return False

@bot.event
async def on_command_error(ctx, error):
    # طباعة الخطأ بالكامل في شاشة البوت لنعرف سبب أي مشكلة فوراً
    print(f"خطأ في الأمر {ctx.command}: {error}")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ **خطأ:** يرجى كتابة الأمر بشكل صحيح وتعبئة جميع المطلوبة!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ **خطأ:** البيانات المدخلة غير صحيحة (تأكد من اختيار عضو صحيح أو رتبة صحيحة).")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def add_points(ctx, staff: discord.Member, points_amount: int, action_name: str):
    data = load_data()
    user_id = str(staff.id)

    if user_id not in data or isinstance(data[user_id], int):
        old_pts = data.get(user_id, 0) if isinstance(data.get(user_id), int) else 0
        data[user_id] = {"points": old_pts, "notified": []}

    user_data = data[user_id]
    user_data["points"] += points_amount
    current_pts = user_data["points"]

    save_data(data)

    await ctx.send(f"✅ تم إضافة **{points_amount}** نقاط لـ {staff.mention} مقابل ({action_name}). مجموع النقاط الآن: **{current_pts}**")

    for milestone_pts, info in sorted(PROMOTION_MILESTONES.items()):
        if current_pts >= milestone_pts and milestone_pts not in user_data["notified"]:
            user_data["notified"].append(milestone_pts)
            save_data(data)
            
            level_name = info["title"]
            role_id = info["role_id"]
            role_mention = f"<@&{role_id}>"

            notif_channel = ctx.guild.get_channel(NOTIFICATION_CHANNEL_ID)
            
            msg = (
                f"📢 **تنبيه ترقية جديد:**\n"
                f"وصل الإداري {staff.mention} إلى **{current_pts}** نقطة "
                f"(أكمل هدف **{milestone_pts}** نقطة) ويستحق الترقية إلى رتبة {role_mention} (**{level_name}**)! يرجى ترقيته."
            )
            
            if notif_channel:
                await notif_channel.send(msg)

# ----------------------------------------------------
# 3. الأوامر الإدارية ونظام الحماية
# ----------------------------------------------------

@bot.event
async def on_ready():
    print(f"تم تشغيل البوت بنجاح باسم: {bot.user} بالبادئة ({PREFIX})")

@bot.command(name="رتبة", aliases=["giverole", "role"])
async def give_role(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await ctx.send(f"✅ تم إعطاء رتبة {role.mention} لـ {member.mention} بنجاح.")
    except discord.Forbidden:
        await ctx.send("❌ **خطأ:** لا يمتلك البوت صلاحية لإعطاء هذه الرتبة (تأكد أن رتبة البوت أعلى من الرتبة المطلوبة).")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {e}")

@bot.command(name="إغلاق", aliases=["اغلاق", "close"])
async def close(ctx):
    channel_name = ctx.channel.name.lower()
    is_support_channel = "ticket" in channel_name or "تكت" in channel_name or "الدعم" in channel_name or "support" in channel_name
    
    if not is_support_channel:
        await ctx.send("⚠️ **تنبيه حماية:** لا يمكن إغلاق هذا الروم لأنه ليس تكت أو دعم فني!")
        return

    await ctx.send("🔒 جاري إغلاق التكت...")
    await add_points(ctx, ctx.author, POINTS_CONFIG["ticket"], "إغلاق تكت")
    await ctx.channel.delete()

@bot.command(name="تحذير", aliases=["warn"])
async def warn(ctx, member: discord.Member, *, reason="بدون سبب"):
    await ctx.send(f"⚠️ تم إعطاء تحذير لـ {member.mention} | السبب: {reason}")
    await add_points(ctx, ctx.author, POINTS_CONFIG["warn"], "إعطاء تحذير")

@bot.command(name="ميوت", aliases=["timeout"])
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="بدون سبب"):
    duration = discord.utils.utcnow() + discord.utils.datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f"🔇 تم إعطاء تايم أوت لـ {member.mention} لمدة {minutes} دقيقة.")
    await add_points(ctx, ctx.author, POINTS_CONFIG["timeout"], "إعطاء تايم أوت")

@bot.command(name="باند", aliases=["حظر", "ban"])
async def ban(ctx, member: discord.Member, *, reason="بدون سبب"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 تم إعطاء باند لـ {member.mention}.")
    await add_points(ctx, ctx.author, POINTS_CONFIG["ban"], "إعطاء باند")

@bot.command(name="نقاط", aliases=["points"])
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), 0)
    pts = user_info["points"] if isinstance(user_info, dict) else user_info
    await ctx.send(f"📊 نقاط {target.mention} الإدارية هي: **{pts}** نقطة.")

@bot.command(name="إضافة_نقاط", aliases=["addpoints"])
async def addpoints(ctx, member: discord.Member, amount: int):
    await add_points(ctx, member, amount, "إضافة يدوية من الإدارة")

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ: التوكن غير موجود في متغيرات البيئة!")
