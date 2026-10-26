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
# 1. إعدادات بوت ديسكورد الأساسية
# ----------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "."

BOT_OWNER_ID = 917414299184533515

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

# رتب الإدارة الصغرى والوسطى المعروفة (بحيث يسحب القديمة ويرقي للجديدة بأمان تام بدون لمس الحصانة)
MANAGEMENT_ROLE_KEYWORDS = [
    "Trainee", "Junior Moderator", "Moderator", "Senior Moderator", "Head Moderator",
    "Junior Administrator", "Senior Administrator", "Supervisor", "Senior Supervisor",
    "Manager", "Senior Manager", "Admin Prime", "Access", "Acting Admin", "Administrator",
    "Operations Manager", "Elite administrator", "Chief Executive"
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

double_points_end_time = 0
processed_tickets = set()

def is_admin_or_owner(ctx_or_interaction):
    author = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
    if author.id == BOT_OWNER_ID:
        return True
    return author.guild_permissions.administrator

def can_manage_points(ctx_or_interaction):
    author = ctx_or_interaction.author if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user
    if author.id == BOT_OWNER_ID or author.guild_permissions.administrator:
        return True
    return any(role.id == POINTS_CONTROL_ROLE_ID for role in getattr(author, 'roles', []))

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

def load_teams_reset():
    return load_json(TEAMS_RESET_FILE)

def save_teams_reset(data):
    save_json(TEAMS_RESET_FILE, data)

def load_cooldowns():
    return load_json(COOLDOWN_FILE)

def save_cooldowns(data):
    save_json(COOLDOWN_FILE, data)

def load_bans():
    return load_json(BANS_FILE)

def save_bans(data):
    save_json(BANS_FILE, data)

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
        is_middle = any(any(keyword.lower() in r.name.lower() for keyword in ["Supervisor", "Manager", "Chief", "Director"]) for r in member.roles)
        required_points = 70 if is_middle else 40
    
    remaining = max(0, required_points - current_pts)
    progress_percent = min(100, int((current_pts / required_points) * 100)) if required_points > 0 else 100
    
    filled_blocks = int(progress_percent / 10)
    empty_blocks = 10 - filled_blocks
    bar = "🟩" * filled_blocks + "⬛" * empty_blocks
    
    return required_points, remaining, progress_percent, bar

# ----------------------------------------------------
# 🧠 دالة الترقية الذكية الآمنة (لا تسحب إلا رتب الإدارة فقط)
# ----------------------------------------------------
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
        is_middle = any(any(keyword.lower() in r.name.lower() for keyword in ["Supervisor", "Manager", "Chief", "Director"]) for r in member.roles)
        required_points = 70 if is_middle else 40
        
        if current_pts >= required_points:
            member_roles_sorted = sorted(member.roles, key=lambda r: r.position, reverse=True)
            current_admin_role = None
            
            for r in member_roles_sorted:
                # التحقق الصارم: هل الرتبة تابعة لأسماء الإدارة المعروفة حصرياً؟
                if any(kw.lower() in r.name.lower() for kw in MANAGEMENT_ROLE_KEYWORDS):
                    current_admin_role = r
                    break
            
            if current_admin_role:
                all_guild_roles_sorted = sorted(guild.roles, key=lambda r: r.position)
                try:
                    curr_idx = all_guild_roles_sorted.index(current_admin_role)
                    if curr_idx < len(all_guild_roles_sorted) - 1:
                        next_role = all_guild_roles_sorted[curr_idx + 1]
                        # نتأكد أن الرتبة التالية ليست حصانة أو تيم أو رتبة غير إدارية
                        if next_role.id not in [TEAM_1_ROLE_ID, TEAM_2_ROLE_ID, BAN_ROLE_ID] and not any(bad in next_role.name.lower() for bad in ["حصانة", "تقاعد", "حماية"]):
                            target_role = next_role
                            role_category_name = "الإدارة الصغرى / الوسطى"
                except Exception as e:
                    print(f"خطأ في البحث عن الرتبة التالية: {e}")
            
            if not target_role and not is_middle:
                # رتبة البداية الافتراضية للإدارة الصغرى (Trainee أو أول رتبة)
                for r in sorted(guild.roles, key=lambda r: r.position):
                    if "Trainee" in r.name or "junior" in r.name.lower():
                        target_role = r
                        break
                if not target_role:
                    target_role = guild.get_role(1540839564506300476)
                role_category_name = "الإدارة الصغرى"

    if target_role and target_role not in member.roles:
        try:
            # سحب الرتب الإدارية القديمة فقط حصرياً (لن تقرب رتب الحصانة أو الأعضاء أبداً)
            roles_to_remove = [
                r for r in member.roles 
                if any(kw.lower() in r.name.lower() for kw in MANAGEMENT_ROLE_KEYWORDS)
                and r.id != target_role.id
                and r.position < target_role.position
            ]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="ترقية ذكية آمنة: سحب الرتب الإدارية القديمة فقط")
            
            await member.add_roles(target_role, reason="ترقية إدارية ذكية جديدة")
            
            data = load_data()
            user_id = str(member.id)
            if user_id in data and isinstance(data[user_id], dict):
                data[user_id]["points"] = 0
                data[user_id]["total_promotions"] = data[user_id].get("total_promotions", 0) + 1
                save_data(data, guild)

            role_ping_str = notif_role.mention if notif_role else ""
            msg = (
                f"{role_ping_str} 👑 **يا فخر الإدارة ويا كفو! ترقية ذكية وتصفير نقاط:**\n"
                f"ما شاء الله، المطنوخ {member.mention} وصل `{required_points}` نقطة وتمت ترقيته تلقائياً إلى `{target_role.name}` ضمن **{role_category_name}**!\n"
                f"🔄 **ملاحظة:** تم سحب رتبتك الإدارية القديمة وتصفير النقاط لانطلاق تحدٍ جديد."
            )
            log_channel = guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(msg)
        except Exception as e:
            print(f"خطأ أثناء الترقية الآمنة: {e}")

