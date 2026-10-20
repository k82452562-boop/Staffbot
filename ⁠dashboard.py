import os
import json
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, session, url_for, jsonify
import requests

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "super-secret-key-nz-2026")

# بيانات البوت المالك
BOT_OWNER_ID = "917414299184533515"
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# أسماء ملفات حفظ البيانات
POINTS_FILE = "points.json"
AUTHORIZED_USERS_FILE = "authorized_users.json"
POINTS_LOGS_FILE = "points_logs.json"
PENALTY_LOGS_FILE = "penalty_logs.json"

# --- دوان مساعدة لإدارة البيانات (JSON) ---
def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_log(filepath, log_entry):
    logs = load_json(filepath, [])
    log_entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs.insert(0, log_entry)  # إضافة الأحدث في البداية
    save_json(filepath, logs)

# --- الواجهة البرمجية المتكاملة (HTML / CSS / JS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم منتدى النظيم | Admin Panel</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0b0f19;
            --bg-secondary: #151c2c;
            --card-bg: #1e293b;
            --accent-color: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --danger: #ef4444;
            --success: #22c55e;
            --warning: #f59e0b;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            margin: 0;
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar Navigation */
        .sidebar {
            width: 260px;
            background-color: var(--bg-secondary);
            padding: 20px;
            display: flex;
            flex-direction: column;
            border-left: 1px solid #334155;
        }

        .sidebar h2 {
            color: var(--accent-color);
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 30px;
        }

        .nav-link {
            color: var(--text-muted);
            text-decoration: none;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: 0.3s;
        }

        .nav-link:hover, .nav-link.active {
            background-color: #0284c7;
            color: #fff;
        }

        /* Main Content Area */
        .main-content {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 1px solid #334155;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-info img {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 2px solid var(--accent-color);
        }

        .card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }

        .card h3 {
            color: var(--accent-color);
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Forms & Inputs */
        .form-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            color: var(--text-muted);
        }

        input, select, textarea, button {
            width: 100%;
            padding: 10px 12px;
            background-color: var(--bg-primary);
            border: 1px solid #334155;
            border-radius: 6px;
            color: #fff;
            box-sizing: border-box;
        }

        button {
            background-color: #0284c7;
            font-weight: bold;
            cursor: pointer;
            border: none;
            transition: 0.2s;
            margin-top: 10px;
        }

        button:hover { background-color: #0369a1; }
        .btn-danger { background-color: var(--danger); }
        .btn-danger:hover { background-color: #dc2626; }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        th, td {
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #334155;
        }

        th { background-color: var(--bg-secondary); color: var(--accent-color); }

        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
        }
        .badge-warn { background-color: var(--warning); color: #000; }
        .badge-timeout { background-color: #eab308; color: #000; }
        .badge-ban { background-color: var(--danger); color: #fff; }

        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>

    <!-- Sidebar -->
    <div class="sidebar">
        <h2>🛡️ لوحة النظيم</h2>
        <a href="#" class="nav-link active" onclick="switchTab('points')"><i class="fa-solid fa-chart-line"></i> إدارة النقاط</a>
        <a href="#" class="nav-link" onclick="switchTab('embed')"><i class="fa-solid fa-pen-to-square"></i> صانع الإمبايد</a>
        <a href="#" class="nav-link" onclick="switchTab('logs')"><i class="fa-solid fa-list-check"></i> لوقات النقاط</a>
        <a href="#" class="nav-link" onclick="switchTab('penalties')"><i class="fa-solid fa-gavel"></i> لوق الحرمانات</a>
        {% if is_owner %}
        <a href="#" class="nav-link" onclick="switchTab('permissions')"><i class="fa-solid fa-user-shield"></i> إعطاء الصلاحيات</a>
        {% endif %}
        <a href="/logout" class="nav-link" style="margin-top: auto; color: var(--danger);"><i class="fa-solid fa-right-from-bracket"></i> تسجيل الخروج</a>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <div class="header">
            <h1>تحكم البوت الرئيسي</h1>
            <div class="user-info">
                <img src="https://cdn.discordapp.com/avatars/{{ user.id }}/{{ user.avatar }}.png" alt="Avatar">
                <div>
                    <strong>{{ user.username }}</strong>
                    <div style="font-size:0.8rem; color: var(--text-muted);">
                        {% if is_owner %}مالك البوت{% else %}عضو مصرح له{% endif %}
                    </div>
                </div>
            </div>
        </div>

        <!-- 1. تبويب النقاط -->
        <div id="points" class="tab-content active">
            <div class="card">
                <h3><i class="fa-solid fa-coins"></i> تعديل إضافة نقاط الأعضاء</h3>
                <form action="/update_points" method="POST">
                    <div class="form-group">
                        <label>ID العضو / الإداري</label>
                        <input type="text" name="target_user_id" placeholder="مثال: 917414299184533515" required>
                    </div>
                    <div class="form-group">
                        <label>عدد النقاط (موجب للإضافة / سالب للخصم)</label>
                        <input type="number" name="points_amount" placeholder="10" required>
                    </div>
                    <div class="form-group">
                        <label>سبب التعديل</label>
                        <input type="text" name="reason" placeholder="إغلاق تكت / مكافأة" required>
                    </div>
                    <button type="submit">تحديث النقاط 🚀</button>
                </form>
            </div>

            <div class="card">
                <h3><i class="fa-solid fa-users"></i> قائمة النقاط الحالية</h3>
                <table>
                    <tr>
                        <th>معرف العضو (ID)</th>
                        <th>النقاط الحالية</th>
                    </tr>
                    {% for u_id, pts in points_data.items() %}
                    <tr>
                        <td>{{ u_id }}</td>
                        <td><strong>{{ pts }}</strong> نقطة</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <!-- 2. تبويب صانع الإمبايد -->
        <div id="embed" class="tab-content">
            <div class="card">
                <h3><i class="fa-solid fa-paper-plane"></i> إرسال Embed مخصص</h3>
                <form action="/send_embed" method="POST">
                    <div class="form-group">
                        <label>ID الروم في الديسكورد</label>
                        <input type="text" name="channel_id" placeholder="123456789012345678" required>
                    </div>
                    <div class="form-group">
                        <label>عنوان الإمبايد</label>
                        <input type="text" name="embed_title" placeholder="أخبار وتحديثات السيرفر" required>
                    </div>
                    <div class="form-group">
                        <label>محتوى الرسالة / الوصف</label>
                        <textarea name="embed_desc" rows="5" placeholder="اكتب التفاصيل هنا..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label>لون الإمبايد</label>
                        <input type="color" name="embed_color" value="#38bdf8" style="height:45px; cursor:pointer;">
                    </div>
                    <button type="submit">إرسال فوراً للديسكورد 📤</button>
                </form>
            </div>
        </div>

        <!-- 3. تبويب لوقات النقاط -->
        <div id="logs" class="tab-content">
            <div class="card">
                <h3><i class="fa-solid fa-history"></i> سجل عمليات النقاط (Points Audit Log)</h3>
                <table>
                    <tr>
                        <th>الوقت</th>
                        <th>المسؤول</th>
                        <th>العضو</th>
                        <th>التغيير</th>
                        <th>السبب</th>
                    </tr>
                    {% for log in points_logs %}
                    <tr>
                        <td>{{ log.timestamp }}</td>
                        <td>{{ log.admin_name }}</td>
                        <td>{{ log.target_id }}</td>
                        <td><strong style="color: {% if log.amount > 0 %}var(--success){% else %}var(--danger){% endif %};">{{ log.amount }}</strong></td>
                        <td>{{ log.reason }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <!-- 4. تبويب لوقات الحرمانات -->
        <div id="penalties" class="tab-content">
            <div class="card">
                <h3><i class="fa-solid fa-gavel"></i> سجل الحرمانات والعقوبات</h3>
                <table>
                    <tr>
                        <th>الوقت</th>
                        <th>نوع العقوبة</th>
                        <th>العضو المخالف</th>
                        <th>الاداري المنفذ</th>
                        <th>السبب</th>
                    </tr>
                    {% for pen in penalty_logs %}
                    <tr>
                        <td>{{ pen.timestamp }}</td>
                        <td><span class="badge badge-{{ pen.type }}">{{ pen.type|upper }}</span></td>
                        <td>{{ pen.target_id }}</td>
                        <td>{{ pen.admin_name }}</td>
                        <td>{{ pen.reason }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <!-- 5. تبويب إدارة الصلاحيات (للمالك فقط) -->
        {% if is_owner %}
        <div id="permissions" class="tab-content">
            <div class="card">
                <h3><i class="fa-solid fa-user-plus"></i> إعطاء صلاحية دخول الموقع لإداري</h3>
                <form action="/grant_access" method="POST">
                    <div class="form-group">
                        <label>ID الإداري المراد إعطاؤه الصلاحية</label>
                        <input type="text" name="new_admin_id" placeholder="ID العضو" required>
                    </div>
                    <button type="submit">إضافة قائمة المصرح لهم 🔑</button>
                </form>
            </div>

            <div class="card">
                <h3><i class="fa-solid fa-users-gear"></i> الأعضاء المصرح لهم حالياً</h3>
                <table>
                    <tr>
                        <th>ID الإداري</th>
                        <th>إجراء</th>
                    </tr>
                    {% for admin_id in authorized_users %}
                    <tr>
                        <td>{{ admin_id }}</td>
                        <td>
                            <form action="/revoke_access" method="POST" style="margin:0;">
                                <input type="hidden" name="remove_id" value="{{ admin_id }}">
                                <button type="submit" class="btn-danger" style="padding: 5px 10px; margin:0; width:auto;">سحب الصلاحية ❌</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
        {% endif %}

    </div>

    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
            
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }
    </script>
</body>
</html>
"""

# --- المسارات البرمجية (Routes) ---

@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    
    user_id = session["user"]["id"]
    authorized_users = load_json(AUTHORIZED_USERS_FILE, [BOT_OWNER_ID])
    
    # التأكد من امتلاك المستخدم صلاحية الدخول
    if user_id != BOT_OWNER_ID and user_id not in authorized_users:
        return f'<div style="text-align:center; padding:50px; background:#0b0f19; color:#fff;"><h2>❌ ليس لديك صلاحية لدخول لوحة التحكم هذه!</h2><a href="/logout" style="color:#38bdf8;">تسجيل الخروج</a></div>'

    is_owner = (user_id == BOT_OWNER_ID)
    points_data = load_json(POINTS_FILE, {})
    points_logs = load_json(POINTS_LOGS_FILE, [])
    penalty_logs = load_json(PENALTY_LOGS_FILE, [])

    return render_template_string(
        HTML_TEMPLATE,
        user=session["user"],
        is_owner=is_owner,
        points_data=points_data,
        points_logs=points_logs,
        penalty_logs=penalty_logs,
        authorized_users=authorized_users
    )

@app.route("/update_points", methods=["POST"])
def update_points():
    if "user" not in session: return redirect("/login")
    
    admin_name = session["user"]["username"]
    target_id = request.form.get("target_user_id")
    amount = int(request.form.get("points_amount", 0))
    reason = request.form.get("reason", "تعديل عبر الموقع")

    # تحديث النقاط
    points_data = load_json(POINTS_FILE, {})
    points_data[target_id] = points_data.get(target_id, 0) + amount
    save_json(POINTS_FILE, points_data)

    # تسجيل اللوق
    add_log(POINTS_LOGS_FILE, {
        "admin_name": admin_name,
        "target_id": target_id,
        "amount": amount,
        "reason": reason
    })

    return redirect("/")

@app.route("/send_embed", methods=["POST"])
def send_embed():
    if "user" not in session: return redirect("/login")
    
    channel_id = request.form.get("channel_id")
    title = request.form.get("embed_title")
    desc = request.form.get("embed_desc")
    color = int(request.form.get("embed_color", "#38bdf8").replace("#", ""), 16)

    # إرسال الرسالة عبر Discord REST API مباشر بدون الحاجة للبوت
    headers = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "embeds": [{
            "title": title,
            "description": desc,
            "color": color,
            "footer": {"text": f"تم الإرسال بواسطة: {session['user']['username']}"}
        }]
    }
    requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages", json=payload, headers=headers)

    return redirect("/")

@app.route("/grant_access", methods=["POST"])
def grant_access():
    if session.get("user", {}).get("id") != BOT_OWNER_ID: return "غير مصرح", 403
    
    new_admin_id = request.form.get("new_admin_id")
    authorized_users = load_json(AUTHORIZED_USERS_FILE, [BOT_OWNER_ID])
    
    if new_admin_id not in authorized_users:
        authorized_users.append(new_admin_id)
        save_json(AUTHORIZED_USERS_FILE, authorized_users)

    return redirect("/")

@app.route("/revoke_access", methods=["POST"])
def revoke_access():
    if session.get("user", {}).get("id") != BOT_OWNER_ID: return "غير مصرح", 403
    
    remove_id = request.form.get("remove_id")
    authorized_users = load_json(AUTHORIZED_USERS_FILE, [BOT_OWNER_ID])
    
    if remove_id in authorized_users and remove_id != BOT_OWNER_ID:
        authorized_users.remove(remove_id)
        save_json(AUTHORIZED_USERS_FILE, authorized_users)

    return redirect("/")

@app.route("/login")
def login():
    discord_url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"
    return redirect(discord_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers)
    access_token = r.json().get('access_token')
    
    user_req = requests.get('https://discord.com/api/v10/users/@me', headers={'Authorization': f'Bearer {access_token}'})
    session["user"] = user_req.json()
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
