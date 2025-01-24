from flask import Flask, request, jsonify, send_from_directory
from google.cloud import speech_v1 as speech
import os
import anthropic

app = Flask(__name__, static_folder='static', static_url_path='')

# Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tidal.json"

# Anthropic API key
CLAUDE_API_KEY = ""  # Замініть на ваш актуальний ключ

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'message': 'No audio file uploaded'}), 400

    audio_file = request.files['audio']
    audio_content = audio_file.read()

    try:
        # Використання Google Speech-to-Text API
        speech_client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_content)

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            language_code="uk-UA",
        )

        response = speech_client.recognize(config=config, audio=audio)

        if not response.results:
            return jsonify({'message': 'No speech detected'}), 400

        transcript = response.results[0].alternatives[0].transcript
        print(f"Transcript: {transcript}")

        # Відправка транскрипції на Claude API через SDK
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        claude_response = client.completions.create(
            model="claude-2.1",
            max_tokens_to_sample=1000,
            prompt=f"\n\nHuman: {transcript}\n\nAssistant:"  # Додано необхідну структуру
        )

        # Log Claude response
        print("Claude response:", claude_response)

        # Обробка відповіді залежно від її структури
        try:
            response_message = claude_response.get('completion', '').strip()
        except AttributeError:
            response_message = claude_response.completion.strip()

        if not response_message:
            print("Claude API did not return a valid response.")
            return jsonify({'message': 'Claude API did not return a valid response'}), 500

        return jsonify({'message': response_message})

    except Exception as e:
        #print(f"Error: {e}")
        return jsonify({'message': 'An error occurred while processing audio'}), 500


if __name__ == '__main__':
    app.run(debug=True)
