import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import time
import asyncio
import re
from datetime import datetime, timedelta

# ----------------------------------------------------
# 1. إعدادات بوت ديسكورد الأساسية والصلاحيات المطلقة
# ----------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = ("!", ".")

# الأونرات والمسؤولون بصلاحيات كاملة على كل شيء
OWNER_IDS = [
    917414299184533515,  # حسابك الأساسي (الحاكم ريان)
    391638472022163456,  # الأيدي الأول
    1526761757497098335  # الأيدي الثاني
]

POINTS_CONTROL_ROLE_ID = 1545520950064316516

ALLOWED_ROLE_IDS = [
    1545520633939624006,  
    1545520950064316516,  
    1540838084151877714   
]

TEAM_1_ROLE_ID = 1562958541856182312
TEAM_2_ROLE_ID = 1562958139530154034

LOG_CHANNEL_ID = 1553913719128588389
NOTIFICATION_CHANNEL_ID = 1541179719297278072   
TICKET_LOG_CHANNEL_ID = 1559469613509640233  
BAN_MODEL_CHANNEL_ID = 1543648161807999077
TIMEOUT_MODEL_CHANNEL_ID = 1543648006258294784
APPLY_SUBMIT_CHANNEL_ID = 1543072562538618930   
APPLY_REVIEW_CHANNEL_ID = 1543073109496692737   
WARN_CHANNEL_ID = 1543647851953791179           
ADMIN_ROLE_PENG_ID = 1545520633939624006        
EVENT_ANNOUNCE_CHANNEL_ID = 1543082133231243365

UNVERIFIED_ROLE_ID = 1545695261446250516      
VERIFIED_ROLE_ID = 1545516954754875523        
BAN_ROLE_ID = 1543325398761345175             

NICKNAME_CHANNEL_ID = 1552311822747443351
NICKNAME_ROLE_ID = 1543071855920029778

WARN_1_ID = 1543278808583372901
WARN_2_ID = 1543278965857198271
WARN_3_ID = 1543279133164048576

BACKUP_CHANNEL_ID = 1553913719128588389

POINTS_CONFIG = {
    "ticket": 1,
    "warn": 1,
    "timeout": 1,
    "ban": 2,          
    "apply_accept": 1 
}

SPECIAL_PROMOTION_ROLE_ID = 1545520950064316516

JUNIOR_ROLES_LIST = [
    1548407040014155806, # أول رتبة في الإدارة
    1548407479396991047,
    1548407580131336283,
    1548407675048689715,
    1548407794426707978,
    1548407869320466583,
    1557535052580262030,
    1557534028259922010,
    1556660525717397644,
    1548407949356048534
]

MIDDLE_ROLES_LIST = [
    1548408037272715465,
    1548408124531154974,
    1548408197176361191,
    1548408266239910020,
    1548408357457756200,
    1540838584922280016,
    1554920899583549521,
    1555165805317197915,
    1555325627647791215
]

SENIOR_HIGHER_ROLES = [
    {"role_id": 1545521154842828890, "points": 200, "name": "الرتبة الأولى (إدارة عليا)"},
    {"role_id": 1545544984638267452, "points": 300, "name": "الرتبة الثانية (إدارة عليا)"},
    {"role_id": 1545545930885828669, "points": 450, "name": "الرتبة الثالثة (إدارة عليا)"},
    {"role_id": 1561308212832116796, "points": 600, "name": "الرتبة الرابعة (إدارة عليا)"},
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
DATA_FILE = "points.json"
COOLDOWN_FILE = "cooldowns.json"
BANS_FILE = "active_bans.json"
TEAMS_RESET_FILE = "teams_reset.json"
TEAM_BONUS_FILE = "team_bonuses.json"
TEAM_PERSISTENT_FILE = "team_persistent_scores.json"
TEAM_STATS_RESET_FILE = "team_stats_resets.json"

double_points_end_time = 0
processed_tickets = set()

active_event = {
    "running": False,
    "activity_type": "",
    "total_pool_points": 0,
    "description": "",
    "end_time": 0,
    "participants": {}
}

def is_admin_or_owner(ctx_or_interaction):
    author = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
    if author.id in OWNER_IDS:
        return True
    return author.guild_permissions.administrator

def is_bot_owner(ctx_or_interaction):
    author = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
    return author.id in OWNER_IDS

def can_manage_points(ctx_or_interaction):
    author = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
    if author.id in OWNER_IDS or author.guild_permissions.administrator:
        return True
    return any(role.id == POINTS_CONTROL_ROLE_ID for role in getattr(author, 'roles', []))

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

def load_teams_reset():
    return load_json(TEAMS_RESET_FILE)

def save_teams_reset(data):
    save_json(TEAMS_RESET_FILE, data)

def load_team_bonuses():
    return load_json(TEAM_BONUS_FILE)

def save_team_bonuses(data):
    save_json(TEAM_BONUS_FILE, data)

def load_team_persistent():
    return load_json(TEAM_PERSISTENT_FILE)

def save_team_persistent(data):
    save_json(TEAM_PERSISTENT_FILE, data)
    bot.loop.create_task(save_teams_persistent_to_discord())

def load_team_stats_reset():
    return load_json(TEAM_STATS_RESET_FILE)

def save_team_stats_reset(data):
    save_json(TEAM_STATS_RESET_FILE, data)

def load_cooldowns():
    return load_json(COOLDOWN_FILE)

def save_cooldowns(data):
    save_json(COOLDOWN_FILE, data)

def load_bans():
    return load_json(BANS_FILE)

def save_bans(data):
    save_json(BANS_FILE, data)

def parse_duration_to_seconds(duration_str: str) -> int:
    duration_str = duration_str.strip().lower()
    numbers = re.findall(r'\d+', duration_str)
    if not numbers:
        return 86400
    
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
                    elif att.filename == "team_persistent_scores.json":
                        await att.save(TEAM_PERSISTENT_FILE)
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

async def save_teams_persistent_to_discord():
    try:
        for guild in bot.guilds:
            channel = guild.get_channel(BACKUP_CHANNEL_ID)
            if channel and os.path.exists(TEAM_PERSISTENT_FILE):
                async for message in channel.history(limit=15):
                    if message.author == bot.user and message.attachments:
                        for att in message.attachments:
                            if att.filename == "team_persistent_scores.json":
                                try:
                                    await message.delete()
                                except:
                                    pass
                file = discord.File(TEAM_PERSISTENT_FILE, filename="team_persistent_scores.json")
                await channel.send("💾 **[حفظ سحابي فوري] تم تأمين نسخة نقاط التيمات:**", file=file)
                break
    except Exception as e:
        print(f"⚠️ خطأ أثناء رفع نسخة التيمات سحابياً: {e}")

async def send_unified_log(guild, title, description, color=discord.Color.from_rgb(30, 144, 255), fields=None):
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        await log_channel.send(embed=embed)

async def get_promotion_progress(member: discord.Member, current_pts: int):
    is_senior_higher = any(r.id == POINTS_CONTROL_ROLE_ID for r in member.roles)
    
    if is_senior_higher:
        current_senior_idx = -1
        for idx, s_info in enumerate(SENIOR_HIGHER_ROLES):
            if any(r.id == s_info["role_id"] for r in member.roles):
                current_senior_idx = idx
                break
        
        if current_senior_idx < len(SENIOR_HIGHER_ROLES) - 1:
            target_info = SENIOR_HIGHER_ROLES[current_senior_idx + 1]
            required_points = target_info["points"]
        else:
            required_points = SENIOR_HIGHER_ROLES[-1]["points"]
    else:
        is_middle = any(r.id in MIDDLE_ROLES_LIST for r in member.roles)
        required_points = 70 if is_middle else 40
    
    remaining = max(0, required_points - current_pts)
    progress_percent = min(100, int((current_pts / required_points) * 100)) if required_points > 0 else 100
    
    filled_blocks = int(progress_percent / 10)
    empty_blocks = 10 - filled_blocks
    bar = "🟩" * filled_blocks + "⬛" * empty_blocks
    
    return required_points, remaining, progress_percent, bar

async def check_and_promote(ctx_or_guild, member: discord.Member, current_pts: int):
    guild = ctx_or_guild.guild if hasattr(ctx_or_guild, 'guild') else ctx_or_guild
    notif_role = guild.get_role(NOTIFICATION_CHANNEL_ID)
    
    target_role = None
    role_category_name = ""
    required_points = 40

    is_senior_higher = any(r.id == POINTS_CONTROL_ROLE_ID for r in member.roles)

    if is_senior_higher:
        current_senior_idx = -1
        for idx, s_info in enumerate(SENIOR_HIGHER_ROLES):
            if any(r.id == s_info["role_id"] for r in member.roles):
                current_senior_idx = idx
                break
        
        next_idx = current_senior_idx + 1
        if next_idx < len(SENIOR_HIGHER_ROLES):
            target_info = SENIOR_HIGHER_ROLES[next_idx]
            required_points = target_info["points"]
            if current_pts >= required_points:
                target_role = guild.get_role(target_info["role_id"])
                role_category_name = "الإدارة العليا المتقدمة"
    else:
        is_middle = any(r.id in MIDDLE_ROLES_LIST for r in member.roles)
        required_points = 70 if is_middle else 40
        
        if current_pts >= required_points:
            current_idx = -1
            master_list = JUNIOR_ROLES_LIST
            
            for idx, rid in enumerate(JUNIOR_ROLES_LIST):
                if any(r.id == rid for r in member.roles):
                    current_idx = idx
                    master_list = JUNIOR_ROLES_LIST
                    break
            
            if current_idx == -1:
                for idx, rid in enumerate(MIDDLE_ROLES_LIST):
                    if any(r.id == rid for r in member.roles):
                        current_idx = idx
                        master_list = MIDDLE_ROLES_LIST
                        break
            
            if current_idx != -1 and current_idx < len(master_list) - 1:
                next_role_id = master_list[current_idx + 1]
                target_role = guild.get_role(next_role_id)
                role_category_name = "الإدارة الصغرى / الوسطى"
            
            if not target_role and not is_middle and JUNIOR_ROLES_LIST:
                target_role = guild.get_role(JUNIOR_ROLES_LIST[0])
                role_category_name = "الإدارة الصغرى"

    if target_role and target_role not in member.roles:
        try:
            all_managed_ids = JUNIOR_ROLES_LIST + MIDDLE_ROLES_LIST
            roles_to_remove = [
                r for r in member.roles 
                if r.id in all_managed_ids and r.id != target_role.id
            ]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="ترقية ذكية: سحب الرتبة الإدارية القديمة")
            
            await member.add_roles(target_role, reason="ترقية إدارية ذكية جديدة")
            
            data = load_data()
            user_id = str(member.id)
            if user_id in data and isinstance(data[user_id], dict):
                data[user_id]["points"] = 0
                data[user_id]["total_promotions"] = data[user_id].get("total_promotions", 0) + 1
                save_data(data, guild)

            role_ping_str = notif_role.mention if notif_role else ""
            msg = (
                f"{role_ping_str} 👑 **يا فخر الإدارة ويا كفو! ترقية ذكية وتصفير نقاط شخصية:**\n"
                f"ما شاء الله، المطنوخ {member.mention} وصل `{required_points}` نقطة وتمت ترقيته تلقائياً إلى `{target_role.name}` ضمن **{role_category_name}**!\n"
                f"🔄 **ملاحظة:** تم تصفير نقاطك الشخصية فقط لانطلاق تحدٍ جديد، ونقاط فريقك (التيم) محفوظة بالكامل."
            )
            log_channel = guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(msg)
        except Exception as e:
            print(f"خطأ أثناء الترقية: {e}")