async def add_points_direct(guild, staff: discord.Member, base_points: int, action_name: str, target_type: str = None):
    global double_points_end_time
    
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
    
    double_text = " 🔥 **(الدبل شغال x2 يا وحش!)**" if is_double_active else ""
    await send_unified_log(
        guild, 
        "📊 | رصد وتوثيق نقاط إدارية", 
        f"تم إيداع `{actual_points}` نقطة في محفظة المطنوخ {staff.mention}{double_text}\n📌 **السبب:** {action_name}\n📈 **رصيده الإجمالي الآن:** `{current_pts}` نقطة",
        discord.Color.from_rgb(46, 204, 113) if not is_double_active else discord.Color.from_rgb(241, 196, 15)
    )
    
    await check_and_promote(guild, staff, current_pts)

# ----------------------------------------------------
# 📊 دالة تحليل أداء وتنافس الفرق
# ----------------------------------------------------
async def calculate_teams_performance(guild: discord.Guild):
    data = load_data()
    reset_data = load_teams_reset()
    
    guild_id_str = str(guild.id)
    team_1_role = guild.get_role(TEAM_1_ROLE_ID)
    team_2_role = guild.get_role(TEAM_2_ROLE_ID)
    
    t1_members = [m for m in guild.members if team_1_role in m.roles] if team_1_role else []
    t1_points = 0
    t1_promotions = 0
    t1_tickets = 0
    t1_identities = 0
    
    for m in t1_members:
        u_info = data.get(str(m.id), {})
        if isinstance(u_info, dict):
            t1_points += u_info.get("points", 0)
            t1_promotions += u_info.get("total_promotions", 0)
            t1_tickets += u_info.get("tickets", 0)
            t1_identities += u_info.get("identities", 0)
        elif isinstance(u_info, int):
            t1_points += u_info

    t2_members = [m for m in guild.members if team_2_role in m.roles] if team_2_role else []
    t2_points = 0
    t2_promotions = 0
    t2_tickets = 0
    t2_identities = 0
    
    for m in t2_members:
        u_info = data.get(str(m.id), {})
        if isinstance(u_info, dict):
            t2_points += u_info.get("points", 0)
            t2_promotions += u_info.get("total_promotions", 0)
            t2_tickets += u_info.get("tickets", 0)
            t2_identities += u_info.get("identities", 0)
        elif isinstance(u_info, int):
            t2_points += u_info

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

