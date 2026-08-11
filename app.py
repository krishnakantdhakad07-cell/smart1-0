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

# 1. API Key Setup
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 🗄️ NAYA DATABASE SYSTEM (Sabke passwords save karne ke liye)
DB_FILE = "users.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    # Agar file nahi hai, toh Admin (Krishnkant) ka account bana do
    default_db = {"krishnkant": {"password": "admin", "role": "admin", "status": "active"}}
    save_db(default_db)
    return default_db

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

# 🧠 MULTI-USER MEMORY ENGINE (Sabki baatein alag-alag yaad rakhega)
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

# --- MAIN BRAIN (Ab isme username bhi pass hoga) ---
def smart1_0_ultimate(audio_file, text_input, image_input, current_user):
    # Agar koi bina login kiye yahan tak aa gaya
    if not current_user:
        return text_input, "Security Alert: Kripya pehle login karein!", None, None

    # User ka personal dimaag nikalo
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

    # 🎨 DIRECT RAM LOGIC
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

    # 🧠 STRICT CREATOR IDENTITY PROMPT 
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
def login_logic(username, password):
    db = load_db()
    if username in db:
        if db[username]["password"] == password:
            if db[username]["status"] == "banned":
                return gr.update(value="❌ Admin ne aapka account Terminate kar diya hai!"), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), None
            # Login Success!
            if db[username]["role"] == "admin":
                # Admin ko Admin Panel dikhao
                return gr.update(value=f"✅ Welcome Boss {username}!"), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), username
            else:
                # Normal user ko sirf app dikhao
                return gr.update(value=f"✅ Welcome {username}!"), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), username
    return gr.update(value="❌ Galat Username ya Password!"), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), None

def register_logic(username, password):
    db = load_db()
    if username == "" or password == "":
        return "❌ Khali naam ya password nahi chalega!"
    if username in db:
        return "❌ Yeh username pehle se kisi ne le liya hai!"
    
    # Naya user save karo
    db[username] = {"password": password, "role": "user", "status": "active"}
    save_db(db)
    return f"✅ Account Ban Gaya! Ab upar se Login karo."

def ban_user(target_user):
    db = load_db()
    if target_user not in db:
        return "❌ Yeh user system mein nahi hai."
    if db[target_user]["role"] == "admin":
        return "❌ Boss ko ban nahi kar sakte!"
    
    db[target_user]["status"] = "banned"
    save_db(db)
    return f"🚫 User '{target_user}' ko hamesha ke liye Terminate kar diya gaya hai!"

def logout_logic():
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), None

# --- 🎨 NAYA FUTURISTIC UI DESIGN (With Auth Screens) ---
custom_theme = gr.themes.Soft(primary_hue="cyan", secondary_hue="blue", neutral_hue="slate", font=[gr.themes.GoogleFont('Orbitron'), 'ui-sans-serif', 'system-ui', 'sans-serif'])

with gr.Blocks(title="Smart1/0 Ultimate", theme=custom_theme) as demo:
    
    # Yeh variable yaad rakhega ki kaunsa user chal raha hai
    current_user_state = gr.State(None)

    gr.Markdown("<h1 style='text-align: center; color: #00d2ff;'>🤖 Project Smart1/0</h1>")
    gr.Markdown("<p style='text-align: center;'><b>Created by Krishnkant</b> | Professional Multi-User System 🛡️</p>")
    
    # ---------------- 1. LOGIN & SIGNUP SCREEN ----------------
    with gr.Group(visible=True) as auth_screen:
        with gr.Row():
            with gr.Column(scale=1, variant="panel"):
                gr.Markdown("### 🔑 S.H.I.E.L.D. Login Panel")
                auth_msg = gr.Markdown("")
                with gr.Tab("Login"):
                    log_user = gr.Textbox(label="Username")
                    log_pass = gr.Textbox(label="Password", type="password")
                    login_btn = gr.Button("Login 🚀", variant="primary")
                
                with gr.Tab("Naya Account Banao"):
                    reg_user = gr.Textbox(label="Naya Username")
                    reg_pass = gr.Textbox(label="Naya Password", type="password")
                    reg_btn = gr.Button("Sign Up 📝")
                    reg_msg = gr.Markdown("")

    # ---------------- 2. MAIN AI APP SCREEN ----------------
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
                gr.Markdown("### 📤 Smart1/0 Output")
                out_input = gr.Textbox(label="Aapki Command:")
                out_text = gr.Textbox(label="📝 Jawab:", lines=4)
                out_audio = gr.Audio(label="🔊 Suniye:", autoplay=True)
                out_image = gr.Image(label="🎨 Art Gallery", type="pil")
        
        logout_btn = gr.Button("🚪 Logout", variant="stop")

    # ---------------- 3. ADMIN PANEL SCREEN (Only for Krishnkant) ----------------
    with gr.Group(visible=False) as admin_screen:
        gr.Markdown("---")
        with gr.Row():
            with gr.Column(variant="panel"):
                gr.Markdown("<h3 style='color: red;'>⚠️ BOSS CONTROL ROOM (Terminate Users)</h3>")
                target_user = gr.Textbox(label="Kisko Ban karna hai? (Username type karein)")
                ban_btn = gr.Button("🚫 TERMINATE USER", variant="stop")
                ban_msg = gr.Textbox(label="Status")

    # --- BUTTON CONNECTIONS ---
    
    # Registration
    reg_btn.click(register_logic, [reg_user, reg_pass], reg_msg)
    
    # Login (Updates visibility of screens)
    login_btn.click(
        login_logic, 
        [log_user, log_pass], 
        [auth_msg, auth_screen, app_screen, admin_screen, current_user_state]
    )
    
    # Logout
    logout_btn.click(
        logout_logic,
        inputs=[],
        outputs=[auth_screen, app_screen, admin_screen, current_user_state]
    )

    # Main AI Trigger (Ab current_user_state bhi jayega dimaag mein)
    btn.click(
        smart1_0_ultimate, 
        [in_audio, in_text, in_img, current_user_state], 
        [out_input, out_text, out_audio, out_image]
    )
    
    # Admin Ban Button
    ban_btn.click(ban_user, [target_user], ban_msg)

if __name__ == "__main__":
    # Ab Gradio ka default auth hata diya hai kyunki humne khudka professional auth banaya hai!
    demo.launch(server_name="0.0.0.0", server_port=7860)
