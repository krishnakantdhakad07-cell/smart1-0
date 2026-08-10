import os
import gradio as gr
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
import requests
import urllib.parse

# API Key Setup
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 🌍 1. WEATHER API
def mausam_batao(shahar="Gwalior"):
    try:
        url = f"https://wttr.in/{shahar}?format=%l+mein+mausam+%C+hai+aur+temperature+%t+hai.&m"
        res = requests.get(url)
        if res.status_code == 200: return res.text
    except: pass
    return "Mausam ka data nahi mil paaya."

# 📰 2. NEWS API (Tech News)
def khabrein_batao():
    try:
        url = "https://saurav.tech/NewsAPI/top-headlines/category/technology/in.json"
        res = requests.get(url).json()
        articles = res.get("articles", [])[:3]
        news = [f"{i+1}. {a['title']}" for i, a in enumerate(articles)]
        return "\n".join(news)
    except: return "Khabrein load nahi ho paayin."

# 💰 3. CRYPTO API
def crypto_batao():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=inr"
        res = requests.get(url).json()
        btc = res['bitcoin']['inr']
        eth = res['ethereum']['inr']
        return f"Bitcoin ka price ₹{btc} aur Ethereum ka price ₹{eth} hai."
    except: return "Crypto ka data abhi down hai."

# 😂 4. JOKE API
def joke_batao():
    try:
        url = "https://v2.jokeapi.dev/joke/Any?type=single"
        res = requests.get(url).json()
        return res.get("joke", "Mujhe abhi koi joke yaad nahi aa raha!")
    except: return "Joke load nahi hua."

# 🧠 MAIN SMART1/0 BRAIN
def smart1_0_brain(audio_file, text_input, image_input):
    user_text = ""
    generated_img_path = None
    
    # Input check
    if text_input and text_input.strip() != "":
        user_text = text_input
    elif audio_file is not None:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                user_text = recognizer.recognize_google(audio_data, language="hi-IN")
            except:
                return "Aawaaz clear nahi thi.", "Maaf karna, main sun nahi paya.", None, None
                
    if user_text == "" and image_input is not None:
        user_text = "Is photo ke baare mein batao."
    elif user_text == "" and image_input is None:
        return "Input nahi mila", "Kripya bolo, type karo ya photo upload karo!", None, None

    # 🕵️‍♂️ SMART ROUTING LOGIC (Keywords pakadna)
    extra_context = ""
    user_text_lower = user_text.lower()
    
    if "mausam" in user_text_lower or "weather" in user_text_lower:
        extra_context += f"\n[LIVE WEATHER DATA: {mausam_batao()}]"
        
    if "news" in user_text_lower or "khabar" in user_text_lower or "khabrein" in user_text_lower:
        extra_context += f"\n[LIVE NEWS DATA: {khabrein_batao()}]"
        
    if "crypto" in user_text_lower or "bitcoin" in user_text_lower or "price" in user_text_lower:
        extra_context += f"\n[LIVE CRYPTO DATA: {crypto_batao()}]"
        
    if "joke" in user_text_lower or "chutkula" in user_text_lower or "hasao" in user_text_lower:
        extra_context += f"\n[LIVE JOKE DATA: {joke_batao()}]"
        
    # 🎨 IMAGE GENERATION LOGIC
    if "photo banao" in user_text_lower or "draw" in user_text_lower or "image banao" in user_text_lower:
        try:
            safe_prompt = urllib.parse.quote(user_text)
            img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}"
            img_data = requests.get(img_url).content
            with open("generated.jpg", 'wb') as handler:
                handler.write(img_data)
            generated_img_path = "generated.jpg"
            extra_context += "\n[SYSTEM INFO: Tumne successfully photo bana kar screen par dikha di hai. User ko ye baat batao!]"
        except:
            extra_context += "\n[SYSTEM INFO: Photo banane mein error aayi.]"

    # Master Prompt
    prompt = f"""You are Smart1/0, an AI created by Krishnkant. 
    You are extremely smart, friendly, and helpful. 
    {extra_context}
    
    Whenever the user asks ANY problem, explain step-by-step in simple Hinglish (Roman Hindi).
    Include short tricks for math if possible.
    If you received LIVE DATA (Weather, News, Crypto, Joke), read it naturally to the user in Hinglish as if you just checked the internet for them.
    STRICT VOICE RULE: DO NOT use complex math symbols, markdown, or LaTeX (NO $, NO ^, NO \). Write numbers/equations in plain words.
    
    User query: {user_text}"""
    
    # AI Generation
    if image_input is not None:
        jawab = model.generate_content([prompt, image_input])
    else:
        jawab = model.generate_content(prompt)
        
    ai_reply = jawab.text
    
    # Text-to-Speech
    tts = gTTS(ai_reply, lang='hi')
    audio_path = "reply.mp3"
    tts.save(audio_path)
    
    # Notice: Ab 4 cheezein wapas ja rahi hain (Text, Jawab, Aawaaz, Aur Photo)
    return user_text, ai_reply, audio_path, generated_img_path

# App ka Ultimate Interface
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
        gr.Audio(label="🔊 Smart1/0 ki Aawaaz:", autoplay=True),
        gr.Image(type="filepath", label="🎨 Smart1/0 ki Banayi Photo (Agar mangi gayi ho)")
    ],
    title="Smart1/0 BY KK 🌤️",
    description="Created by Krishnkant | Ultimate Version: Mausam, Khabrein, Crypto, aur AI Image Generation!"
)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
