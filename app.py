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
def smart1_0_ultimate(audio_file, text_input, image_input):
    user_text = ""
    ai_photo = None
    
    # Input Handling
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

    # Keyword Detection
    user_lower = user_text.lower()
    context = ""
    
    if "mausam" in user_lower or "weather" in user_lower:
        context += f"\n[LIVE WEATHER: {get_weather()}]"
    if "news" in user_lower or "khabar" in user_lower:
        context += f"\n[LIVE NEWS: {get_news()}]"

    # 🎨 PHOTO GENERATION LOGIC (Keyword: "banao", "draw", "photo", "image")
    image_keywords = ["banao", "draw", "photo", "image", "generate", "picture"]
    if any(word in user_lower for word in image_keywords):
        try:
            # Pollinations AI use kar rahe hain (Free & No Key)
            clean_prompt = urllib.parse.quote(user_text)
            ai_photo = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=1024&nologo=true"
            context += "\n[SYSTEM: Photo successfully generate ho gayi hai aur niche box mein dikh rahi hai. User ko khushi se batao!]"
        except:
            context += "\n[SYSTEM: Photo generation fail ho gayi.]"

    # AI Instruction
    prompt = f"""You are Smart1/0, a super-AI created by Krishnkant.
    Be friendly like a brother. Use simple Hinglish.
    {context}
    
    IMPORTANT: If a photo was generated (see context), confirm it to the user.
    Don't say 'I am a text model'. You are an All-in-One AI!
    User Query: {user_text}"""

    # Generate Text
    response = model.generate_content([prompt, image_input]) if image_input else model.generate_content(prompt)
    ai_text = response.text

    # Generate Voice
    tts = gTTS(ai_text, lang='hi')
    tts.save("voice.mp3")
    
    return user_text, ai_text, "voice.mp3", ai_photo

# --- GRADIO UI (4 Output Boxes) ---
with gr.Blocks(title="Smart1/0 Ultimate") as demo:
    gr.Markdown("# 🤖 Project Smart1/0: Ultimate Super-AI")
    gr.Markdown("Created by **Krishnkant** | Mausam, Khabrein, aur AI Art!")
    
    with gr.Row():
        with gr.Column():
            in_audio = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Boliye")
            in_text = gr.Textbox(label="⌨️ Type karein")
            in_img = gr.Image(sources=["webcam", "upload"], type="pil", label="👁️ E.D.I.T.H. (Vision)")
            btn = gr.Button("Submit 🚀")
            
        with gr.Column():
            out_input = gr.Textbox(label="Aapne pucha:")
            out_text = gr.Textbox(label="📝 Smart1/0 ka Jawab:")
            out_audio = gr.Audio(label="🔊 Suniye:", autoplay=True)
            out_image = gr.Image(label="🎨 Smart1/0 ki Art Gallery") # YE RAHA PHOTO BOX!

    btn.click(smart1_0_ultimate, [in_audio, in_text, in_img], [out_input, out_text, out_audio, out_image])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
