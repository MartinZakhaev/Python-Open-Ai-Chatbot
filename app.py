import os
import string
import re
import nltk
import openai
import speech_recognition as sr
import re
import spacy
from nltk.tokenize import sent_tokenize, word_tokenize
from gtts import gTTS
from io import BytesIO
from playsound import playsound
from flask import Flask, render_template, request, jsonify
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
from nltk.tag import CRFTagger
from flair.embeddings import TokenEmbeddings, WordEmbeddings, StackedEmbeddings, BertEmbeddings
from typing import List
# from flair.data_fetcher import NLPTaskDataFetcher, NLPTask
# corpus = NLPTaskDataFetcher.load_corpus(NLPTask.UD_INDONESIAN)

nltk.download("punkt")
nltk.download("stopwords")
nltk.download("averaged_perceptron_tagger")

nlp = spacy.load('en_core_web_sm')

ct = CRFTagger()
ct.set_model_file("all_indo_man_tag_corpus_model.crf.tagger")

sr.__version__

app = Flask(__name__)

openai.api_key = "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"

messages = [{"role": "system", "content": "Kamu adalah seorang ahli yang mempunyai spesialisasi dalam bidang perbaikan printer"}]

stemmer = SnowballStemmer("english")

thematic_roles = ['AGENT', 'THEME', 'INSTRUMENT', 'BENEFICIARY',
                  'EXPERIENCER', 'CO-AGENT', 'CO-THEME', 'AT-LOC', 'FROM-LOC', 'TO-LOC', 'PATH-LOC',
                  'AT-TIME', 'FROM-TIME', 'TO-TIME', 'AT-VALUE', 'FROM-VALUE', 'TO-VALUE',
                  'AT-POSS', 'FROM-POSS', 'TO-POSS']

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
    # return response, play_sound()
    return response
    # return response, tokenize()

