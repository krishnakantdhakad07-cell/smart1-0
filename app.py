import os
import gradio as gr
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
from PIL import Image

# Secret Environment Variable se key uthana
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

def smart1_0_brain(audio_file, text_input, image_input):
    user_text = ""
    
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
        user_text = "Is photo mein jo problem ya object hai, uske baare mein batao ya solve karo."
    elif user_text == "" and image_input is None:
        return "Input nahi mila", "Kripya bolo, type karo ya photo upload karo!", None

    prompt = f"""You are Smart1/0, an AI created by Krishnkant. 
    You are an extremely smart but very friendly tutor. 
    
    Whenever the user asks ANY Math, Science, or logical problem:
    1. EXPLANATION: Explain the concept step-by-step in very simple, conversational Hinglish (Roman Hindi).
    2. SHORT TRICK: Always include a 'Short Trick' or a quick shortcut method to solve the problem in seconds, if possible.
    3. STRICT VOICE RULE: DO NOT use complex math symbols, markdown, or LaTeX (NO $, NO ^, NO \). 
       Write all equations in plain English words so a Text-to-Speech engine can speak them perfectly.
    
    User query: {user_text}"""
    
    if image_input is not None:
        jawab = model.generate_content([prompt, image_input])
    else:
        jawab = model.generate_content(prompt)
        
    ai_reply = jawab.text
    
    tts = gTTS(ai_reply, lang='hi')
    audio_path = "reply.mp3"
    tts.save(audio_path)
    
    return user_text, ai_reply, audio_path

app = gr.Interface(
    fn=smart1_0_brain,
    inputs=[
        gr.Audio(sources=["microphone"], type="filepath", label="🎙️ Boliye"),
        gr.Textbox(label="⌨️ Type karein"),
        gr.Image(sources=["webcam", "upload"], type="pil", label="👁️ E.D.I.T.H. (Live Camera ya Upload)")
    ],
    outputs=[
        gr.Textbox(label="Aapka Input:"), 
        gr.Textbox(label="📝 Smart1/0 ka Text Jawab:"), 
        gr.Audio(label="🔊 Smart1/0 ki Aawaaz:", autoplay=True)
    ],
    title="Project Smart1/0 🤖👁️🎙️",
    description="Created by Krishnkant | Permanent Web Version"
)

if __name__ == "__main__":
    # Render Server ke liye Port 7860 On karna
    app.launch(server_name="0.0.0.0", server_port=7860)
