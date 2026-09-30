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
    return "Staffbot Ultimate OP 24/7 with Exclusive Ticket Claim System is Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ----------------------------------------------------
# 1. الثوابت والأيدي (IDs) المطلوبة للسيرفر
# ----------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "."

ALLOWED_ROLE_IDS = [
    1545520633939624006,  
    1545520950064316516,  
    1540838084151877714   
]

# الرومات والأيدي الأساسية
LOG_CHANNEL_ID = 1553913719128588389
NOTIFICATION_CHANNEL_ID = 1541179719297278072   # أيدي رتبة إشعار الترقية

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

# أيدي نظام التكتات الجديد
TICKET_PANEL_CHANNEL_ID = 1543094490468847666
TICKET_CATEGORY_ID = 1546498225404379279
STAFF_ROLE_ID = 1545520633939624006
OWNER_ROLE_ID = 1535687924425818283

WARN_1_ID = 1543278808583372901
WARN_2_ID = 1543278965857198271
WARN_3_ID = 1543279133164048576

POINTS_CONFIG = {
    "ticket": 10,
    "warn": 10,
    "timeout": 10,
    "ban": 20,          # نقاط الحرمان 20 نقطة
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
        embed = discord.Embed(title="⚠️ | خطأ في المدخلات", description="تأكد من اختيار عضو أو منشن رتبة بشكل صحيح.", color=discord.Color.gold())
        await ctx.send(embed=embed, delete_after=5)

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

def save_data(data):
    save_json(DATA_FILE, data)

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
                    save_data(data)

                role_ping_str = notif_role.mention if notif_role else ""
                msg = (
                    f"{role_ping_str} 🎉 **ترقية إدارية وتصفير نقاط:**\n"
                    f"وصل الإداري {member.mention} وتمت ترقيته إلى الرتبة الجديدة `{target_role.name}` ضمن **{role_category_name}**!\n"
                    f"🔄 **ملاحظة:** تم سحب رتبته القديمة وتصفير نقاطه بنجاح."
                )
                log_channel = guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(msg)
            except Exception as e:
                print(f"خطأ أثناء منح الترقية وسحب القديمة: {e}")

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

    save_data(data)
    
    double_text = " 🔥 **(تم تطبيق دبل النقاط x2!)**" if is_double_active else ""
    await send_unified_log(
        guild, 
        "📊 | احتساب وتسجيل نقاط", 
        f"تم إضافة `{actual_points}` نقطة للإداري {staff.mention}{double_text}\n📌 **السبب / الإنجاز:** {action_name}\n📈 **المجموع الحالي:** `{current_pts}` نقطة",
        discord.Color.green() if not is_double_active else discord.Color.gold()
    )
    
    await check_and_promote(guild, staff, current_pts)

# ----------------------------------------------------
# 2. نظام التكتات والتحكم (Support Tickets System)
# ----------------------------------------------------
class TicketControlView(discord.ui.View):
    def __init__(self, ticket_owner: discord.Member):
        super().__init__(timeout=None)
        self.ticket_owner = ticket_owner
        self.claimed_by = None

    @discord.ui.button(label="استدعاء العضو", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="ticket_call_member_v2")
    async def call_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ هذا الزر مخصص للإدارة فقط.", ephemeral=True)
            return
        await interaction.response.send_message(f"👤 {self.ticket_owner.mention}, الإداري {interaction.user.mention} يستدعي أطراف التكت هنا.")

    @discord.ui.button(label="استدعاء الإدارة", style=discord.ButtonStyle.secondary, emoji="🔔", custom_id="ticket_call_staff_v2")
    async def call_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ هذا الزر مخصص للإدارة فقط.", ephemeral=True)
            return
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        owner_role = interaction.guild.get_role(OWNER_ROLE_ID)
        staff_ping = staff_role.mention if staff_role else ""
        owner_ping = owner_role.mention if owner_role else ""
        await interaction.response.send_message(f"🔔 {staff_ping} {owner_ping} — تم طلب حضور الإدارة بواسطة {interaction.user.mention} في هذا التكت.")

    @discord.ui.button(label="استلام التكت", style=discord.ButtonStyle.green, emoji="🛡️", custom_id="ticket_claim_v2")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ هذا الزر مخصص للإدارة فقط.", ephemeral=True)
            return
        
        self.claimed_by = interaction.user
        button.disabled = True
        button.label = f"استلمها: {interaction.user.name}"
        await interaction.message.edit(view=self)

        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ROLE_ID)

        # قفل الروم: يظل متاحاً فقط لصاحب التكت والإداري المستلم، بينما باقي الإدارة يمكنهم الرؤية دون الكتابة
        try:
            await interaction.channel.set_permissions(guild.default_role, send_messages=False)
            if staff_role:
                # بقية الإدارة يقدرون يشوفون الروم (read_messages=True) لكن ممنوعين من الكتابة (send_messages=False)
                await interaction.channel.set_permissions(staff_role, read_messages=True, send_messages=False)
            
            # صاحب التكت والإداري المستلم مسموح لهم بالكتابة
            await interaction.channel.set_permissions(self.ticket_owner, read_messages=True, send_messages=True)
            await interaction.channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        except Exception as e:
            print(f"خطأ في تعديل صلاحيات التكت: {e}")

        await interaction.response.send_message(f"🛡️ **تم استلام التكت بنجاح بواسطة الإداري:** {interaction.user.mention}\n🔒 **تم تقييد الكتابة في الروم وأصبح مرئياً لباقي الإدارة للقراءة فقط.**")

    @discord.ui.button(label="إضافة عضو", style=discord.ButtonStyle.blurple, emoji="➕", custom_id="ticket_add_member_v2")
    async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ هذا الزر مخصص للإدارة فقط.", ephemeral=True)
            return
        
        await interaction.response.send_message("✍️ يرجى عمل منشن (Mention) للعضو الذي ترغب في إضافته للتكت في رسالة جديدة خلال 30 ثانية.", ephemeral=True)
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and len(m.mentions) > 0

        try:
            msg = await bot.wait_for('message', timeout=30.0, check=check)
            target_member = msg.mentions[0]
            await interaction.channel.set_permissions(target_member, read_messages=True, send_messages=True)
            await msg.delete()
            await interaction.followup.send(f"✅ تمت إضافة العضو {target_member.mention} إلى التكت بنجاح بواسطة {interaction.user.mention}.")
        except Exception:
            await interaction.followup.send("⌛ انقطعت الاستجابة أو لم تقم بمنشن أي عضو.", ephemeral=True)

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تكت دعم فني", style=discord.ButtonStyle.blurple, emoji="🎫", custom_id="open_ticket_btn_v2")
    async def open_ticket(self, interaction: discord.Interaction, custom_id: str = None):
        guild = interaction.guild
        category = guild.get_category(TICKET_CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)
        owner_role = guild.get_role(OWNER_ROLE_ID)

        for ch in guild.text_channels:
            if ch.topic and str(interaction.user.id) in ch.topic:
                await interaction.response.send_message(f"❌ لديك تكت مفتوح مسبقاً: {ch.mention}", ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if owner_role:
            overwrites[owner_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
            topic=f"صاحب التكت ID: {interaction.user.id}"
        )

        embed = discord.Embed(
            title="🎫 | الدعم الفني - منتدى النظيم",
            description=f"أهلاً بك {interaction.user.mention}\nيرجى شرح مشكلتك أو طلبك بالتفصيل وسيتم خدمتك في أقرب وقت ممكن من قبل الإدارة.\n\nاستخدم الأزرار أدناه للتحكم بالتكت.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="منتدى النظيم | قسم الدعم الفني")

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
        description="إذا كنت تواجه مشكلة أو تحتاج إلى مساعدة أو استفسار، يرجى الضغط على الزر أدناه لفتح تكت خاص وسيتم التواصل معك مباشرة.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="منتدى النظيم | قسم الدعم الفني")
    
    view = TicketPanelView()
    await ctx.send(embed=embed, view=view)

# ----------------------------------------------------
# 3. نظام التقديم بالزر
# ----------------------------------------------------
class ApplyReviewView(discord.ui.View):
    def __init__(self, applicant: discord.Member, guild: discord.Guild):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.guild = guild

    @discord.ui.button(label="قبول التقديم", style=discord.ButtonStyle.green, custom_id="accept_apply_persistent_v6")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ لا تملك صلاحية قبول التقديمات.", ephemeral=True)
            return

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
                await self.applicant.remove_roles(unverified_role, reason=f"قبول التقديم بواسطة {interaction.user.name}")
            if verified_role and verified_role not in self.applicant.roles:
                await self.applicant.add_roles(verified_role, reason=f"قبول التقديم بواسطة {interaction.user.name}")
        except Exception as e:
            print(f"خطأ في تعديل رتب التقديم: {e}")

        await add_points_direct(self.guild, interaction.user, POINTS_CONFIG["apply_accept"], "قبول تقديم هوية عضو")

        embed = discord.Embed(
            title="✅ | تم قبول التقديم بنجاح",
            description=f"تم قبول العضو {self.applicant.mention} بواسطة الإداري {interaction.user.mention}\n✨ **تم سحب (غير مفعل) ومنحه رتبة (مفعل)**!",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed)
        
        try:
            await self.applicant.send(f"🎉 مبارك! تم قبول تقديمك في سيرفر **{self.guild.name}** ومنحك رتبة التفعيل.")
        except:
            pass

    @discord.ui.button(label="رفض التقديم", style=discord.ButtonStyle.red, custom_id="reject_apply_persistent_v6")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ لا تملك صلاحية رفض التقديمات.", ephemeral=True)
            return

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
            title="❌ | تم رفض التقديم",
            description=f"للأسف تم رفض تقديم العضو {self.applicant.mention} بواسطة الإداري {interaction.user.mention}\n⏳ **تم تطبيق وقت انتظار 10 دقائق قبل إمكانية التقديم مجدداً.**",
            color=discord.Color.red()
        )
        await interaction.channel.send(embed=embed)
        try:
            await self.applicant.send(f"❌ نعتذر لك، تم رفض تقديمك في سيرفر **{self.guild.name}**. يمكنك إعادة التقديم بعد مرور 10 دقائق.")
        except:
            pass

class ApplyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تقديم", style=discord.ButtonStyle.blurple, emoji="📝", custom_id="start_apply_persistent_view_v6")
    async def start_apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        cooldowns = load_cooldowns()
        
        if user_id in cooldowns:
            elapsed = time.time() - cooldowns[user_id]
            if elapsed < 600:
                remaining = int(600 - elapsed)
                mins = remaining // 60
                secs = remaining % 60
                await interaction.response.send_message(f"⏳ **عذرًا!** تم رفض تقديمك السابق، يرجى الانتظار لمدة `{mins} دقيقة و {secs} ثانية` قبل التقديم مرة أخرى.", ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)
        
        try:
            await interaction.user.send("✨ **أهلاً بك في نظام التقديم الرسمي!** يرجى الإجابة على الأسئلة التالية بدقة (سؤال بسؤال).")
        except discord.Forbidden:
            await interaction.followup.send("❌ **يرجى فتح الخاص (Direct Messages)** لتتمكن من استقبال أسئلة التقديم!", ephemeral=True)
            return

        questions = [
            "**1. اسمك ؟**",
            "**2. عمرك ؟**",
            "**3. اسم حسابك المستعار في روبلوكس ؟**",
            "**4. اسم حسابك الاساسي في روبلوكس ؟**",
            "**5. الحلف - اقسم بالله العظيم انا فلان الفلان لاخرب رولات منتدى النظيم ولا اضرهم باي شكل من الاشكال ولا ادمر سمعته (اكتب: أقسم بالله)**"
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
                await interaction.user.send("⌛ انقطعت الاستجابة بسبب التأخير. يرجى الضغط على زر التقديم من جديد في السيرفر.")
                return

        review_channel = interaction.guild.get_channel(APPLY_REVIEW_CHANNEL_ID)
        if review_channel:
            embed = discord.Embed(
                title="📥 | تقديم هوية جديد (عبر زر الخاص)",
                color=discord.Color.gold(),
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
            await review_channel.send(content=f"🔔 {admin_role_mention} يوجد تقديم هوية جديد بانتظار المراجعة!", embed=embed, view=view)
        
        await interaction.user.send("✅ **تم استلام إجاباتك وإرسالها للإدارة بنجاح!** سيتم إبلاغك فور مراجعتها.")

@bot.command(name="بانل_تقديم", aliases=["panel_apply"])
async def panel_apply(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    
    try:
        await ctx.message.delete()
    except Exception:
        pass

    embed = discord.Embed(
        title="📋 | نظام تقديم الهوية الرسمي",
        description="لتقديم طلب الحصول على الهوية وتفعيل حسابك في السيرفر، يرجى الضغط على الزر أدناه وسيتم التواصل معك مباشرة في الخاصة (DM) للإجابة على الأسئلة.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="منتدى النظيم | قسم الإدارة")
    
    view = ApplyButtonView()
    await ctx.send(embed=embed, view=view)

# ----------------------------------------------------
# 4. نظام تغيير الاسم التلقائي في روم "اسم حسابك"
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
            await member.edit(nick=new_nickname, reason="تغيير الاسم التلقائي عبر روم اسم حسابك")
            
            role_to_add = guild.get_role(NICKNAME_ROLE_ID)
            if role_to_add and role_to_add not in member.roles:
                await member.add_roles(role_to_add, reason="منح رتبة اسم حسابك تلقائياً")

            try:
                await member.send(f"✅ **تم تغيير اسمك بنجاح في سيرفر {guild.name} إلى:** `{new_nickname}` ومنحك الرتبة الخاصة.")
            except Exception:
                pass

        except Exception as e:
            print(f"خطأ في تغيير اسم العضو أو إعطائه الرتبة: {e}")

# ----------------------------------------------------
# 5. الأوامر الأساسية والإدارية
# ----------------------------------------------------

@bot.event
async def on_ready():
    bot.add_view(ApplyButtonView())
    bot.add_view(TicketPanelView())
    print(f"🚀 [ULTIMATE OP BOT - EXCLUSIVE CLAIM READY] تم تشغيل البوت بنجاح باسم: {bot.user}")

@bot.command(name="دبل_نقاط", aliases=["doublepoints", "دبل"])
async def double_points(ctx):
    global double_points_end_time
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ هذا الأمر مخصص حصرياً لأصحاب صلاحية الأدمنستريتور (Administrator) فقط.", delete_after=5)
        return

    double_points_end_time = time.time() + 3600

    embed = discord.Embed(
        title="🔥 | تم تفعيل دبل النقاط (Double Points)!",
        description=f"بواسطة الأدمن: {ctx.author.mention}\n⏳ **تم تفعيل مضاعفة النقاط (x2) لجميع الإداريين لمدة ساعة كاملة (60 دقيقة)!**",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
    await send_unified_log(ctx.guild, "🔥 | تفعيل دبل النقاط", f"قام الأدمن {ctx.author.mention} بتفعيل دبل النقاط لمدة ساعة كاملة.", discord.Color.gold())

@bot.command(name="رتبة", aliases=["giverole"])
async def give_role(ctx, member: discord.Member, role: discord.Role):
    if not ctx.author.guild_permissions.administrator:
        if ctx.author.top_role <= role:
            await ctx.send("❌ **خطأ أمني:** لا يمكنك منح رتبة تساوي أو أعلى من أعلى رتبة تمتلكها!", delete_after=6)
            return

    try:
        await member.add_roles(role)
        embed = discord.Embed(title="✅ | إدارة الرتب الفاخرة", description=f"تم بنجاح منح رتبة {role.mention} للعضو {member.mention}", color=discord.Color.green())
        await ctx.send(embed=embed)
        await send_unified_log(ctx.guild, "🛡️ | تعديل الرتب", f"الإداري {ctx.author.mention} قام بمنح رتبة {role.mention} للعضو {member.mention}")
    except discord.Forbidden:
        await ctx.send("❌ **خطأ:** لا يمتلك البوت صلاحية كافية لتعديل رتب هذا الشخص.")

@bot.command(name="سحب_رتبة", aliases=["removerole"])
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    if not ctx.author.guild_permissions.administrator:
        if ctx.author.top_role <= role:
            await ctx.send("❌ **خطأ أمني:** لا يمكنك سحب رتبة تساوي أو أعلى من أعلى رتبة تمتلكها!", delete_after=6)
            return

    try:
        await member.remove_roles(role)
        embed = discord.Embed(title="🔄 | إدارة الرتب الفاخرة", description=f"تم بنجاح سحب رتبة {role.mention} من العضو {member.mention}", color=discord.Color.orange())
        await ctx.send(embed=embed)
        await send_unified_log(ctx.guild, "🛡️ | تعديل الرتب", f"الإداري {ctx.author.mention} قام بسحب رتبة {role.mention} من العضو {member.mention}")
    except discord.Forbidden:
        await ctx.send("❌ **خطأ:** لا يمتلك البوت صلاحية كافية.")

@bot.command(name="حرمان")
async def ban_role_cmd(ctx, member: discord.Member, duration: str, *, reason: str):
    guild = ctx.guild
    ban_role = guild.get_role(BAN_ROLE_ID)
    if not ban_role:
        await ctx.send("❌ **خطأ:** لم يتم العثور على رتبة الحرمان في السيرفر.")
        return

    proof = ctx.message.attachments[0].url if ctx.message.attachments else (guild.banner.url if guild.banner else guild.icon.url if guild.icon else "لا يوجد")

    try:
        roles_to_remove = [r for r in member.roles if not r.is_default() and r.id != BAN_ROLE_ID and r < guild.me.top_role]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"عقوبة حرمان بواسطة {ctx.author.name}")
        await member.add_roles(ban_role, reason=f"تطبيق عقوبة الحرمان بواسطة {ctx.author.name}")

        ban_model_channel = guild.get_channel(BAN_MODEL_CHANNEL_ID)
        
        ban_model_msg = (
            f"__**\n"
            f"`نموذج حـرمـان  الـرول `\n\n"
            f"- اســم الإداريـ : {ctx.author.mention}\n\n"
            f"- اسـم الـشـخـص  : {member.mention}\n\n"
            f"- ســبـب الـحـرمـان : {reason}\n\n"
            f"- الـمـده : {duration}\n\n"
            f"- دلـيـل : {proof}\n"
            f"**__"
        )

        if ban_model_channel:
            await ban_model_channel.send(ban_model_msg)
            await ctx.send(f"✅ تم تنفيذ الحرمان وإرسال النموذج إلى روم **{ban_model_channel.name}** بنجاح!", delete_after=5)
        else:
            await ctx.send(ban_model_msg)

        await send_unified_log(
            guild, "🚫 | عقوبة حرمان رول", 
            f"**الإداري:** {ctx.author.mention}\n**العضو:** {member.mention}\n**المدة:** {duration}\n**السبب:** {reason}", 
            discord.Color.dark_red()
        )

        data = load_data()
        user_id = str(ctx.author.id)
        if user_id not in data or not isinstance(data[user_id], dict):
            data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
        data[user_id]["bans"] += 1
        save_data(data)

        await add_points_direct(guild, ctx.author, POINTS_CONFIG["ban"], "تطبيق عقوبة حرمان رول")

    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء تنفيذ الحرمان: {e}")

@bot.command(name="ميوت", aliases=["timeout"])
async def timeout(ctx, member: discord.Member, minutes: int, *, reason: str):
    guild = ctx.guild
    duration_delta = discord.utils.utcnow() + discord.utils.datetime.timedelta(minutes=minutes)
    
    proof = ctx.message.attachments[0].url if ctx.message.attachments else (guild.banner.url if guild.banner else guild.icon.url if guild.icon else "لا يوجد")

    try:
        await member.timeout(duration_delta, reason=reason)

        timeout_model_channel = guild.get_channel(TIMEOUT_MODEL_CHANNEL_ID)

        timeout_model_msg = (
            f"**\n"
            f"`نموذج سـجـل تـايـم `\n\n"
            f" اسـم الـاداري : {ctx.author.mention}\n\n"
            f" اسـم الشـخـص : {member.mention}\n\n"
            f"الـمـده : {minutes} دقيقة\n\n"
            f"الـسـبـب: {reason}\n\n"
            f"دلـيـل : {proof}\n"
            f"**"
        )

        if timeout_model_channel:
            await timeout_model_channel.send(timeout_model_msg)
            await ctx.send(f"✅ تم تنفيذ الميوت وإرسال النموذج إلى روم **{timeout_model_channel.name}** بنجاح!", delete_after=5)
        else:
            await ctx.send(timeout_model_msg)

        await send_unified_log(
            guild, "🔇 | عقوبة إسكات (تايم)", 
            f"**الإداري:** {ctx.author.mention}\n**العضو:** {member.mention}\n**المدة:** {minutes} دقيقة\n**السبب:** {reason}", 
            discord.Color.dark_orange()
        )

        data = load_data()
        user_id = str(ctx.author.id)
        if user_id not in data or not isinstance(data[user_id], dict):
            data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
        data[user_id]["timeouts"] += 1
        save_data(data)

        await add_points_direct(guild, ctx.author, POINTS_CONFIG["timeout"], "تطبيق عقوبة تايم")

    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء تنفيذ الميوت: {e}")

@bot.command(name="تحذير", aliases=["warn"])
async def warn(ctx, member: discord.Member, *, reason="بدون سبب"):
    guild = ctx.guild
    r_warn1 = guild.get_role(WARN_1_ID)
    r_warn2 = guild.get_role(WARN_2_ID)
    r_warn3 = guild.get_role(WARN_3_ID)

    assigned_warn_name = "تحذير أول"
    duration_text = "ثلاث ايام"
    try:
        if r_warn2 in member.roles:
            if r_warn2: await member.remove_roles(r_warn2)
            if r_warn3: await member.add_roles(r_warn3)
            assigned_warn_name = "تحذير ثالث"
            duration_text = "٧ ايام"
        elif r_warn1 in member.roles:
            if r_warn1: await member.remove_roles(r_warn1)
            if r_warn2: await member.add_roles(r_warn2)
            assigned_warn_name = "تحذير ثاني"
            duration_text = "خمس ايام"
        else:
            if r_warn1: await member.add_roles(r_warn1)
            assigned_warn_name = "تحذير أول"
            duration_text = "ثلاث ايام"
    except Exception as e:
        print(f"خطأ في تبديل رتب التحذيرات: {e}")

    proof = ctx.message.attachments[0].url if ctx.message.attachments else (guild.banner.url if guild.banner else guild.icon.url if guild.icon else ctx.author.display_avatar.url)

    embed = discord.Embed(
        title="⚠️ | تنبيه وتحذير إداري",
        description=f"تم تحذير العضو {member.mention}\n📌 **الرتبة المطبقة:** `{assigned_warn_name}`\n📝 **السبب:** {reason}",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

    warn_channel = guild.get_channel(WARN_CHANNEL_ID)
    if warn_channel:
        warning_msg = (
            f"__**\n"
            f"`نموذج التحذيرات`\n\n"
            f"- اسـم الـاداري : {ctx.author.mention}\n\n"
            f"- اســم الـشـخـص : {member.mention}\n\n"
            f"- الـتـحـذيـر رقـم كـم : {assigned_warn_name}\n\n"
            f"- الـمـده : {duration_text}\n\n"
            f"- الـسبب: {reason}\n\n"
            f"- دلـيـل : {proof}\n"
            f"**__"
        )
        await warn_channel.send(warning_msg)

    await send_unified_log(
        guild, "⚠️ | تحذير إداري جديد", 
        f"**الإداري:** {ctx.author.mention}\n**العضو:** {member.mention}\n**النوع:** {assigned_warn_name}\n**السبب:** {reason}", 
        discord.Color.red()
    )

    data = load_data()
    user_id = str(ctx.author.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
    data[user_id]["warns"] += 1
    save_data(data)

    await add_points_direct(guild, ctx.author, POINTS_CONFIG["warn"], "إعطاء تحذير إداري")

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

@bot.command(name="إغلاق", aliases=["اغلاق", "close"])
async def close(ctx):
    channel_name = ctx.channel.name.lower()
    if not any(k in channel_name for k in ["ticket", "تكت", "الدعم", "support"]):
        await ctx.send("⚠️ **حماية:** لا يمكن استخدام أمر الإغلاق هنا!")
        return

    await ctx.send("🔒 جاري أرشيف وإغلاق التكت بنجاح...")
    await add_points_direct(ctx.guild, ctx.author, POINTS_CONFIG["ticket"], "إغلاق تكت وإنجاز")
    await ctx.channel.delete()

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

    embed = discord.Embed(title=f"🛡️ | بروفايل الإداري: {target.name}", color=discord.Color.blurple())
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="📊 النقاط", value=f"`{pts}` نقطة", inline=True)
    embed.add_field(name="🎫 التكتات والتقديمات", value=f"`{tickets}` إنجاز", inline=True)
    embed.add_field(name="⚠️️ التحذيرات", value=f"`{warns}` تحذير", inline=True)
    embed.add_field(name="🔇 الميوتات", value=f"`{timeouts}` مرة", inline=True)
    embed.add_field(name="🔨 الباندات", value=f"`{bans}` باند", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="نقاط", aliases=["points"])
async def points(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_data()
    user_info = data.get(str(target.id), 0)
    pts = user_info["points"] if isinstance(user_info, dict) else user_info
    embed = discord.Embed(title="📊 | استعلام النقاط", description=f"نقاط الإداري {target.mention} الحالية هي: **{pts}** نقطة.", color=discord.Color.blue())
    embed.set_thumbnail(url=target.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="إضافة_نقاط", aliases=["addpoints"])
async def addpoints(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        return
    data = load_data()
    user_id = str(member.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
    data[user_id]["points"] += amount
    save_data(data)
    await ctx.send(f"✨ تم إضافة `{amount}` نقطة لـ {member.mention}")
    
    await send_unified_log(
        ctx.guild, "✨ | إضافة نقاط إدارية", 
        f"بواسطة الإداري {ctx.author.mention} تم إضافة `{amount}` نقطة للإداري {member.mention}",
        discord.Color.green()
    )
    
    await check_and_promote(ctx, member, data[user_id]["points"])

@bot.command(name="خصم_نقاط", aliases=["removepoints"])
async def removepoints(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        return
    data = load_data()
    user_id = str(member.id)
    if user_id in data and isinstance(data[user_id], dict):
        data[user_id]["points"] = max(0, data[user_id]["points"] - amount)
        save_data(data)
        await ctx.send(f"📉 تم خصم `{amount}` نقطة من {member.mention}.")
        
        await send_unified_log(
            ctx.guild, "📉 | خصم نقاط إدارية", 
            f"بواسطة الإداري {ctx.author.mention} تم خصم `{amount}` نقطة من الإداري {member.mention}",
            discord.Color.orange()
        )
    else:
        await ctx.send("❌ هذا العضو ليس لديه نقاط مسجلة.")

@bot.command(name="تصفير_نقاط", aliases=["resetpoints"])
async def resetpoints(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.administrator:
        return
    data = load_data()
    user_id = str(member.id)
    if user_id in data:
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
        save_data(data)
        await ctx.send(f"🔄 تم تصفير نقاط الإداري {member.mention}.")
        
        await send_unified_log(
            ctx.guild, "🔄 | تصفير نقاط إداري", 
            f"بواسطة الإداري {ctx.author.mention} تم تصفير نقاط الإداري {member.mention}",
            discord.Color.red()
        )

@bot.command(name="توب", aliases=["leaderboard", "top"])
async def leaderboard(ctx):
    data = load_data()
    if not data:
        await ctx.send("📊 لا توجد بيانات كافية.")
        return

    sorted_users = []
    for user_id, info in data.items():
        pts = info["points"] if isinstance(info, dict) else info
        sorted_users.append((int(user_id), pts))
    sorted_users.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title="🏆 | لوحة الشرف وصدارة الإداريين", color=discord.Color.gold())
    description = ""
    for index, (uid, pts) in enumerate(sorted_users[:10], start=1):
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"`#{index}`"
        description += f"{medal} <@{uid}> — **{pts}** نقطة\n"
    embed.description = description
    await ctx.send(embed=embed)

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
