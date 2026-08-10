import os
import gradio as gr
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
import requests
import urllib.parse

# 1. API Key Setup
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 🧠 MEMORY ENGINE
chat_session = model.start_chat(history=[])

# --- HELPER FUNCTIONS ---
def get_weather(city="Gwalior"):
    try:
        res = requests.get(f"https://wttr.in/{city}?format=%l:+%C+%t&m", timeout=5)
        return res.text if res.status_code == 200 else "Data unavailable"
    except: return "Weather API Error"

def get_news():
    try:
        res = requests.get("https://saurav.tech/NewsAPI/top-headlines/category/technology/in.json", timeout=5).json()
        return "\n".join([f"- {a['title']}" for a in res['articles'][:3]])
    except: return "News unavailable"

# --- MAIN BRAIN ---
def smart1_0_ultimate(audio_file, text_input, image_input):
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
            ai_photo = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=512&height=512&nologo=true"
        except:
            pass

    prompt = f"""[SYSTEM CONTEXT: {context} 
    Rule: Be friendly. Speak in simple Hinglish. DO NOT use markdown/complex math symbols. Write plain text for text-to-speech.]
    
    User Query: {user_text}"""

    try:
        if image_input is not None:
            response = chat_session.send_message([prompt, image_input])
        else:
            response = chat_session.send_message(prompt)
        ai_text = response.text
    except Exception as e:
        ai_text = "Mujhe samajh nahi aaya, kripya dobara bataiye."

    tts = gTTS(ai_text, lang='hi')
    tts.save("voice.mp3")
    
    return user_text, ai_text, "voice.mp3", ai_photo

# --- UI DESIGN (Clean & Safe) ---
custom_theme = gr.themes.Soft(
    primary_hue="cyan",
    secondary_hue="blue",
    neutral_hue="slate"
)

with gr.Blocks(title="Smart1/0 Ultimate", theme=custom_theme) as demo:
    gr.Markdown("<h1 style='text-align: center; color: #00d2ff;'>🤖 Project Smart1/0</h1>")
    gr.Markdown("<p style='text-align: center;'><b>Created by Krishnkant</b></p>")
    
    with gr.Row():
        with gr.Column(scale=1):
            in_audio = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Boliye")
            in_text = gr.Textbox(label="⌨️ Type karein", placeholder="Apni command yahan likhein...")
            in_img = gr.Image(sources=["webcam", "upload"], type="pil", label="👁️ E.D.I.T.H. (Vision)")
            btn = gr.Button("🚀 SYSTEM START", variant="primary")
            
        with gr.Column(scale=1):
            out_input = gr.Textbox(label="Aapki Command:")
            out_text = gr.Textbox(label="📝 Jawab:", lines=4)
            out_audio = gr.Audio(label="🔊 Suniye:", autoplay=True)
            out_image = gr.Image(label="🎨 Art Gallery")

    btn.click(smart1_0_ultimate, [in_audio, in_text, in_img], [out_input, out_text, out_audio, out_image])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, analytics_enabled=False)
