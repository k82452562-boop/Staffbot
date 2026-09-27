import discord
from discord.ext import commands
import json
import os

# ----------------------------------------------------
# 1. إعدادات البوت والتوكن والبادئة والصلاحيات
# ----------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

PREFIX = "."  # البادئة الخاصة بالأوامر

# ID الرتبة المسموح لها استخدام البوت
ALLOWED_ROLE_ID = 1545520633939624006

# ID روم الإشعارات الخاص بالتنبيهات عند الترقية
NOTIFICATION_CHANNEL_ID = 1553848524205072474

# توزيع النقاط حسب نظام الإنجازات
POINTS_CONFIG = {
    "ticket": 10,   # إغلاق تكت (10 نقاط)
    "warn": 10,     # تحذير (10 نقاط)
    "timeout": 10,  # تايم أوت / ميوت (10 نقاط)
    "ban": 10       # باند / حظر (10 نقاط)
}

# أهداف نقاط الترقية المحددة ورتبها
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

bot = commands.Bot(command_prefix=PREFIX, intents=intents)
DATA_FILE = "points.json"

# فحص صلاحيات استخدام البوت (أدمن أو صاحب الرتبة المحددة)
@bot.check
async def check_permissions(ctx):
    is_admin = ctx.author.guild_permissions.administrator
    has_role = any(role.id == ALLOWED_ROLE_ID for role in getattr(ctx.author, 'roles', []))
    
    if is_admin or has_role:
        return True
    
    await ctx.send("❌ **عذرًا:** استخدام أوامر هذا البوت مخصص فقط للأدمن أو الإداريين المصرّح لهم!")
    return False

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        pass
    else:
        print(f"حدث خطأ: {error}")

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

    # فحص الأهداف المحددة وإرسال إشعار في روم الإشعارات المحدد فقط
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
            else:
                await ctx.send(f"⚠️ لم يتم العثور على روم الإشعارات المحدد، هذا هو الإشعار:\n{msg}")

# ----------------------------------------------------
# 3. الأوامر الإدارية
# ----------------------------------------------------

@bot.event
async def on_ready():
    print(f"تم تشغيل البوت بنجاح باسم: {bot.user} بالبادئة ({PREFIX})")

# أمر إعطاء رتبة لعضو
@bot.command(name="رتبة", aliases=["اعطاء_رتبة", "إعطاء_رتبة", "giverole", "role"])
async def give_role(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await ctx.send(f"✅ تم إعطاء رتبة {role.mention} لـ {member.mention} بنجاح.")
    except discord.Forbidden:
        await ctx.send("❌ **خطأ:** لا يمتلك البوت صلاحية لإعطاء هذه الرتبة (تأكد أن رتبة البوت أعلى من الرتبة المراد إعطاؤها في إعدادات السيرفر).")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء إعطاء الرتبة: {e}")

# أمر إغلاق التكت المحمي (10 نقاط)
@bot.command(name="إغلاق", aliases=["اغلاق", "close"])
async def close(ctx):
    channel_name = ctx.channel.name.lower()
    is_ticket = "ticket" in channel_name or "تكت" in channel_name or (ctx.channel.category and "ticket" in ctx.channel.category.name.lower())
    
    if not is_ticket:
        await ctx.send("⚠️ **تنبيه حماية:** هذا الأمر مخصص لإغلاق قنوات التكتات فقط!")
        return

    await ctx.send("🔒 جاري إغلاق التكت...")
    await add_points(ctx, ctx.author, POINTS_CONFIG["ticket"], "إغلاق تكت")
    await ctx.channel.delete()

# أمر تحذير (10 نقاط)
@bot.command(name="تحذير", aliases=["warn"])
async def warn(ctx, member: discord.Member, *, reason="بدون سبب"):
    await ctx.send(f"⚠️ تم إعطاء تحذير لـ {member.mention} | السبب: {reason}")
    await add_points(ctx, ctx.author, POINTS_CONFIG["warn"], "إعطاء تحذير")

# أمر تايم أوت / ميوت (10 نقاط)
@bot.command(name="ميوت", aliases=["تايم_أوت", "تايم_اوت", "timeout"])
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="بدون سبب"):
    duration = discord.utils.utcnow() + discord.utils.datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f"🔇 تم إعطاء تايم أوت لـ {member.mention} لمدة {minutes} دقيقة.")
    await add_points(ctx, ctx.author, POINTS_CONFIG["timeout"], "إعطاء تايم أوت")

# أمر باند / حظر (10 نقاط)
@bot.command(name="باند", aliases=["حظر", "ban"])
async def ban(ctx, member: discord.Member, *, reason="بدون سبب"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 تم إعطاء باند لـ {member.mention}.")
    await add_points(ctx, ctx.author, POINTS_CONFIG["ban"], "إعطاء باند")

# أمر عرض النقاط
@bot.command(name="نقاط", aliases=["points"])
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), 0)
    pts = user_info["points"] if isinstance(user_info, dict) else user_info
    await ctx.send(f"📊 نقاط {target.mention} الإدارية هي: **{pts}** نقطة.")

# أمر إضافة نقاط يدويًا
@bot.command(name="إضافة_نقاط", aliases=["اضافة_نقاط", "addpoints"])
async def addpoints(ctx, member: discord.Member, amount: int):
    await add_points(ctx, member, amount, "إضافة يدوية من الإدارة")

bot.run(TOKEN)
