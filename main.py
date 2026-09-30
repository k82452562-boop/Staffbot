import discord
from discord.ext import commands
import json
import os
import time
from flask import Flask
from threading import Thread

# ----------------------------------------------------
# سيرفر Flask لإبقاء البوت نشطاً على Render 24/7
# ----------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Staffbot Ultimate Enterprise 24/7 - Online & Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ----------------------------------------------------
# الثوابت وأيدي الرولات والقنوات (كاملة ومحدثة)
# ----------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "."

ALLOWED_ROLE_IDS = [
    1545520633939624006,  
    1545520950064316516,  
    1540838084151877714   
]

LOG_CHANNEL_ID = 1553913719128588389
NOTIFICATION_CHANNEL_ID = 1541179719297278072   

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
    "warn": 10,
    "timeout": 10,
    "ban": 20,          
    "apply_accept": 10,
    "ticket_claim": 5,
    "ticket_close": 5   # نقاط إغلاق التكت للإداري
}

JUNIOR_ROLES = [
    1548407040014155806,
    1548407479396991047,
    1548407580131336283,
    1548407675048689715,
    1548407794426707978,
    1548407869320466583,
    1548407949356048534
]

MIDDLE_ROLES = [
    1548408037272715465,
    1548408124531154974,
    1548408197176361191,
    1548408266239910020,
    1548408357457756200
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)
DATA_FILE = "points.json"
COOLDOWN_FILE = "cooldowns.json"
double_points_end_time = 0

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="⚠️ | نقص في البيانات", description="يرجى كتابة الأمر بشكل صحيح وتعبئة كافة الحقول المطلوبة.", color=discord.Color.gold())
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(title="⚠ | خطأ في المدخلات", description="تأكد من اختيار عضو أو منشن رتبة بشكل صحيح.", color=discord.Color.gold())
        await ctx.send(embed=embed, delete_after=5)

# ----------------------------------------------------
# نظام الحفظ السحابي التلقائي عبر ديسكورد
# ----------------------------------------------------
async def fetch_points_from_discord():
    try:
        channel = bot.get_channel(BACKUP_CHANNEL_ID)
        if not channel:
            return {}
        async for message in channel.history(limit=20):
            if message.author == bot.user and message.attachments:
                for att in message.attachments:
                    if att.filename == "points_backup.json":
                        await att.save(DATA_FILE)
                        with open(DATA_FILE, "r", encoding="utf-8") as f:
                            return json.load(f)
    except Exception as e:
        print(f"⚠️ خطأ أثناء استرجاع النقاط من ديسكورد: {e}")
    return {}

async def save_points_to_discord(guild):
    try:
        channel = guild.get_channel(BACKUP_CHANNEL_ID)
        if not channel:
            return
        if os.path.exists(DATA_FILE):
            async for message in channel.history(limit=10):
                if message.author == bot.user and message.attachments:
                    for att in message.attachments:
                        if att.filename == "points_backup.json":
                            try:
                                await message.delete()
                            except:
                                pass
            file = discord.File(DATA_FILE, filename="points_backup.json")
            await channel.send("💾 **[Cloud Backup] النسخة الاحتياطية التلقائية لنقاط الإداريين:**", file=file)
    except Exception as e:
        print(f"⚠️ خطأ أثناء رفع النسخة الاحتياطية لديسكورد: {e}")

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
        print(f"❌ خطأ أثناء حفظ الملف {filename}: {e}")

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

