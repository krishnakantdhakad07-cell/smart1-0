import os
import json
import gradio as gr
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
import requests
import urllib.parse
import io
from PIL import Image
import re 

# 1. API Key Setup
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 🗄️ DATABASE SYSTEM
DB_FILE = "users.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    default_db = {
        "krishnkant": {
            "password": "admin", 
            "pin": "0000", 
            "email": "admin@gmail.com", 
            "mobile": "0000000000", 
            "dob": "01/01/2000",
            "role": "admin", 
            "status": "active"
        }
    }
    save_db(default_db)
    return default_db

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def get_all_users():
    db = load_db()
    user_list = "### 📋 Registered Users KYC List:\n\n"
    for u, details in db.items():
        status_emoji = "🟢" if details.get('status', 'active') == "active" else "🔴"
        role_emoji = "👑" if details.get('role', 'user') == "admin" else "👤"
        
        email = details.get('email', 'N/A')
        mobile = details.get('mobile', 'N/A')
        dob = details.get('dob', 'N/A')
        
        user_list += f"{status_emoji} **{u}** | Role: {role_emoji} {details.get('role', 'user').upper()} | Status: {details.get('status', 'active').upper()}\n"
        user_list += f"📧 **Email:** {email} | 📱 **Mobile:** {mobile} | 🎂 **DOB:** {dob}\n"
        user_list += "---\n" 
    return user_list

# 🧠 MULTI-USER MEMORY ENGINE
user_chat_sessions = {}

def get_user_session(username):
    if username not in user_chat_sessions:
        user_chat_sessions[username] = model.start_chat(history=[])
    return user_chat_sessions[username]

# --- SARE HELPER FUNCTIONS ---
def get_weather(city="Gwalior"):
    try:
        res = requests.get(f"https://wttr.in/{city}?format=%l:+%C+%t&m")
        return res.text if res.status_code == 200 else "Data unavailable"
    except: return "Weather API Error"

def get_news():
    try:
        res = requests.get("https://saurav.tech/NewsAPI/top-headlines/category/technology/in.json").json()
        return "\n".join([f"- {a['title']}" for a in res['articles'][:3]])
    except: return "News unavailable"

# --- MAIN BRAIN ---
def smart1_0_ultimate(audio_file, text_input, image_input, current_user):
    if not current_user:
        return text_input, "Security Alert: Kripya pehle login karein!", None, None

    chat_session = get_user_session(current_user)
    user_text = ""
    ai_photo = None
    
    if text_input and text_input.strip() != "":
        user_text = text_input
    elif audio_file is not None:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                user_text = recognizer.recognize_google(audio_data, language="hi-IN")
            except: return "Sound unclear", "Maaf karna, sun nahi paya.", None, None

    if not user_text and image_input: user_text = "Is photo ko describe karo."
    if not user_text: return "No Input", "Kuch toh bolo ya likho!", None, None

    user_lower = user_text.lower()
    context = ""
    
    if "mausam" in user_lower or "weather" in user_lower:
        context += f"\n[LIVE WEATHER: {get_weather()}]"
    if "news" in user_lower or "khabar" in user_lower:
        context += f"\n[LIVE NEWS: {get_news()}]"

    image_keywords = ["banao", "draw", "photo", "image", "generate", "picture"]
    if any(word in user_lower for word in image_keywords):
        try:
            clean_prompt = urllib.parse.quote(user_text)
            img_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=1024&nologo=true&seed=42"
            response = requests.get(img_url)
            if response.status_code == 200:
                ai_photo = Image.open(io.BytesIO(response.content))
                context += "\n[SYSTEM: Photo successfully generate ho gayi hai.]"
        except:
            context += f"\n[SYSTEM: Photo generation fail ho gayi.]"

    prompt = f"""[CRITICAL SYSTEM IDENTITY: Tumhara naam 'Smart1/0' hai. Tumhe 'Krishnkant' ne banaya hai. Agar user pooche ki tumhe kisne banaya, toh tumhara STRICT jawab hona chahiye ki tumhe Krishnkant ne banaya hai.]
    [SYSTEM CONTEXT: User ka naam '{current_user}' hai. Usey uske naam se bula sakte ho. {context} 
    Rule: Be friendly. Speak in simple Hinglish. DO NOT use markdown.]
    
    User Query: {user_text}"""

    try:
        if image_input is not None:
            response = chat_session.send_message([prompt, image_input])
        else:
            response = chat_session.send_message(prompt)
        ai_text = response.text
    except:
        ai_text = "Mujhe samajh nahi aaya, kripya dobara bataiye."

    tts = gTTS(ai_text, lang='hi')
    tts.save("voice.mp3")
    
    return user_text, ai_text, "voice.mp3", ai_photo

