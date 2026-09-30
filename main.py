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
    return "Staffbot Ultimate Full Production 24/7 - Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ----------------------------------------------------
# الثوابت وأيدي الرولات والقنوات (كاملة بدون نقصان)
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

TICKET_PANEL_CHANNEL_ID = 1543094490468847666
TICKET_CATEGORY_ID = 1546498225404379279
STAFF_ROLE_ID = 1545520633939624006
OWNER_ROLE_ID = 1535687924425818283

WARN_1_ID = 1543278808583372901
WARN_2_ID = 1543278965857198271
WARN_3_ID = 1543279133164048576

BACKUP_CHANNEL_ID = 1553913719128588389  

POINTS_CONFIG = {
    "ticket": 10,
    "warn": 10,
    "timeout": 10,
    "ban": 20,          
    "apply_accept": 10 
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
        embed = discord.Embed(title="⚠️ | خطأ في المدخلات", description="تأكد من اختيار عضو أو منشن رتبة بشكل صحيح.", color=discord.Color.gold())
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
        data[user_id] = {"points": old_pts, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}

    user_data = data[user_id]
    user_data["points"] = user_data.get("points", 0) + actual_points
    current_pts = user_data["points"]

    if "تقديم" in action_name or "تكت" in action_name:
        user_data["tickets"] = user_data.get("tickets", 0) + 1

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
# 1. نظام إعطاء وسحب النقاط اليدوي الكامل
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
        data[user_id] = {"points": old_pts, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}

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
        data[user_id] = {"points": old_pts, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}

    data[user_id]["points"] = max(0, data[user_id]["points"] - points)
    new_pts = data[user_id]["points"]
    save_data(data, ctx.guild)

    await ctx.send(f"✅ تم سحب `{points}` نقطة من الإداري {member.mention}. المجموع: `{new_pts}`")
    await send_unified_log(ctx.guild, "➖ | تعديل نقاط يدوي (خصم)", f"قام {ctx.author.mention} بخصم `{points}` نقطة من {member.mention}\n📈 المجموع الجديد: `{new_pts}`", discord.Color.red())

# ----------------------------------------------------
# 2. نظام التكتات والتحكم الدائم المتكامل
# ----------------------------------------------------
class TicketControlView(discord.ui.View):
    def __init__(self, ticket_owner: discord.Member):
        super().__init__(timeout=None)
        self.ticket_owner = ticket_owner
        self.claimed_by = None

    @discord.ui.button(label="استدعاء العضو", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="ticket_call_member_v99")
    async def call_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"👤 {self.ticket_owner.mention}, الإداري {interaction.user.mention} يستدعي أطراف التكت هنا.")

    @discord.ui.button(label="استدعاء الإدارة", style=discord.ButtonStyle.secondary, emoji="🔔", custom_id="ticket_call_staff_v99")
    async def call_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        owner_role = interaction.guild.get_role(OWNER_ROLE_ID)
        staff_ping = staff_role.mention if staff_role else ""
        owner_ping = owner_role.mention if owner_role else ""
        await interaction.response.send_message(f"🔔 {staff_ping} {owner_ping} — تم طلب حضور الإدارة بواسطة {interaction.user.mention} في هذا التكت.")

    @discord.ui.button(label="استلام التكت", style=discord.ButtonStyle.green, emoji="🛡️", custom_id="ticket_claim_v99")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.claimed_by = interaction.user
        button.disabled = True
        button.label = f"استلمها: {interaction.user.name}"
        await interaction.message.edit(view=self)

        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ROLE_ID)

        try:
            await interaction.channel.set_permissions(guild.default_role, send_messages=False)
            if staff_role:
                await interaction.channel.set_permissions(staff_role, read_messages=True, send_messages=False)
            await interaction.channel.set_permissions(self.ticket_owner, read_messages=True, send_messages=True)
            await interaction.channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        except Exception as e:
            print(f"خطأ في تعديل الصلاحيات: {e}")

        await interaction.response.send_message(f"🛡 **تم استلام التكت بواسطة:** {interaction.user.mention}\n🔒 **تم تقييد الكتابة وأصبح الروم مرئياً للإدارة للقراءة فقط.**")

    @discord.ui.button(label="إضافة عضو", style=discord.ButtonStyle.blurple, emoji="➕", custom_id="ticket_add_member_v99")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✍️ يرجى عمل منشن (Mention) للعضو الذي ترغب في إضافته للتكت خلال 30 ثانية.", ephemeral=True)
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and len(m.mentions) > 0

        try:
            msg = await bot.wait_for('message', timeout=30.0, check=check)
            target_member = msg.mentions[0]
            await interaction.channel.set_permissions(target_member, read_messages=True, send_messages=True)
            await msg.delete()
            await interaction.followup.send(f"✅ تمت إضافة العضو {target_member.mention} للتكت بنجاح.")
        except Exception:
            await interaction.followup.send("⌛ انقطعت الاستجابة أو لم تقم بمنشن أي عضو.", ephemeral=True)

    @discord.ui.button(label="إغلاق التكت", style=discord.ButtonStyle.red, emoji="🔒", custom_id="ticket_close_btn_v99")
    async def close_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 جاري أرشيف وإغلاق التكت...")
        await add_points_direct(interaction.guild, interaction.user, POINTS_CONFIG["ticket"], "إغلاق تكت عبر الأزرار وإنجاز")
        await interaction.channel.delete()

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تكت دعم فني", style=discord.ButtonStyle.blurple, emoji="🎫", custom_id="open_ticket_btn_v99")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        category = guild.get_category(TICKET_CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)
        owner_role = guild.get_role(OWNER_ROLE_ID)

        for ch in guild.text_channels:
            if ch.topic and str(interaction.user.id) in ch.topic:
                await interaction.followup.send(f"❌ لديك تكت مفتوح مسبقاً: {ch.mention}", ephemeral=True)
                return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if owner_role:
            overwrites[owner_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=category,
                overwrites=overwrites,
                topic=f"صاحب التكت ID: {interaction.user.id}"
            )
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ أثناء إنشاء الروم: {e}", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎫 | الدعم الفني - منتدى النظيم",
            description=f"أهلاً بك {interaction.user.mention}\nيرجى شرح مشكلتك بالتفصيل وستتم خدمتك قريباً.",
            color=discord.Color.blue()
        )
        view = TicketControlView(ticket_owner=interaction.user)
        await ticket_channel.send(content=f"🔔 {interaction.user.mention} | <@&{STAFF_ROLE_ID}>", embed=embed, view=view)
        await interaction.followup.send(f"✅ تم فتح تكت الدعم الفني الخاص بك بنجاح: {ticket_channel.mention}", ephemeral=True)