async def add_points_direct(guild, staff: discord.Member, base_points: int, action_name: str, target_type: str = None):
    global double_points_end_time, active_event
    
    is_double_active = time.time() < double_points_end_time
    actual_points = (base_points * 2) if is_double_active else base_points
    
    data = load_data()
    user_id = str(staff.id)

    if user_id not in data or not isinstance(data[user_id], dict):
        old_pts = data.get(user_id, 0) if isinstance(data.get(user_id), int) else 0
        data[user_id] = {"points": old_pts, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}

    user_data = data[user_id]
    user_data["points"] = user_data.get("points", 0) + actual_points
    current_pts = user_data["points"]

    if target_type == "ticket":
        user_data["tickets"] = user_data.get("tickets", 0) + 1
    elif target_type == "identity":
        user_data["identities"] = user_data.get("identities", 0) + 1

    save_data(data, guild)

    if active_event["running"]:
        match_type = active_event["activity_type"]
        if match_type == "all" or target_type == match_type:
            active_event["participants"][staff.id] = active_event["participants"].get(staff.id, 0) + 1

    guild_id_str = str(guild.id)
    persistent = load_team_persistent()
    if guild_id_str not in persistent:
        persistent[guild_id_str] = {"t1_total": 0, "t2_total": 0}

    team_1_role = guild.get_role(TEAM_1_ROLE_ID)
    team_2_role = guild.get_role(TEAM_2_ROLE_ID)

    if team_1_role and team_1_role in staff.roles:
        persistent[guild_id_str]["t1_total"] = persistent[guild_id_str].get("t1_total", 0) + actual_points
    elif team_2_role and team_2_role in staff.roles:
        persistent[guild_id_str]["t2_total"] = persistent[guild_id_str].get("t2_total", 0) + actual_points
    save_team_persistent(persistent)
    
    double_text = " 🔥 **(الدبل شغال x2 يا وحش!)**" if is_double_active else ""
    await send_unified_log(
        guild, 
        "📊 | رصد وتوثيق نقاط إدارية", 
        f"تم إيداع `{actual_points}` نقطة في محفظة المطنوخ {staff.mention}{double_text}\n📌 **السبب:** {action_name}\n📈 **رصيده الإجمالي الآن:** `{current_pts}` نقطة",
        discord.Color.from_rgb(46, 204, 113) if not is_double_active else discord.Color.from_rgb(241, 196, 15)
    )
    
    await check_and_promote(guild, staff, current_pts)

