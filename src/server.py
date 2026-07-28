import os
import sys
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import run_react_agent_stream
from providers import get_llm_provider

# Trỏ Flask tới thư mục ui/ để phục vụ file HTML
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ui_dir = os.path.join(base_dir, 'ui')

app = Flask(__name__, static_folder=ui_dir, static_url_path='')
CORS(app)

# Khởi tạo provider 1 lần khi chạy server
provider = get_llm_provider()

@app.route('/')
def index():
    """Phục vụ file giao diện ChatUI"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API nhận câu hỏi và trả về phản hồi từ ReAct Agent"""
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Vui lòng cung cấp tham số message'}), 400
    
    user_message = data['message']
    print(f"\n🌐 [Web API] Người dùng hỏi: {user_message}")
    
    try:
        # Gọi run_react_agent_stream và trả về luồng SSE
        return Response(stream_with_context(run_react_agent_stream(user_message, provider, answers=None)), mimetype='text/event-stream')
    except Exception as e:
        print(f"❌ [Web API] Lỗi: {e}")
        return jsonify({'error': f'Xin lỗi, đã xảy ra lỗi hệ thống: {str(e)}'}), 500

if __name__ == '__main__':
    print("==================================================")
    print("🚀 Bắt đầu chạy Web Server tại http://localhost:5001")
    print("==================================================")
    app.run(host='0.0.0.0', port=5001, debug=True)
