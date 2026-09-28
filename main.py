import discord
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread

# ----------------------------------------------------
# سيرفر Flask لإبقاء البوت نشطاً على Render 24/7
# ----------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Staffbot OP Ultimate 24/7 is Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ----------------------------------------------------
# 1. إعدادات البوت والثوابت وأيدي الرتب
# ----------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "."

ALLOWED_ROLE_IDS = [
    1545520633939624006,  
    1545520950064316516,  
    1540838084151877714   
]

NOTIFICATION_CHANNEL_ID = 1553848524205072474
LOG_CHANNEL_ID = 1553913719128588389

POINTS_CONFIG = {
    "ticket": 10,
    "warn": 10,
    "timeout": 10,
    "ban": 10,
    "role_command": 20
}

# رتب الإدارة الصغرى (مرتبة تصاعدياً من الأولى إلى الأخيرة)
JUNIOR_ROLES = [
    1548407040014155806, # 1
    1548407479396991047, # 2
    1548407580131336283, # 3
    1548407675048689715, # 4
    1548407794426707978, # 5
    1548407869320466583, # 6
    1548407949356048534  # 7
]

# رتب الإدارة الوسطى (مرتبة تصاعدياً من الأولى إلى الأخيرة)
MIDDLE_ROLES = [
    1548408037272715465, # 1
    1548408124531154974, # 2
    1548408197176361191, # 3
    1548408266239910020, # 4
    1548408357457756200  # 5
]

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
    
    embed = discord.Embed(
        title="⛔ | صلاحيات غير صالحة",
        description="عذرًا، أنت لا تملك الصلاحية الكافية لاستخدام هذا الأمر الإداري.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed, delete_after=5)
    return False

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="⚠️ | نقص في البيانات", description="يرجى كتابة الأمر بشكل صحيح وتعبئة كافة الحقول المطلوبة.", color=discord.Color.gold())
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(title="⚠️ | خطأ في المدخلات", description="تأكد من اختيار عضو أو رتبة صحيحة.", color=discord.Color.gold())
        await ctx.send(embed=embed, delete_after=5)

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

async def check_and_promote(ctx, member: discord.Member, current_pts: int):
    guild = ctx.guild
    notif_channel = guild.get_channel(NOTIFICATION_CHANNEL_ID)
    
    target_role_id = None
    role_category_name = ""

    # تحديد الفئة بناءً على النقاط ورتب العضو الحالية
    if current_pts >= 700:
        # نبحث إذا كان يملك رتبة حالية في الوسطى
        current_middle_index = -1
        for idx, r_id in enumerate(MIDDLE_ROLES):
            if guild.get_role(r_id) in member.roles:
                current_middle_index = idx
                break
        
        if current_middle_index == -1:
            # إذا لم يكن يملك أي رتبة وسطى، نعطيه الرتبة الأولى في الوسطى
            target_role_id = MIDDLE_ROLES[0]
        elif current_middle_index < len(MIDDLE_ROLES) - 1:
            # إذا كان يملك رتبة، نعطيه الرتبة التي تليها مباشرة
            target_role_id = MIDDLE_ROLES[current_middle_index + 1]
        
        role_category_name = "الإدارة الوسطى"

    elif 400 <= current_pts < 700:
        # نبحث إذا كان يملك رتبة حالية في الصغرى
        current_junior_index = -1
        for idx, r_id in enumerate(JUNIOR_ROLES):
            if guild.get_role(r_id) in member.roles:
                current_junior_index = idx
                break
        
        if current_junior_index == -1:
            # إذا لم يكن يملك أي رتبة صغرى، نعطيه الأولى
            target_role_id = JUNIOR_ROLES[0]
        elif current_junior_index < len(JUNIOR_ROLES) - 1:
            # نعطيه الرتبة التي تليها مباشرة
            target_role_id = JUNIOR_ROLES[current_junior_index + 1]
            
        role_category_name = "الإدارة الصغرى"

    if target_role_id:
        target_role = guild.get_role(target_role_id)
        if target_role and target_role not in member.roles:
            try:
                # إزالة الرتب القديمة التابعة لنفس الفئة إن وجدت لتنظيم الرتب (اختياري) أو إبقائها
                await member.add_roles(target_role)
                
                # تصفير النقاط بعد الترقية مباشرة
                data = load_data()
                user_id = str(member.id)
                if user_id in data and isinstance(data[user_id], dict):
                    data[user_id]["points"] = 0
                    save_data(data)

                if notif_channel:
                    msg = (
                        f"🎉 **ترقية إدارية وتصفير نقاط:**\n"
                        f"وصل الإداري {member.mention} وتمت ترقيته إلى الرتبة التالية `{target_role.name}` ضمن **{role_category_name}**!\n"
                        f"🔄 **ملاحظة:** تم تصفير نقاطه بنجاح ليبدأ رحلة المنافسة للرتبة التي تليها."
                    )
                    await notif_channel.send(msg)
            except Exception as e:
                print(f"خطأ أثناء منح الترقية والتصفير: {e}")