async def calculate_teams_performance(guild: discord.Guild):
    reset_data = load_teams_reset()
    bonuses = load_team_bonuses()
    persistent = load_team_persistent()
    stats_resets = load_team_stats_reset()
    
    guild_id_str = str(guild.id)
    team_1_role = guild.get_role(TEAM_1_ROLE_ID)
    team_2_role = guild.get_role(TEAM_2_ROLE_ID)
    
    t1_members = [m for m in guild.members if team_1_role in m.roles] if team_1_role else []
    t2_members = [m for m in guild.members if team_2_role in m.roles] if team_2_role else []

    guild_persistent = persistent.get(guild_id_str, {"t1_total": 0, "t2_total": 0})
    t1_points = guild_persistent.get("t1_total", 0)
    t2_points = guild_persistent.get("t2_total", 0)

    guild_stats_reset = stats_resets.get(guild_id_str, {
        "t1_tickets_base": 0, "t1_identities_base": 0, "t1_promotions_base": 0,
        "t2_tickets_base": 0, "t2_identities_base": 0, "t2_promotions_base": 0
    })

    data = load_data()
    t1_promotions_raw = t1_tickets_raw = t1_identities_raw = 0
    for m in t1_members:
        u_info = data.get(str(m.id), {})
        if isinstance(u_info, dict):
            t1_promotions_raw += u_info.get("total_promotions", 0)
            t1_tickets_raw += u_info.get("tickets", 0)
            t1_identities_raw += u_info.get("identities", 0)

    t2_promotions_raw = t2_tickets_raw = t2_identities_raw = 0
    for m in t2_members:
        u_info = data.get(str(m.id), {})
        if isinstance(u_info, dict):
            t2_promotions_raw += u_info.get("total_promotions", 0)
            t2_tickets_raw += u_info.get("tickets", 0)
            t2_identities_raw += u_info.get("identities", 0)

    t1_tickets = max(0, t1_tickets_raw - guild_stats_reset.get("t1_tickets_base", 0))
    t1_identities = max(0, t1_identities_raw - guild_stats_reset.get("t1_identities_base", 0))
    t1_promotions = max(0, t1_promotions_raw - guild_stats_reset.get("t1_promotions_base", 0))

    t2_tickets = max(0, t2_tickets_raw - guild_stats_reset.get("t2_tickets_base", 0))
    t2_identities = max(0, t2_identities_raw - guild_stats_reset.get("t2_identities_base", 0))
    t2_promotions = max(0, t2_promotions_raw - guild_stats_reset.get("t2_promotions_base", 0))

    guild_bonus = bonuses.get(guild_id_str, {"t1_extra": 0, "t2_extra": 0})
    t1_points += guild_bonus.get("t1_extra", 0)
    t2_points += guild_bonus.get("t2_extra", 0)

    reset_info = reset_data.get(guild_id_str, {"t1_base": 0, "t2_base": 0, "time": 0})
    if isinstance(reset_info, dict):
        t1_competitive = max(0, t1_points - reset_info.get("t1_base", 0))
        t2_competitive = max(0, t2_points - reset_info.get("t2_base", 0))
        last_reset_time = reset_info.get("time", 0)
    else:
        t1_competitive = t1_points
        t2_competitive = t2_points

    if t1_competitive > t2_competitive:
        best_team = f"🏆 التيم الأول ({team_1_role.name if team_1_role else 'فريق 1'}) متصدر المنافسة الأسبوعية!"
    elif t2_competitive > t1_competitive:
        best_team = f"🏆 التيم الثاني ({team_2_role.name if team_2_role else 'فريق 2'}) متصدر المنافسة الأسبوعية!"
    else:
        best_team = "🤝 تعادل تام بين الفريقين في النقاط التنافسية الأسبوعية!"

    reset_date_str = datetime.fromtimestamp(last_reset_time).strftime('%Y-%m-%d %H:%M') if last_reset_time else "من البداية"

    embed = discord.Embed(
        title="⚔️ | تقرير أداء الفرق ومقارنة المنافسة الأسبوعية",
        description=f"إليك تفاصيل أداء ومقارنة الفريقين (منذ تصفير الأسبوع: `{reset_date_str}`):\n\n{best_team}",
        color=discord.Color.from_rgb(241, 196, 15),
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(
        name=f"🛡️ التيم الأول: {team_1_role.name if team_1_role else 'غير موجودة'}",
        value=(
            f"👥 **عدد الأعضاء:** `{len(t1_members)}` عضواً\n"
            f"💳 **المجموع التنافسي الأسبوعي:** `{t1_competitive}` نقطة\n"
            f"👑 **إجمالي الترقيات:** `{t1_promotions}` مرة\n"
            f"🎫 **التكتات المنجزة:** `{t1_tickets}`\n"
            f"🪪 **الهويات المفعلة:** `{t1_identities}`"
        ),
        inline=False
    )
    
    embed.add_field(
        name=f"🛡️ التيم الثاني: {team_2_role.name if team_2_role else 'غير موجودة'}",
        value=(
            f"👥 **عدد الأعضاء:** `{len(t2_members)}` عضواً\n"
            f"💳 **المجموع التنافسي الأسبوعي:** `{t2_competitive}` نقطة\n"
            f"👑 **إجمالي الترقيات:** `{t2_promotions}` مرة\n"
            f"🎫 **التكتات المنجزة:** `{t2_tickets}`\n"
            f"🪪 **الهويات المفعلة:** `{t2_identities}`"
        ),
        inline=False
    )
    
    embed.set_footer(text="منتدى النظيم | نظام تقييم الأداء الموحد")
    return embed

class TeamPointsModal(discord.ui.Modal):
    def __init__(self, team_id: int, action_type: str, team_name: str):
        super().__init__(title=f"إدارة نقاط: {team_name}")
        self.team_id = team_id
        self.action_type = action_type
        self.team_name = team_name

        self.amount_input = discord.ui.TextInput(
            label="عدد النقاط",
            placeholder="اكتب عدد النقاط هنا (مثال: 50)",
            min_length=1,
            max_length=5,
            required=True
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للأونرات فقط!", ephemeral=True)
            return

        try:
            val = int(self.amount_input.value.strip())
        except ValueError:
            await interaction.response.send_message("❌ يرجى إدخال رقم صحيح يا طويل العمر!", ephemeral=True)
            return

        guild = interaction.guild
        guild_id_str = str(guild.id)
        bonuses = load_team_bonuses()
        if guild_id_str not in bonuses:
            bonuses[guild_id_str] = {"t1_extra": 0, "t2_extra": 0}

        key = "t1_extra" if self.team_id == 1 else "t2_extra"

        if self.action_type == "add":
            bonuses[guild_id_str][key] += val
            msg = f"✨ تم إضافة `{val}` نقطة إلى **{self.team_name}** بنجاح!"
        elif self.action_type == "remove":
            bonuses[guild_id_str][key] -= val
            msg = f"📉 تم خصم `{val}` نقطة من **{self.team_name}** بنجاح!"

        save_team_bonuses(bonuses)
        await interaction.response.send_message(msg, ephemeral=True)

class TeamsControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("❌ هذه الأزرار مخصصة للأونرات فقط ولا تتدخل بشي يا الذيب!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="➕ إضافة (تيم 1)", style=discord.ButtonStyle.green, custom_id="t1_add_btn_v21")
    async def t1_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        t1_role = guild.get_role(TEAM_1_ROLE_ID)
        name = t1_role.name if t1_role else "التيم الأول"
        await interaction.response.send_modal(TeamPointsModal(team_id=1, action_type="add", team_name=name))

    @discord.ui.button(label="➖ خصم (تيم 1)", style=discord.ButtonStyle.blurple, custom_id="t1_remove_btn_v21")
    async def t1_remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        t1_role = guild.get_role(TEAM_1_ROLE_ID)
        name = t1_role.name if t1_role else "التيم الأول"
        await interaction.response.send_modal(TeamPointsModal(team_id=1, action_type="remove", team_name=name))

    @discord.ui.button(label="🔄 تصفير (تيم 1)", style=discord.ButtonStyle.danger, custom_id="t1_reset_btn_v21")
    async def t1_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        guild_id_str = str(guild.id)
        bonuses = load_team_bonuses()
        if guild_id_str not in bonuses:
            bonuses[guild_id_str] = {"t1_extra": 0, "t2_extra": 0}
        bonuses[guild_id_str]["t1_extra"] = 0
        save_team_bonuses(bonuses)
        
        t1_role = guild.get_role(TEAM_1_ROLE_ID)
        name = t1_role.name if t1_role else "التيم الأول"
        await interaction.response.send_message(f"🔄 تم تصفير نقاط **{name}** الإضافية بنجاح!", ephemeral=True)

    @discord.ui.button(label="➕ إضافة (تيم 2)", style=discord.ButtonStyle.green, custom_id="t2_add_btn_v21")
    async def t2_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        t2_role = guild.get_role(TEAM_2_ROLE_ID)
        name = t2_role.name if t2_role else "التيم الثاني"
        await interaction.response.send_modal(TeamPointsModal(team_id=2, action_type="add", team_name=name))

    @discord.ui.button(label="➖ خصم (تيم 2)", style=discord.ButtonStyle.blurple, custom_id="t2_remove_btn_v21")
    async def t2_remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        t2_role = guild.get_role(TEAM_2_ROLE_ID)
        name = t2_role.name if t2_role else "التيم الثاني"
        await interaction.response.send_modal(TeamPointsModal(team_id=2, action_type="remove", team_name=name))

    @discord.ui.button(label="🔄 تصفير (تيم 2)", style=discord.ButtonStyle.danger, custom_id="t2_reset_btn_v21")
    async def t2_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        guild_id_str = str(guild.id)
        bonuses = load_team_bonuses()
        if guild_id_str not in bonuses:
            bonuses[guild_id_str] = {"t1_extra": 0, "t2_extra": 0}
        bonuses[guild_id_str]["t2_extra"] = 0
        save_team_bonuses(bonuses)
        
        t2_role = guild.get_role(TEAM_2_ROLE_ID)
        name = t2_role.name if t2_role else "التيم الثاني"
        await interaction.response.send_message(f"🔄 تم تصفير نقاط **{name}** الإضافية بنجاح!", ephemeral=True)

class TeamsResetView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تصفير تنافس الفرق الأسبوعي", style=discord.ButtonStyle.danger, emoji="🔄", custom_id="reset_teams_weekly_virtual_v28")
    async def reset_teams_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin_or_owner(interaction):
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للأدمنستريتر فقط!", ephemeral=True)
            return

        guild = interaction.guild
        guild_id_str = str(guild.id)
        bonuses = load_team_bonuses()
        persistent = load_team_persistent()
        
        guild_persistent = persistent.get(guild_id_str, {"t1_total": 0, "t2_total": 0})
        t1_base = guild_persistent.get("t1_total", 0)
        t2_base = guild_persistent.get("t2_total", 0)

        guild_bonus = bonuses.get(guild_id_str, {"t1_extra": 0, "t2_extra": 0})
        t1_base += guild_bonus.get("t1_extra", 0)
        t2_base += guild_bonus.get("t2_extra", 0)

        reset_data = load_teams_reset()
        reset_data[guild_id_str] = {
            "t1_base": t1_base,
            "t2_base": t2_base,
            "time": time.time()
        }
        save_teams_reset(reset_data)

        team_1_role = guild.get_role(TEAM_1_ROLE_ID)
        team_2_role = guild.get_role(TEAM_2_ROLE_ID)
        t1_members = [m for m in guild.members if team_1_role in m.roles] if team_1_role else []
        t2_members = [m for m in guild.members if team_2_role in m.roles] if team_2_role else []
        data = load_data()

        t1_t_sum = t1_i_sum = t1_p_sum = 0
        for m in t1_members:
            u_info = data.get(str(m.id), {})
            if isinstance(u_info, dict):
                t1_t_sum += u_info.get("tickets", 0)
                t1_i_sum += u_info.get("identities", 0)
                t1_p_sum += u_info.get("total_promotions", 0)

        t2_t_sum = t2_i_sum = t2_p_sum = 0
        for m in t2_members:
            u_info = data.get(str(m.id), {})
            if isinstance(u_info, dict):
                t2_t_sum += u_info.get("tickets", 0)
                t2_i_sum += u_info.get("identities", 0)
                t2_p_sum += u_info.get("total_promotions", 0)

        stats_resets = load_team_stats_reset()
        stats_resets[guild_id_str] = {
            "t1_tickets_base": t1_t_sum, "t1_identities_base": t1_i_sum, "t1_promotions_base": t1_p_sum,
            "t2_tickets_base": t2_t_sum, "t2_identities_base": t2_i_sum, "t2_promotions_base": t2_p_sum
        }
        save_team_stats_reset(stats_resets)

        await interaction.response.send_message("🔄 **تم تصفير المجموع التنافسي وإحصائيات التكتات والترقيات الأسبوعية للفرق بالكامل!** 🎉", ephemeral=True)
        await send_unified_log(guild, "🔄 | تصفير تنافس وإحصائيات الفرق", f"قام الأدمن {interaction.user.mention} بتصفير التنافس وإحصائيات التكتات والترقيات للفرق أسبوعياً.", discord.Color.from_rgb(231, 76, 60))

# ----------------------------------------------------
# 🏅 مودال إعدادات الفعالية الجديدة
# ----------------------------------------------------
class EventSetupModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="إنشاء وإطلاق فعالية إدارية جديدة")

        self.activity_input = discord.ui.TextInput(
            label="نوع النشاط (تكتات / هويات / تحذيرات / الكل)",
            placeholder="اكتب: تكتات، هويات، أو الكل",
            required=True,
            max_length=20
        )
        self.total_pool_input = discord.ui.TextInput(
            label="إجمالي النقاط الكاملة للفعالية",
            placeholder="مثال: 30",
            required=True,
            max_length=5
        )
        self.duration_input = discord.ui.TextInput(
            label="المدة بالدقائق",
            placeholder="مثال: 30",
            required=True,
            max_length=5
        )
        self.title_input = discord.ui.TextInput(
            label="عنوان أو وصف الفعالية",
            placeholder="مثال: فعالية إغلاق التكتات الكبرى",
            required=True,
            max_length=100
        )

        self.add_item(self.activity_input)
        self.add_item(self.total_pool_input)
        self.add_item(self.duration_input)
        self.add_item(self.title_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للأونرات فقط!", ephemeral=True)
            return

        valid_types = {
            "تكتات": "ticket", "ticket": "ticket",
            "هويات": "identity", "identity": "identity",
            "تحذيرات": "warn", "warn": "warn",
            "تايم": "timeout", "timeout": "timeout",
            "حرمان": "ban", "ban": "ban",
            "الكل": "all", "all": "all"
        }

        act_raw = self.activity_input.value.strip().lower()
        if act_raw not in valid_types:
            await interaction.response.send_message("❌ نوع النشاط غير صحيح! اكتب (تكتات، هويات، تحذيرات، تايم، حرمان، أو الكل).", ephemeral=True)
            return

        try:
            pool_pts = int(self.total_pool_input.value.strip())
            duration_mins = int(self.duration_input.value.strip())
        except ValueError:
            await interaction.response.send_message("❌ يرجى إدخال أرقام صحيحة في خانة النقاط والمدة!", ephemeral=True)
            return

        mapped_type = valid_types[act_raw]
        title_text = self.title_input.value.strip()

        global active_event
        if active_event["running"]:
            await interaction.response.send_message("⚠️ فيه فعالية شغال حالياً! انتظر لين تنتهي.", ephemeral=True)
            return

        guild = interaction.guild
        announce_channel = guild.get_channel(EVENT_ANNOUNCE_CHANNEL_ID)
        staff_ping_role = guild.get_role(1545520633939624006)
        ping_str = staff_ping_role.mention if staff_ping_role else "<@&1545520633939624006>"

        active_event = {
            "running": True,
            "activity_type": mapped_type,
            "total_pool_points": pool_pts,
            "description": title_text,
            "end_time": time.time() + (duration_mins * 60),
            "participants": {}
        }

        embed = discord.Embed(
            title="🎉 | إطلاق فعالية إدارية كبرى جديدة!",
            description=(
                f"يا طاقم الإدارة ويا أبطال منتدى النظيم!\n\n"
                f"🏆 **اسم الفعالية / المطلوب:**\n`{title_text}`\n\n"
                f"📌 **نوع النشاط المستهدف:** `{mapped_type}`\n"
                f"💎 **إجمالي نقاط الفعالية الكلية:** `{pool_pts} نقطة`\n"
                f"⏱️ **الوقت المحدد:** `{duration_mins} دقيقة`\n"
                f"🎁 **طريقة التتويج:** عند انتهاء الوقت، سيظهر ترتيب التوب تلقائياً في روم الإعلانات لتوزيع النقاط بالطريقة اللي تناسبك!\n\n"
                f"👇 **شدوا حيلكم، البوت يتابع أداء الجميع طوال فترة الفعالية!**"
            ),
            color=discord.Color.from_rgb(241, 196, 15),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="منتدى النظيم | فعاليات الإدارة الكبرى")

        if announce_channel:
            await announce_channel.send(content=f"🔔 {ping_str} **تنبيه ببدء الفعالية الرسمية!**", embed=embed)
        
        await interaction.response.send_message(f"✅ **تم إطلاق الفعالية بنجاح تام وإرسال الإعلان في روم الإعلانات!**", ephemeral=True)

        async def finish_event_after_delay():
            global active_event
            await asyncio.sleep(duration_mins * 60)
            
            if not active_event["running"]:
                return

            active_event["running"] = False
            participants = active_event["participants"]

            if participants:
                sorted_participants = sorted(participants.items(), key=lambda x: x[1], reverse=True)
                
                result_desc = "🏁 **انتهت الفعالية الإدارية! إليكم ترتيب التوب التلقائي حسب الأداء:**\n\n"
                for idx, (uid, count) in enumerate(sorted_participants, 1):
                    member = guild.get_member(uid)
                    member_str = member.mention if member else f"<@{uid}>"
                    result_desc += f"`#{idx}` {member_str} — العمليات المنجزة: `{count}`\n"
                
                result_desc += f"\n👇 **يا الأونر، اضغط على الزر أدناه لتوزيع نقاط الفعالية ({pool_pts} نقطة إجمالية) على المراكز حسب احتياجك!**"

                control_embed = discord.Embed(
                    title="📊 | تقرير نتائج الفعالية وجهوزية التوزيع",
                    description=result_desc,
                    color=discord.Color.from_rgb(52, 152, 219),
                    timestamp=discord.utils.utcnow()
                )
                control_embed.set_footer(text="منتدى النظيم | لوحة تحكم الفعاليات")

                view = EventDistributeView(sorted_participants, guild, ping_str, announce_channel)
                
                if announce_channel:
                    await announce_channel.send(content=f"📢 {ping_str} **انتهت الفعالية! بانتظار توزيع الجوائز:**", embed=control_embed, view=view)
            else:
                if announce_channel:
                    await announce_channel.send(content=f"📢 {ping_str} **انتهت الفعالية:** للأسف لم يشارك أحد أو يسجل أي إنجاز خلال هذه الفترة.")

            active_event["participants"] = {}

        bot.loop.create_task(finish_event_after_delay())

# ----------------------------------------------------
# 🏅 مودال توزيع النقاط المخصص لكل مركز (توب الفعالية)
# ----------------------------------------------------
class EventRewardModal(discord.ui.Modal):
    def __init__(self, sorted_participants, guild, ping_str, announce_channel):
        super().__init__(title="توزيع جوائز ونقاط الفعالية")
        self.sorted_participants = sorted_participants
        self.guild = guild
        self.ping_str = ping_str
        self.announce_channel = announce_channel

        self.rank1_input = discord.ui.TextInput(
            label="المركز الأول (نقاط)",
            placeholder="مثال: 15",
            required=True,
            max_length=4
        )
        self.rank2_input = discord.ui.TextInput(
            label="المركز الثاني (نقاط)",
            placeholder="مثال: 10",
            required=False,
            max_length=4
        )
        self.rank3_input = discord.ui.TextInput(
            label="المركز الثالث (نقاط)",
            placeholder="مثال: 5",
            required=False,
            max_length=4
        )
        self.rest_input = discord.ui.TextInput(
            label="باقي المشاركين (نقاط لكل شخص)",
            placeholder="مثال: 1",
            required=False,
            max_length=4
        )

        self.add_item(self.rank1_input)
        self.add_item(self.rank2_input)
        self.add_item(self.rank3_input)
        self.add_item(self.rest_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("❌ مخصص للأونرات فقط!", ephemeral=True)
            return

        try:
            r1_pts = int(self.rank1_input.value.strip()) if self.rank1_input.value else 0
            r2_pts = int(self.rank2_input.value.strip()) if self.rank2_input.value else 0
            r3_pts = int(self.rank3_input.value.strip()) if self.rank3_input.value else 0
            rest_pts = int(self.rest_input.value.strip()) if self.rest_input.value else 0
        except ValueError:
            await interaction.response.send_message("❌ يرجى إدخال أرقام صحيحة في خانات النقاط!", ephemeral=True)
            return

        data = load_data()
        guild_id_str = str(self.guild.id)
        persistent = load_team_persistent()
        if guild_id_str not in persistent:
            persistent[guild_id_str] = {"t1_total": 0, "t2_total": 0}

        team_1_role = self.guild.get_role(TEAM_1_ROLE_ID)
        team_2_role = self.guild.get_role(TEAM_2_ROLE_ID)

        result_desc = "🏁 **تم إعلان نتائج الفعالية وتوزيع النقاط على المراكز حسب اختيار الأونر:**\n\n"

        for idx, (uid, count) in enumerate(self.sorted_participants):
            member = self.guild.get_member(uid)
            member_str = member.mention if member else f"<@{uid}>"

            if idx == 0:
                awarded = r1_pts
                medal = "🥇 المركز الأول"
            elif idx == 1:
                awarded = r2_pts
                medal = "🥈 المركز الثاني"
            elif idx == 2:
                awarded = r3_pts
                medal = "🥉 المركز الثالث"
            else:
                awarded = rest_pts
                medal = f"🏅 المركز #{idx+1}"

            result_desc += f"{medal} — {member_str} (العمليات المنجزة: `{count}`) ➔ **+{awarded} نقطة**\n"

            if awarded > 0:
                uid_str = str(uid)
                if uid_str not in data or not isinstance(data[uid_str], dict):
                    data[uid_str] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}
                
                data[uid_str]["points"] += awarded

                if member:
                    if team_1_role and team_1_role in member.roles:
                        persistent[guild_id_str]["t1_total"] = persistent[guild_id_str].get("t1_total", 0) + awarded
                    elif team_2_role and team_2_role in member.roles:
                        persistent[guild_id_str]["t2_total"] = persistent[guild_id_str].get("t2_total", 0) + awarded
                
                save_data(data, self.guild)

        save_team_persistent(persistent)

        result_embed = discord.Embed(
            title="🏆 | نتائج الفعالية وتتويج الأبطال",
            description=result_desc,
            color=discord.Color.from_rgb(241, 196, 15),
            timestamp=discord.utils.utcnow()
        )
        result_embed.set_footer(text="منتدى النظيم | لوحة الفعاليات الكبرى")

        if self.announce_channel:
            await self.announce_channel.send(content=f"📢 {self.ping_str} **إعلان نتائج وتتويج الفعالية:**", embed=result_embed)
        
        await interaction.response.send_message("✅ **تم توزيع النقاط على المشاركين وإضافتها لمحفظتهم وتيماتهم بنجاح تام!**", ephemeral=True)

class EventDistributeView(discord.ui.View):
    def __init__(self, sorted_participants, guild, ping_str, announce_channel):
        super().__init__(timeout=None)
        self.sorted_participants = sorted_participants
        self.guild = guild
        self.ping_str = ping_str
        self.announce_channel = announce_channel

    @discord.ui.button(label="🎁 توزيع النقاط والجوائز حسب المراكز (توب)", style=discord.ButtonStyle.green, custom_id="distribute_event_rewards_btn_v10")
    async def distribute_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("❌ هذا الزر مخصص للأونرات فقط!", ephemeral=True)
            return

        await interaction.response.send_modal(EventRewardModal(self.sorted_participants, self.guild, self.ping_str, self.announce_channel))

# ----------------------------------------------------
# 🔘 لوحة وزر بدء الفعالية (.فعاليات)
# ----------------------------------------------------
class StartEventPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 بدء فعالية جديدة", style=discord.ButtonStyle.green, custom_id="open_event_setup_modal_btn_v6")
    async def open_modal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in OWNER_IDS:
            await interaction.response.send_message("❌ هذا الزر مخصص للأونرات فقط!", ephemeral=True)
            return
        await interaction.response.send_modal(EventSetupModal())

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

    if message.channel.id == TICKET_LOG_CHANNEL_ID:
        if message.id in processed_tickets:
            return

        staff_member = None
        full_text = ""

        for embed in message.embeds:
            title_text = embed.title or ""
            desc_text = embed.description or ""
            full_text += f"\n{title_text}\n{desc_text}"
            
            for field in embed.fields:
                field_name = field.name or ""
                field_val = field.value or ""
                full_text += f"\n{field_name}: {field_val}"

                if "المستلم" in field_name:
                    user_ids = re.findall(r'(\d{17,19})', field_val)
                    if user_ids:
                        possible_staff = message.guild.get_member(int(user_ids[0]))
                        if possible_staff and not possible_staff.bot:
                            staff_member = possible_staff

        if not staff_member and "المستلم" in full_text:
            parts = full_text.split("المستلم")
            if len(parts) > 1:
                target_section = parts[1][:150]
                user_ids = re.findall(r'(\d{17,19})', target_section)
                if user_ids:
                    possible_staff = message.guild.get_member(int(user_ids[0]))
                    if possible_staff and not possible_staff.bot:
                        staff_member = possible_staff

        if staff_member:
            processed_tickets.add(message.id)
            if len(processed_tickets) > 1000:
                processed_tickets.pop()

            await add_points_direct(
                message.guild, 
                staff_member, 
                1, 
                "إغلاق تذكرة (تسجيل نقاط المستلم)", 
                target_type="ticket"
            )

class ApplyReviewView(discord.ui.View):
    def __init__(self, applicant: discord.Member, guild: discord.Guild):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.guild = guild
        self.is_completed = False
        
        for child in self.children:
            child.disabled = True

    @discord.ui.button(label="قبول التقديم", style=discord.ButtonStyle.green, custom_id="accept_apply_persistent_v21")
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

        await add_points_direct(self.guild, staff, 1, f"قبول تقديم هوية العضو ({self.applicant.name})", target_type="identity")
        await interaction.response.send_message(f"✅ **كفو والله! تم قبول التقديم بواسطة المطنوخ {staff.mention} ونزلت النقاط برصيده!**")

        try:
            embed = interaction.message.embeds[0]
            embed.set_field_at(0, name="👤 المتقدم", value=f"{self.applicant.mention}\n✅ **تم القبول بواسطة:** {staff.mention}", inline=False)
            await interaction.message.edit(embed=embed, view=self)
        except Exception:
            pass

    @discord.ui.button(label="رفض التقديم", style=discord.ButtonStyle.red, custom_id="reject_apply_persistent_v21")
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

    @discord.ui.button(label="تقديم الهوية", style=discord.ButtonStyle.blurple, emoji="📝", custom_id="start_apply_persistent_view_v21")
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
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(
        title="📋 | نظام تقديم الهوية الرسمي",
        description="تبي تطلع الهوية وتفعل حسابك بالسيرفر؟ اضغط على الزر تحت وبيجيك البوت في الخاص مباشرة يدردش معك ويأخذ بياناتك بكل سهولة.",
        color=discord.Color.from_rgb(52, 152, 219)
    )
    embed.set_footer(text="منتدى النظيم | قيادة السيرفر العليا")
    await ctx.send(embed=embed, view=ApplyButtonView())

# ----------------------------------------------------
# 🔍 أمر فحص الأعضاء وإعطاء رتبة غير الموثق
# ----------------------------------------------------
@bot.command(name="فحص_الرتب", aliases=["فحص", "check_roles"])
async def check_roles_cmd(ctx):
    if ctx.author.id not in OWNER_IDS:
        await ctx.send("❌ عذراً، هذا الأمر مخصص للأونرات فقط!", delete_after=5)
        return

    msg = await ctx.send("🔍 **جاري فحص جميع أعضاء السيرفر وتوزيع الرتب على من ليس لديهم أي رتبة... انتظر شوي!**")
    
    guild = ctx.guild
    target_role = guild.get_role(UNVERIFIED_ROLE_ID)
    
    if not target_role:
        await msg.edit(content="❌ خطأ: الرتبة المستهدفة غير موجودة بالسيرفر!")
        return

    count = 0
    for member in guild.members:
        if member.bot:
            continue
        
        if len(member.roles) <= 1:
            try:
                await member.add_roles(target_role, reason="فحص تلقائي: منح الرتبة للأعضاء الذين بلا رتب")
                count += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"خطأ في إعطاء الرتبة لـ {member.name}: {e}")

    await msg.edit(content=f"✅ **تم الانتهاء من الفحص بنجاح!**\nتم إعطاء رتبة العضو غير الموثق لـ **`{count}`** عضو ممن لم يكونوا يمتلكون أي رتبة.")

# ----------------------------------------------------
# ✨ أمر تفعيل جماعي
# ----------------------------------------------------
@bot.command(name="تفعيل_الكل", aliases=["تفعيل", "verify_all"])
async def verify_all_cmd(ctx):
    if ctx.author.id not in OWNER_IDS:
        await ctx.send("❌ عذراً، هذا الأمر مخصص للأونرات فقط!", delete_after=5)
        return

    msg = await ctx.send("⚡ **جاري منح رتبة التفعيل لكل من يمتلك رتبة الاسم... انتظر لحظات!**")

    guild = ctx.guild
    source_role_id = 1543071855920029778  
    target_role_id = 1545516954754875523  

    source_role = guild.get_role(source_role_id)
    target_role = guild.get_role(target_role_id)

    if not source_role or not target_role:
        await msg.edit(content="❌ خطأ: إحدى الرتبتين غير موجودة بالسيرفر وتأكد من الآديات!")
        return

    count = 0
    for member in guild.members:
        if member.bot:
            continue
        
        if source_role in member.roles and target_role not in member.roles:
            try:
                await member.add_roles(target_role, reason="تفعيل جماعي: منح رتبة التفعيل")
                count += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"خطأ في تفعيل العضو {member.name}: {e}")

    await msg.edit(content=f"✅ **تم إتمام التفعيل الجماعي بنجاح!**\nتم منح رتبة التفعيل لـ **`{count}`** عضو.")

# ----------------------------------------------------
# 👑 أمر توظيف إداري معدل (.توظيف @الشخص الرقم)
# ----------------------------------------------------
@bot.command(name="توظيف", aliases=["hire"])
async def hire_staff_cmd(ctx, member: discord.Member, *, identity_number: str):
    if ctx.author.id not in OWNER_IDS:
        await ctx.send("❌ عذراً، هذا الأمر مخصص للأونرات فقط!", delete_after=5)
        return

    guild = ctx.guild
    staff_role = guild.get_role(ADMIN_ROLE_PENG_ID) # رتبة طاقم الإدارة (1545520633939624006)
    first_junior_role = guild.get_role(JUNIOR_ROLES_LIST[0]) # أول رتبة في الإدارة (1548407040014155806)

    if not staff_role or not first_junior_role:
        await ctx.send("❌ خطأ: إحدى رتب التوظيف الأساسية غير موجودة بالسيرفر!")
        return

    # تنظيف اسم العضو وإزالة NZM | لو كانت موجودة واستبدالها بـ NZ ﹝الرقم﹞
    current_nick = member.display_name
    clean_name = current_nick
    if "NZM |" in clean_name:
        clean_name = clean_name.replace("NZM |", "").strip()
    elif clean_name.startswith("NZM"):
        clean_name = clean_name[3:].strip()

    new_nickname = f"NZ ﹝{identity_number.strip()}﹞ {clean_name}"
    if len(new_nickname) > 32:
        new_nickname = new_nickname[:32]

    try:
        # تعديل الاسم وإعطاء الرتب
        await member.edit(nick=new_nickname, reason=f"توظيف إداري برقم الهوية بواسطة الأونر {ctx.author.name}")

        roles_to_add = []
        if staff_role not in member.roles:
            roles_to_add.append(staff_role)
        if first_junior_role not in member.roles:
            roles_to_add.append(first_junior_role)

        if roles_to_add:
            await member.add_roles(*roles_to_add, reason=f"توظيف إداري بواسطة الأونر {ctx.author.name}")

        await ctx.send(f"🎉 **مبروك للمطنوخ {member.mention}!** تم توظيفه وتعديل اسمه إلى `{new_nickname}` ونزلت رتب الإدارة بنجاح.")

        # إرسال لوق التوظيف
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="💼 | توظيف إداري جديد",
                description=f"**الأونر المسؤول:** {ctx.author.mention}\n**العضو المُوَظَّف:** {member.mention}\n**الاسم الجديد:** `{new_nickname}`\n**الرتب الممنوحة:**\n▫️ {staff_role.mention}\n▫️ {first_junior_role.mention}",
                color=discord.Color.from_rgb(46, 204, 113),
                timestamp=discord.utils.utcnow()
            )
            await log_channel.send(embed=embed)

        try:
            await member.send(f"🎉 **يا هلا يا الذيب!** تم قبولك وتوظيفك في الإدارة بـ **{guild.name}** وتم تعديل اسمك إلى `{new_nickname}` ونزلت رتبك بنجاح.")
        except:
            pass

    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء توظيف العضو: {e}")

