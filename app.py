import traceback
from flask import Flask, render_template, request, jsonify
import uuid
from dotenv import load_dotenv
from test.test_processing import process_uploaded_file
from utils import is_product_recommendation_request
from threading import Thread, Lock

load_dotenv()

app = Flask(__name__)

processing_status = {}
process_lock = Lock()

@app.route('/')
def index():
    return render_template('index.html')

def process_with_assistant(text, text_type, unique_id):
    pass

def process_with_assistant_async(text, text_type, unique_id):
    thread = Thread(target=process_with_assistant, args=(text, text_type, unique_id))
    thread.start()
    return jsonify(success=True, user_id=unique_id, message="処理を開始しました")

@app.route('/submit', methods=['POST'])
def recievingdata():
    text = request.form['text']
    unique_id = str(uuid.uuid4())

    try:
        if is_product_recommendation_request(text):
            text_type = "request"
        else:
            text_type = "question"

        return process_with_assistant_async(text, text_type, unique_id)
    except Exception as e:
        error_message = traceback.format_exc()
        return jsonify({
            "status": "error",
            "message": error_message
        })

@app.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('test.html')

def process_file_async(process_id, file_content, process_with_assistant, is_product_recommendation_request):
    try:
        with process_lock:
            processing_status[process_id] = {
                'status': 'processing',
                'message': '処理を開始しました'
            }

        results = process_uploaded_file(file_content, process_with_assistant, is_product_recommendation_request)

        with process_lock:
            processing_status[process_id] = {
                'status': 'completed',
                'results': results
            }

    except Exception as e:
        with process_lock:
            processing_status[process_id] = {
                'status': 'error',
                'message': str(e)
            }

@app.route('/test/upload', methods=['POST'])
def test_upload():
    try:
        if 'text' not in request.form:
            return jsonify({'status': 'error', 'message': 'テキストがありません'})

        text = request.form['text']
        process_id = str(uuid.uuid4())

        with process_lock:
            processing_status[process_id] = {
                'status': 'initializing',
                'message': '処理を初期化中'
            }

        thread = Thread(
            target=process_file_async,
            args=(
                process_id,
                text,
                process_with_assistant,
                is_product_recommendation_request
            )
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'status': 'processing',
            'process_id': process_id,
            'message': '処理を開始しました'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"エラーが発生しました: {str(e)}"})

@app.route('/test/status/<process_id>', methods=['GET'])
def get_status(process_id):
    try:
        with process_lock:
            if process_id not in processing_status:
                return jsonify({
                    'status': 'error', 
                    'message': f"処理が見つかりません。process_id: {process_id}。現在の処理数: {len(processing_status)}"
                })
            status_data = processing_status[process_id]
            return jsonify(status_data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"ステータス取得中にエラーが発生しました: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
