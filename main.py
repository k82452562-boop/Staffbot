import discord
from discord.ext import commands
import json
import os
import time
import asyncio
import re

# ----------------------------------------------------
# 1. الثوابت والأيدي (IDs) المطلوبة للسيرفر
# ----------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "."

# 🎯 أيدي الحاكم ريان (صاحب السيادة والتحكم الكلي)
BOT_OWNER_ID = 917414299184533515

ALLOWED_ROLE_IDS = [
    1545520633939624006,  
    1545520950064316516,  
    1540838084151877714   
]

# الرومات والأيدي
LOG_CHANNEL_ID = 1553913719128588389
NOTIFICATION_CHANNEL_ID = 1541179719297278072   

# 🎯 أيدي روم لوق التكتات
TICKET_LOG_CHANNEL_ID = 1543094678038257784  

BAN_MODEL_CHANNEL_ID = 1543648161807999077
TIMEOUT_MODEL_CHANNEL_ID = 1543648006258294784

APPLY_SUBMIT_CHANNEL_ID = 1543072562538618930   
APPLY_REVIEW_CHANNEL_ID = 1543073109496692737   
WARN_CHANNEL_ID = 1543647851953791179           
ADMIN_ROLE_PENG_ID = 1545520633939624006        

UNVERIFIED_ROLE_ID = 1545695261446250516      
VERIFIED_ROLE_ID = 1545516954754875523        
BAN_ROLE_ID = 1543325398761345175             

# أيدي روم تغيير الاسم ورتبة الأسماء الجديدة
NICKNAME_CHANNEL_ID = 1552311822747443351
NICKNAME_ROLE_ID = 1543071855920029778

WARN_1_ID = 1543278808583372901
WARN_2_ID = 1543278965857198271
WARN_3_ID = 1543279133164048576

# روم النسخ الاحتياطي السحابي للنقاط في ديسكورد
BACKUP_CHANNEL_ID = 1553913719128588389

POINTS_CONFIG = {
    "ticket": 10,
    "warn": 10,
    "timeout": 10,
    "ban": 20,          
    "apply_accept": 10 
}

SPECIAL_PROMOTION_ROLE_ID = 1545520950064316516

JUNIOR_BASE_ROLE_ID = 1540839564506300476

JUNIOR_ROLES = [
    1548407040014155806,
    1548407479396991047,
    1548407580131336283,
    1548407675048689715,
    1548407794426707978,
    1548407869320466583,
    1548407949356048534
]

MIDDLE_BASE_ROLE_ID = 1540838084151877714

MIDDLE_ROLES = [
    1540838084151877714,
    1548408124531154974,
    1548408197176361191,
    1548408266239910020,
    1548408357457756200,
    1540838584922280016,
    1554920899583549521,
    1555165805317197915,
    1555325627647791215
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
DATA_FILE = "points.json"
COOLDOWN_FILE = "cooldowns.json"

double_points_end_time = 0

# ----------------------------------------------------
# دالة فحص صلاحية الأدمنستريتر فقط
# ----------------------------------------------------
def is_admin_or_owner(ctx_or_interaction):
    author = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
    if author.id == BOT_OWNER_ID:
        return True
    return author.guild_permissions.administrator

# ----------------------------------------------------
# دالة البحث عن العضو بالاسم أو اليوزر نيم
# ----------------------------------------------------
async def find_member_by_name(guild: discord.Guild, query: str):
    query = query.strip().lower()
    if query.isdigit():
        member = guild.get_member(int(query))
        if member:
            return member
        try:
            return await guild.fetch_member(int(query))
        except:
            pass

    for member in guild.members:
        if query in member.name.lower() or (member.nick and query in member.nick.lower()):
            return member
    return None

# ----------------------------------------------------
# دالة تحليل المدة الزمنية
# ----------------------------------------------------
def parse_duration_to_seconds(duration_str: str) -> int:
    duration_str = duration_str.strip().lower()
    numbers = re.findall(r'\d+', duration_str)
    if not numbers:
        return 259200
    
    val = int(numbers[0])
    if "دقيقة" in duration_str or "دقائق" in duration_str or "m" in duration_str:
        return val * 60
    elif "ساعة" in duration_str or "ساعات" in duration_str or "h" in duration_str:
        return val * 3600
    elif "يوم" in duration_str or "ايام" in duration_str or "أيام" in duration_str or "d" in duration_str:
        return val * 86400
    elif "شهر" in duration_str or "اشهر" in duration_str:
        return val * 86400 * 30
    return val * 86400

@bot.check
async def check_permissions(ctx):
    if is_admin_or_owner(ctx):
        return True
    
    has_role = any(role.id in ALLOWED_ROLE_IDS for role in getattr(ctx.author, 'roles', []))
    if has_role:
        return True

    embed = discord.Embed(
        title="⚠️ | وين رايح يا الذيب؟ الصلاحيات ما تكفي",
        description="هالأوامر والأنظمة مخصصة للطاقم الإداري المصرح له فقط.",
        color=discord.Color.from_rgb(200, 30, 30)
    )
    await ctx.send(embed=embed, delete_after=5)
    return False

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="⚠️ | ناقصتك تفاصيل يا الكفو", description="امسح الأمر واكتبه كامل ومضبوط.", color=discord.Color.from_rgb(220, 150, 20))
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(title="⚠️ | لخبطة في المدخلات", description="تأكد من كتابة اسم العضو أو البيانات بالشكل السليم.", color=discord.Color.from_rgb(220, 150, 20))
        await ctx.send(embed=embed, delete_after=5)

# دوال الحفظ والقراءة الآمنة
async def fetch_points_from_discord():
    try:
        channel = bot.get_channel(BACKUP_CHANNEL_ID)
        if not channel:
            return
        async for message in channel.history(limit=30):
            if message.attachments:
                for att in message.attachments:
                    if att.filename == "points_backup.json":
                        await att.save(DATA_FILE)
                        return
    except Exception as e:
        print(f"⚠️ خطأ أثناء استرجاع النسخة الاحتياطية: {e}")

async def save_points_to_discord(guild):
    try:
        channel = guild.get_channel(BACKUP_CHANNEL_ID)
        if not channel:
            return
        if os.path.exists(DATA_FILE):
            async for message in channel.history(limit=15):
                if message.author == bot.user and message.attachments:
                    for att in message.attachments:
                        if att.filename == "points_backup.json":
                            try:
                                await message.delete()
                            except:
                                pass
            file = discord.File(DATA_FILE, filename="points_backup.json")
            await channel.send("💾 **[حفظ سحابي فوري] تم تأمين نسخة النقاط:**", file=file)
    except Exception as e:
        print(f"⚠️ خطأ أثناء رفع النسخة الاحتياطية: {e}")

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json(filename, data):
    try:
        temp_file = filename + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filename)
    except Exception as e:
        print(f"❌ خطأ بالحفظ: {e}")

def load_data():
    return load_json(DATA_FILE)

def save_data(data, guild=None):
    save_json(DATA_FILE, data)
    if guild:
        bot.loop.create_task(save_points_to_discord(guild))

def load_cooldowns():
    return load_json(COOLDOWN_FILE)

def save_cooldowns(data):
    save_json(COOLDOWN_FILE, data)

