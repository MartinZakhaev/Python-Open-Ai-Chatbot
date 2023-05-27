import openai
from gtts import gTTS
from io import BytesIO
from IPython.display import Audio
from flask import Flask, render_template, request, jsonify

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
    # fp = BytesIO()
    # tts_res = gTTS(text=response, lang="id")
    # tts_res.write_to_fp(fp)
    # fp.seek(0)
    # return Audio(fp.read(), autoplay=True)
    # fp.close()
    return response
    # return get_chat_response(input)

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