async def add_points(ctx, staff: discord.Member, points_amount: int, action_name: str):
    data = load_data()
    user_id = str(staff.id)

    if user_id not in data or not isinstance(data[user_id], dict):
        old_pts = data.get(user_id, 0) if isinstance(data.get(user_id), int) else 0
        data[user_id] = {"points": old_pts, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}

    user_data = data[user_id]
    user_data["points"] = user_data.get("points", 0) + points_amount
    current_pts = user_data["points"]

    if "تكت" in action_name:
        user_data["tickets"] = user_data.get("tickets", 0) + 1
    elif "تحذير" in action_name:
        user_data["warns"] = user_data.get("warns", 0) + 1
    elif "تايم أوت" in action_name:
        user_data["timeouts"] = user_data.get("timeouts", 0) + 1
    elif "باند" in action_name:
        user_data["bans"] = user_data.get("bans", 0) + 1

    save_data(data)

    embed = discord.Embed(
        title="✨ | إضافة نقاط إدارية فاخرة",
        description=f"تم إضافة **+{points_amount}** نقطة لـ {staff.mention}\n📌 **السبب:** `{action_name}`\n📊 **المجموع الحالي:** `{current_pts}` نقطة",
        color=discord.Color.brand_green()
    )
    embed.set_thumbnail(url=staff.display_avatar.url)
    await ctx.send(embed=embed)

    await send_log(
        ctx,
        title="📥 | سجل العمليات الإدارية المفصل",
        description=f"**الإداري المستهدف:** {staff.mention}\n**النقاط المضافة:** `+{points_amount}`\n**العملية:** {action_name}\n**المجموع الكلي:** `{current_pts}` نقطة",
        color=discord.Color.green()
    )

    await check_and_promote(ctx, staff, current_pts)

def find_role(guild, role_identifier):
    if role_identifier.isdigit():
        return guild.get_role(int(role_identifier))
    cleaned_id = role_identifier.replace("<&", "").replace(">", "").replace("@", "")
    if cleaned_id.isdigit():
        return guild.get_role(int(cleaned_id))
    for role in guild.roles:
        if role_identifier.lower() in role.name.lower():
            return role
    return None

# ----------------------------------------------------
# 2. الأوامر المتكاملة والتحكم السريع
# ----------------------------------------------------

@bot.event
async def on_ready():
    print(f"🚀 [ULTIMATE OP BOT WITH SMART NEXT-ROLE PROMOTION] تم تشغيل البوت بنجاح باسم: {bot.user}")

@bot.command(name="رتبة", aliases=["إعطاء_رتبة", "giverole", "role"])
async def give_role(ctx, member: discord.Member, *, role_identifier: str):
    role = find_role(ctx.guild, role_identifier)
    if not role:
        await ctx.send("❌ **خطأ:** لم يتم العثور على الرتبة المطلوبة.")
        return
    try:
        await member.add_roles(role)
        embed = discord.Embed(title="✅ | إدارة الرتب الفاخرة", description=f"تم بنجاح منح رتبة {role.mention} للعضو {member.mention}", color=discord.Color.green())
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ **خطأ:** لا يمتلك البوت صلاحية كافية لتنفيذ هذا.")