# --- 🔒 AUTHENTICATION & ADMIN LOGIC ---
def login_logic(username, password, pin):
    db = load_db()
    if username in db:
        if db[username]["password"] == password and db[username].get("pin", "0000") == pin:
            if db[username]["status"] == "banned":
                return gr.update(value="❌ Admin ne aapka account Terminate kar diya hai!"), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), None, get_all_users()
            
            if db[username]["role"] == "admin":
                return gr.update(value=f"✅ Welcome Boss {username}!"), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), username, get_all_users()
            else:
                return gr.update(value=f"✅ Welcome {username}!"), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), username, get_all_users()
    return gr.update(value="❌ Galat Username, Password ya PIN! Access Denied."), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), None, get_all_users()

def register_logic(username, email, mobile, dob_day, dob_month, dob_year, password, pin):
    db = load_db()
    
    if not dob_day or not dob_month or not dob_year:
        return "❌ Error: Date of Birth poori select karein!"
        
    dob = f"{dob_day}/{dob_month}/{dob_year}"
    
    if not all([username, email, mobile, password, pin]):
        return "❌ Error: Sabhi fields bharna COMPULSORY hai!"
    
    # ⚠️ STRICT EMAIL VALIDATION (Sirf @gmail.com)
    if not email.endswith("@gmail.com"):
        return "❌ Error: Invalid Email! Sirf @gmail.com accounts allowed hain."
        
    # ⚠️ STRICT MOBILE VALIDATION (Sirf 10 numbers)
    if not (mobile.isdigit() and len(mobile) == 10):
        return "❌ Error: Invalid Mobile! Mobile mein sirf 10 numbers hone chahiye (koi ABCD nahi)."
        
    if len(pin) < 4:
        return "❌ Error: Security PIN kam se kam 4 digits ka hona chahiye!"
        
    if username in db:
        return "❌ Error: Yeh username pehle se kisi ne le liya hai!"
    
    db[username] = {
        "password": password, 
        "pin": pin, 
        "email": email,
        "mobile": mobile,
        "dob": dob,
        "role": "user", 
        "status": "active"
    }
    save_db(db)
    return f"✅ Account Ban Gaya! Ab Login tab par ja kar login karein."

def ban_user(target_user):
    db = load_db()
    if target_user not in db:
        return "❌ Yeh user system mein nahi hai.", get_all_users()
    if db[target_user]["role"] == "admin":
        return "❌ Boss ko ban nahi kar sakte!", get_all_users()
    db[target_user]["status"] = "banned"
    save_db(db)
    return f"🚫 User '{target_user}' ko Terminate kar diya gaya hai!", get_all_users()

def restore_user(target_user):
    db = load_db()
    if target_user not in db:
        return "❌ Yeh user system mein nahi hai.", get_all_users()
    db[target_user]["status"] = "active"
    save_db(db)
    return f"✅ User '{target_user}' ko wapas Restore kar diya gaya hai!", get_all_users()

def logout_logic():
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), None

