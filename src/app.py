"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import ast
import json
import os
import re
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


def _parse_llm_action(text: str) -> Dict[str, str]:
    """
    Trích Action hoặc Final Answer từ output LLM theo định dạng REACT_SYSTEM_PROMPT.

    Lưu ý quan trọng: vì gọi provider.generate() không có stop-sequence, LLM đôi khi
    KHÔNG dừng lại đúng lúc sau "Action:" như hướng dẫn mà tự bịa tiếp cả Observation
    giả và Final Answer trong cùng một lần sinh. Nếu Action xuất hiện trước Final Answer
    trong text, phải ưu tiên xử lý Action và bỏ qua toàn bộ phần bịa phía sau — vì hệ
    thống mới là bên có quyền cung cấp Observation thật, không phải LLM tự tưởng tượng.
    """
    action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", text, re.DOTALL)
    final_match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)

    if action_match and (not final_match or action_match.start() < final_match.start()):
        return {
            "type": "action",
            "tool": action_match.group(1).strip(),
            "raw_args": action_match.group(2).strip(),
            # Chỉ giữ phần text tới hết Action thật -> loại bỏ Observation/Final Answer bịa phía sau
            "clean_text": text[:action_match.end()].strip(),
        }

    if final_match:
        return {"type": "final_answer", "content": final_match.group(1).strip()}

    return {"type": "unrecognized", "content": text.strip()}


def _parse_tool_args(raw_args: str):
    """
    Parse chuỗi tham số trong 'Action: tool[...]' thành tuple args để gọi AVAILABLE_TOOLS.
    Dùng ast.literal_eval để an toàn hơn eval(); nếu không phải Python literal hợp lệ
    (vd. career_id viết trần không có dấu ngoặc kép) thì coi cả chuỗi là 1 tham số string.
    """
    raw_args = raw_args.strip()
    if not raw_args:
        return ()

    # LLM đôi khi viết tham số dạng keyword (vd. answers={...}) dù prompt yêu cầu vị trí
    # (tool[tham_số]). Tool trong AVAILABLE_TOOLS chỉ nhận positional args, nên bóc phần
    # "tên_biến=" đứng trước cấu trúc/giá trị trước khi parse.
    cleaned = re.sub(r'\b[A-Za-z_]\w*\s*=\s*(?=[\{\[\'"\d])', '', raw_args)

    try:
        return ast.literal_eval(f"({cleaned},)")
    except (ValueError, SyntaxError):
        return (raw_args.strip("'\""),)


def run_react_agent(user_query: str, provider, answers: Dict[str, int] = None):
    """
    Vòng lặp ReAct Agent THẬT (Thought -> Action -> Observation) có Guardrails.
    LLM tự suy luận dựa trên REACT_SYSTEM_PROMPT để chọn tool trong AVAILABLE_TOOLS
    (Role 2) và tham số phù hợp; hệ thống thực thi tool, trả Observation lại cho
    LLM ở bước kế tiếp — lặp tới khi có Final Answer hoặc chạm Guardrail MAX_ITERATIONS.

    answers: kết quả khảo sát RIASEC (từ collect_riasec_answers), được đính kèm vào
    prompt ban đầu để LLM có dữ liệu thật gọi run_personality_assessment.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    prompt = f"Câu hỏi của người dùng: {user_query}"
    if answers:
        prompt += f"\nKết quả khảo sát RIASEC của người dùng (thang điểm 1-5 mỗi trait): {answers}"

    step = 0
    answered = False

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        llm_output = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        parsed = _parse_llm_action(llm_output)

        if parsed["type"] == "final_answer":
            print(f"🧠 {llm_output.strip()}")
            print(f"🏁 Final Answer: {parsed['content']}")
            answered = True
            break

        if parsed["type"] == "action":
            tool_name = parsed["tool"]
            clean_text = parsed["clean_text"]
            print(f"🧠 {clean_text}")

            tool_fn = AVAILABLE_TOOLS.get(tool_name)
            if tool_fn is None:
                observation = f"LỖI: Tool '{tool_name}' không tồn tại trong AVAILABLE_TOOLS."
            else:
                try:
                    args = _parse_tool_args(parsed["raw_args"])
                    observation = tool_fn(*args)
                except Exception as e:
                    observation = f"LỖI: Tham số cho tool '{tool_name}' không hợp lệ ({e})."

            print(f"👁️ Observation: {observation}")
            # Chỉ đưa lại phần Thought/Action THẬT (clean_text) vào context, KHÔNG đưa
            # phần Observation/Final Answer mà LLM có thể đã tự bịa thêm phía sau.
            prompt += f"\n{clean_text}\nObservation: {observation}"
            continue

        # LLM không tuân theo định dạng Thought/Action/Final Answer -> vẫn tính 1 bước,
        # đưa lỗi format vào Observation để LLM tự sửa ở bước sau (hoặc chạm Guardrail).
        print(f"🧠 (LLM không tuân theo định dạng bắt buộc):\n{llm_output.strip()}")
        prompt += (
            f"\n{llm_output.strip()}"
            "\nObservation: LỖI: Không nhận diện được Action hoặc Final Answer đúng định dạng."
        )

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
