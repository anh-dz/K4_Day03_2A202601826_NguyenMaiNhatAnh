"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from typing import Dict
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    RIASEC_SURVEY_QUESTIONS,
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")

    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def collect_riasec_answers(input_func=input) -> Dict[str, int]:
    """
    Chạy bộ khảo sát RIASEC chuẩn (RIASEC_SURVEY_QUESTIONS trong prompts.py):
    12 câu Likert 1-5, 2 câu/trait. Điểm mỗi trait = trung bình 2 câu, làm tròn
    về số nguyên gần nhất để khớp input schema của run_personality_assessment.

    Đây là nguồn "answers" xác định (deterministic) — KHÔNG để LLM tự đoán điểm
    qua hội thoại tự do, tránh kết quả không tái lập được giữa các lần chạy.
    """
    print("\n📋 KHẢO SÁT ĐỊNH HƯỚNG TÍNH CÁCH RIASEC")
    print("Trả lời mỗi câu bằng điểm từ 1 (Rất không đồng ý) đến 5 (Rất đồng ý).\n")

    scores_by_trait: Dict[str, list] = {}

    for item in RIASEC_SURVEY_QUESTIONS:
        trait = item["trait"]
        while True:
            raw = input_func(f"[{trait}] {item['question']} (1-5): ").strip()
            if raw.isdigit() and 1 <= int(raw) <= 5:
                scores_by_trait.setdefault(trait, []).append(int(raw))
                break
            print("⚠️ Vui lòng nhập số nguyên từ 1 đến 5.")

    return {
        trait: round(sum(scores) / len(scores))
        for trait, scores in scores_by_trait.items()
    }


def run_react_agent(user_query: str, provider, answers: Dict[str, int] = None):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    3 bước dùng đúng 3 tool định hướng nghề nghiệp từ AVAILABLE_TOOLS (Role 2):
    chấm RIASEC -> match nghề phù hợp -> xem chi tiết nghề được gợi ý nhiều nhất.

    answers: kết quả khảo sát RIASEC (từ collect_riasec_answers). Nếu không
    truyền vào (vd. chạy demo tự động, không tương tác), dùng vector mẫu mặc định.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    if answers is None:
        answers = {"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}

    step = 0
    profile_vector = None
    top_career_id = None
    answered = False

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        if step == 1:
            print("🧠 Thought: Cần chấm trắc nghiệm RIASEC trước để hiểu tính cách người dùng.")
            print(f"🛠️ Action: run_personality_assessment[{answers}]")

            obs = AVAILABLE_TOOLS["run_personality_assessment"](answers)
            print(f"👁️ Observation: {obs}")
            profile_vector = json.loads(obs)["profile_vector"]

        elif step == 2:
            print("🧠 Thought: Đã có vector tính cách, giờ tìm nghề phù hợp nhất với hồ sơ này.")
            print(f"🛠️ Action: match_profile_to_careers[{profile_vector}, 1]")

            obs = AVAILABLE_TOOLS["match_profile_to_careers"](profile_vector, 1)
            print(f"👁️ Observation: {obs}")
            top_career_id = json.loads(obs)["matches"][0]["career_id"]

        elif step == 3:
            print("🧠 Thought: Lấy chi tiết nghề được gợi ý nhiều nhất để tư vấn đầy đủ.")
            print(f"🛠️ Action: get_career_detail[{top_career_id}]")

            obs = AVAILABLE_TOOLS["get_career_detail"](top_career_id)
            print(f"👁️ Observation: {obs}")

            detail = json.loads(obs)
            print("🧠 Thought: Tôi đã có đủ thông tin để trả lời.")
            print(f"🏁 Final Answer: Dựa trên tính cách của bạn, nghề phù hợp nhất là "
                  f"**{detail['name']}** — {detail['description']}")
            answered = True
            break

    if not answered:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT ĐỊNH HƯỚNG SỰ NGHIỆP")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json")

    user_query = "Tôi muốn được định hướng nghề nghiệp phù hợp với tính cách của mình."

    # --- SO SÁNH 1: CHATBOT BASELINE (không có tool) ---
    print("\n=== SO SÁNH 1: CHATBOT BASELINE (không có tool) ===")
    run_baseline_chatbot(user_query, provider)

    # --- SO SÁNH 2: REACT AGENT (có tool, đúng workflow thiết kế) ---
    # Workflow chuẩn: khảo sát RIASEC -> chấm điểm -> match nghề -> xem chi tiết nghề.
    print("\n=== SO SÁNH 2: REACT AGENT (khảo sát RIASEC + tool định hướng) ===")
    try:
        survey_answers = collect_riasec_answers()
    except EOFError:
        survey_answers = None
        print("\nℹ️ Không có input tương tác (stdin EOF) -> dùng vector RIASEC mẫu mặc định.")

    run_react_agent(user_query, provider, answers=survey_answers)
