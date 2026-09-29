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
    return "Staffbot Ultimate OP 24/7 with Custom Ban & Timeout Templates is Active!"

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

NOTIFICATION_CHANNEL_ID = 1553848524205072474
LOG_CHANNEL_ID = 1553913719128588389

APPLY_SUBMIT_CHANNEL_ID = 1543072562538618930   
APPLY_REVIEW_CHANNEL_ID = 1543073109496692737   
WARN_CHANNEL_ID = 1543647851953791179           
ADMIN_ROLE_PENG_ID = 1545520633939624006        

UNVERIFIED_ROLE_ID = 1545695261446250516      
VERIFIED_ROLE_ID = 1545516954754875523        
BAN_ROLE_ID = 1543325398761345175             

WARN_1_ID = 1543278808583372901
WARN_2_ID = 1543278965857198271
WARN_3_ID = 1543279133164048576

POINTS_CONFIG = {
    "ticket": 10,
    "warn": 10,
    "timeout": 10,
    "ban": 10,
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

async def check_and_promote(ctx_or_guild, member: discord.Member, current_pts: int):
    guild = ctx_or_guild.guild if hasattr(ctx_or_guild, 'guild') else ctx_or_guild
    notif_channel = guild.get_channel(NOTIFICATION_CHANNEL_ID)
    
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

                if notif_channel:
                    msg = (
                        f"🎉 **ترقية إدارية وتصفير نقاط:**\n"
                        f"وصل الإداري {member.mention} وتمت ترقيته إلى الرتبة الجديدة `{target_role.name}` ضمن **{role_category_name}**!\n"
                        f"🔄 **ملاحظة:** تم سحب رتبته القديمة وتصفير نقاطه بنجاح."
                    )
                    await notif_channel.send(msg)
            except Exception as e:
                print(f"خطأ أثناء منح الترقية وسحب القديمة: {e}")

async def add_points_direct(guild, staff: discord.Member, points_amount: int, action_name: str):
    data = load_data()
    user_id = str(staff.id)

    if user_id not in data or not isinstance(data[user_id], dict):
        old_pts = data.get(user_id, 0) if isinstance(data.get(user_id), int) else 0
        data[user_id] = {"points": old_pts, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}

    user_data = data[user_id]
    user_data["points"] = user_data.get("points", 0) + points_amount
    current_pts = user_data["points"]

    if "تقديم" in action_name:
        user_data["tickets"] = user_data.get("tickets", 0) + 1

    save_data(data)
    await check_and_promote(guild, staff, current_pts)

# ----------------------------------------------------
# 2. نظام التقديم بالزر (يفتح في الخاص سؤال بسؤال)
# ----------------------------------------------------
class ApplyReviewView(discord.ui.View):
    def __init__(self, applicant: discord.Member, guild: discord.Guild):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.guild = guild

    @discord.ui.button(label="قبول التقديم", style=discord.ButtonStyle.green, custom_id="accept_apply_dm_v6")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ لا تملك صلاحية قبول التقديمات.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        unverified_role = self.guild.get_role(UNVERIFIED_ROLE_ID)
        verified_role = self.guild.get_role(VERIFIED_ROLE_ID)

        try:
            if unverified_role and unverified_role in self.applicant.roles:
                await self.applicant.remove_roles(unverified_role, reason=f"قبول التقديم بواسطة {interaction.user.name}")
            if verified_role and verified_role not in self.applicant.roles:
                await self.applicant.add_roles(verified_role, reason=f"قبول التقديم بواسطة {interaction.user.name}")
        except Exception as e:
            print(f"خطأ في تعديل رتب التقديم: {e}")

        await add_points_direct(self.guild, interaction.user, POINTS_CONFIG["apply_accept"], "قبول تقديم عضو")

        embed = discord.Embed(
            title="✅ | تم قبول التقديم بنجاح",
            description=f"تم قبول العضو {self.applicant.mention} بواسطة الإداري {interaction.user.mention}\n✨ **تم سحب (غير مفعل) ومنحه رتبة (مفعل)**، وإضافة 10 نقاط للإداري!",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed)
        
        try:
            await self.applicant.send(f"🎉 مبارك! تم قبول تقديمك في سيرفر **{self.guild.name}** ومنحك رتبة التفعيل.")
        except:
            pass

    @discord.ui.button(label="رفض التقديم", style=discord.ButtonStyle.red, custom_id="reject_apply_dm_v6")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator and not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
            await interaction.response.send_message("❌ لا تملك صلاحية رفض التقديمات.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
        embed = discord.Embed(
            title="❌ | تم رفض التقديم",
            description=f"للأسف تم رفض تقديم العضو {self.applicant.mention} بواسطة الإداري {interaction.user.mention}.",
            color=discord.Color.red()
        )
        await interaction.channel.send(embed=embed)
        try:
            await self.applicant.send(f"❌ نعتذر لك، تم رفض تقديمك في سيرفر **{self.guild.name}**.")
        except:
            pass

class ApplyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تقديم", style=discord.ButtonStyle.blurple, emoji="📝", custom_id="start_apply_persistent_btn_v4")
    async def start_apply(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    
    await ctx.message.delete()
    embed = discord.Embed(
        title="📋 | نظام تقديم الهوية الرسمي",
        description="لتقديم طلب الحصول على الهوية وتفعيل حسابك في السيرفر، يرجى الضغط على الزر أدناه وسيتم التواصل معك مباشرة في الخاصة (DM) للإجابة على الأسئلة.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="منتدى النظيم | قسم الإدارة")
    
    view = ApplyButtonView()
    await ctx.send(embed=embed, view=view)

# ----------------------------------------------------
# 3. الأوامر الأساسية والإدارية
# ----------------------------------------------------

@bot.event
async def on_ready():
    bot.add_view(ApplyButtonView())
    print(f"🚀 [ULTIMATE OP BOT - CUSTOM BAN & TIMEOUT] تم تشغيل البوت بنجاح باسم: {bot.user}")

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
    except discord.Forbidden:
        await ctx.send("❌ **خطأ:** لا يمتلك البوت صلاحية كافية.")

@bot.command(name="حرمان")
async def ban_role_cmd(ctx, member: discord.Member, duration: str, *, reason: str):
    guild = ctx.guild
    ban_role = guild.get_role(BAN_ROLE_ID)
    if not ban_role:
        await ctx.send("❌ **خطأ:** لم يتم العثور على رتبة الحرمان في السيرفر.")
        return

    # استخراج الدليل (الصورة أو الرابط إن وجد مع الرسالة)
    proof = ctx.message.attachments[0].url if ctx.message.attachments else "لا يوجد"

    try:
        roles_to_remove = [r for r in member.roles if not r.is_default() and r.id != BAN_ROLE_ID and r < guild.me.top_role]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"عقوبة حرمان بواسطة {ctx.author.name}")
        await member.add_roles(ban_role, reason=f"تطبيق عقوبة الحرمان بواسطة {ctx.author.name}")

        # إرسال النموذج المطلوب بالصيغة بالحرف الواحد
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
        await ctx.send(ban_model_msg)
        await send_log(ctx, title="🚫 | سجل الحرمان", description=f"**العضو:** {member.mention}\n**بواسطة:** {ctx.author.mention}\n**المدة:** {duration}\n**السبب:** {reason}", color=discord.Color.dark_red())

        # إضافة النقاط للإداري
        data = load_data()
        user_id = str(ctx.author.id)
        if user_id not in data or not isinstance(data[user_id], dict):
            data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
        data[user_id]["points"] += POINTS_CONFIG["ban"]
        data[user_id]["bans"] += 1
        save_data(data)
        await check_and_promote(ctx, ctx.author, data[user_id]["points"])

    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء تنفيذ الحرمان: {e}")

@bot.command(name="ميوت", aliases=["timeout"])
async def timeout(ctx, member: discord.Member, minutes: int, *, reason: str):
    duration_delta = discord.utils.utcnow() + discord.utils.datetime.timedelta(minutes=minutes)
    
    # استخراج الدليل (الصورة أو الرابط إن وجد)
    proof = ctx.message.attachments[0].url if ctx.message.attachments else "لا يوجد"

    try:
        await member.timeout(duration_delta, reason=reason)

        # إرسال نموذج سجل تايم المطلوب بالصيغة بالحرف الواحد
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
        await ctx.send(timeout_model_msg)

        # إضافة النقاط للإداري
        data = load_data()
        user_id = str(ctx.author.id)
        if user_id not in data or not isinstance(data[user_id], dict):
            data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
        data[user_id]["points"] += POINTS_CONFIG["timeout"]
        data[user_id]["timeouts"] += 1
        save_data(data)
        await check_and_promote(ctx, ctx.author, data[user_id]["points"])

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
            f"- دلـيـل : {ctx.author.mention}\n"
            f"**__"
        )
        await warn_channel.send(warning_msg)

    data = load_data()
    user_id = str(ctx.author.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
    data[user_id]["points"] += POINTS_CONFIG["warn"]
    data[user_id]["warns"] += 1
    save_data(data)
    await check_and_promote(ctx, ctx.author, data[user_id]["points"])

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
    data = load_data()
    user_id = str(ctx.author.id)
    if user_id not in data or not isinstance(data[user_id], dict):
        data[user_id] = {"points": 0, "tickets": 0, "warns": 0, "timeouts": 0, "bans": 0}
    data[user_id]["points"] += POINTS_CONFIG["ticket"]
    data[user_id]["tickets"] += 1
    save_data(data)
    await check_and_promote(ctx, ctx.author, data[user_id]["points"])
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
    embed.add_field(name="⚠️ التحذيرات", value=f"`{warns}` تحذير", inline=True)
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