@bot.command(name="عقوبات", aliases=["عقوبة", "penalties"])
async def penalties_cmd(ctx):
    embed = discord.Embed(
        title="⚠️ | تنبيه نظام الإدارة وسهولة العقوبات",
        description=(
            "يا هلا ومرحبابك يا المطنوخ.\n\n"
            "جميع أوامر العقوبات صارت مبسطة وسريعة **عبر أوامر السلاش (Slash Commands)** لتكون واضحة وفورية:\n\n"
            "🔹 **1. `/تحذير`** - لتسجيل تحذير رسمي على العضو.\n"
            "🔹 **2. `/تايم_أوت`** - لكتم العضو بالدقائق المحددة.\n"
            "🔹 **3. `/حرمان`** - لحرمان العضو مؤقتاً من رتبه مع حفظها وإرجاعها تلقائياً.\n"
            "🔹 **4. `/اعفاء`** - لرفع الحرمان عن العضو وإرجاع رتبه السابقة فوراً.\n\n"
            "فقط اكتب `/` في الشات واختر الأمر بكل سهولة يا وحش! 🚀"
        ),
        color=discord.Color.from_rgb(241, 196, 15)
    )
    embed.set_footer(text="منتدى النظيم | النظام الإداري الموحد")
    try:
        await ctx.message.delete()
    except:
        pass
    await ctx.send(embed=embed, delete_after=15)