@app.route("/get-mic-input")
def mic_input():
    r = sr.Recognizer()
    sr.Microphone(device_index=4)
    with sr.Microphone() as source:
        print("Ucapkan sesuatu...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio, language="id-ID")
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

@app.route("/tokenize", methods=["GET", "POST"])
def tokenize():
        text = request.form["text"]
        text = text.lower()
        translation_table = str.maketrans("", "", string.digits)
        translated_text = text.translate(translation_table)
        clean_text = " ".join(translated_text.split())
        sentence_token = sent_tokenize(clean_text)
        for sentence in sentence_token:
            print(sentence)
            if sentence == ".":
                sentence_token.remove(sentence)
        word_tokens = []
        for sentence in range(len(sentence_token)):
            token = word_tokenize(sentence_token[sentence])
            for item in token:
                if string.punctuation.__contains__(item):
                    token.remove(item)
            word_tokens.append(token)
        return jsonify(word_tokens)

@app.route("/stem", methods=["GET", "POST"])
def stem():
    token_string = request.form["token_list"]
    token_string = re.sub(r'[""]', "", token_string)
    token_string = token_string.replace("]", "").replace("[", "")
    token_list = token_string.split(",")
    stemmed_token = [stemmer.stem(word) for word in token_list]
    return jsonify(stemmed_token)    

@app.route("/stopword-removal", methods=["GET", "POST"])
def stopword_removal():
    filtered_list = []
    stop_words = set(stopwords.words("english"))
    stemmed_string = request.form["stem_list"]
    stemmed_string = re.sub(r'[""]', "", stemmed_string)
    stemmed_string = stemmed_string.replace("]", "").replace("[", "")
    stemmed_list = stemmed_string.split(",")
    stemmed_token = [stemmer.stem(word) for word in stemmed_list]
    for word in stemmed_token:
        if word not in stop_words:
            filtered_list.append(word)
    return jsonify(filtered_list)  
  
@app.route("/pos-tagging", methods=["GET", "POST"])
def pos_tagging():
    pos_tagging = []
    clean_string = request.form["filtered_list"]
    clean_string = re.sub(r'[""]', "", clean_string)
    clean_string = clean_string.replace("]", "").replace("[", "")
    clean_string = clean_string.split(",")
    clean_list = [stemmer.stem(word) for word in clean_string]
    pos_tag_list = nltk.pos_tag(clean_list)
    return jsonify(pos_tag_list)

@app.route("/parser", methods=["GET", "POST"])
def topdown():
    pos_tagging = []
    clean_string = request.form["clean_list"]
    clean_string = re.sub(r'[""]', "", clean_string)
    clean_string = clean_string.replace("]", "").replace("[", "")
    clean_string = clean_string.split(",")
    clean_list = [stemmer.stem(word) for word in clean_string]
    pos_tag_list = nltk.pos_tag(clean_list)
    chunkGram = r"""VB: {}"""
    chunkParser = nltk.RegexpParser(chunkGram)
    chunked = chunkParser.parse(pos_tag_list)
    return "nothing"   

@app.route("/themerole", methods=["GET", "POST"])
def themerole():
    sentence = request.form["sentence"]
    theme_role = themerole_process(sentence)
    return jsonify(theme_role)

@app.route("/logical",  methods=["GET", "POST"])
def logical_form():
    verb_tags = ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]
    predicate = ""
    subject = ""
    object = ""
    preposition = ""

    sentence = request.form["sentence"]
    tokens = nltk.word_tokenize(sentence)

    pos_tag_list = nltk.pos_tag(tokens)

    for i, tag in enumerate(pos_tag_list):
        if tag[1] in verb_tags:
            predicate += tag[0].upper() + " "
            if i > 0 and pos_tag_list[i-1][1] == "MD":
                predicate = pos_tag_list[i-1][0].upper() + " " + predicate
        elif tag[1] == "NN":
            if not subject:
                subject = "(" + tag[0].upper() + ")"
            elif not object and not subject:
                object = "( " + "THE " + tag[0].upper() + ")"
            else:
                object = "(" + "THE " + tag[0].upper() + ")"
        elif tag[1] == "IN":
            preposition = "(" + tag[0].upper() + " "

    if preposition:
        preposition += object + ")"

    predicate_argument = predicate.strip() + " " + subject + " " + object + " " + preposition if preposition else (predicate.strip(), subject, object)
    print(predicate_argument)
    return jsonify(predicate_argument)

def themerole_process(sentence):
    sentence = nlp(sentence)
    for token in sentence:
        if token.dep_ == 'ROOT':
            predicate = token.lemma_
            arguments = []
            for child in token.children:
                if child.dep_ in ('nsubj', 'nsubjpass'):
                    arguments.append(('AGENT', child.text))
                elif child.dep_ == 'dobj':
                    arguments.append(('THEME', child.text))
                elif child.dep_ == 'prep':
                    preposition = child.text.upper()
                    pp_tokens = [tok.text for tok in child.subtree]
                    pp = ' '.join(pp_tokens).upper()
                    if preposition == 'WITH':
                        arguments.append(('INSTRUMENT', pp))
                    elif preposition == 'FOR':
                        arguments.append(('BENEFICIARY', pp))
                    elif preposition in ('AT', 'IN', 'ON', 'FROM', 'TO', 'INTO', 'THROUGH', 'OVER'):
                        arguments.append((preposition + '-LOC', pp))
                    elif preposition in ('BEFORE', 'AFTER', 'DURING', 'SINCE', 'UNTIL'):
                        arguments.append((preposition + '-TIME', pp))
                    elif preposition in ('ABOUT', 'BETWEEN', 'FROM', 'TO', 'ON', 'WITHIN'):
                        arguments.append((preposition + '-VALUE', pp))
                    elif preposition in ('OF', 'TO'):
                        if child.children and child.children[0].dep_ == 'pobj':
                            arguments.append((preposition + '-POSS', child.children[0].text))
            # add default AT-TIME thematic role
            arguments.append(('AT-TIME', 'PAST'))
            return tuple([(role, value) for role, value in arguments if role in thematic_roles])

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)