async def send_unified_log(guild, title, description, color=discord.Color.from_rgb(30, 144, 255), fields=None):
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        await log_channel.send(embed=embed)

async def check_and_promote(ctx_or_guild, member: discord.Member, current_pts: int):
    guild = ctx_or_guild.guild if hasattr(ctx_or_guild, 'guild') else ctx_or_guild
    notif_role = guild.get_role(NOTIFICATION_CHANNEL_ID)
    
    target_role_id = None
    role_category_name = ""

    has_special_role = any(r.id == SPECIAL_PROMOTION_ROLE_ID for r in member.roles)
    required_points = 5000 if has_special_role else 400

    if current_pts < required_points:
        return

    middle_index = -1
    for idx, r_id in enumerate(MIDDLE_ROLES):
        if any(r.id == r_id for r in member.roles):
            middle_index = idx
            break

    junior_index = -1
    for idx, r_id in enumerate(JUNIOR_ROLES):
        if any(r.id == r_id for r in member.roles):
            junior_index = idx
            break

    has_junior_base = any(r.id == JUNIOR_BASE_ROLE_ID for r in member.roles)
    has_middle_base = any(r.id == MIDDLE_BASE_ROLE_ID for r in member.roles)

    if middle_index != -1 or has_middle_base:
        if middle_index != -1 and middle_index < len(MIDDLE_ROLES) - 1:
            target_role_id = MIDDLE_ROLES[middle_index + 1]
            role_category_name = "الإدارة الوسطى / العليا"
        elif middle_index == -1 and has_middle_base:
            target_role_id = MIDDLE_ROLES[1] if len(MIDDLE_ROLES) > 1 else MIDDLE_ROLES[0]
            role_category_name = "الإدارة الوسطى / العليا"

    elif junior_index != -1 or has_junior_base:
        if junior_index != -1:
            if junior_index < len(JUNIOR_ROLES) - 1:
                target_role_id = JUNIOR_ROLES[junior_index + 1]
                role_category_name = "الإدارة الصغرى"
            else:
                target_role_id = MIDDLE_ROLES[0]
                role_category_name = "الإدارة الوسطى"
        elif has_junior_base:
            target_role_id = JUNIOR_ROLES[0]
            role_category_name = "الإدارة الصغرى"

    elif current_pts >= 400 and not has_special_role:
        target_role_id = JUNIOR_ROLES[0]
        role_category_name = "الإدارة الصغرى"

    if target_role_id:
        target_role = guild.get_role(target_role_id)
        if target_role and target_role not in member.roles:
            try:
                roles_to_remove = [
                    guild.get_role(rid) for rid in JUNIOR_ROLES + MIDDLE_ROLES 
                    if guild.get_role(rid) and guild.get_role(rid) in member.roles and rid != target_role_id and rid != SPECIAL_PROMOTION_ROLE_ID
                ]
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove, reason="ترقية مستحقة: سحب الرتب القديمة")
                
                await member.add_roles(target_role, reason="ترقية إدارية جديدة")
                
                data = load_data()
                user_id = str(member.id)
                if user_id in data and isinstance(data[user_id], dict):
                    data[user_id]["points"] = 0
                    save_data(data, guild)

                role_ping_str = notif_role.mention if notif_role else ""
                msg = (
                    f"{role_ping_str} 👑 **يا فخر الإدارة ويا كفو! ترقية نارية وتصفير نقاط:**\n"
                    f"ما شاء الله، المطنوخ {member.mention} تقفّل عنده `{required_points}` نقطة وتمت ترقيته رسمياً إلى `{target_role.name}` ضمن **{role_category_name}**!\n"
                    f"🔄 **ملاحظة:** تم سحب الرتبة القديمة وتصفير النقاط لانطلاق تحدٍ جديد."
                )
                log_channel = guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(msg)
            except Exception as e:
                print(f"خطأ أثناء الترقية: {e}")

async def add_points_direct(guild, staff: discord.Member, base_points: int, action_name: str, target_type: str = None):
    global double_points_end_time
    
    is_double_active = time.time() < double_points_end_time
    actual_points = (base_points * 2) if is_double_active else base_points
    
    data = load_data()
    user_id = str(staff.id)

    if user_id not in data or not isinstance(data[user_id], dict):
        old_pts = data.get(user_id, 0) if isinstance(data.get(user_id), int) else 0
        data[user_id] = {"points": old_pts, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0}

    user_data = data[user_id]
    user_data["points"] = user_data.get("points", 0) + actual_points
    current_pts = user_data["points"]

    if target_type == "ticket":
        user_data["tickets"] = user_data.get("tickets", 0) + 1
    elif target_type == "identity":
        user_data["identities"] = user_data.get("identities", 0) + 1

    save_data(data, guild)
    
    double_text = " 🔥 **(الدبل شغال x2 يا وحش!)**" if is_double_active else ""
    await send_unified_log(
        guild, 
        "📊 | رصد وتوثيق نقاط إدارية", 
        f"تم إيداع `{actual_points}` نقطة في محفظة المطنوخ {staff.mention}{double_text}\n📌 **السبب:** {action_name}\n📈 **رصيده الإجمالي الآن:** `{current_pts}` نقطة",
        discord.Color.from_rgb(46, 204, 113) if not is_double_active else discord.Color.from_rgb(241, 196, 15)
    )
    
    await check_and_promote(guild, staff, current_pts)

# ----------------------------------------------------
# النماذج والأزرار
# ----------------------------------------------------
class AddPointsModal(discord.ui.Modal, title="✨ | إضافة نقاط للإداري"):
    user_input = discord.ui.TextInput(label="اسم العضو أو اليوزر نيم", placeholder="اكتب اسم العضو هنا...", required=True)
    amount_input = discord.ui.TextInput(label="عدد النقاط", placeholder="مثال: 50", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = await find_member_by_name(guild, self.user_input.value.strip())
        if not member:
            await interaction.response.send_message("❌ ما لقينا العضو بالسيرفر بهذا الاسم.", ephemeral=True)
            return
        try:
            amount = int(self.amount_input.value.strip())
        except:
            await interaction.response.send_message("❌ تأكد إنك كتبت رقماً صحيحاً للنقاط.", ephemeral=True)
            return

        data = load_data()
        user_id = str(member.id)
        if user_id not in data or not isinstance(data[user_id], dict):
            data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0}
        data[user_id]["points"] += amount
        save_data(data, guild)

        await interaction.response.send_message(f"✨ تم إضافة `{amount}` نقطة لـ {member.mention} بنجاح!", ephemeral=True)
        await send_unified_log(guild, "✨ | إضافة نقاط إدارية", f"بواسطة {interaction.user.mention} تم إضافة `{amount}` نقطة للإداري {member.mention}", discord.Color.from_rgb(46, 204, 113))
        await check_and_promote(guild, member, data[user_id]["points"])