@bot.command(name="حذف", aliases=["delete", "del"])
async def delete_channel_cmd(ctx):
    if ctx.author.id not in OWNER_IDS:
        await ctx.send("❌ عذراً يا الحبيب، أمر الحذف مخصص للأونرات فقط!", delete_after=5)
        return
    try:
        await ctx.send("💥 جاري حذف الروم يا طويل العمر...")
        await asyncio.sleep(1)
        await ctx.channel.delete(reason=f"حذف الروم بأمر الأونر")
    except Exception as e:
        await ctx.send(f"❌ عذراً، ما قدرت أحذف الروم: {e}")

@bot.command(name="اونر", aliases=["owner"])
async def owner_call_cmd(ctx):
    required_staff_role_id = 1545520633939624006
    has_staff_role = any(role.id == required_staff_role_id for role in ctx.author.roles)

    if not has_staff_role and not is_admin_or_owner(ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(f"{ctx.author.mention} ماتقدر تمنشن ياهطف !!!", delete_after=7)
        return

    try:
        await ctx.message.delete()
    except:
        pass

    target_role_id = 1567062184004026488
    role = ctx.guild.get_role(target_role_id)
    role_mention = role.mention if role else f"<@&{target_role_id}>"

    channel_name = ctx.channel.name.lower()
    if "تذكرة" in channel_name or "تكت" in channel_name or "ticket" in channel_name:
        try:
            await ctx.channel.edit(name="مطلوب-اونر", reason=f"طلب أونر بواسطة {ctx.author.name}")
        except Exception as e:
            print(f"خطأ في تغيير اسم الروم: {e}")

        embed = discord.Embed(
            title="🚨 | طلب حضور الأونر",
            description=f"الإداري {ctx.author.mention} يطلب حضور الأونر في التكت!\n📌 **تمت تنميش الرتبة:** {role_mention}",
            color=discord.Color.from_rgb(231, 76, 60),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="منتدى النظيم | نداء الأونرات السريع")
        await ctx.send(content=role_mention, embed=embed)
    else:
        embed = discord.Embed(
            title="⚠️ | تنبيه نداء الأونر",
            description=f"الإداري {ctx.author.mention} قام بنداء الأونرات.\n📌 **الرتبة المستدعية:** {role_mention}\n*(ملاحظة: هذا ليس روم تكت، لذلك لم يتم تغيير اسم الروم).*",
            color=discord.Color.from_rgb(241, 196, 15),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="منتدى النظيم | نداء الأونرات السريع")
        await ctx.send(content=role_mention, embed=embed)

# ----------------------------------------------------
# 🏆 أمر .فعاليات (يعرض الإمبيد وزر بدء الفعالية)
# ----------------------------------------------------
@bot.command(name="فعاليات", aliases=["فعالية"])
async def events_panel_command(ctx):
    if ctx.author.id not in OWNER_IDS:
        await ctx.send("❌ هذا الأمر مخصص للأونرات فقط يا الذيب!", delete_after=5)
        return

    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="🎉 | لوحة إدارة وتحكم الفعاليات الإدارية",
        description=(
            "أهلاً بك يا الحاكم ريان.\n\n"
            "من خلال هذه اللوحة، يمكنك بدء فعالية إدارية جديدة وتحديد (نوع النشاط، إجمالي النقاط، المدة، والعنوان) عبر زر الإعدادات أدناه بكل سهولة وسرعة! 🚀"
        ),
        color=discord.Color.from_rgb(241, 196, 15),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="منتدى النظيم | لوحة الفعاليات المركزية")
    await ctx.send(embed=embed, view=StartEventPanelView())

