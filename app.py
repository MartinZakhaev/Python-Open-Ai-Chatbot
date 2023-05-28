import os
import openai
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
from playsound import playsound
from flask import Flask, render_template, request, jsonify

sr.__version__

app = Flask(__name__)

openai.api_key = "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"

messages = [{"role": "system", "content": "Kamu adalah seorang ahli yang mempunyai spesialisasi dalam bidang perbaikan printer"}]

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    input = msg
    response = get_chat_response(input)
    tts_res = gTTS(text=response, lang="id")
    tts_res.save("res.mp3")
    def play_sound():
        playsound("res.mp3")
        os.remove("res.mp3")
    return response, play_sound()

@app.route("/get-mic-input")
def mic_input():
    r = sr.Recognizer()
    sr.Microphone()
    with sr.Microphone() as source:
        print("Ucapkan sesuatu...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio, language="id-ID")
        # print("Anda mengucapkan:", text)
        return jsonify({"text": text})
    except sr.UnknownValueError:
        print('Audio unintelligible')
    except sr.RequestError as e:
        print("Cannot obtain result: {0}".format(e))
    

def get_chat_response(user_input):
    messages.append({"role": "user", "content": user_input})
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = messages
    )
    bot_reply = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": bot_reply})
    text = bot_reply
    return bot_reply

if __name__ == "__main__":
    app.run()