class RemovePointsModal(discord.ui.Modal, title="📉 | خصم نقاط من الإداري"):
    user_input = discord.ui.TextInput(label="اسم العضو أو اليوزر نيم", placeholder="اكتب اسم العضو هنا...", required=True)
    amount_input = discord.ui.TextInput(label="عدد النقاط المراد خصمها", placeholder="مثال: 20", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = await find_member_by_name(guild, self.user_input.value.strip())
        if not member:
            await interaction.response.send_message("❌ ما لقينا العضو بالسيرفر بهذا الاسم.", ephemeral=True)
            return
        try:
            amount = int(self.amount_input.value.strip())
        except:
            await interaction.response.send_message("❌ تأكد إنك كتبت رقماً صحيحاً.", ephemeral=True)
            return

        data = load_data()
        user_id = str(member.id)
        if user_id in data and isinstance(data[user_id], dict):
            data[user_id]["points"] = max(0, data[user_id]["points"] - amount)
            save_data(data, guild)
            await interaction.response.send_message(f"📉 تم خصم `{amount}` نقطة من {member.mention} بنجاح.", ephemeral=True)
            await send_unified_log(guild, "📉 | خصم نقاط إدارية", f"بواسطة {interaction.user.mention} تم خصم `{amount}` نقطة من الإداري {member.mention}", discord.Color.from_rgb(230, 126, 34))
        else:
            await interaction.response.send_message("❌ هذا العضو ليس لديه نقاط مسجلة.", ephemeral=True)

class ResetPointsModal(discord.ui.Modal, title="🔄 | تصفير نقاط إداري"):
    user_input = discord.ui.TextInput(label="اسم العضو أو اليوزر نيم", placeholder="اكتب اسم العضو هنا لتصفير نقاطه...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = await find_member_by_name(guild, self.user_input.value.strip())
        if not member:
            await interaction.response.send_message("❌ ما لقينا العضو بالسيرفر بهذا الاسم.", ephemeral=True)
            return

        data = load_data()
        user_id = str(member.id)
        if user_id in data:
            data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0}
            save_data(data, guild)
            await interaction.response.send_message(f"🔄 تم تصفير نقاط {member.mention} بالكامل بنجاح!", ephemeral=True)
            await send_unified_log(guild, "🔄 | تصفير نقاط إداري", f"بواسطة {interaction.user.mention} تم تصفير نقاط الإداري {member.mention}", discord.Color.from_rgb(231, 76, 60))
        else:
            await interaction.response.send_message("❌ العضو ليس لديه سجل نقاط.", ephemeral=True)

async def auto_remove_warn(guild: discord.Guild, member_id: int, role_to_remove: discord.Role, duration_seconds: int):
    await asyncio.sleep(duration_seconds)
    member = guild.get_member(member_id)
    if not member:
        return
    
    r_warn2 = guild.get_role(WARN_2_ID)
    r_warn3 = guild.get_role(WARN_3_ID)

    if role_to_remove.id == WARN_1_ID and (r_warn2 in member.roles or r_warn3 in member.roles):
        return
    if role_to_remove.id == WARN_2_ID and r_warn3 in member.roles:
        return

    try:
        if role_to_remove in member.roles:
            await member.remove_roles(role_to_remove, reason="انتهت مدة التحذير المحددة")
            await send_unified_log(guild, "🟢 | انتهاء مدة التحذير", f"تم بحمد الله إزالة `{role_to_remove.name}` تلقائياً عن العضو {member.mention} لانقضاء المدة.", discord.Color.from_rgb(46, 204, 113))
    except Exception as e:
        print(f"خطأ في إزالة التحذير التلقائي: {e}")

class WarnModal(discord.ui.Modal, title="⚠ | لوحة توثيق التحذير الإداري"):
    user_input = discord.ui.TextInput(label="اسم العضو أو اليوزر نيم في السيرفر", placeholder="اكتب اسم العضو هنا...", required=True)
    duration_input = discord.ui.TextInput(label="المدة (مثال: 3 ايام / 5 دقائق)", placeholder="راح يزول التحذير تلقائياً بعدها", required=True)
    reason_input = discord.ui.TextInput(label="سبب التحذير بالتفصيل", style=discord.TextStyle.paragraph, placeholder="اكتب التفاصيل هنا...", required=True)
    proof_input = discord.ui.TextInput(label="رابط الدليل (اختياري)", placeholder="رابط صورة أو فيديو...", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        query = self.user_input.value.strip()
        member = await find_member_by_name(guild, query)

        if not member:
            await interaction.response.send_message(f"❌ **ما لقيته يا الغالي:** ما فيه عضو بالسيرفر بهذا الاسم (`{query}`). تأكد منه زين.", ephemeral=True)
            return

        r_warn1 = guild.get_role(WARN_1_ID)
        r_warn2 = guild.get_role(WARN_2_ID)
        r_warn3 = guild.get_role(WARN_3_ID)

        assigned_warn_role = r_warn1
        assigned_warn_name = "تحذير أول"
        try:
            if r_warn2 and r_warn2 in member.roles:
                if r_warn2: await member.remove_roles(r_warn2)
                if r_warn3: await member.add_roles(r_warn3)
                assigned_warn_role = r_warn3
                assigned_warn_name = "تحذير ثالث"
            elif r_warn1 and r_warn1 in member.roles:
                if r_warn1: await member.remove_roles(r_warn1)
                if r_warn2: await member.add_roles(r_warn2)
                assigned_warn_role = r_warn2
                assigned_warn_name = "تحذير ثاني"
            else:
                if r_warn1: await member.add_roles(r_warn1)
                assigned_warn_role = r_warn1
                assigned_warn_name = "تحذير أول"
        except Exception as e:
            print(f"خطأ في منح رتبة التحذير: {e}")

        proof = self.proof_input.value.strip() if self.proof_input.value else "لا يوجد"
        reason = self.reason_input.value.strip()
        duration_text = self.duration_input.value.strip()
        duration_sec = parse_duration_to_seconds(duration_text)

        warn_channel = guild.get_channel(WARN_CHANNEL_ID)
        if warn_channel:
            warning_msg = (
                f"__**\n"
                f"`سجل التحذيرات الرسمي`\n\n"
                f"- اسـم الإداري : {interaction.user.mention}\n\n"
                f"- اســم العضو : {member.mention}\n\n"
                f"- نـوع التـحـذيـر : {assigned_warn_name}\n\n"
                f"- الـمـده : {duration_text}\n\n"
                f"- الـسـبـب: {reason}\n\n"
                f"- الـدليـل : {proof}\n"
                f"**__"
            )
            await warn_channel.send(warning_msg)

        await send_unified_log(
            guild, "⚠️ | تحذير إداري صارم", 
            f"**الإداري:** {interaction.user.mention}\n**العضو المخالف:** {member.mention}\n**التصنيف:** {assigned_warn_name}\n**المدة:** {duration_text}\n**السبب:** {reason}", 
            discord.Color.from_rgb(231, 76, 60)
        )

        data = load_data()
        user_id = str(interaction.user.id)
        if user_id not in data or not isinstance(data[user_id], dict):
            data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0}
        data[user_id]["warns"] += 1
        save_data(data, guild)

        await add_points_direct(guild, interaction.user, POINTS_CONFIG["warn"], f"تطبيق {assigned_warn_name}")
        await interaction.response.send_message(f"✅ **يا كفو! تم تطبيق {assigned_warn_name} على {member.mention} ونزلت نقاطك في الرصيد بنجاح!**", ephemeral=True)

        if assigned_warn_role:
            bot.loop.create_task(auto_remove_warn(guild, member.id, assigned_warn_role, duration_sec))

class TimeoutModal(discord.ui.Modal, title="🔇 | لوحة توثيق التايم أوت (الميوت)"):
    user_input = discord.ui.TextInput(label="اسم العضو أو اليوزر نيم في السيرفر", placeholder="اكتب اسم العضو هنا...", required=True)
    minutes_input = discord.ui.TextInput(label="المدة بالدقائق", placeholder="مثال: 60 (يعني ساعة)", required=True)
    reason_input = discord.ui.TextInput(label="سبب الإسكات", style=discord.TextStyle.paragraph, required=True)
    proof_input = discord.ui.TextInput(label="رابط الدليل (اختياري)", placeholder="رابط الدليل...", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        query = self.user_input.value.strip()
        member = await find_member_by_name(guild, query)

        if not member:
            await interaction.response.send_message(f"❌ **ما لقيته:** ما فيه عضو بالسيرفر بهذا الاسم (`{query}`).", ephemeral=True)
            return

        try:
            minutes = int(self.minutes_input.value.strip())
        except:
            await interaction.response.send_message("❌ **خطأ:** تأكد إنك كتبت رقماً صحيحاً للمدة بالدقائق.", ephemeral=True)
            return

        reason = self.reason_input.value.strip()
        proof = self.proof_input.value.strip() if self.proof_input.value else "لا يوجد"
        duration_delta = discord.utils.utcnow() + discord.utils.datetime.timedelta(minutes=minutes)

        try:
            await member.timeout(duration_delta, reason=reason)
            timeout_model_channel = guild.get_channel(TIMEOUT_MODEL_CHANNEL_ID)
            timeout_model_msg = (
                f"**\n"
                f"`سجل التايم أوت الرسمي`\n\n"
                f" اسـم الإداري : {interaction.user.mention}\n\n"
                f" اسـم العضو : {member.mention}\n\n"
                f"الـمـده : {minutes} دقيقة\n\n"
                f"الـسـبـب: {reason}\n\n"
                f"الـدليـل : {proof}\n"
                f"**"
            )
            if timeout_model_channel:
                await timeout_model_channel.send(timeout_model_msg)

            await send_unified_log(
                guild, "🔇 | عقوبة إسكات (تايم أوت)", 
                f"**الإداري:** {interaction.user.mention}\n**العضو:** {member.mention}\n**المدة:** {minutes} دقيقة\n**السبب:** {reason}", 
                discord.Color.from_rgb(230, 126, 34)
            )

            data = load_data()
            user_id = str(interaction.user.id)
            if user_id not in data or not isinstance(data[user_id], dict):
                data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0}
            data[user_id]["timeouts"] += 1
            save_data(data, guild)

            await add_points_direct(guild, interaction.user, POINTS_CONFIG["timeout"], "تطبيق عقوبة تايم")
            await interaction.response.send_message(f"✅ **تم كتم العضو {member.mention} لمدة {minutes} دقيقة بنجاح تام!**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ عذراً، حصل خطأ أثناء التايم أوت: {e}", ephemeral=True)

class BanModal(discord.ui.Modal, title="🚫 | لوحة توثيق حرمان الرول"):
    user_input = discord.ui.TextInput(label="اسم العضو أو اليوزر نيم في السيرفر", placeholder="اكتب اسم العضو هنا...", required=True)
    duration_input = discord.ui.TextInput(label="المدة (مثال: اسبوع / 3 ايام)", required=True)
    reason_input = discord.ui.TextInput(label="سبب الحرمان", style=discord.TextStyle.paragraph, required=True)
    proof_input = discord.ui.TextInput(label="رابط الدليل (اختياري)", placeholder="رابط الدليل...", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        query = self.user_input.value.strip()
        member = await find_member_by_name(guild, query)

        if not member:
            await interaction.response.send_message(f"❌ **ما لقيته:** ما فيه عضو بالسيرفر بهذا الاسم (`{query}`).", ephemeral=True)
            return

        ban_role = guild.get_role(BAN_ROLE_ID)
        if not ban_role:
            await interaction.response.send_message("❌ رتبة الحرمان مش موجودة بالسيرفر يا الحبيب.", ephemeral=True)
            return

        duration = self.duration_input.value.strip()
        reason = self.reason_input.value.strip()
        proof = self.proof_input.value.strip() if self.proof_input.value else "لا يوجد"

        try:
            roles_to_remove = [r for r in member.roles if not r.is_default() and r.id != BAN_ROLE_ID and r < guild.me.top_role]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"عقوبة حرمان بواسطة {interaction.user.name}")
            await member.add_roles(ban_role, reason=f"تطبيق عقوبة الحرمان بواسطة {interaction.user.name}")

            ban_model_channel = guild.get_channel(BAN_MODEL_CHANNEL_ID)
            ban_model_msg = (
                f"__**\n"
                f"`سجل حرمان الرول الرسمي`\n\n"
                f"- اسـم الإداري : {interaction.user.mention}\n\n"
                f"- اسـم العضو : {member.mention}\n\n"
                f"- الـسـبـب : {reason}\n\n"
                f"- الـمـده : {duration}\n\n"
                f"- الـدليـل : {proof}\n"
                f"**__"
            )
            if ban_model_channel:
                await ban_model_channel.send(ban_model_msg)

            await send_unified_log(
                guild, "🚫 | عقوبة حرمان رول قاسية", 
                f"**الإداري:** {interaction.user.mention}\n**العضو:** {member.mention}\n**المدة:** {duration}\n**السبب:** {reason}", 
                discord.Color.from_rgb(142, 68, 173)
            )

            data = load_data()
            user_id = str(interaction.user.id)
            if user_id not in data or not isinstance(data[user_id], dict):
                data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0}
            data[user_id]["bans"] += 1
            save_data(data, guild)

            await add_points_direct(guild, interaction.user, POINTS_CONFIG["ban"], "تطبيق عقوبة حرمان رول")
            await interaction.response.send_message(f"✅ **تم تطبيق الحرمان على {member.mention} وتوثيق السجل بكل فخر!**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ عذراً، صار خطأ بتنفيذ الحرمان: {e}", ephemeral=True)

class PenaltiesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تحذير إداري", style=discord.ButtonStyle.secondary, emoji="⚠️", custom_id="btn_warn_penalties_v1")
    async def btn_warn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WarnModal())

    @discord.ui.button(label="تايم أوت / ميوت", style=discord.ButtonStyle.secondary, emoji="🔇", custom_id="btn_timeout_penalties_v1")
    async def btn_timeout(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TimeoutModal())

    @discord.ui.button(label="حرمان رول", style=discord.ButtonStyle.danger, emoji="🚫", custom_id="btn_ban_penalties_v1")
    async def btn_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BanModal())

# ----------------------------------------------------
# 3. داشبورد الحاكم ريان الحصرية والخاصة 🎛️
# ----------------------------------------------------
class OwnerDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إضافة نقاط", style=discord.ButtonStyle.success, emoji="✨", custom_id="dash_add_pts")
    async def dash_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != BOT_OWNER_ID:
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للحاكم ريان فقط!", ephemeral=True)
            return
        await interaction.response.send_modal(AddPointsModal())

    @discord.ui.button(label="خصم نقاط", style=discord.ButtonStyle.danger, emoji="📉", custom_id="dash_remove_pts")
    async def dash_rem(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != BOT_OWNER_ID:
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للحاكم ريان فقط!", ephemeral=True)
            return
        await interaction.response.send_modal(RemovePointsModal())

    @discord.ui.button(label="تصفير نقاط", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="dash_reset_pts")
    async def dash_res(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != BOT_OWNER_ID:
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للحاكم ريان فقط!", ephemeral=True)
            return
        await interaction.response.send_modal(ResetPointsModal())

    @discord.ui.button(label="تفعيل دبل النقاط (x2)", style=discord.ButtonStyle.success, emoji="🔥", custom_id="dash_double_pts")
    async def dash_double(self, interaction: discord.Interaction, button: discord.ui.Button):
        global double_points_end_time
        if interaction.user.id != BOT_OWNER_ID:
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للحاكم ريان فقط!", ephemeral=True)
            return
        double_points_end_time = time.time() + 3600
        await interaction.response.send_message("🔥 **تم تفعيل مضاعفة النقاط (x2) لكافة الإداريين لمدة ساعة كاملة عبر الداشبورد!**", ephemeral=True)
        await send_unified_log(interaction.guild, "🔥 | تفعيل دبل النقاط", f"قام الحاكم ريان بتفعيل دبل النقاط لمدة ساعة عبر لوحة التحكم.", discord.Color.from_rgb(241, 196, 15))

    @discord.ui.button(label="نشر بانل التقديم", style=discord.ButtonStyle.primary, emoji="📋", custom_id="dash_panel_apply")
    async def dash_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != BOT_OWNER_ID:
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للحاكم ريان فقط!", ephemeral=True)
            return
        embed = discord.Embed(
            title="📋 | نظام تقديم الهوية الرسمي",
            description="تبي تطلع الهوية وتفعل حسابك بالسيرفر؟ اضغط على الزر تحت وبيجيك البوت في الخاص مباشرة يدردش معك ويأخذ بياناتك بكل سهولة.",
            color=discord.Color.from_rgb(52, 152, 219)
        )
        embed.set_footer(text="منتدى النظيم | قيادة السيرفر العليا")
        view = ApplyButtonView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ **تم إرسال بانل التقديم في هذا الروم بنجاح!**", ephemeral=True)

    @discord.ui.button(label="لوحة الشرف (التوب)", style=discord.ButtonStyle.secondary, emoji="🏆", custom_id="dash_top")
    async def dash_top(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != BOT_OWNER_ID:
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للحاكم ريان فقط!", ephemeral=True)
            return
        data = load_data()
        if not data:
            await interaction.response.send_message("📊 لا توجد بيانات كافية حتى الآن.", ephemeral=True)
            return
        sorted_users = []
        for user_id, info in data.items():
            pts = info["points"] if isinstance(info, dict) else info
            sorted_users.append((int(user_id), pts))
        sorted_users.sort(key=lambda x: x[1], reverse=True)

        embed = discord.Embed(title="🏆 | لوحة الشرف وصدارة المطانيخ", color=discord.Color.from_rgb(241, 196, 15))
        description = ""
        for index, (uid, pts) in enumerate(sorted_users[:10], start=1):
            medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"`#{index}`"
            description += f"{medal} <@{uid}> — **{pts}** نقطة\n"
        embed.description = description
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="لوحة", aliases=["dashboard", "owner_panel"])
async def owner_dashboard(ctx):
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("❌ عذراً يا الحبيب، هذا الأمر مخصص للحاكم ريان فقط!", delete_after=5)
        return
    
    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="🎛️ | لوحة تحكم الحاكم ريان الخاصة (Dashboard)",
        description="أهلاً بك يا الحاكم ريان في لوحتك الخاصة المخصصة لإدارة العمليات والأنظمة والنقاط بضغطة زر وبدون تعقيد:\n\n"
                    "✨ **إضافة نقاط:** لإيداع نقاط في رصيد أي إداري فوراً.\n"
                    "📉 **خصم نقاط:** لخصم النقاط عند المخالفة.\n"
                    "🔄 **تصفير نقاط:** لتصفير السجل وإرجاعه صفر.\n"
                    "🔥 **تفعيل الدبل:** تفعيل مضاعفة نقاط الإداريين لمدة ساعة.\n"
                    "📋 **نشر البانل:** إرسال بانل تقديم الهويات في الروم.\n"
                    "🏆 **لوحة الشرف:** عرض قائمة المتصدرين بشكل فوري.",
        color=discord.Color.from_rgb(155, 89, 182)
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text="منتدى النظيم | لوحة التحكم السيادية للحاكم ريان")
    
    view = OwnerDashboardView()
    await ctx.send(embed=embed, view=view)

# ----------------------------------------------------
# 4. نظام قراءة لوق التكتات وإضافة النقاط تلقائياً للمستلم 🎟️ (محدث حسب شكل الرسالة الجديد)
# ----------------------------------------------------
@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.channel.id == NICKNAME_CHANNEL_ID and not message.author.bot:
        try:
            await message.delete()
        except Exception:
            pass

        guild = message.guild
        member = message.author
        raw_name = message.content.strip()

        if raw_name:
            new_nickname = f"NZM | {raw_name}"
            if len(new_nickname) > 32:
                new_nickname = new_nickname[:32]

            try:
                await member.edit(nick=new_nickname, reason="تغيير الاسم تلقائياً")
                role_to_add = guild.get_role(NICKNAME_ROLE_ID)
                if role_to_add and role_to_add not in member.roles:
                    await member.add_roles(role_to_add, reason="منح رتبة اسم الحساب تلقائياً")
                try:
                    await member.send(f"✅ **يا هلا يا الذيب! تم تعديل اسمك بالسيرفر إلى:** `{new_nickname}` ونزلت رتبتك بنجاح.")
                except Exception:
                    pass
            except Exception as e:
                print(f"خطأ في تعديل الاسم: {e}")

    # قراءة لوق التكتات بناءً على الشكل الجديد (النص أو الإيمبد)
    if message.channel.id == TICKET_LOG_CHANNEL_ID and message.author.bot:
        staff_member = None
        full_text = message.content or ""
        
        for embed in message.embeds:
            if embed.description:
                full_text += "\n" + embed.description
            if embed.title:
                full_text += "\n" + embed.title

        # استخراج الأيدي من المينشن (مثال: <@123456789>)
        user_ids = re.findall(r'<@!?(\d+)>', full_text)
        if user_ids:
            staff_member = message.guild.get_member(int(user_ids[0]))

        # إذا ما حصل المينشن، نبحث عن أي أيدي إداري بارز في النص
        if not staff_member:
            all_numbers = re.findall(r'(\d{17,19})', full_text)
            for num in all_numbers:
                possible_member = message.guild.get_member(int(num))
                if possible_member and not possible_member.bot:
                    staff_member = possible_member
                    break

        if staff_member:
            await add_points_direct(
                message.guild, 
                staff_member, 
                POINTS_CONFIG["ticket"], 
                "استلام تذكرة (عبر لوق التكتات)", 
                target_type="ticket"
            )

# ----------------------------------------------------
# 5. نظام التقديم الخارق بالزر
# ----------------------------------------------------
class ApplyReviewView(discord.ui.View):
    def __init__(self, applicant: discord.Member, guild: discord.Guild):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.guild = guild
        self.is_completed = False
        
        for child in self.children:
            child.disabled = True

    @discord.ui.button(label="قبول التقديم", style=discord.ButtonStyle.green, custom_id="accept_apply_persistent_v12")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin_or_owner(interaction) and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ ما عندك صلاحية تقبل التقديمات يا الغالي.", ephemeral=True)
            return

        if self.is_completed:
            await interaction.response.send_message("⚠️ سبق أحد الإداريين وحسم الطلب خلاص!", ephemeral=True)
            return

        self.is_completed = True
        staff = interaction.user

        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        unverified_role = self.guild.get_role(UNVERIFIED_ROLE_ID)
        verified_role = self.guild.get_role(VERIFIED_ROLE_ID)

        try:
            if unverified_role and unverified_role in self.applicant.roles:
                await self.applicant.remove_roles(unverified_role, reason="قبول تقديم الهوية")
            if verified_role and verified_role not in self.applicant.roles:
                await self.applicant.add_roles(verified_role, reason="قبول تقديم الهوية")
        except Exception as e:
            print(f"خطأ في تعديل رتب التقديم: {e}")

        try:
            await self.applicant.send(f"🎉 **يا كفو ويا هلا بك!** تم قبول تقديمك في سيرفر **{self.guild.name}** ونزلت رتبة الهوية.")
        except:
            pass

        await add_points_direct(self.guild, staff, POINTS_CONFIG["apply_accept"], f"قبول تقديم هوية العضو ({self.applicant.name})", target_type="identity")
        await interaction.response.send_message(f"✅ **كفو والله! تم قبول التقديم بواسطة المطنوخ {staff.mention} ونزلت النقاط برصيده!**")

        try:
            embed = interaction.message.embeds[0]
            embed.set_field_at(0, name="👤 المتقدم", value=f"{self.applicant.mention}\n✅ **تم القبول بواسطة:** {staff.mention}", inline=False)
            await interaction.message.edit(embed=embed, view=self)
        except Exception:
            pass

    @discord.ui.button(label="رفض التقديم", style=discord.ButtonStyle.red, custom_id="reject_apply_persistent_v12")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin_or_owner(interaction) and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ ما عندك صلاحية ترفض التقديمات.", ephemeral=True)
            return

        if self.is_completed:
            await interaction.response.send_message("⚠️ سبق أحد الإداريين وحسم الطلب خلاص!", ephemeral=True)
            return

        self.is_completed = True
        staff = interaction.user

        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        cooldowns = load_cooldowns()
        cooldowns[str(self.applicant.id)] = time.time()
        save_cooldowns(cooldowns)
        
        embed = discord.Embed(
            title="❌ | رفض تقديم",
            description=f"للأسف تم رفض تقديم العضو {self.applicant.mention} بواسطة المطنوخ {staff.mention}.\n⏳ **طبقنا عليه فترة انتظار 10 دقائق قبل يقدر يرجع يقدم مرة ثانية.**",
            color=discord.Color.from_rgb(231, 76, 60)
        )
        await interaction.channel.send(embed=embed)
        try:
            await self.applicant.send(f"❌ نعتذر منك، تم رفض تقديمك في **{self.guild.name}**. تقدر ترجع تقدم بعد 10 دقائق.")
        except:
            pass

class ApplyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تقديم الهوية", style=discord.ButtonStyle.blurple, emoji="📝", custom_id="start_apply_persistent_view_v12")
    async def start_apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        cooldowns = load_cooldowns()
        
        if user_id in cooldowns:
            elapsed = time.time() - cooldowns[user_id]
            if elapsed < 600:
                remaining = int(600 - elapsed)
                mins = remaining // 60
                secs = remaining % 60
                await interaction.response.send_message(f"⏳ **يا الحبيب اركد شوي!** باقي معك `{mins} دقيقة و {secs} ثانية` عشان تقدر تقدم ثانية.", ephemeral=True)
                return

        cooldowns[user_id] = time.time()
        save_cooldowns(cooldowns)

        await interaction.response.defer(ephemeral=True)
        
        try:
            await interaction.user.send("✨ **يا هلا بك في نظام التقديم الرسمي!** رد على الأسئلة بالترتيب وناخذك خطوة بخطوة يا الذيب.")
        except discord.Forbidden:
            await interaction.followup.send("❌ **افتح الخاص حقك أول (DM)** عشان أقدر أرسل لك أسئلة التقديم يا الغالي!", ephemeral=True)
            return

        questions = [
            "**1. اسمك الكريم ؟**",
            "**2. كم عمرك ؟**",
            "**3. وش اسم حسابك المستعار في روبلوكس ؟**",
            "**4. وش اسم حسابك الأساسي في روبلوكس ؟**",
            "**5. الحلف - أقسم بالله العظيم أنا فلان الفلان لا أخرب رولات منتدى النظيم ولا أضرهم بأي شكل من الأشكال ولا أدمر سمعته (اكتب: أقسم بالله)**"
        ]

        answers = []
        def check(m):
            return m.author.id == interaction.user.id and isinstance(m.channel, discord.DMChannel)

        for q in questions:
            await interaction.user.send(q)
            try:
                msg = await bot.wait_for('message', timeout=120.0, check=check)
                answers.append(msg.content)
            except Exception:
                await interaction.user.send("⌛ تأخرت بالرد والوقت خلص. اضغط زر التقديم بالسيرفر وارجع حاول من جديد.")
                return

        review_channel = interaction.guild.get_channel(APPLY_REVIEW_CHANNEL_ID)
        if review_channel:
            embed = discord.Embed(
                title="📥 | تقديم هوية جديد بالخاص",
                description="⏳ **اقرأ إجابات المتقدم كويس... (الأزرار بتفتح تلقائياً بعد 5 ثوانٍ)**",
                color=discord.Color.from_rgb(241, 196, 15),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="👤 المتقدم", value=interaction.user.mention, inline=False)
            embed.add_field(name="1. الاسم", value=answers[0], inline=False)
            embed.add_field(name="2. العمر", value=answers[1], inline=False)
            embed.add_field(name="3. الحساب المستعار (روبلوكس)", value=answers[2], inline=False)
            embed.add_field(name="4. الحساب الأساسي (روبلوكس)", value=answers[3], inline=False)
            embed.add_field(name="5. حلف اليمين", value=answers[4], inline=False)
            embed.set_footer(text=f"معرف العضو: {interaction.user.id}")

            admin_role_mention = f"<@&{ADMIN_ROLE_PENG_ID}>"
            view = ApplyReviewView(applicant=interaction.user, guild=interaction.guild)
            
            sent_message = await review_channel.send(content=f"🔔 {admin_role_mention} فيه تقديم هوية جديد جاهز للمراجعة!", embed=embed, view=view)
            
            async def enable_buttons_after_delay(msg, v):
                await asyncio.sleep(5)
                if not v.is_completed:
                    for child in v.children:
                        child.disabled = False
                    try:
                        emb = msg.embeds[0]
                        emb.description = "✅ **اتفتحت الأزرار! راجع وقرر (أول إداري يتصرف بياخذ النقاط ويحسم الطلب).**"
                        await msg.edit(embed=emb, view=v)
                    except Exception:
                        pass

            bot.loop.create_task(enable_buttons_after_delay(sent_message, view))
        
        await interaction.user.send("✅ **وصلت إجاباتك للإدارة بنجاح!** أول ما يراجعونها بيجيك العلم.")

@bot.command(name="بانل_تقديم", aliases=["panel_apply"])
async def panel_apply(ctx):
    if not is_admin_or_owner(ctx):
        await ctx.send("❌ هذا الأمر مخصص للأدمنستريتر فقط!")
        return

    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        title="📋 | نظام تقديم الهوية الرسمي",
        description="تبي تطلع الهوية وتفعل حسابك بالسيرفر؟ اضغط على الزر تحت وبيجيك البوت في الخاص مباشرة يدردش معك ويأخذ بياناتك بكل سهولة.",
        color=discord.Color.from_rgb(52, 152, 219)
    )
    embed.set_footer(text="منتدى النظيم | قيادة السيرفر العليا")
    
    view = ApplyButtonView()
    await ctx.send(embed=embed, view=view)

