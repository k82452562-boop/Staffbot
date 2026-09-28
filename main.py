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
    return "Bot is running 24/7!"

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

# الأيدي المسموح لها استخدام الأوامر العامة للإدارة
ALLOWED_ROLE_IDS = [
    1545520633939624006,  
    1545520950064316516,  
    1540838084151877714   
]

NOTIFICATION_CHANNEL_ID = 1553848524205072474
LOG_CHANNEL_ID = 1553913719128588389  # آيدي روم اللوق للعمليات

POINTS_CONFIG = {
    "ticket": 10,
    "warn": 10,
    "timeout": 10,
    "ban": 10,
    "role_command": 20  # نقاط أمر رول الجديد
}

PROMOTION_MILESTONES = {
    400: {"title": "الإدارة الصغرى", "role_id": 1545520950064316516},
    700: {"title": "الإدارة الوسطى", "role_id": 1540838084151877714},
    1000: {"title": "الإدارة العليا", "role_id": 1545520950064316516}
}

# ----------------------------------------------------
# 2. تهيئة البوت وقاعدة البيانات مع الحفظ الفوري
# ----------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)
DATA_FILE = "points.json"

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
    print(f"خطأ في الأمر {ctx.command}: {error}")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ **خطأ:** يرجى كتابة الأمر بشكل صحيح وتعبئة جميع الحقول المطلوبة!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ **خطأ:** البيانات المدخلة غير صحيحة (تأكد من اختيار عضو صحيح).")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.flush()
        os.fsync(f.fileno())

async def send_log(ctx, title, description, color):
    guild = ctx.guild
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=f"بواسطة الإداري: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await log_channel.send(embed=embed)

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

    await send_log(
        ctx,
        title="📥 | سجل إضافة نقاط",
        description=f"**الإداري المستهدف:** {staff.mention}\n**النقاط المضافة:** `+{points_amount}`\n**السبب / العملية:** {action_name}\n**المجموع الحالي:** `{current_pts}` نقطة",
        color=discord.Color.green()
    )

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

def find_role(guild, role_identifier):
    if role_identifier.isdigit():
        return guild.get_role(int(role_identifier))
    
    # تنظيف المنشن إذا تم إدخاله بالخطأ كمنشن كامل مثل <@&ID>
    cleaned_id = role_identifier.replace("<&", "").replace(">", "").replace("@", "")
    if cleaned_id.isdigit():
        return guild.get_role(int(cleaned_id))
    
    for role in guild.roles:
        if role_identifier.lower() in role.name.lower():
            return role
    return None

# ----------------------------------------------------
# 3. الأوامر الإدارية ونظام الحماية
# ----------------------------------------------------

@bot.event
async def on_ready():
    print(f"تم تشغيل البوت بنجاح باسم: {bot.user} بالبادئة ({PREFIX})")

# أمر إعطاء رتبة بالشكل المطلوب (.رتبة @العضو الرتبة)
@bot.command(name="رتبة", aliases=["إعطاء_رتبة", "giverole", "role"])
async def give_role(ctx, member: discord.Member, *, role_identifier: str):
    role = find_role(ctx.guild, role_identifier)
    if not role:
        await ctx.send(f"❌ **خطأ:** لم يتم العثور على الرتبة المطابقة لـ ({role_identifier}).")
        return
    
    try:
        await member.add_roles(role)
        embed = discord.Embed(
            title="✅ | تم إعطاء الرتبة بنجاح",
            description=f"تم إعطاء رتبة {role.mention} للعضو {member.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ **خطأ:** لا يمتلك البوت صلاحية لإعطاء هذه الرتبة (تأكد أن رتبة البوت أعلى).")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {e}")

# أمر سحب رتبة
@bot.command(name="سحب_رتبة", aliases=["removerole", "takerole"])
async def remove_role(ctx, member: discord.Member, *, role_identifier: str):
    role = find_role(ctx.guild, role_identifier)
    if not role:
        await ctx.send(f"❌ **خطأ:** لم يتم العثور على الرتبة المطابقة لـ ({role_identifier}).")
        return
    
    try:
        await member.remove_roles(role)
        embed = discord.Embed(
            title="🔄 | تم سحب الرتبة بنجاح",
            description=f"تم سحب رتبة {role.mention} من العضو {member.mention}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ **خطأ:** لا يمتلك البوت صلاحية لسحب هذه الرتبة.")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {e}")

# أمر رول الجديد (يرسل رسالة الرول المخصصة ويعطي 20 نقطة)
@bot.command(name="رول")
async def role_play_message(ctx):
    host_mention = ctx.author.mention
    game_role_mention = "<@&1553782083933966353>"
    
    message_content = (
        f"**تم فتح رول بلاي**\n"
        f"الـهـوسـت : {host_mention}\n"
        f"نـرجـو مـنـكـم قـرائـة الـقـوانـيـن\n\n"
        f"https://discord.com/channels/1517046511714963466/1543074260606648451\n\n"
        f"انـتـظـر رسـالـة إضـافـة الـهـوسـت ثـم تـوجـه\n\n"
        f"https://discord.com/channels/1517046511714963466/1543081098051846184\n\n"
        f"ونـرجـو عـدم ازعـاج الـهـوسـت .\n\n"
        f"|| {game_role_mention} ||"
    )
    
    await ctx.message.delete()  # مسح رسالة الأمر لتبقى الرسالة نظيفة
    await ctx.send(message_content)
    
    # إضافة 20 نقطة للإداري تلقائياً وتسجيلها
    await add_points(ctx, ctx.author, POINTS_CONFIG["role_command"], "فتح رول بلاي (أمر رول)")