@tasks.loop(minutes=1)
async def check_expired_bans():
    bans_data = load_bans()
    if not bans_data:
        return
    
    current_time = time.time()
    updated = False
    
    for guild_id_str, members_dict in list(bans_data.items()):
        guild = bot.get_guild(int(guild_id_str))
        if not guild:
            continue
            
        ban_role = guild.get_role(BAN_ROLE_ID)
        for member_id_str, ban_info in list(members_dict.items()):
            if current_time >= ban_info["expires_at"]:
                member = guild.get_member(int(member_id_str))
                if member:
                    try:
                        if ban_role and ban_role in member.roles:
                            await member.remove_roles(ban_role, reason="انتهت مدة الحرمان - إرجاع الرتب")
                        
                        roles_to_restore = []
                        for rid in ban_info["saved_roles"]:
                            r = guild.get_role(rid)
                            if r and r < guild.me.top_role and not r.is_default() and not r.managed:
                                roles_to_restore.append(r)
                                
                        if roles_to_restore:
                            await member.add_roles(*roles_to_restore, reason="انتهاء الحرمان وإرجاع الرتب السابقة تلقائياً")
                            
                        log_ch = guild.get_channel(LOG_CHANNEL_ID)
                        if log_ch:
                            await log_ch.send(embed=discord.Embed(title="♻️ | انتهاء الحرمان وإرجاع الرتب", description=f"العضو {member.mention} انتهت فترة حرمانه وتم استرجاع رتبه السابقة تلقائياً.", color=discord.Color.green()))
                    except Exception as e:
                        print(f"خطأ في إرجاع رتب العضو بعد انتهاء الحرمان: {e}")
                
                del members_dict[member_id_str]
                updated = True
                
        if not members_dict:
            del bans_data[guild_id_str]
            
    if updated:
        save_bans(bans_data)

@bot.event
async def on_ready():
    bot.add_view(TeamsResetView())
    bot.add_view(TeamsControlView())
    bot.add_view(ApplyButtonView())
    bot.add_view(StartEventPanelView())
    if not check_expired_bans.is_running():
        check_expired_bans.start()
        
    for guild in bot.guilds:
        await fetch_points_from_discord()
        break
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم مزامنة {len(synced)} أمر سلاش عربي بنجاح!")
    except Exception as e:
        print(f"❌ خطأ في مزامنة أوامر السلاش: {e}")
    print(f"🚀 [بوت منتدى النظيم شغّال بنجاح تام] باسم: {bot.user}")

# ----------------------------------------------------
# 🛡️ أوامر العقوبات والسلاش المبسطة والكاملة
# ----------------------------------------------------

@bot.tree.command(name="أداء", description="عرض تقارير أداء ومقارنة الفرق ونقاطهم وعدد ترقياتهم")
async def performance_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = await calculate_teams_performance(interaction.guild)
    view = TeamsResetView() if is_admin_or_owner(interaction) else None
    await interaction.followup.send(embed=embed, view=view)

@bot.command(name="تيمات", aliases=["teams_panel"])
async def teams_panel_cmd(ctx):
    if ctx.author.id not in OWNER_IDS:
        await ctx.send("❌ عذراً يا الحبيب، هذه القائمة مخصصة للأونرات فقط!", delete_after=5)
        return
    try:
        await ctx.message.delete()
    except:
        pass

    guild = ctx.guild
    t1_role = guild.get_role(TEAM_1_ROLE_ID)
    t2_role = guild.get_role(TEAM_2_ROLE_ID)
    t1_name = t1_role.name if t1_role else "التيم الأول"
    t2_name = t2_role.name if t2_role else "التيم الثاني"

    embed = discord.Embed(
        title="⚔️ | لوحة إدارة وتحكم تيمات منتدى النظيم",
        description=(
            f"أهلاً بك يا الحاكم ريان. من خلال هذه اللوحة التفاعلية يمكنك إدارة نقاط الفريقين بكل سهولة:\n\n"
            f"🔹 **التيم الأول:** `{t1_name}`\n"
            f"🔹 **التيم الثاني:** `{t2_name}`\n\n"
            f"👇 **اختر الإجراء المناسب للأزرار بالأسفل:**"
        ),
        color=discord.Color.from_rgb(241, 196, 15),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="لوحة تحكم الأونر الخاصة | منتدى النظيم")
    await ctx.send(embed=embed, view=TeamsControlView())

@bot.tree.command(name="تحذير", description="[عقوبة سريعة] تطبيق تحذير إداري رسمي على عضو")
@app_commands.describe(member="اختر العضو المخالف", duration="حدد المدة (مثال: 3 ايام)", reason="اكتب سبب التحذير بوضوح", proof="رابط الدليل (اختياري)")
async def warn_slash(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str, proof: str = "لا يوجد"):
    guild = interaction.guild
    r_warn1, r_warn2, r_warn3 = guild.get_role(WARN_1_ID), guild.get_role(WARN_2_ID), guild.get_role(WARN_3_ID)

    assigned_warn_name = "تحذير أول"
    try:
        if r_warn2 and r_warn2 in member.roles:
            if r_warn2: await member.remove_roles(r_warn2)
            if r_warn3: await member.add_roles(r_warn3)
            assigned_warn_name = "تحذير ثالث"
        elif r_warn1 and r_warn1 in member.roles:
            if r_warn1: await member.remove_roles(r_warn1)
            if r_warn2: await member.add_roles(r_warn2)
            assigned_warn_name = "تحذير ثاني"
        else:
            if r_warn1: await member.add_roles(r_warn1)
            assigned_warn_name = "تحذير أول"
    except Exception as e: print(f"خطأ في منح رتبة التحذير: {e}")

    warn_channel = guild.get_channel(WARN_CHANNEL_ID)
    if warn_channel:
        warning_msg = f"__**\n`سجل التحذيرات الرسمي`\n\n- اسـم الإداري : {interaction.user.mention}\n\n- اســم العضو : {member.mention}\n\n- نـوع التـحـذيـر : {assigned_warn_name}\n\n- الـمـده : {duration}\n\n- الـسـبـب: {reason}\n\n- الـدليـل : {proof}\n**__"
        await warn_channel.send(warning_msg)

    data = load_data()
    uid = str(interaction.user.id)
    if uid not in data or not isinstance(data[uid], dict):
        data[uid] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}
    data[uid]["warns"] += 1
    save_data(data, guild)

    if active_event["running"]:
        if active_event["activity_type"] == "all" or active_event["activity_type"] == "warn":
            active_event["participants"][interaction.user.id] = active_event["participants"].get(interaction.user.id, 0) + 1

    await add_points_direct(guild, interaction.user, 1, f"تطبيق {assigned_warn_name}")
    await interaction.response.send_message(f"✅ **تم تطبيق {assigned_warn_name} على {member.mention} واُضيفت النقاط برصيدك بنجاح!**", ephemeral=True)