# ----------------------------------------------------
# 6. الأوامر الأساسية والأمر الشامل (.عقوبات)
# ----------------------------------------------------

@bot.command(name="عقوبات", aliases=["عقوبة", "penalties"])
async def penalties_cmd(ctx):
    embed = discord.Embed(
        title="⚖️ | لوحة إدارة العقوبات والحزم الإداري",
        description=(
            "يا هلا ومرحبابك يا المطنوخ. اختر نوع العقوبة المطلوبة من الأزرار تحت، وراح يفتح لك نموذج فوري تعبي فيه التفاصيل:\n\n"
            "⚠️ **[ تحذير إداري ]** ↞ يعطي رتب التحذير بالترتيب (أول، ثاني، ثالث) ويزول تلقائياً بعد انتهاء مدته.\n"
            "🔇 **[ تايم أوت / ميوت ]** ↞ يكتم العضو ويوثق نموذج التايم بالروم المخصص.\n"
            "🚫 **[ حرمان رول ]** ↞ يسحب رتب العضو ويعطيه رتبة الحرمان مع حفظ السجل."
        ),
        color=discord.Color.from_rgb(231, 76, 60)
    )
    embed.set_footer(text="منتدى النظيم | النظام الإداري الموحد")
    view = PenaltiesView()
    await ctx.send(embed=embed, view=view)

