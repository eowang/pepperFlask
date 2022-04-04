import os
import time
import boto3
import openai
from flask import Flask, redirect, render_template, request, url_for, jsonify 
from deepspeech import Model
import pandas as pd 
import random
import string

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

start_sequence = "\nAI:"
restart_sequence = "\nHuman: "

transcribe = boto3.client('transcribe',
aws_access_key_id = 'AKIATTYTQWDSQPG27FGR',
aws_secret_access_key = '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',
region_name = "us-west-2")


def amazon_transcribe(audio_file_name):
    job_uri = "s3://pepperaudio/" + audio_file_name 
    letters = string.ascii_lowercase + string.digits
    job_name = ''.join(random.choice(letters) for i in range(10))
    file_format = audio_file_name.split('.')[1]

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat = file_format,
        LanguageCode='en-US')

    while True:
        result = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if result['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        time.sleep(15)
    if result['TranscriptionJob']['TranscriptionJobStatus'] == "COMPLETED":
        data = pd.read_json(result['TranscriptionJob']['Transcript']['TranscriptFileUri'])
    return data['results'][1][0]['transcript']

def GPT3(text):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=generate_prompt(text),
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
    )
    return response.choices[0].text 


@app.route("/")
def index():
    input = amazon_transcribe('sample1.wav')
    output = GPT3(input)

    return jsonify({"Pepper": output})



def generate_prompt(text):
    return """The following is a conversation with an AI assistant. 
    The assistant is very polite and helpful.\n\n
    Human: Hello, who are you?\nAI: I am Pepper, an AI created by Eric and Eric. 
    How can I help you today?\nHuman:{}\nAI:""".format(
        text
    )


