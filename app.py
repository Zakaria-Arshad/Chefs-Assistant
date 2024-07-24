import os
import time

import requests
from flask import Flask, request, render_template, jsonify
import boto3
from dotenv import load_dotenv
from RagProcessing import RagProcessing
from Database import Database

load_dotenv()
app = Flask(__name__)
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

@app.route('/', methods=['GET'])
def upload_file():  # put application's code here
    return render_template('index.html')

@app.route("/chat", methods=['GET'])
def chat():
    return render_template('chat.html')

@app.route("/query", methods=['POST'])
def query():
    data = request.get_json()
    user_query = data['query']
    response = processor.generate(user_query)
    return jsonify(response)


@app.route("/uploadToS3", methods=['POST'])
def uploadToS3():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file part'}), 400

        file = request.files['audio']

        s3.upload_fileobj(file, S3_BUCKET, file.filename, ExtraArgs={'ContentType': 'audio/wav'})
        file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file.filename}"
        print("Upload to S3 Finished")
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
        job_name = job_args["TranscriptionJobName"]

        response = transcribe.start_transcription_job(**job_args)
        status = get_transcription_status(job_name)

        while status not in {"COMPLETED", "FAILED"}:
            time.sleep(10)
            status = get_transcription_status(job_name)

        if status == "COMPLETED":
            print("Transcription Job Completed")
            transcript_file_uri = get_transcription_result(job_name)
            transcript_response = requests.get(transcript_file_uri)
            if transcript_response.status_code == 200:
                transcript_json = transcript_response.json()
                data_result = transcript_json["results"]["transcripts"][0]["transcript"]
                if data_result:
                    original_id = Database.insertOriginalDocumentIntoDatabase(data_result)
                    if original_id:
                        processor.storeInVectorStore(data_result, str(original_id))
            else:
                return jsonify({'error': 'Failed to fetch transcription result'}), 500
        else:
            return jsonify({'error': 'Transcription job failed'}), 500

        return jsonify({'file_url': file_url}), 200

    except Exception as e:
        return jsonify({'error': 'An error occurred', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