@bot.command(name="بانل_التكت", aliases=["ticketpanel"])
async def ticket_panel(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        title="🎫 | نظام تكتات الدعم الفني",
        description="إذا كنت تواجه مشكلة أو تحتاج إلى مساعدة، اضغط على الزر أدناه لفتح تكت خاص.",
        color=discord.Color.blue()
    )
    view = TicketPanelView()
    await ctx.send(embed=embed, view=view)

# ----------------------------------------------------
# 3. نظام التقديم بالزر والخاص الكامل
# ----------------------------------------------------
class ApplyReviewView(discord.ui.View):
    def __init__(self, applicant: discord.Member, guild: discord.Guild):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.guild = guild

    @discord.ui.button(label="قبول التقديم", style=discord.ButtonStyle.green, custom_id="accept_apply_persistent_v99")
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

    @discord.ui.button(label="رفض التقديم", style=discord.ButtonStyle.red, custom_id="reject_apply_persistent_v99")
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

    @discord.ui.button(label="تقديم", style=discord.ButtonStyle.blurple, emoji="📝", custom_id="start_apply_persistent_view_v99")
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
# 4. نظام العقوبات والتحذيرات والبان والتايم آوت الكامل
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
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
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
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
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
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
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
# 5. نظام تغيير الاسم التلقائي الكامل
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
# 6. الأحداث والبروفايل والأوامر العامة
# ----------------------------------------------------
@bot.event
async def on_ready():
    bot.add_view(ApplyButtonView())
    bot.add_view(TicketPanelView())

    for guild in bot.guilds:
        await fetch_points_from_discord()
        break
    print(f"🚀 [BOT READY & PERSISTENT VIEWS LOADED] تم تشغيل البوت بنجاح: {bot.user}")

@bot.command(name="بروفايل", aliases=["profile", "stats"])
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0})
    if isinstance(user_info, int):
        user_info = {"points": user_info, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}

    embed = discord.Embed(title=f"🛡 | بروفايل الإداري: {target.name}", color=discord.Color.blurple())
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="📊 النقاط", value=f"{user_info.get('points', 0)} نقطة", inline=True)
    embed.add_field(name="🎫 التكتات", value=f"{user_info.get('tickets', 0)} إنجاز", inline=True)
    embed.add_field(name="⚠ التحذيرات", value=f"{user_info.get('warns', 0)} تحذير", inline=True)
    embed.add_field(name="🔇 التايم آوت", value=f"{user_info.get('timeouts', 0)} إجراء", inline=True)
    embed.add_field(name="🔨 الباندات", value=f"{user_info.get('bans', 0)} بان", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="نقاط", aliases=["points"])
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), 0)
    pts = user_info["points"] if isinstance(user_info, dict) else user_info
    embed = discord.Embed(title="📊 | استعلام النقاط", description=f"نقاط الإداري {target.mention} الحالية هي: **{pts}** نقطة.", color=discord.Color.blue())
    await ctx.send(embed=embed)

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