@bot.tree.command(name="تايم_أوت", description="[عقوبة سريعة] إسكات عضو لمدة معينة بالدقائق")
@app_commands.describe(member="اختر العضو", minutes="المدة بالدقائق (مثال: 10)", reason="سبب الكتم", proof="رابط الدليل (اختياري)")
async def timeout_slash(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str, proof: str = "لا يوجد"):
    guild = interaction.guild
    duration_delta = discord.utils.utcnow() + discord.utils.datetime.timedelta(minutes=minutes)
    try:
        await member.timeout(duration_delta, reason=reason)
        timeout_channel = guild.get_channel(TIMEOUT_MODEL_CHANNEL_ID)
        if timeout_channel:
            msg = f"**\n`سجل التايم أوت الرسمي`\n\n اسـم الإداري : {interaction.user.mention}\n\n اسـم العضو : {member.mention}\n\nالـمـده : {minutes} دقيقة\n\nالـسـبـب: {reason}\n\nالـدليـل : {proof}\n**"
            await timeout_channel.send(msg)

        data = load_data()
        uid = str(interaction.user.id)
        if uid not in data or not isinstance(data[uid], dict):
            data[uid] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}
        data[uid]["timeouts"] += 1
        save_data(data, guild)

        if active_event["running"]:
            if active_event["activity_type"] == "all" or active_event["activity_type"] == "timeout":
                active_event["participants"][interaction.user.id] = active_event["participants"].get(interaction.user.id, 0) + 1

        await add_points_direct(guild, interaction.user, 1, "تطبيق عقوبة تايم أوت")
        await interaction.response.send_message(f"✅ **تم كتم العضو {member.mention} لمدة {minutes} دقيقة بنجاح!**", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ تعذر تنفيذ التايم أوت: {e}", ephemeral=True)

@bot.tree.command(name="حرمان", description="[عقوبة سريعة] حرمان عضو من الرتب مع حفظها وإرجاعها تلقائياً")
@app_commands.describe(member="اختر العضو المخالف", duration="مدة الحرمان (مثال: 3 ايام)", reason="سبب الحرمان", proof="رابط الدليل (اختياري)")
async def ban_slash(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str, proof: str = "لا يوجد"):
    guild = interaction.guild
    ban_role = guild.get_role(BAN_ROLE_ID)
    if not ban_role:
        return await interaction.response.send_message("❌ رتبة الحرمان غير موجودة بالسيرفر!", ephemeral=True)

    try:
        saved_roles = [
            r.id for r in member.roles 
            if not r.is_default() and r.id != BAN_ROLE_ID and r < guild.me.top_role and not r.managed
        ]
        
        roles_to_remove = [
            r for r in member.roles 
            if not r.is_default() and r.id != BAN_ROLE_ID and r < guild.me.top_role and not r.managed
        ]
        
        if roles_to_remove: 
            await member.remove_roles(*roles_to_remove, reason=f"حرمان بواسطة {interaction.user.name}")
        await member.add_roles(ban_role, reason=f"حرمان بواسطة {interaction.user.name}")

        duration_seconds = parse_duration_to_seconds(duration)
        expires_at = time.time() + duration_seconds
        
        bans_data = load_bans()
        guild_id_str = str(guild.id)
        if guild_id_str not in bans_data:
            bans_data[guild_id_str] = {}
            
        bans_data[guild_id_str][str(member.id)] = {
            "saved_roles": saved_roles,
            "expires_at": expires_at
        }
        save_bans(bans_data)

        ban_channel = guild.get_channel(BAN_MODEL_CHANNEL_ID)
        if ban_channel:
            msg = f"__**\n`سجل حرمان الرول الرسمي`\n\n- اسـم الإداري : {interaction.user.mention}\n\n- اسـم العضو : {member.mention}\n\n- الـسـبـب : {reason}\n\n- الـمـده : {duration} (تنتهي تلقائياً)\n\n- الـدليـل : {proof}\n**__"
            await ban_channel.send(msg)

        data = load_data()
        uid = str(interaction.user.id)
        if uid not in data or not isinstance(data[uid], dict):
            data[uid] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}
        data[uid]["bans"] += 1
        save_data(data, guild)

        if active_event["running"]:
            if active_event["activity_type"] == "all" or active_event["activity_type"] == "ban":
                active_event["participants"][interaction.user.id] = active_event["participants"].get(interaction.user.id, 0) + 1

        await add_points_direct(guild, interaction.user, 2, "تطبيق عقوبة حرمان رول")
        await interaction.response.send_message(f"✅ **تم تطبيق الحرمان على {member.mention} بنجاح، وسيتم استرجاع رتبه تلقائياً بعد انتهاء المدة!**", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ تعذر تطبيق الحرمان: {e}", ephemeral=True)

@bot.tree.command(name="اعفاء", description="[عقوبة سريعة] رفع الحرمان عن العضو وإرجاع رتبه السابقة فوراً")
@app_commands.describe(member="اختر العضو المراد إعفاؤه")
async def unban_slash(interaction: discord.Interaction, member: discord.Member):
    if not is_admin_or_owner(interaction) and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
        return await interaction.response.send_message("❌ ما عندك صلاحية لتنفيذ أمر الإعفاء يا الغالي!", ephemeral=True)

    guild = interaction.guild
    guild_id_str = str(guild.id)
    bans_data = load_bans()
    
    ban_role = guild.get_role(BAN_ROLE_ID)
    
    try:
        if ban_role and ban_role in member.roles:
            await member.remove_roles(ban_role, reason=f"إعفاء بواسطة {interaction.user.name}")

        roles_restored = False
        if guild_id_str in bans_data and str(member.id) in bans_data[guild_id_str]:
            saved_role_ids = bans_data[guild_id_str][str(member.id)].get("saved_roles", [])
            roles_to_restore = []
            for rid in saved_role_ids:
                r = guild.get_role(rid)
                if r and r < guild.me.top_role and not r.is_default() and not r.managed:
                    roles_to_restore.append(r)
            
            if roles_to_restore:
                await member.add_roles(*roles_to_restore, reason=f"إعفاء وإرجاع الرتب بواسطة {interaction.user.name}")
                roles_restored = True
            
            del bans_data[guild_id_str][str(member.id)]
            if not bans_data[guild_id_str]:
                del bans_data[guild_id_str]
            save_bans(bans_data)

        log_ch = guild.get_channel(BAN_MODEL_CHANNEL_ID) or guild.get_channel(LOG_CHANNEL_ID)
        if log_ch:
            embed_log = discord.Embed(
                title="♻️ | إعفاء ورفع حرمان إداري",
                description=f"**الإداري:** {interaction.user.mention}\n**العضو المعفي:** {member.mention}\n**الحالة:** تم رفع الحرمان وإرجاع رتبه السابقة.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            await log_ch.send(embed=embed_log)

        restore_msg = "وتم استرجاع رتبه السابقة بنجاح!" if roles_restored else "وتم رفع رتبة الحرمان عنه."
        await interaction.response.send_message(f"✅ **تم إعفاء العضو {member.mention} {restore_msg}**", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ تعذر تنفيذ الإعفاء: {e}", ephemeral=True)

@bot.tree.command(name="إضافة_نقاط", description="إضافة نقاط لعضو إداري (خاص للقيادة)")
@app_commands.describe(member="العضو الإداري", amount="عدد النقاط")
async def addpoints_slash(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not can_manage_points(interaction):
        return await interaction.response.send_message("❌ هذا الأمر مخصص للرتب القيادية المصرح لها فقط!", ephemeral=True)
        
    if member.id == interaction.user.id and any(role.id == POINTS_CONTROL_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(f"❌ {interaction.user.mention} ماتقدر تعطي نفسك نقاط يالوح", ephemeral=False)
        return

    data = load_data()
    uid = str(member.id)
    if uid not in data or not isinstance(data[uid], dict):
        data[uid] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}
    data[uid]["points"] += amount
    save_data(data, interaction.guild)
    await interaction.response.send_message(f"✨ تم إضافة `{amount}` نقطة لـ {member.mention} بنجاح!")
    await check_and_promote(interaction, member, data[uid]["points"])

@bot.tree.command(name="خصم_نقاط", description="خصم نقاط من عضو إداري (خاص للقيادة)")
@app_commands.describe(member="العضو", amount="عدد النقاط الخصم")
async def removepoints_slash(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not can_manage_points(interaction):
        return await interaction.response.send_message("❌ هذا الأمر مخصص للرتب القيادية المصرح لها فقط!", ephemeral=True)
    data = load_data()
    uid = str(member.id)
    if uid in data and isinstance(data[uid], dict):
        data[uid]["points"] = max(0, data[uid]["points"] - amount)
        save_data(data, interaction.guild)
        await interaction.response.send_message(f"📉 تم خصم `{amount}` نقطة من {member.mention}.")

@bot.tree.command(name="تصفير_نقاط", description="تصفير نقاط عضو إداري بالكامل (خاص للقيادة)")
@app_commands.describe(member="العضو المراد تصفير نقاطه")
async def resetpoints_slash(interaction: discord.Interaction, member: discord.Member):
    if not can_manage_points(interaction):
        return await interaction.response.send_message("❌ هذا الأمر مخصص للرتب القيادية المصرح لها فقط!", ephemeral=True)
    data = load_data()
    uid = str(member.id)
    if uid in data:
        data[uid] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}
        save_data(data, interaction.guild)
        await interaction.response.send_message(f"🔄 تم تصفير نقاط {member.mention} بالكامل بنجاح!")

@bot.tree.command(name="نقاط", description="عرض رصيد النقاط ومؤشر التقدم والمتبقي للترقية")
@app_commands.describe(member="العضو (اختياري)")
async def points_slash(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    data = load_data()
    user_info = data.get(str(target.id), {"points": 0})
    pts = user_info.get("points", 0) if isinstance(user_info, dict) else user_info
    
    req_pts, rem_pts, percent, bar = await get_promotion_progress(target, pts)

    embed = discord.Embed(
        title=f"✨ | محفظة نقاط المطنوخ",
        description=f"العضو: {target.mention}\n\n"
                    f"💳 **الرصيد الحالي:** `{pts}` نقطة\n"
                    f"🎯 **الهدف القادم:** `{req_pts}` نقطة\n"
                    f"⏳ **المتبقي للترقية:** باقي لك **{rem_pts}** نقطة فقط!\n\n"
                    f"📊 **مؤشر التقدم:**\n{bar} (`{percent}%`)",
        color=discord.Color.from_rgb(46, 204, 113),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_footer(text="منتدى النظيم | قسم الرقابة الإدارية")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="أداء", aliases=["performance", "teams"])
async def performance_cmd(ctx):
    embed = await calculate_teams_performance(ctx.guild)
    view = TeamsResetView() if is_admin_or_owner(ctx) else None
    await ctx.send(embed=embed, view=view)

@bot.command(name="help", aliases=["مساعدة", "الأوامر", "اوامر"])
async def help_command(ctx):
    embed = discord.Embed(
        title="⚔️ | لوحة التحكم وأوامر منتدى النظيم الخارقة",
        description="يا هلا ومرحبابك يا ريس! هذي قائمة الأوامر والأنظمة كاملة:",
        color=discord.Color.from_rgb(241, 196, 15),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(
        name="📊 ┋ أوامر النقاط والفرق والبروفايلات",
        value="▫️ `.أداء`\n▫️ `.تيمات`\n▫️ `.نقاط`\n▫️ `.بروفايل`\n▫️ `.توب`\n▫️ `.إضافة_نقاط`\n▫️ `.خصم_نقاط`\n▫️ `.تصفير_نقاط`\n▫️ `.تصفير_الفرق`\n▫️ `.دبل_نقاط`",
        inline=False
    )
    embed.add_field(
        name="🛡️ ┋ أوامر العقوبات والفعاليات والتوظيف",
        value="▫️ `/تحذير`\n▫️ `/تايم_أوت`\n▫️ `/حرمان`\n▫️ `/اعفاء`\n▫️ `.فعاليات` (لبدء فعالية جديدة)\n▫️ `.توظيف <منشن> <الرقم>` (لتوظيف إداري وتعديل اسمه)\n▫️ `.فحص_الرتب`\n▫️ `.تفعيل_الكل`\n▫️ `!اونر` (لاستدعاء الأอนر)",
        inline=False
    )
    embed.set_footer(text=f"طلب بواسطة: {ctx.author.name}")
    await ctx.send(embed=embed)

@bot.command(name="دبل_نقاط", aliases=["doublepoints", "دبل"])
async def double_points(ctx):
    if not is_admin_or_owner(ctx):
        await ctx.send("❌ مخصص للأدمنستريتر والأونرات فقط!")
        return
    global double_points_end_time
    double_points_end_time = time.time() + 3600
    await ctx.send("🔥 **تم تفعيل مضاعفة النقاط (x2) لمدة ساعة كاملة!**")

@bot.command(name="رتبة", aliases=["giverole"])
async def give_role(ctx, member: discord.Member, role: discord.Role):
    if not is_admin_or_owner(ctx) and ctx.author.top_role <= role:
        return await ctx.send("❌ ما يمديك تعطي رتبة أعلى من رتبتك!", delete_after=6)
    try:
        await member.add_roles(role)
        await ctx.send(f"✅ تم إعطاء رتبة {role.mention} لـ {member.mention}.")
    except:
        await ctx.send("❌ البوت ما عنده صلاحية.")

@bot.command(name="سحب_رتبة", aliases=["removerole"])
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    if not is_admin_or_owner(ctx) and ctx.author.top_role <= role:
        return await ctx.send("❌ ما يمديك تسحب رتبة أعلى من رتبتك!", delete_after=6)
    try:
        await member.remove_roles(role)
        await ctx.send(f"🔄 تم سحب رتبة {role.mention} من {member.mention}.")
    except:
        await ctx.send("❌ البوت ما عنده صلاحية.")

@bot.command(name="إغلاق", aliases=["اغلاق", "close"])
async def close(ctx):
    await ctx.send("⚠️ **الإغلاق يكون عن طريق زر التكت فقط يا الذيب!**")

@bot.command(name="بروفايل", aliases=["profile", "stats"])
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0})
    if isinstance(user_info, int):
        user_info = {"points": user_info, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}
    
    pts = user_info.get('points', 0)
    req_pts, rem_pts, percent, bar = await get_promotion_progress(target, pts)

    embed = discord.Embed(
        title=f"🛡️ | السجل الإداري السيادي لـ {target.name}",
        description=f"إليك تفاصيل أداء وحالة المطنوخ الإدارية داخل سيرفر منتدى النظيم.",
        color=discord.Color.from_rgb(241, 196, 15),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    embed.add_field(name="📊 إجمالي النقاط", value=f"`{pts}` / `{req_pts}` نقطة للترقية", inline=True)
    embed.add_field(name="📈 نسبة التقدم", value=f"`{percent}%`\n{bar}", inline=False)
    embed.add_field(name="🎯 المتبقي للترقية", value=f"باقي لك **{rem_pts}** نقطة وتوصل رتبتك التالية يا وحش!", inline=False)
    
    embed.add_field(name="👑 عدد الترقيات", value=f"`{user_info.get('total_promotions', 0)}` مرة", inline=True)
    embed.add_field(name="🎫 التكتات", value=f"`{user_info.get('tickets', 0)}`", inline=True)
    embed.add_field(name="🪪 الهويات", value=f"`{user_info.get('identities', 0)}`", inline=True)
    
    embed.set_footer(text="منتدى النظيم | نظام الأداء الإداري الموحد", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    await ctx.send(embed=embed)

@bot.command(name="نقاط", aliases=["points"])
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), {"points": 0})
    pts = user_info.get("points", 0) if isinstance(user_info, dict) else user_info
    
    req_pts, rem_pts, percent, bar = await get_promotion_progress(target, pts)

    embed = discord.Embed(
        title=f"✨ | محفظة نقاط المطنوخ",
        description=f"العضو: {target.mention}\n\n"
                    f"💳 **الرصيد الحالي:** `{pts}` نقطة\n"
                    f"🎯 **الهدف القادم:** `{req_pts}` نقطة\n"
                    f"⏳ **المتبقي للترقية:** باقي لك **{rem_pts}** نقطة فقط!\n\n"
                    f"📊 **مؤشر التقدم:**\n{bar} (`{percent}%`)",
        color=discord.Color.from_rgb(46, 204, 113),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_footer(text="منتدى النظيم | قسم الرقابة الإدارية")
    await ctx.send(embed=embed)

@bot.command(name="إضافة_نقاط", aliases=["addpoints"])
async def addpoints(ctx, member: discord.Member, amount: int):
    if not can_manage_points(ctx): return await ctx.send("❌ مخصص للرتب القيادية فقط!")
    
    if member.id == ctx.author.id and any(role.id == POINTS_CONTROL_ROLE_ID for role in ctx.author.roles):
        await ctx.send(f"❌ {ctx.author.mention} ماتقدر تعطي نفسك نقاط يالوح")
        return

    data = load_data()
    uid = str(member.id)
    if uid not in data or not isinstance(data[uid], dict): data[uid] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}
    data[uid]["points"] += amount
    save_data(data, ctx.guild)
    await ctx.send(f"✨ تم إضافة `{amount}` نقطة لـ {member.mention}.")
    await check_and_promote(ctx, member, data[uid]["points"])

@bot.command(name="خصم_نقاط", aliases=["removepoints"])
async def removepoints(ctx, member: discord.Member, amount: int):
    if not can_manage_points(ctx): return await ctx.send("❌ مخصص للرتب القيادية فقط!")
    data = load_data()
    uid = str(member.id)
    if uid in data and isinstance(data[uid], dict):
        data[uid]["points"] = max(0, data[uid]["points"] - amount)
        save_data(data, ctx.guild)
        await ctx.send(f"📉 تم خصم `{amount}` نقطة من {member.mention}.")

@bot.command(name="تصفير_نقاط", aliases=["resetpoints"])
async def resetpoints(ctx, member: discord.Member):
    if not can_manage_points(ctx): return await ctx.send("❌ مخصص للرتب القيادية فقط!")
    data = load_data()
    uid = str(member.id)
    if uid in data:
        data[uid] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0, "identities": 0, "total_promotions": 0}
        save_data(data, ctx.guild)
        await ctx.send(f"🔄 تم تصفير نقاط {member.mention}.")

@bot.command(name="توب", aliases=["leaderboard", "top"])
async def leaderboard(ctx: commands.Context):
    data = load_data()
    if not data: return await ctx.send("📊 لا توجد بيانات.")
    sorted_users = sorted([(int(uid), info["points"] if isinstance(info, dict) else info) for uid, info in data.items()], key=lambda x: x[1], reverse=True)
    desc = "".join([f"`#{i}` <@{uid}> — **{pts}** نقطة\n" for i, (uid, pts) in enumerate(sorted_users[:10], 1)])
    await ctx.send(embed=discord.Embed(title="🏆 | لوحة الشرف", description=desc, color=discord.Color.from_rgb(241, 196, 15)))

@bot.command(name="تصفير_الفرق", aliases=["reset_teams"])
async def reset_teams_cmd(ctx):
    if not is_admin_or_owner(ctx):
        await ctx.send("❌ مخصص للأدمنستريتر والأونرات فقط!")
        return
    
    guild = ctx.guild
    guild_id_str = str(guild.id)
    bonuses = load_team_bonuses()
    persistent = load_team_persistent()
    
    guild_persistent = persistent.get(guild_id_str, {"t1_total": 0, "t2_total": 0})
    t1_base = guild_persistent.get("t1_total", 0)
    t2_base = guild_persistent.get("t2_total", 0)

    guild_bonus = bonuses.get(guild_id_str, {"t1_extra": 0, "t2_extra": 0})
    t1_base += guild_bonus.get("t1_extra", 0)
    t2_base += guild_bonus.get("t2_extra", 0)

    reset_data = load_teams_reset()
    reset_data[guild_id_str] = {
        "t1_base": t1_base,
        "t2_base": t2_base,
        "time": time.time()
    }
    save_teams_reset(reset_data)

    team_1_role = guild.get_role(TEAM_1_ROLE_ID)
    team_2_role = guild.get_role(TEAM_2_ROLE_ID)
    t1_members = [m for m in guild.members if team_1_role in m.roles] if team_1_role else []
    t2_members = [m for m in guild.members if team_2_role in m.roles] if team_2_role else []
    data = load_data()

    t1_t_sum = t1_i_sum = t1_p_sum = 0
    for m in t1_members:
        u_info = data.get(str(m.id), {})
        if isinstance(u_info, dict):
            t1_t_sum += u_info.get("tickets", 0)
            t1_i_sum += u_info.get("identities", 0)
            t1_p_sum += u_info.get("total_promotions", 0)

    t2_t_sum = t2_i_sum = t2_p_sum = 0
    for m in t2_members:
        u_info = data.get(str(m.id), {})
        if isinstance(u_info, dict):
            t2_t_sum += u_info.get("tickets", 0)
            t2_i_sum += u_info.get("identities", 0)
            t2_p_sum += u_info.get("total_promotions", 0)

    stats_resets = load_team_stats_reset()
    stats_resets[guild_id_str] = {
        "t1_tickets_base": t1_t_sum, "t1_identities_base": t1_i_sum, "t1_promotions_base": t1_p_sum,
        "t2_tickets_base": t2_t_sum, "t2_identities_base": t2_i_sum, "t2_promotions_base": t2_p_sum
    }
    save_team_stats_reset(stats_resets)

    await ctx.send("🔄 **تم تصفير المجموع التنافسي وإحصائيات التكتات والترقيات الأسبوعية للفرق بالكامل!** 🚀")
    await send_unified_log(guild, "🔄 | تصفير تنافس وإحصائيات الفرق", f"قام {ctx.author.mention} بتصفير التنافس وإحصائيات التكتات والترقيات للفرق أسبوعياً.", discord.Color.from_rgb(231, 76, 60))

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ: يرجى وضع متغير DISCORD_TOKEN.")
