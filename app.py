import os
import time

import requests
from flask import Flask, request, flash, redirect, render_template_string, url_for, render_template, jsonify
from werkzeug.utils import secure_filename
import boto3
from dotenv import load_dotenv
import pytesseract
from ImageProcessor import ImageProcessor
from RagProcessing import RagProcessing

load_dotenv()
app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['TXT_DOCS'] = './docs'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
S3_BUCKET = os.getenv('S3_BUCKET')
S3_REGION = os.getenv('S3_REGION')
AWS_ACCESS_KEY_ID = os.getenv('ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('SECRET_ACCESS_KEY')
s3 = boto3.client('s3', region_name=S3_REGION,
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
transcribe = boto3.client('transcribe')
processor = RagProcessing()

def allowed_image_file(filename):
    file_extension = filename.split(".")[-1]
    return file_extension in ["jpg", "jpeg", "png"]
def allowed_text_file(filename):
    file_extension = filename.split(".")[-1]
    return file_extension in ["txt"]

@app.route('/', methods=['GET', 'POST'])
def upload_file():  # put application's code here
    # if request.method == 'POST':
    #     if 'file' not in request.files:
    #         flash('No file part')
    #         return redirect(request.url)
    #     file = request.files['file']
    #     if file.filename == '':
    #         flash('No selected file')
    #         return redirect(request.url)
    #     # if file and allowed_image_file(file.filename):  # should add allowed file security later
    #     #     filename = secure_filename(file.filename)
    #     #     file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    #     if file and allowed_text_file(file.filename):
    #         filename = secure_filename(file.filename)
    #         file.save(os.path.join(app.config['TXT_DOCS'], filename))
    # files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html')


# @app.route("/delete", methods=['GET', 'POST'])
# def delete_file():
#     selected_files = request.form.getlist("selected_files")
#     for file in selected_files:
#         os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
#     return redirect(url_for('upload_file'))
#
# @app.route("/ocr", methods=['GET', 'POST'])
# def ocr():
#     imageProcessor = ImageProcessor()
#     selected_files = request.form.getlist("selected_files")
#     for file in selected_files:
#         imageProcessor.processImage(os.path.join("./uploads/", file))
#     return redirect(url_for('upload_file'))

@app.route("/chat", methods=['GET', 'POST'])
def chat():
    # for file in os.listdir(app.config['TXT_DOCS']):
    #     processor.storeInVectorStore(os.path.join(app.config['TXT_DOCS'], file))
    return render_template('chat.html')

@app.route("/query", methods=['POST', 'GET'])
def query():
    data = request.get_json()
    user_query = data['query']
    response = processor.generate(user_query)
    return jsonify(response)

@app.route("/uploadToS3", methods=['POST'])
def uploadToS3():
    # TO DO: Add more validation in case of problems
    # TO DO: try catch for uploading the file
    # TO DO: separate into multiple functions -> one for upload to S3, one for transcribe
    # TO DO: don't return audio file
    # Limit audio length?
    #
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file part'}), 400
    file = request.files['audio']
    s3.upload_fileobj(file, S3_BUCKET, file.filename, ExtraArgs={'ContentType': 'audio/wav'})
    file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file.filename}"

    def get_transcription_status(job_name):
        response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        return response['TranscriptionJob']['TranscriptionJobStatus']

    def get_transcription_result(job_name):
        response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        transcript_file_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
        return transcript_file_uri

    job_args = {
        "TranscriptionJobName": file.filename,
        "Media": {"MediaFileUri": file_url},
        "MediaFormat": "wav",
        "LanguageCode": "en-US",
    }
    job_name = job_args["TranscriptionJobName"] # file.filename

    response = transcribe.start_transcription_job(**job_args)

    status = get_transcription_status(job_name)
    while status not in {"COMPLETED", "FAILED"}:
        print("Processing")
        time.sleep(10)
        status = get_transcription_status(job_name)

    if status == "COMPLETED":
        transcript_file_uri = get_transcription_result(job_name)
        transcript_json = requests.get(transcript_file_uri).json()
        data_result = transcript_json["results"]["transcripts"][0]["transcript"]
        # save to normal storage -> get id
        processor.storeInVectorStore(data_result) # this needs to decide whether or not to add to existing doc or not
    else:
        print("Oops! Error.")


    return jsonify({'file_url': file_url}), 200

if __name__ == '__main__':
    app.run()