@bot.command(name="حذف", aliases=["delete", "del"])
async def delete_channel_cmd(ctx):
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("❌ عذراً يا الحبيب، أمر الحذف مخصص للحاكم ريان فقط ولا يحق لأي إداري استخدامه!")
        return

    try:
        await ctx.send("💥 جاري حذف الروم يا طويل العمر...")
        await asyncio.sleep(1)
        await ctx.channel.delete(reason=f"حذف الروم بأمر الحاكم ريان ({ctx.author.name})")
    except Exception as e:
        await ctx.send(f"❌ عذراً، ما قدرت أحذف الروم: {e}")

@bot.event
async def on_ready():
    bot.add_view(ApplyButtonView())
    bot.add_view(PenaltiesView())
    bot.add_view(OwnerDashboardView())
    for guild in bot.guilds:
        await fetch_points_from_discord()
        break
    print(f"🚀 [بوت منتدى النظيم الخارق شغال بنجاح تام] باسم: {bot.user}")

@bot.command(name="help", aliases=["مساعدة", "الأوامر", "اوامر"])
async def help_command(ctx):
    embed = discord.Embed(
        title="⚔️ | لوحة التحكم وأوامر منتدى النظيم الخارقة",
        description="يا هلا ومرحبابك يا ريس! هذي قائمة الأوامر والأنظمة كاملة ومضبوطة بلهجتنا الفخمة:",
        color=discord.Color.from_rgb(241, 196, 15),
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(
        name="📊 ┋ أوامر النقاط والبروفايلات",
        value=(
            "▫️ `.نقاط [@العضو]` ↞ استعلام عن رصيد النقاط.\n"
            "▫️ `.بروفايل [@العضو]` ↞ كشف حساب إداري متكامل (تكتات، هويات، عقوبات).\n"
            "▫️ `.توب` ↞ قائمة صدارة المطانيخ بالإدارة.\n"
            "▫️ `.إضافة_نقاط [@العضو] [العدد]` ↞ إضافة نقاط *(للأدمنستريتر)*.\n"
            "▫️ `.خصم_نقاط [@العضو] [العدد]` ↞ خصم نقاط *(للأدمنستريتر)*.\n"
            "▫️ `.تصفير_نقاط [@العضو]` ↞ تصفير السجل *(للأدمنستريتر)*.\n"
            "▫️ `.دبل_نقاط` ↞ تفعيل دبل النقاط (x2) لمدة ساعة *(للأدمنستريتر)*."
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ ┋ لوحة العقوبات والحزم والداشبورد",
        value=(
            "▫️ `.عقوبات` ↞ فتح لوحة الأزرار والنماذج (تحذير، تايم، حرمان).\n"
            "▫️ `.لوحة` ↞ فتح لوحة تحكم الداشبورد التفاعلية الشاملة *(الحاكم ريان)*.\n"
            "▫️ `.إغلاق` ↞ تنبيه بأن الإغلاق عن طريق زر التكت فقط."
        ),
        inline=False
    )

    embed.add_field(
        name="⚙️ ┋ إدارة الرتب والفعاليات",
        value=(
            "▫️ `.رتبة [@العضو] [الرتبة]` ↞ إعطاء رتبة مع حماية الرتب الأعلى.\n"
            "▫️ `.سحب_رتبة [@العضو] [الرتبة]` ↞ سحب رتبة محددة.\n"
            "▫️ `.بانل_تقديم` ↞ تنزيل بانل التقديم التفاعلي *(للأدمنستريتر)*.\n"
            "▫️ `.حذف` ↞ حذف الروم الحالي *(الحاكم ريان حصرياً)*."
        ),
        inline=False
    )

    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else ctx.author.display_avatar.url)
    embed.set_footer(text=f"طلب بواسطة: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command(name="دبل_نقاط", aliases=["doublepoints", "دبل"])
async def double_points(ctx):
    if not is_admin_or_owner(ctx):
        await ctx.send("❌ هذا الأمر مخصص للأدمنستريتر فقط!")
        return

    global double_points_end_time
    double_points_end_time = time.time() + 3600

    embed = discord.Embed(
        title="🔥 | ولّعت! تم تفعيل دبل النقاط (Double Points)",
        description=f"بواسطة الإداري {ctx.author.mention}\n⏳ **تم تفعيل مضاعفة النقاط (x2) لكافة الإداريين لمدة ساعة كاملة (60 دقيقة)! شدوا حيلكم يا أبطال.**",
        color=discord.Color.from_rgb(241, 196, 15)
    )
    await ctx.send(embed=embed)
    await send_unified_log(ctx.guild, "🔥 | تفعيل دبل النقاط", f"قام الإداري {ctx.author.mention} بتفعيل دبل النقاط لمدة ساعة.", discord.Color.from_rgb(241, 196, 15))

@bot.command(name="رتبة", aliases=["giverole"])
async def give_role(ctx, member: discord.Member, role: discord.Role):
    if not is_admin_or_owner(ctx):
        if ctx.author.top_role <= role:
            await ctx.send("❌ **يا الحبيب:** ما يمديك تعطي رتبة أعلى من رتبتك أو تساويها!", delete_after=6)
            return

    try:
        await member.add_roles(role)
        embed = discord.Embed(title="✅ | تعيين رتبة", description=f"تم إعطاء رتبة {role.mention} للكفو {member.mention} بنجاح.", color=discord.Color.from_rgb(46, 204, 113))
        await ctx.send(embed=embed)
        await send_unified_log(ctx.guild, "🛡️ | تعديل رتبة", f"الإداري {ctx.author.mention} عطى رتبة {role.mention} للعضو {member.mention}")
    except discord.Forbidden:
        await ctx.send("❌ البوت ما عنده صلاحية يعدل رتب هذا الشخص.")

@bot.command(name="سحب_رتبة", aliases=["removerole"])
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    if not is_admin_or_owner(ctx):
        if ctx.author.top_role <= role:
            await ctx.send("❌ **يا الحبيب:** ما يمديك تسحب رتبة أعلى من رتبتك أو تساويها!", delete_after=6)
            return

    try:
        await member.remove_roles(role)
        embed = discord.Embed(title="🔄 | سحب رتبة", description=f"تم سحب رتبة {role.mention} من العضو {member.mention}.", color=discord.Color.from_rgb(230, 126, 34))
        await ctx.send(embed=embed)
        await send_unified_log(ctx.guild, "🛡️ | تعديل رتبة", f"الإداري {ctx.author.mention} سحب رتبة {role.mention} من العضو {member.mention}")
    except discord.Forbidden:
        await ctx.send("❌ البوت ما عنده صلاحية يعدل رتب هذا الشخص.")

@bot.command(name="إغلاق", aliases=["اغلاق", "close"])
async def close(ctx):
    channel_name = ctx.channel.name.lower()
    if not any(k in channel_name for k in ["ticket", "تكت", "الدعم", "support"]):
        await ctx.send("⚠ **تنبيه:** الأمر هذا مخصص لرومات التكت فقط!")
        return

    embed = discord.Embed(
        title="⚠️ | تنبيه إغلاق التكت",
        description="**الإغلاق يكون عن طريق زر التكت فقط يا الذيب!**\n*(ونزلَت نقاطك في وقت استلامك للتذكرة)*",
        color=discord.Color.from_rgb(241, 196, 15)
    )
    await ctx.send(embed=embed)

@bot.command(name="بروفايل", aliases=["profile", "stats"])
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0})
    if isinstance(user_info, int):
        user_info = {"points": user_info, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0}

    pts = user_info.get("points", 0)
    tickets = user_info.get("tickets", 0)
    warns = user_info.get("warns", 0)
    timeouts = user_info.get("timeouts", 0)
    bans = user_info.get("bans", 0)
    identities = user_info.get("identities", 0)

    embed = discord.Embed(title=f"🛡️ | السجل الإداري للمطنوخ: {target.name}", color=discord.Color.from_rgb(52, 152, 219))
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="📊 النقاط الحالية", value=f"`{pts}` نقطة", inline=True)
    embed.add_field(name="🎫 التكتات المنجزة", value=f"`{tickets}` تكت", inline=True)
    embed.add_field(name="🪪 الهويات المقبولة", value=f"`{identities}` هوية", inline=True)
    embed.add_field(name="⚠️ التحذيرات", value=f"`{warns}` تحذير", inline=True)
    embed.add_field(name="🔇 الميوتات (تايم)", value=f"`{timeouts}` مرة", inline=True)
    embed.add_field(name="🔨 الحرمان والباندات", value=f"`{bans}` مرة", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="نقاط", aliases=["points"])
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), 0)
    pts = user_info["points"] if isinstance(user_info, dict) else user_info
    embed = discord.Embed(title="📊 | استعلام النقاط", description=f"رصيد نقاط المطنوخ {target.mention} الحالي هو: **{pts}** نقطة.", color=discord.Color.from_rgb(41, 128, 185))
    embed.set_thumbnail(url=target.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="إضافة_نقاط", aliases=["addpoints"])