@bot.command(name="سحب_رتبة", aliases=["removerole", "takerole"])
async def remove_role(ctx, member: discord.Member, *, role_identifier: str):
    role = find_role(ctx.guild, role_identifier)
    if not role:
        await ctx.send("❌ **خطأ:** لم يتم العثور على الرتبة المطلوبة.")
        return
    try:
        await member.remove_roles(role)
        embed = discord.Embed(title="🔄 | إدارة الرتب الفاخرة", description=f"تم بنجاح سحب رتبة {role.mention} من العضو {member.mention}", color=discord.Color.orange())
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ **خطأ:** لا يمتلك البوت صلاحية كافية لتنفيذ هذا.")

@bot.command(name="رول")
async def role_play_message(ctx):
    host_mention = ctx.author.mention
    game_role_mention = "<@&1553782083933966353>"
    
    message_content = (
        f"**✨ ┋ تم فتح رول بلاي رسمي**\n\n"
        f"👤 **الـهـوسـت :** {host_mention}\n"
        f"📌 **نـرجـو مـنـكـم قـرائـة الـقـوانـيـن بعناية:**\n"
        f"🔗 https://discord.com/channels/1517046511714963466/1543074260606648451\n\n"
        f"⏳ **انـتـظـر رسـالـة إضـافـة الـهـوسـت ثـم تـوجـه إلى:**\n"
        f"🔗 https://discord.com/channels/1517046511714963466/1543081098051846184\n\n"
        f"⚠️ **رجاءً، نـرجـو عـدم ازعـاج الـهـوسـت.**\n\n"
        f"|| {game_role_mention} ||"
    )
    
    await ctx.message.delete()
    await ctx.send(message_content)
    await add_points(ctx, ctx.author, POINTS_CONFIG["role_command"], "فتح رول بلاي (أمر رول)")

@bot.command(name="إغلاق", aliases=["اغلاق", "close"])
async def close(ctx):
    channel_name = ctx.channel.name.lower()
    if not any(k in channel_name for k in ["ticket", "تكت", "الدعم", "support"]):
        await ctx.send("⚠️ **حماية:** لا يمكن استخدام أمر الإغلاق هنا!")
        return

    await ctx.send("🔒 جاري أرشيف وإغلاق التكت بنجاح...")
    await add_points(ctx, ctx.author, POINTS_CONFIG["ticket"], "إغلاق تكت")
    await ctx.channel.delete()

@bot.command(name="تحذير", aliases=["warn"])
async def warn(ctx, member: discord.Member, *, reason="بدون سبب"):
    embed = discord.Embed(title="⚠️ | تنبيه إداري فاخر", description=f"تم تحذير العضو {member.mention}\n📝 **السبب:** {reason}", color=discord.Color.red())
    await ctx.send(embed=embed)
    await add_points(ctx, ctx.author, POINTS_CONFIG["warn"], "إعطاء تحذير")

@bot.command(name="ميوت", aliases=["timeout"])
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="بدون سبب"):
    duration = discord.utils.utcnow() + discord.utils.datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    embed = discord.Embed(title="🔇 | عقوبة إسكات فاخرة", description=f"تم إسكات {member.mention} لمدة `{minutes}` دقيقة.\n📝 **السبب:** {reason}", color=discord.Color.dark_orange())
    await ctx.send(embed=embed)
    await add_points(ctx, ctx.author, POINTS_CONFIG["timeout"], "إعطاء تايم أوت")

@bot.command(name="باند", aliases=["حظر", "ban"])
async def ban(ctx, member: discord.Member, *, reason="بدون سبب"):
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 | عقوبة الحظر النهائي الفاخرة", description=f"تم حظر العضو {member.mention} من السيرفر.\n📝 **السبب:** {reason}", color=discord.Color.dark_red())
    await ctx.send(embed=embed)
    await add_points(ctx, ctx.author, POINTS_CONFIG["ban"], "إعطاء باند")