# أمر إغلاق التكت
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
    embed = discord.Embed(title="⚠️ | تنبيه تحذير", description=f"تم إعطاء تحذير لـ {member.mention}\n**السبب:** {reason}", color=discord.Color.red())
    await ctx.send(embed=embed)
    await add_points(ctx, ctx.author, POINTS_CONFIG["warn"], "إعطاء تحذير")

@bot.command(name="ميوت", aliases=["timeout"])
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="بدون سبب"):
    duration = discord.utils.utcnow() + discord.utils.datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    embed = discord.Embed(title="🔇 | عقوبة تايم أوت", description=f"تم إسكات {member.mention} لمدة `{minutes}` دقيقة.\n**السبب:** {reason}", color=discord.Color.dark_orange())
    await ctx.send(embed=embed)
    await add_points(ctx, ctx.author, POINTS_CONFIG["timeout"], "إعطاء تايم أوت")

@bot.command(name="باند", aliases=["حظر", "ban"])
async def ban(ctx, member: discord.Member, *, reason="بدون سبب"):
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 | عقوبة الحظر (باند)", description=f"تم حظر {member.mention} نهائياً.\n**السبب:** {reason}", color=discord.Color.dark_red())
    await ctx.send(embed=embed)
    await add_points(ctx, ctx.author, POINTS_CONFIG["ban"], "إعطاء باند")

@bot.command(name="نقاط", aliases=["points"])
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), 0)
    pts = user_info["points"] if isinstance(user_info, dict) else user_info
    
    embed = discord.Embed(title="📊 | نظام النقاط الإدارية", description=f"نقاط الإداري {target.mention} هي: **{pts}** نقطة.", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="إضافة_نقاط", aliases=["addpoints"])
async def addpoints(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ **عذرًا:** أمر إضافة النقاط يدوياً مخصص للأدمنستريتور (المسؤولين) فقط!")
        return
    await add_points(ctx, member, amount, "إضافة يدوية من الأدمن")

@bot.command(name="تصفير_نقاط", aliases=["resetpoints"])
async def resetpoints(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ **عذرًا:** أمر تصفير النقاط مخصص للأدمنستريتور (المسؤولين) فقط!")
        return

    data = load_data()
    user_id = str(member.id)

    if user_id in data:
        if isinstance(data[user_id], dict):
            data[user_id]["points"] = 0
            data[user_id]["notified"] = []
        else:
            data[user_id] = {"points": 0, "notified": []}
        
        save_data(data)
        await ctx.send(f"🔄 تم تصفير نقاط الإداري {member.mention} وأصبحت **0** نقطة بنجاح.")
        
        await send_log(
            ctx,
            title="🔄 | سجل تصفير نقاط (عضو)",
            description=f"**الإداري الذي تم تصفير نقاطه:** {member.mention}\n**الحالة:** أصبحت نقاطه `0`",
            color=discord.Color.orange()
        )
    else:
        await ctx.send(f"⚠️ العضو {member.mention} ليس لديه أي نقاط مسجلة مسبقاً.")

@bot.command(name="تصفير_الكل", aliases=["resetall"])
async def resetall(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ **عذرًا:** أمر تصفير جميع النقاط مخصص للأدمنستريتور (المسؤولين) فقط!")
        return

    save_data({})
    await ctx.send("🧹 **تم تصفير جميع نقاط الإداريين في السيرفر بالكامل وأصبحت 0 للجميع!**")
    
    await send_log(
        ctx,
        title="🧹 | سجل تصفير شامل (الكل)",
        description=f"**الحدث:** تم تصفير نقاط **جميع** الإداريين في السيرفر بالكامل بواسطة الأدمن {ctx.author.mention}.",
        color=discord.Color.red()
    )

@bot.command(name="توب", aliases=["leaderboard", "top"])
async def leaderboard(ctx):
    data = load_data()
    if not data:
        await ctx.send("📊 لا توجد أي نقاط مسجلة حتى الآن في السيرفر.")
        return

    sorted_users = []
    for user_id, info in data.items():
        pts = info["points"] if isinstance(info, dict) else info
        sorted_users.append((int(user_id), pts))
    
    sorted_users.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 | لوحة صدارة الإداريين",
        color=discord.Color.gold()
    )
    
    description = ""
    for index, (uid, pts) in enumerate(sorted_users[:10], start=1):
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"`#{index}`"
        description += f"{medal} <@{uid}> — **{pts}** نقطة\n"

    embed.description = description if description else "لا توجد بيانات كافية."
    embed.set_footer(text=f"بواسطة بوت الإدارة • طلب بواسطة {ctx.author.name}")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ: التوكن غير موجود في متغيرات البيئة!")