async def addpoints(ctx, member: discord.Member, amount: int):
    if not is_admin_or_owner(ctx):
        await ctx.send("❌ هذا الأمر مخصص للأدمنستريتر فقط!")
        return

    data = load_data()
    user_id = str(member.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0}
    data[user_id]["points"] += amount
    save_data(data, ctx.guild)
    await ctx.send(f"✨ تم إضافة `{amount}` نقطة لـ {member.mention} بواسطة {ctx.author.mention}.")
    
    await send_unified_log(
        ctx.guild, "✨ | إضافة نقاط إدارية", 
        f"بواسطة الإداري {ctx.author.mention} تم إضافة `{amount}` نقطة للإداري {member.mention}",
        discord.Color.from_rgb(46, 204, 113)
    )
    
    await check_and_promote(ctx, member, data[user_id]["points"])

@bot.command(name="خصم_نقاط", aliases=["removepoints"])
async def removepoints(ctx, member: discord.Member, amount: int):
    if not is_admin_or_owner(ctx):
        await ctx.send("❌ هذا الأمر مخصص للأدمنستريتر فقط!")
        return

    data = load_data()
    user_id = str(member.id)
    if user_id in data and isinstance(data[user_id], dict):
        data[user_id]["points"] = max(0, data[user_id]["points"] - amount)
        save_data(data, ctx.guild)
        await ctx.send(f"📉 تم خصم `{amount}` نقطة من {member.mention} بواسطة {ctx.author.mention}.")
        
        await send_unified_log(
            ctx.guild, "📉 | خصم نقاط إدارية", 
            f"بواسطة الإداري {ctx.author.mention} تم خصم `{amount}` نقطة من الإداري {member.mention}",
            discord.Color.from_rgb(230, 126, 34)
        )
    else:
        await ctx.send("❌ هذا العضو ليس لديه نقاط مسجلة.")