async def send_unified_log(guild, title, description, color=discord.Color.blue(), fields=None):
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
    all_admin_roles_ids = JUNIOR_ROLES + MIDDLE_ROLES

    if current_pts >= 700:
        current_middle_index = -1
        for idx, r_id in enumerate(MIDDLE_ROLES):
            if guild.get_role(r_id) in member.roles:
                current_middle_index = idx
                break
        if current_middle_index == -1:
            target_role_id = MIDDLE_ROLES[0]
        elif current_middle_index < len(MIDDLE_ROLES) - 1:
            target_role_id = MIDDLE_ROLES[current_middle_index + 1]
        role_category_name = "الإدارة الوسطى"

    elif 400 <= current_pts < 700:
        current_junior_index = -1
        for idx, r_id in enumerate(JUNIOR_ROLES):
            if guild.get_role(r_id) in member.roles:
                current_junior_index = idx
                break
        if current_junior_index == -1:
            target_role_id = JUNIOR_ROLES[0]
        elif current_junior_index < len(JUNIOR_ROLES) - 1:
            target_role_id = JUNIOR_ROLES[current_junior_index + 1]
        role_category_name = "الإدارة الصغرى"

    if target_role_id:
        target_role = guild.get_role(target_role_id)
        if target_role and target_role not in member.roles:
            try:
                roles_to_remove = [guild.get_role(rid) for rid in all_admin_roles_ids if guild.get_role(rid) in member.roles and rid != target_role_id]
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove, reason="ترقية إدارية: سحب الرتبة القديمة")
                await member.add_roles(target_role, reason="ترقية إدارية جديدة")
                
                data = load_data()
                user_id = str(member.id)
                if user_id in data and isinstance(data[user_id], dict):
                    data[user_id]["points"] = 0
                elif user_id in data:
                    data[user_id] = 0
                save_data(data, guild)

                role_ping_str = notif_role.mention if notif_role else ""
                msg = (
                    f"{role_ping_str} 🎉 **ترقية إدارية جديدة وتصفير النقاط:**\n"
                    f"وصل الإداري {member.mention} وتمت ترقيته إلى الرتبة الجديدة `{target_role.name}` ضمن **{role_category_name}**!\n"
                    f"🔄 **ملاحظة:** تم تصفير نقاطه تلقائياً ليبدأ رحلة جديدة للصعود."
                )
                log_channel = guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(msg)
            except Exception as e:
                print(f"خطأ أثناء الترقية والتصفير: {e}")

async def add_points_direct(guild, staff: discord.Member, base_points: int, action_name: str):
    global double_points_end_time
    is_double_active = time.time() < double_points_end_time
    actual_points = (base_points * 2) if is_double_active else base_points
    
    data = load_data()
    user_id = str(staff.id)

    if user_id not in data or not isinstance(data[user_id], dict):
        old_pts = data.get(user_id, 0) if isinstance(data.get(user_id), int) else 0
        data[user_id] = {"points": old_pts, "warns": 0, "timeouts": 0, "bans": 0}

    user_data = data[user_id]
    user_data["points"] = user_data.get("points", 0) + actual_points
    current_pts = user_data["points"]

    save_data(data, guild)
    
    double_text = " 🔥 **(تم تطبيق دبل النقاط x2!)**" if is_double_active else ""
    await send_unified_log(
        guild, 
        "📊 | احتساب وتسجيل نقاط", 
        f"تم إضافة `{actual_points}` نقطة للإداري {staff.mention}{double_text}\n📌 **السبب / الإنجاز:** {action_name}\n📈 **المجموع الحالي:** `{current_pts}` نقطة",
        discord.Color.green() if not is_double_active else discord.Color.gold()
    )
    await check_and_promote(guild, staff, current_pts)