# --- 🎨 CLEAN & PROFESSIONAL UI DESIGN ---
# Font ekdum simple, clean aur smooth kar diya hai (Apple/Google style)
custom_theme = gr.themes.Soft(
    primary_hue="blue", 
    secondary_hue="slate", 
    neutral_hue="slate", 
    font=['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
)

with gr.Blocks(title="SMART 1/0", theme=custom_theme) as demo:
    current_user_state = gr.State(None)

    # ⚠️ CLEAN BLACK BOLD HEADING WITH FIRE ICON
    gr.Markdown("<h1 style='text-align: center; color: black; font-weight: bold;'>🔥 [SMART 1/0]</h1>")
    gr.Markdown("<p style='text-align: center; color: #555;'><b>Created by Krishnkant</b> | Protected by Strict KYC & 2FA Security 🛡️</p>")
    
    with gr.Group(visible=True) as auth_screen:
        with gr.Row():
            with gr.Column(scale=1, variant="panel"):
                gr.Markdown("### 🔑 S.H.I.E.L.D. Login Panel")
                auth_msg = gr.Markdown("")
                with gr.Tab("Login"):
                    log_user = gr.Textbox(label="Username")
                    log_pass = gr.Textbox(label="Password", type="password")
                    log_pin = gr.Textbox(label="4-Digit Security PIN (2FA)", type="password", placeholder="****")
                    login_btn = gr.Button("Login 🚀", variant="primary")
                
                with gr.Tab("Naya Account Banao (Strict KYC)"):
                    reg_user = gr.Textbox(label="1. Naya Username")
                    reg_email = gr.Textbox(label="2. Email Address", placeholder="sirf @gmail.com allowed hai")
                    reg_mobile = gr.Textbox(label="3. Mobile Number", placeholder="Sirf 10 digits number")
                    
                    gr.Markdown("**4. Date of Birth (Select Karein)**")
                    with gr.Row():
                        reg_dob_day = gr.Dropdown(choices=[str(i).zfill(2) for i in range(1, 32)], label="Day", interactive=True)
                        reg_dob_month = gr.Dropdown(choices=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], label="Month", interactive=True)
                        reg_dob_year = gr.Dropdown(choices=[str(i) for i in range(2015, 1950, -1)], label="Year", interactive=True)
                        
                    reg_pass = gr.Textbox(label="5. Set Password", type="password")
                    reg_pin = gr.Textbox(label="6. Set 4-Digit Security PIN", type="password", placeholder="****")
                    
                    reg_btn = gr.Button("Sign Up 📝")
                    reg_msg = gr.Markdown("")

    with gr.Group(visible=False) as app_screen:
        gr.Markdown(f"### 🟢 System Online")
        with gr.Row():
            with gr.Column(scale=1, variant="panel"):
                gr.Markdown("### 📥 Command Center")
                in_audio = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Boliye")
                in_text = gr.Textbox(label="⌨️ Type karein")
                in_img = gr.Image(sources=["webcam", "upload"], type="pil", label="👁️ E.D.I.T.H.")
                btn = gr.Button("🚀 SYSTEM START", variant="primary")
                
            with gr.Column(scale=1, variant="panel"):
                gr.Markdown("### 📤 Output")
                out_input = gr.Textbox(label="Aapki Command:")
                out_text = gr.Textbox(label="📝 Jawab:", lines=4)
                out_audio = gr.Audio(label="🔊 Suniye:", autoplay=True)
                out_image = gr.Image(label="🎨 Art Gallery", type="pil")
        
        logout_btn = gr.Button("🚪 Logout", variant="stop")

    with gr.Group(visible=False) as admin_screen:
        gr.Markdown("---")
        with gr.Row():
            with gr.Column(variant="panel"):
                gr.Markdown("<h3 style='color: red; font-weight: bold;'>⚠️ BOSS CONTROL ROOM</h3>")
                user_list_display = gr.Markdown("Loading...")
                refresh_btn = gr.Button("🔄 Refresh List", size="sm")
                gr.Markdown("---")
                target_user = gr.Textbox(label="Action ke liye Username type karein:")
                with gr.Row():
                    ban_btn = gr.Button("🚫 TERMINATE USER", variant="stop")
                    restore_btn = gr.Button("♻️ RESTORE USER", variant="primary")
                admin_msg = gr.Textbox(label="Action Status")

    # --- BUTTON CONNECTIONS ---
    reg_btn.click(
        register_logic, 
        [reg_user, reg_email, reg_mobile, reg_dob_day, reg_dob_month, reg_dob_year, reg_pass, reg_pin], 
        reg_msg
    )
    
    login_btn.click(
        login_logic, 
        [log_user, log_pass, log_pin], 
        [auth_msg, auth_screen, app_screen, admin_screen, current_user_state, user_list_display]
    )
    
    logout_btn.click(logout_logic, inputs=[], outputs=[auth_screen, app_screen, admin_screen, current_user_state])
    btn.click(smart1_0_ultimate, [in_audio, in_text, in_img, current_user_state], [out_input, out_text, out_audio, out_image])
    
    refresh_btn.click(get_all_users, inputs=[], outputs=[user_list_display])
    ban_btn.click(ban_user, [target_user], [admin_msg, user_list_display])
    restore_btn.click(restore_user, [target_user], [admin_msg, user_list_display])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