# ----------------------------------------------------
# 🔄 زر تصفير المجموع التنافسي للفرق فقط
# ----------------------------------------------------
class TeamsResetView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تصفير تنافس الفرق الأسبوعي", style=discord.ButtonStyle.danger, emoji="🔄", custom_id="reset_teams_weekly_virtual_v5")
    async def reset_teams_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin_or_owner(interaction):
            await interaction.response.send_message("❌ هذه اللوحة مخصصة للأدمنستريتر فقط!", ephemeral=True)
            return

        guild = interaction.guild
        data = load_data()
        team_1_role = guild.get_role(TEAM_1_ROLE_ID)
        team_2_role = guild.get_role(TEAM_2_ROLE_ID)
        
        t1_base = 0
        if team_1_role:
            for m in guild.members:
                if team_1_role in m.roles:
                    u_info = data.get(str(m.id), {})
                    t1_base += u_info.get("points", 0) if isinstance(u_info, dict) else (u_info if isinstance(u_info, int) else 0)

        t2_base = 0
        if team_2_role:
            for m in guild.members:
                if team_2_role in m.roles:
                    u_info = data.get(str(m.id), {})
                    t2_base += u_info.get("points", 0) if isinstance(u_info, dict) else (u_info if isinstance(u_info, int) else 0)

        reset_data = load_teams_reset()
        reset_data[str(guild.id)] = {
            "t1_base": t1_base,
            "t2_base": t2_base,
            "time": time.time()
        }
        save_teams_reset(reset_data)

        await interaction.response.send_message("🔄 **تم تصفير المجموع التنافسي الأسبوعي للفرق في أمر الأداء بنجاح!**\n*(ملاحظة: نقاط الإداريين الشخصية ومحافظهم وترقياتهم في أمان ولم تُمس نهائياً).* 🎉", ephemeral=True)
        await send_unified_log(guild, "🔄 | تصفير تنافس الفرق الأسبوعي", f"قام الأدمن {interaction.user.mention} بتصفير المجموع التنافسي الأسبوعي للفرق لبدء جولة جديدة.", discord.Color.from_rgb(231, 76, 60))

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
                POINTS_CONFIG["ticket"], 
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
    try: await ctx.message.delete()
    except: pass
    embed = discord.Embed(
        title="📋 | نظام تقديم الهوية الرسمي",
        description="تبي تطلع الهوية وتفعل حسابك بالسيرفر؟ اضغط على الزر تحت وبيجيك البوت في الخاص مباشرة يدردش معك ويأخذ بياناتك بكل سهولة.",
        color=discord.Color.from_rgb(52, 152, 219)
    )
    embed.set_footer(text="منتدى النظيم | قيادة السيرفر العليا")
    await ctx.send(embed=embed, view=ApplyButtonView())