# ----------------------------------------------------
# أوامر النقاط والشرف
# ----------------------------------------------------
@bot.command(name="إعطاء_نقاط", aliases=["givepoints"])
async def give_points(ctx, member: discord.Member, points: int):
    if not any(r.id in ALLOWED_ROLE_IDS for r in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.", delete_after=5)
        return

    data = load_data()
    user_id = str(member.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        old_pts = data.get(user_id, 0) if isinstance(data.get(user_id), int) else 0
        data[user_id] = {"points": old_pts, "warns": 0, "timeouts": 0, "bans": 0}

    data[user_id]["points"] += points
    new_pts = data[user_id]["points"]
    save_data(data, ctx.guild)

    await ctx.send(f"✅ تم إضافة `{points}` نقطة بنجاح إلى الإداري {member.mention}. المجموع: `{new_pts}`")
    await send_unified_log(ctx.guild, "➕ | تعديل نقاط يدوي (إضافة)", f"قام {ctx.author.mention} بإضافة `{points}` نقطة لـ {member.mention}\n📈 المجموع الجديد: `{new_pts}`")
    await check_and_promote(ctx, member, new_pts)

@bot.command(name="سحب_نقاط", aliases=["removepoints"])
async def remove_points(ctx, member: discord.Member, points: int):
    if not any(r.id in ALLOWED_ROLE_IDS for r in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.", delete_after=5)
        return

    data = load_data()
    user_id = str(member.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        old_pts = data.get(user_id, 0) if isinstance(data.get(user_id), int) else 0
        data[user_id] = {"points": old_pts, "warns": 0, "timeouts": 0, "bans": 0}

    data[user_id]["points"] = max(0, data[user_id]["points"] - points)
    new_pts = data[user_id]["points"]
    save_data(data, ctx.guild)

    await ctx.send(f"✅ تم سحب `{points}` نقطة من الإداري {member.mention}. المجموع: `{new_pts}`")
    await send_unified_log(ctx.guild, "➖ | تعديل نقاط يدوي (خصم)", f"قام {ctx.author.mention} بخصم `{points}` نقطة من {member.mention}\n📈 المجموع الجديد: `{new_pts}`", discord.Color.red())

@bot.command(name="نقاط", aliases=["points"])
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), 0)
    pts = user_info["points"] if isinstance(user_info, dict) else user_info
    embed = discord.Embed(title="📊 | استعلام النقاط", description=f"نقاط الإداري {target.mention} الحالية هي: **{pts}** نقطة.", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="توب", aliases=["top"])
async def top_staff(ctx):
    data = load_data()
    if not data:
        await ctx.send("📭 لا توجد بيانات نقاط مسجلة حتى الآن.")
        return

    sorted_staff = sorted(
        data.items(), 
        key=lambda x: x[1]["points"] if isinstance(x[1], dict) else x[1], 
        reverse=True
    )

    embed = discord.Embed(title="🏆 | لوحة الشرف - أعلى الإداريين نقاطاً", color=discord.Color.gold())
    desc = ""
    for idx, (uid, info) in enumerate(sorted_staff[:10], 1):
        member = ctx.guild.get_member(int(uid))
        name = member.mention if member else f"مستخدم (`{uid}`)"
        pts = info["points"] if isinstance(info, dict) else info
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"`#{idx}`"
        desc += f"{medal} {name} — **{pts}** نقطة\n"

    embed.description = desc if desc else "لا توجد بيانات."
    await ctx.send(embed=embed)

@bot.command(name="تصفير_الكل", aliases=["resetall"])
async def reset_all(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ هذا الأمر خاص بمسؤولي السيرفر فقط.", delete_after=5)
        return
    
    save_data({}, ctx.guild)
    await ctx.send("🗑️ تم تصفير نقاط جميع الإداريين بنجاح!")
    await send_unified_log(ctx.guild, "🗑️ | تصفير النقاط", f"قام المسؤول {ctx.author.mention} بتصفير نقاط جميع الإداريين.", discord.Color.red())

# ----------------------------------------------------
# نظام إغلاق وفتح الروم العادي (Lock / Unlock)
# ----------------------------------------------------
@bot.command(name="قفل", aliases=["lock"])
async def lock_channel(ctx):
    if not any(r.id in ALLOWED_ROLE_IDS for r in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ ليس لديك صلاحية لإغلاق الروم.", delete_after=5)
        return

    try:
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_message = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = discord.Embed(title="🔒 | تم إغلاق الروم", description=f"تم إغلاق الروم بواسطة {ctx.author.mention}.", color=discord.Color.red())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {e}")

@bot.command(name="فتح", aliases=["unlock"])
async def unlock_channel(ctx):
    if not any(r.id in ALLOWED_ROLE_IDS for r in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ ليس لديك صلاحية لفتح الروم.", delete_after=5)
        return

    try:
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_message = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = discord.Embed(title="🔓 | تم فتح الروم", description=f"تم فتح الروم بواسطة {ctx.author.mention}.", color=discord.Color.green())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {e}")

# ----------------------------------------------------
# نظام إغلاق التكت أو الدعم الفني مع التحقق وزر التأكيد
# ----------------------------------------------------
class ConfirmCloseTicketView(discord.ui.View):
    def __init__(self, staff: discord.Member):
        super().__init__(timeout=60)
        self.staff = staff

    @discord.ui.button(label="نعم، متأكد", style=discord.ButtonStyle.red, emoji="✅")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.staff.id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ ليس لديك صلاحية لتأكيد هذا الإجراء.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.response.send_message("🔒 **تم تأكيد الإغلاق. جاري حذف تكت الدعم وإضافة النقاط...**")
        
        # إضافة النقاط للإداري الذي أغلق التكت
        await add_points_direct(interaction.guild, self.staff, POINTS_CONFIG["ticket_close"], f"إغلاق تكت/دعم فني: {interaction.channel.name}")
        await send_unified_log(interaction.guild, "🔒 | إغلاق تكت / دعم فني", f"قام الإداري {self.staff.mention} بإغلاق التكت `{interaction.channel.name}` بنجاح.", discord.Color.red())

        import asyncio
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete(reason=f"Closed by {self.staff}")
        except Exception:
            pass

    @discord.ui.button(label="إلغاء", style=discord.ButtonStyle.grey, emoji="✖️")
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.staff.id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ ليس لديك صلاحية للإلغاء.", ephemeral=True)
            return
        
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass
        await interaction.response.send_message("❌ تم إلغاء عملية إغلاق التكت.", ephemeral=True)

@bot.command(name="اغلاق", aliases=["close"])
async def close_ticket_command(ctx):
    if not any(r.id in ALLOWED_ROLE_IDS for r in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ ليس لديك صلاحية لاستخدام هذا الأمر.", delete_after=5)
        return

    # التحقق مما إذا كانت القناة تكت أو دعم فني (من اسم القناة أو اسم الكاتيجوري)
    channel_name = ctx.channel.name.lower()
    category_name = ctx.channel.category.name.lower() if ctx.channel.category else ""
    
    is_ticket_or_support = (
        "ticket" in channel_name or 
        "تكت" in channel_name or 
        "support" in channel_name or 
        "دعم" in channel_name or 
        "ticket" in category_name or 
        "تكت" in category_name or 
        "support" in category_name or 
        "دعم" in category_name
    )

    if not is_ticket_or_support:
        embed_err = discord.Embed(
            title="❌ | خطأ في الاستخدام",
            description="لا يمكنك استخدام هذا الأمر إلا داخل قنوات **التكتات أو الدعم الفني**!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed_err, delete_after=6)
        return

    embed = discord.Embed(
        title="⚠️ | تأكيد إغلاق التكت / الدعم الفني",
        description=f"هل أنت متأكد من رغبتك في إغلاق تكت الدعم الحالي يا {ctx.author.mention}؟\n(سيتم حذف الروم واحتساب النقاط فور التأكيد).",
        color=discord.Color.gold()
    )
    view = ConfirmCloseTicketView(staff=ctx.author)
    await ctx.send(embed=embed, view=view)

# ----------------------------------------------------
# نظام التقديم بالزر والخاص
# ----------------------------------------------------
class ApplyReviewView(discord.ui.View):
    def __init__(self, applicant: discord.Member, guild: discord.Guild):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.guild = guild

    @discord.ui.button(label="قبول التقديم", style=discord.ButtonStyle.green, custom_id="accept_apply_persistent_v200")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
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
                await self.applicant.remove_roles(unverified_role)
            if verified_role and verified_role not in self.applicant.roles:
                await self.applicant.add_roles(verified_role)
        except Exception as e:
            print(f"خطأ في الرتب: {e}")

        await add_points_direct(self.guild, interaction.user, POINTS_CONFIG["apply_accept"], "قبول تقديم هوية عضو")
        await interaction.channel.send(f"✅ تم قبول التقديم للعضو {self.applicant.mention} بواسطة {interaction.user.mention}")
        try:
            await self.applicant.send(f"🎉 مبارك! تم قبول تقديمك في سيرفر **{self.guild.name}**.")
        except:
            pass

    @discord.ui.button(label="رفض التقديم", style=discord.ButtonStyle.red, custom_id="reject_apply_persistent_v200")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        cooldowns = load_cooldowns()
        cooldowns[str(self.applicant.id)] = time.time()
        save_cooldowns(cooldowns)
        
        await interaction.channel.send(f"❌ تم رفض تقديم العضو {self.applicant.mention} بواسطة {interaction.user.mention}")
        try:
            await self.applicant.send(f"❌ نعتذر لك، تم رفض تقديمك في سيرفر **{self.guild.name}**.")
        except:
            pass

class ApplyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تقديم", style=discord.ButtonStyle.blurple, emoji="📝", custom_id="start_apply_persistent_view_v200")
    async def start_apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        cooldowns = load_cooldowns()
        
        if user_id in cooldowns:
            elapsed = time.time() - cooldowns[user_id]
            if elapsed < 600:
                remaining = int(600 - elapsed)
                mins = remaining // 60
                secs = remaining % 60
                await interaction.response.send_message(f"⏳ يرجى الانتظار لمدة `{mins} دقيقة و {secs} ثانية` قبل التقديم مجدداً.", ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.user.send("✨ **أهلاً بك في نظام التقديم الرسمي!** أجب على الأسئلة التالية:")
        except discord.Forbidden:
            await interaction.followup.send("❌ **يرجى فتح الخاص (Direct Messages)** لاستقبال أسئلة التقديم!", ephemeral=True)
            return

        questions = [
            "**1. اسمك ؟**",
            "**2. عمرك ؟**",
            "**3. اسم حسابك المستعار في روبلوكس ؟**",
            "**4. اسم حسابك الاساسي في روبلوكس ؟**",
            "**5. الحلف (اكتب: أقسم بالله)**"
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
                await interaction.user.send("⌛ انتهى الوقت. يرجى إعادة المحاولة من السيرفر.")
                return

        review_channel = interaction.guild.get_channel(APPLY_REVIEW_CHANNEL_ID)
        if review_channel:
            embed = discord.Embed(title="📥 | تقديم هوية جديد", color=discord.Color.gold())
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="👤 المتقدم", value=interaction.user.mention, inline=False)
            embed.add_field(name="1. الاسم", value=answers[0], inline=False)
            embed.add_field(name="2. العمر", value=answers[1], inline=False)
            embed.add_field(name="3. المستعار", value=answers[2], inline=False)
            embed.add_field(name="4. الأساسي", value=answers[3], inline=False)
            embed.add_field(name="5. الحلف", value=answers[4], inline=False)

            view = ApplyReviewView(applicant=interaction.user, guild=interaction.guild)
            await review_channel.send(content=f"🔔 <@&{ADMIN_ROLE_PENG_ID}> تقديم جديد بانتظار المراجعة!", embed=embed, view=view)
        
        await interaction.user.send("✅ **تم إرسال إجاباتك للإدارة بنجاح!**")

@bot.command(name="بانل_تقديم", aliases=["panel_apply"])
async def panel_apply(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(title="📋 | نظام تقديم الهوية الرسمي", description="اضغط على الزر أدناه لبدء التقديم في الخاصة.", color=discord.Color.blue())
    view = ApplyButtonView()
    await ctx.send(embed=embed, view=view)

# ----------------------------------------------------
# نظام العقوبات (بان، تايم آوت، تحذيرات)
# ----------------------------------------------------
@bot.command(name="بان", aliases=["ban"])
async def staff_ban(ctx, member: discord.Member, *, reason=None):
    if not any(r.id in ALLOWED_ROLE_IDS for r in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
        return
    try:
        await member.ban(reason=reason)
    except Exception as e:
        await ctx.send(f"❌ تعذر حظر العضو: {e}")
        return

    data = load_data()
    user_id = str(ctx.author.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        data[user_id] = {"points": 0, "warns": 0, "timeouts": 0, "bans": 0}
    data[user_id]["bans"] = data[user_id].get("bans", 0) + 1
    save_data(data, ctx.guild)

    await add_points_direct(ctx.guild, ctx.author, POINTS_CONFIG["ban"], f"حظر عضو: {member.name}")
    await ctx.send(f"🔨 تم حظر العضو {member.mention} بنجاح.")

    ban_model_ch = ctx.guild.get_channel(BAN_MODEL_CHANNEL_ID)
    if ban_model_ch:
        embed = discord.Embed(title="🔨 | تسجيل عقوبة حظر (Ban)", color=discord.Color.red())
        embed.add_field(name="المشرف", value=ctx.author.mention, inline=True)
        embed.add_field(name="العضو المحظور", value=f"{member} (`{member.id}`)", inline=True)
        embed.add_field(name="السبب", value=reason or "بدون سبب محدد", inline=False)
        await ban_model_ch.send(embed=embed)

@bot.command(name="تايم_آوت", aliases=["timeout", "mute"])
async def staff_timeout(ctx, member: discord.Member, minutes: int, *, reason=None):
    if not any(r.id in ALLOWED_ROLE_IDS for r in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
        return
    
    duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
    try:
        await member.timeout(duration, reason=reason)
    except Exception as e:
        await ctx.send(f"❌ تعذر إسكات العضو: {e}")
        return

    data = load_data()
    user_id = str(ctx.author.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        data[user_id] = {"points": 0, "warns": 0, "timeouts": 0, "bans": 0}
    data[user_id]["timeouts"] = data[user_id].get("timeouts", 0) + 1
    save_data(data, ctx.guild)

    await add_points_direct(ctx.guild, ctx.author, POINTS_CONFIG["timeout"], f"إسكات (Timeout) لعضو لمدة {minutes} دقيقة")
    await ctx.send(f"🔇 تم إعطاء تايم آوت للعضو {member.mention} لمدة `{minutes}` دقيقة.")

    to_model_ch = ctx.guild.get_channel(TIMEOUT_MODEL_CHANNEL_ID)
    if to_model_ch:
        embed = discord.Embed(title="🔇 | تسجيل عقوبة إسكات (Timeout)", color=discord.Color.gold())
        embed.add_field(name="المشرف", value=ctx.author.mention, inline=True)
        embed.add_field(name="العضو", value=f"{member} (`{member.id}`)", inline=True)
        embed.add_field(name="المدة", value=f"{minutes} دقيقة", inline=True)
        embed.add_field(name="السبب", value=reason or "بدون سبب", inline=False)
        await to_model_ch.send(embed=embed)

@bot.command(name="تحذير", aliases=["warn"])
async def staff_warn(ctx, member: discord.Member, *, reason=None):
    if not any(r.id in ALLOWED_ROLE_IDS for r in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
        return

    w1 = ctx.guild.get_role(WARN_1_ID)
    w2 = ctx.guild.get_role(WARN_2_ID)
    w3 = ctx.guild.get_role(WARN_3_ID)

    action_text = "تم إعطاء تحذير"
    try:
        if w1 and w1 not in member.roles:
            await member.add_roles(w1)
            action_text = "تحذير أول (Warn 1)"
        elif w2 and w2 not in member.roles:
            if w1 in member.roles:
                await member.remove_roles(w1)
            await member.add_roles(w2)
            action_text = "تحذير ثاني (Warn 2)"
        elif w3 and w3 not in member.roles:
            if w2 in member.roles:
                await member.remove_roles(w2)
            await member.add_roles(w3)
            action_text = "تحذير ثالث (Warn 3 - خطر)"
    except Exception as e:
        print(f"خطأ في إعطاء رتب التحذير: {e}")

    data = load_data()
    user_id = str(ctx.author.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        data[user_id] = {"points": 0, "warns": 0, "timeouts": 0, "bans": 0}
    data[user_id]["warns"] = data[user_id].get("warns", 0) + 1
    save_data(data, ctx.guild)

    await add_points_direct(ctx.guild, ctx.author, POINTS_CONFIG["warn"], f"تحذير عضو: {member.name}")
    await ctx.send(f"⚠️ تم تسجيل {action_text} للعضو {member.mention}.")

    warn_ch = ctx.guild.get_channel(WARN_CHANNEL_ID)
    if warn_ch:
        embed = discord.Embed(title=f"⚠️ | تسجيل {action_text}", color=discord.Color.orange())
        embed.add_field(name="المشرف", value=ctx.author.mention, inline=True)
        embed.add_field(name="العضو المحذر", value=f"{member} (`{member.id}`)", inline=True)
        embed.add_field(name="السبب", value=reason or "بدون سبب محدد", inline=False)
        await warn_ch.send(embed=embed)

# ----------------------------------------------------
# نظام تغيير الاسم التلقائي
# ----------------------------------------------------
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return

    if message.channel.id == NICKNAME_CHANNEL_ID:
        try:
            await message.delete()
        except Exception:
            pass

        guild = message.guild
        member = message.author
        raw_name = message.content.strip()
        if not raw_name:
            return

        new_nickname = f"NZM | {raw_name}"
        if len(new_nickname) > 32:
            new_nickname = new_nickname[:32]

        try:
            await member.edit(nick=new_nickname, reason="تغيير الاسم التلقائي")
            role_to_add = guild.get_role(NICKNAME_ROLE_ID)
            if role_to_add and role_to_add not in member.roles:
                await member.add_roles(role_to_add)
        except Exception as e:
            print(f"خطأ في تعديل الاسم: {e}")

# ----------------------------------------------------
# الأحداث والبروفايل
# ----------------------------------------------------
@bot.event
async def on_ready():
    bot.add_view(ApplyButtonView())
    for guild in bot.guilds:
        await fetch_points_from_discord()
        break
    print(f"🚀 [ULTIMATE BOT READY 100%] تم تشغيل البوت بنجاح والتحقق من التكتات والدعم الفني: {bot.user}")

@bot.command(name="بروفايل", aliases=["profile", "stats"])
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), {"points": 0, "warns": 0, "timeouts": 0, "bans": 0})
    if isinstance(user_info, int):
        user_info = {"points": user_info, "warns": 0, "timeouts": 0, "bans": 0}

    embed = discord.Embed(title=f"🛡 | بروفايل الإداري: {target.name}", color=discord.Color.blurple())
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="📊 النقاط", value=f"{user_info.get('points', 0)} نقطة", inline=True)
    embed.add_field(name="⚠ التحذيرات", value=f"{user_info.get('warns', 0)} تحذير", inline=True)
    embed.add_field(name="🔇 التايم آوت", value=f"{user_info.get('timeouts', 0)} إجراء", inline=True)
    embed.add_field(name="🔨 الباندات", value=f"{user_info.get('bans', 0)} بان", inline=True)
    await ctx.send(embed=embed)

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