@bot.command(name="تصفير_نقاط", aliases=["resetpoints"])
async def resetpoints(ctx, member: discord.Member):
    if not is_admin_or_owner(ctx):
        await ctx.send("❌ هذا الأمر مخصص للأدمنستريتر فقط!")
        return

    data = load_data()
    user_id = str(member.id)
    if user_id in data:
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0}
        save_data(data, ctx.guild)
        await ctx.send(f"🔄 تم تصفير نقاط الإداري {member.mention} بنجاح بواسطة {ctx.author.mention}.")
        
        await send_unified_log(
            ctx.guild, "🔄 | تصفير نقاط إداري", 
            f"بواسطة الإداري {ctx.author.mention} تم تصفير نقاط الإداري {member.mention}",
            discord.Color.from_rgb(231, 76, 60)
        )

@bot.command(name="توب", aliases=["leaderboard", "top"])
async def leaderboard(ctx):
    data = load_data()
    if not data:
        await ctx.send("📊 لا توجد بيانات كافية حتى الآن.")
        return

    sorted_users = []
    for user_id, info in data.items():
        pts = info["points"] if isinstance(info, dict) else info
        sorted_users.append((int(user_id), pts))
    sorted_users.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title="🏆 | لوحة الشرف وصدارة المطانيخ", color=discord.Color.from_rgb(241, 196, 15))
    description = ""
    for index, (uid, pts) in enumerate(sorted_users[:10], start=1):
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"`#{index}`"
        description += f"{medal} <@{uid}> — **{pts}** نقطة\n"
    embed.description = description
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ: يرجى وضع متغير DISCORD_TOKEN في إعدادات Railway (Variables).")