@bot.command(name="عقوبات", aliases=["عقوبة", "penalties"])
async def penalties_cmd(ctx):
    embed = discord.Embed(
        title="⚠️ | تنبيه نظام الإدارة",
        description=(
            "يا هلا ومرحبابك يا المطنوخ.\n\n"
            "تم إلغاء الأوامر القديمة للعقوبات، وصار تنفيذ العقوبات **حصرياً عبر أوامر السلاش (Slash Commands)** لتكون أسرع وأسهل!\n\n"
            "🔹 **الأوامر المتاحة الآن:**\n"
            "👉 `/تحذير` - لتطبيق تحذير إداري وتوثيقه تلقائياً.\n"
            "👉 `/تايم_أوت` - لكتم العضو بالمدة المطلوبة.\n"
            "👉 `/حرمان` - لتطبيق رتبة الحرمان وسحب الرتبة.\n\n"
            "فقط اكتب علامة `/` في الشات واختر الأمر المناسب يا وحش! 🚀"
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
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("❌ عذراً يا الحبيب، أمر الحذف مخصص للحاكم ريان فقط!", delete_after=5)
        return
    try:
        await ctx.send("💥 جاري حذف الروم يا طويل العمر...")
        await asyncio.sleep(1)
        await ctx.channel.delete(reason=f"حذف الروم بأمر الحاكم ريان")
    except Exception as e:
        await ctx.send(f"❌ عذراً، ما قدرت أحذف الروم: {e}")

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
                            if r and r <= guild.me.top_role and not r.is_default():
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
    bot.add_view(ApplyButtonView())
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
# أوامر السلاش العربية (Slash Commands)
# ----------------------------------------------------

@bot.tree.command(name="أداء", description="عرض تقارير أداء ومقارنة الفرق ونقاطهم وعدد ترقياتهم")
async def performance_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = await calculate_teams_performance(interaction.guild)
    view = TeamsResetView() if is_admin_or_owner(interaction) else None
    await interaction.followup.send(embed=embed, view=view)

@bot.tree.command(name="تحذير", description="تطبيق تحذير إداري رسمي على عضو")
@app_commands.describe(member="العضو المخالف", duration="المدة (مثال: 3 ايام)", reason="سبب التحذير", proof="رابط الدليل (اختياري)")
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

    await add_points_direct(guild, interaction.user, POINTS_CONFIG["warn"], f"تطبيق {assigned_warn_name}")
    await interaction.response.send_message(f"✅ **تم تطبيق {assigned_warn_name} على {member.mention} واُضيفت النقاط برصيدك بنجاح!**", ephemeral=True)

@bot.tree.command(name="تايم_أوت", description="إسكات عضو لمدة معينة بالدقائق")
@app_commands.describe(member="العضو", minutes="المدة بالدقائق", reason="السبب", proof="رابط الدليل (اختياري)")
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

        await add_points_direct(guild, interaction.user, POINTS_CONFIG["timeout"], "تطبيق عقوبة تايم أوت")
        await interaction.response.send_message(f"✅ **تم كتم العضو {member.mention} لمدة {minutes} دقيقة بنجاح!**", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ تعذر تنفيذ التايم أوت: {e}", ephemeral=True)

@bot.tree.command(name="حرمان", description="حرمان عضو من الرتب مع حفظها وإرجاعها تلقائياً")
@app_commands.describe(member="العضو المخالف", duration="المدة", reason="السبب", proof="رابط الدليل (اختياري)")
async def ban_slash(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str, proof: str = "لا يوجد"):
    guild = interaction.guild
    ban_role = guild.get_role(BAN_ROLE_ID)
    if not ban_role:
        return await interaction.response.send_message("❌ رتبة الحرمان غير موجودة!", ephemeral=True)

    try:
        saved_roles = [r.id for r in member.roles if not r.is_default() and r.id != BAN_ROLE_ID and r < guild.me.top_role]
        
        roles_to_remove = [r for r in member.roles if not r.is_default() and r.id != BAN_ROLE_ID and r < guild.me.top_role]
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

        await add_points_direct(guild, interaction.user, POINTS_CONFIG["ban"], "تطبيق عقوبة حرمان رول")
        await interaction.response.send_message(f"✅ **تم تطبيق الحرمان على {member.mention} وتوثيق السجل، وسيتم استرجاع رتبه تلقائياً بعد انتهاء المدة!**", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ تعذر تطبيق الحرمان: {e}", ephemeral=True)

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

# ----------------------------------------------------
# الأوامر النصية العادية بالبادئة (.)
# ----------------------------------------------------

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
        value="▫️ `.أداء` (لعرض مقارنة وإحصائيات الفريقين وزر التصفير الافتراضي)\n▫️ `.نقاط`\n▫️ `.بروفايل`\n▫️ `.توب`\n▫️ `.إضافة_نقاط`\n▫️ `.خصم_نقاط`\n▫️ `.تصفير_نقاط`\n▫️ `.تصفير_الفرق`\n▫️ `.دبل_نقاط`",
        inline=False
    )
    embed.set_footer(text=f"طلب بواسطة: {ctx.author.name}")
    await ctx.send(embed=embed)

@bot.command(name="دبل_نقاط", aliases=["doublepoints", "دبل"])
async def double_points(ctx):
    if not is_admin_or_owner(ctx):
        await ctx.send("❌ مخصص للأدمنستريتر فقط!")
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
        await ctx.send("❌ مخصص للأدمنستريتر فقط!")
        return
    
    guild = ctx.guild
    data = load_data()
    team_1_role = guild.get_role(TEAM_1_ROLE_ID)
    team_2_role = guild.get_role(TEAM_2_ROLE_ID)
    
    t1_base = 0
    if team_1_role:
        for m in guild.members:
            if team_1_role in m.roles:
                u_info = data.get(str(m.id), {})
                t1_base += u_info.get("points", 0) if isinstance(u_info, dict) else (u_info if isinstance(u_info, int) else 0)

    t2_base = 0
    if team_2_role:
        for m in guild.members:
            if team_2_role in m.roles:
                u_info = data.get(str(m.id), {})
                t2_base += u_info.get("points", 0) if isinstance(u_info, dict) else (u_info if isinstance(u_info, int) else 0)

    reset_data = load_teams_reset()
    reset_data[str(guild.id)] = {
        "t1_base": t1_base,
        "t2_base": t2_base,
        "time": time.time()
    }
    save_teams_reset(reset_data)

    await ctx.send("🔄 **تم تصفير المجموع التنافسي الأسبوعي للفرق في أمر الأداء بنجاح!** *(نقاط الإداريين الشخصية محفوظة بالكامل ولم تُمس).* 🚀")
    await send_unified_log(guild, "🔄 | تصفير تنافس الفرق الأسبوعي", f"قام {ctx.author.mention} بتصفير المجموع التنافسي الأسبوعي للفرق.", discord.Color.from_rgb(231, 76, 60))

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ: يرجى وضع متغير DISCORD_TOKEN.")