@bot.command(name="بروفايل", aliases=["profile", "stats"])
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0})
    
    if isinstance(user_info, int):
        user_info = {"points": user_info, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}

    pts = user_info.get("points", 0)
    tickets = user_info.get("tickets", 0)
    warns = user_info.get("warns", 0)
    timeouts = user_info.get("timeouts", 0)
    bans = user_info.get("bans", 0)

    embed = discord.Embed(title=f"🛡️ | إحصائيات وبروفايل الإداري: {target.name}", color=discord.Color.blurple())
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="📊 النقاط الإدارية الحالية", value=f"`{pts}` نقطة", inline=True)
    embed.add_field(name="🎫 التكتات المغلقة", value=f"`{tickets}` تكت", inline=True)
    embed.add_field(name="⚠️ التحذيرات المسجلة", value=f"`{warns}` تحذير", inline=True)
    embed.add_field(name="🔇 العقوبات (ميوت)", value=f"`{timeouts}` مرة", inline=True)
    embed.add_field(name="🔨 عقوبات الباند", value=f"`{bans}` باند", inline=True)
    embed.set_footer(text="نظام الإدارة الفاخر • تصفير تلقائي وترقية للرتبة التالية")
    
    await ctx.send(embed=embed)

@bot.command(name="نقاط", aliases=["points"])
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), 0)
    pts = user_info["points"] if isinstance(user_info, dict) else user_info
    
    embed = discord.Embed(title="📊 | استعلام النقاط الفاخر", description=f"نقاط الإداري {target.mention} الحالية هي: **{pts}** نقطة.", color=discord.Color.blue())
    embed.set_thumbnail(url=target.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="إضافة_نقاط", aliases=["addpoints"])
async def addpoints(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        return
    await add_points(ctx, member, amount, "تحكم سريع: إضافة يدوية من الأدمن")

@bot.command(name="خصم_نقاط", aliases=["removepoints"])
async def removepoints(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        return
    data = load_data()
    user_id = str(member.id)
    if user_id in data and isinstance(data[user_id], dict):
        data[user_id]["points"] = max(0, data[user_id]["points"] - amount)
        save_data(data)
        await ctx.send(f"📉 **تحكم سريع:** تم خصم `{amount}` نقطة من الإداري {member.mention}.")
    else:
        await ctx.send("❌ هذا العضو ليس لديه نقاط مسجلة مسبقاً.")

@bot.command(name="تصفير_نقاط", aliases=["resetpoints"])
async def resetpoints(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.administrator:
        return

    data = load_data()
    user_id = str(member.id)
    if user_id in data:
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
        save_data(data)
        await ctx.send(f"🔄 **تحكم سريع:** تم تصفير إحصائيات ونقاط الإداري {member.mention} بنجاح.")

@bot.command(name="تصفير_الكل", aliases=["resetall"])
async def resetall(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    save_data({})
    await ctx.send("🧹 **تحكم سريع:** تم تصفير جميع نقاط وإحصائيات إداريين السيرفر بالكامل!")

@bot.command(name="توب", aliases=["leaderboard", "top"])
async def leaderboard(ctx):
    data = load_data()
    if not data:
        await ctx.send("📊 لا توجد بيانات كافية لعرض لوحة الصدارة.")
        return

    sorted_users = []
    for user_id, info in data.items():
        pts = info["points"] if isinstance(info, dict) else info
        sorted_users.append((int(user_id), pts))
    
    sorted_users.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title="🏆 | لوحة الشرف وصدارة الإداريين الفاخرة", color=discord.Color.gold())
    description = ""
    for index, (uid, pts) in enumerate(sorted_users[:10], start=1):
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"`#{index}`"
        description += f"{medal} <@{uid}> — **{pts}** نقطة\n"

    embed.description = description
    embed.set_footer(text=f"طلب بواسطة {ctx.author.name} • النظام الفاخر للإدارة")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
