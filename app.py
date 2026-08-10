import os
import gradio as gr
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
from PIL import Image
import requests # NAYI LIBRARY INTERNET KE LIYE

# API Key Setup
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 🌤️ NAYA FUNCTION: Live Mausam Laane Ke Liye
def mausam_batao(shahar="Gwalior"):
    try:
        # Humne &m laga diya hai taaki Celsius mein aaye
        url = f"https://wttr.in/{shahar}?format=%l+mein+mausam+%C+hai+aur+temperature+%t+hai.&m"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return ""
    except:
        return ""

def smart1_0_brain(audio_file, text_input, image_input):
    user_text = ""
    
    # Input check karna
    if text_input and text_input.strip() != "":
        user_text = text_input
    elif audio_file is not None:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                user_text = recognizer.recognize_google(audio_data, language="hi-IN")
            except:
                return "Aawaaz clear nahi thi.", "Maaf karna, main sun nahi paya.", None
                
    if user_text == "" and image_input is not None:
        user_text = "Is photo mein jo problem ya object hai, uske baare mein batao."
    elif user_text == "" and image_input is None:
        return "Input nahi mila", "Kripya bolo, type karo ya photo upload karo!", None

    # 🧠 NAYA LOGIC: Agar user ne Mausam/Weather pucha hai, toh live data le aao
    extra_context = ""
    user_text_lower = user_text.lower()
    
    if "mausam" in user_text_lower or "weather" in user_text_lower:
        live_data = mausam_batao("Gwalior") # Abhi default Gwalior rakha hai
        extra_context = f"\n[CRITICAL INFO: Internet se live weather data aa gaya hai: '{live_data}'. Is data ka use karke user ko natural tarike se jawab do.]\n"

    # Master Prompt
    prompt = f"""You are Smart1/0, an AI created by Krishnkant. 
    You are an extremely smart but very friendly tutor and assistant. {extra_context}
    
    Whenever the user asks ANY Math, Science, or logical problem:
    1. EXPLANATION: Explain step-by-step in very simple Hinglish (Roman Hindi).
    2. SHORT TRICK: Include a quick shortcut method if possible.
    
    STRICT VOICE RULE: DO NOT use complex symbols, markdown, or LaTeX. Write equations in plain English words so a Text-to-Speech engine can speak them.
    
    User query: {user_text}"""
    
    # AI se Jawab Mangna
    if image_input is not None:
        jawab = model.generate_content([prompt, image_input])
    else:
        jawab = model.generate_content(prompt)
        
    ai_reply = jawab.text
    
    # Text-to-Speech
    tts = gTTS(ai_reply, lang='hi')
    audio_path = "reply.mp3"
    tts.save(audio_path)
    
    return user_text, ai_reply, audio_path

app = gr.Interface(
    fn=smart1_0_brain,
    inputs=[
        gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Boliye"),
        gr.Textbox(label="⌨️ Type karein"),
        gr.Image(sources=["webcam", "upload"], type="pil", label="👁️ E.D.I.T.H.")
    ],
    outputs=[
        gr.Textbox(label="Aapka Input:"), 
        gr.Textbox(label="📝 Smart1/0 ka Text Jawab:"), 
        gr.Audio(label="🔊 Smart1/0 ki Aawaaz:", autoplay=True)
    ],
    title="Smart1/0 CODE BY KRISHNKANT",
    description="Created by Krishnkant | Weather Update Live!"
)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
