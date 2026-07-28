# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Minh Đức
- **Student ID**: 2A202601946
- **Date**: 28/07/2026
- **Role**: Role 4 — Core Developer / Integrator (đầu mối lắp ráp `src/app.py`)

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**:
  - `src/app.py` — file lắp ráp trung tâm: `run_baseline_chatbot()`, `run_react_agent()` (vòng lặp ReAct thật, không phải kịch bản cứng), `run_react_agent_stream()` (bản streaming cho web UI), `collect_riasec_answers()` (khảo sát RIASEC chuẩn qua CLI), `suggest_riasec_from_story()` (gợi ý điểm từ mô tả tự do có guardrail), `_parse_llm_action()` / `_parse_tool_args()` (parser Action/Final Answer).
  - `src/server.py` — Flask backend nối `app.py` với `ui/index.html`: endpoint `/api/chat` (SSE streaming), `/api/survey-questions`, `/api/survey-suggest`.
  - `src/providers.py` — vá Multi-Provider Adapter (`GeminiProvider`) để ReAct loop chạy ổn định với API thật.
  - `ui/index.html` — sửa lỗi luồng dữ liệu streaming và thêm luồng khảo sát RIASEC mặc định trước khi vào chat tự do.

- **Code Highlights**:
  - `src/app.py` — vòng lặp ReAct thật (không hardcode step):
    ```python
    while step < MAX_ITERATIONS:
        step += 1
        llm_output = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        parsed = _parse_llm_action(llm_output)
        if parsed["type"] == "final_answer":
            ...
            break
        if parsed["type"] == "action":
            observation = AVAILABLE_TOOLS[parsed["tool"]](*_parse_tool_args(parsed["raw_args"]))
            prompt += f"\n{parsed['clean_text']}\nObservation: {observation}"
    ```
  - `_parse_llm_action()` xử lý đúng trường hợp LLM **tự bịa tiếp** Observation/Final Answer sau khi đã viết Action thật (vì gọi API không có stop-sequence): ưu tiên Action nếu xuất hiện trước Final Answer trong text, cắt bỏ toàn bộ phần bịa phía sau bằng `text[:action_match.end()]`.
  - `src/providers.py` — `_build_config()`: tắt `thinking_config` cho model "-lite" (không hỗ trợ), và tự động retry tối đa 3 lần khi Gemini trả `finish_reason=MALFORMED_RESPONSE` (response rỗng ngẫu nhiên phía Google).
  - `ui/index.html` — sửa bug `chunkStr.split('\\n')` (tách theo chuỗi ký tự `\n` thay vì ký tự xuống dòng thật) và thêm cơ chế buffer giữ dòng SSE dở dang giữa 2 lần đọc mạng.

- **Documentation**: `app.py` là điểm nối duy nhất giữa 3 mảnh của nhóm — `tools.py` (Role 2) cung cấp `AVAILABLE_TOOLS`, `prompts.py` (Role 3) cung cấp `REACT_SYSTEM_PROMPT`/`MAX_ITERATIONS`/`RIASEC_SURVEY_QUESTIONS`, `config/test_cases.json` (Role 1) cung cấp bộ test. `run_react_agent()` gọi LLM với `REACT_SYSTEM_PROMPT`, parse Action, gọi tool thật qua `AVAILABLE_TOOLS`, rồi nạp `Observation` ngược vào prompt cho bước kế — đúng chu trình Thought → Action → Observation của ReAct, có Guardrail `MAX_ITERATIONS` chặn lặp vô tận.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: ReAct Agent liên tục chạm Guardrail (`Đã đạt giới hạn tối đa 5 bước`) dù logic hoàn toàn đúng — quan sát qua log `--- 🔄 Vòng lặp ReAct (Step X/5) ---` thấy nhiều bước bị in ra `(LLM không tuân theo định dạng bắt buộc):` với nội dung **rỗng**.

- **Log Source**: Log console khi chạy `python src/app.py` / `python src/server.py`, ví dụ:
  ```
  --- 🔄 Vòng lặp ReAct (Step 2/5) ---
  🧠 (LLM không tuân theo định dạng bắt buộc):

  --- 🔄 Vòng lặp ReAct (Step 3/5) ---
  ...
  🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa 5 bước. Ngắt lặp an toàn!
  ```
  Đào sâu bằng cách gọi trực tiếp `google-genai` SDK và in `response.candidates` thu được bằng chứng cụ thể:
  ```
  finish_reason: FinishReason.MALFORMED_RESPONSE
  full candidate: [Candidate(content=Content(), finish_reason=<FinishReason.MALFORMED_RESPONSE...>)]
  ```

- **Diagnosis**: Không phải lỗi prompt hay tool spec. Có 2 nguyên nhân riêng biệt chồng lên nhau:
  1. Model "thinking" (`gemini-3.5-flash`) dùng hết `max_output_tokens` cho phần suy luận ẩn, không còn token để viết câu trả lời → `response.text` rỗng.
  2. Ngay cả sau khi tắt thinking (đổi sang bản `-lite`), Google API đôi khi trả `finish_reason=MALFORMED_RESPONSE` — lỗi tạm thời không xác định phía server, xảy ra ngẫu nhiên (test lại y hệt request cũ vẫn thành công), không liên quan đến nội dung prompt.

- **Solution**: Trong `GeminiProvider._build_config()` (src/providers.py): không gửi `thinking_config` cho model có "lite" trong tên; đặt `max_output_tokens=2048` rõ ràng. Trong `generate()`/`generate_stream()`: tự động thử lại tối đa 3 lần khi `response.text` rỗng, thay vì để 1 bước hỏng lãng phí luôn 1/5 quota Guardrail của ReAct Agent. Sau khi vá, tỉ lệ agent hoàn thành trong budget 5 bước tăng rõ rệt qua các lần test lặp lại.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Block `Thought` buộc LLM phải tường minh hoá lý do trước khi hành động — ví dụ agent tự viết "Cần chấm trắc nghiệm RIASEC trước để hiểu tính cách người dùng" trước khi gọi `run_personality_assessment`, rồi mới quyết định gọi `match_profile_to_careers` dựa trên `profile_vector` thật nhận được từ Observation. Chatbot Baseline không có bước này nên khi hỏi "nghề nào phù hợp với tôi", nó chỉ hỏi ngược lại chung chung hoặc (nếu không giới hạn prompt chặt) tự bịa ra một nghề không có căn cứ số liệu nào.

2.  **Reliability**: Agent thực tế **kém tin cậy hơn** Chatbot trong 2 tình huống: (a) khi API không ổn định (rate limit 429, response rỗng MALFORMED_RESPONSE) — mỗi lần gọi thêm là một điểm có thể lỗi, trong khi Chatbot chỉ gọi 1 lần; (b) khi LLM không tuân thủ định dạng `Action: tool[tham_số]` (viết dạng keyword `key=value` thay vì positional, hoặc tự bịa tiếp Observation giả ngay sau Action thật do không có stop-sequence) — phải viết thêm logic parse phòng thủ (`_parse_tool_args`, ưu tiên Action trước Final Answer) mà Chatbot không cần.

3.  **Observation**: Observation là thứ quyết định toàn bộ hướng đi của các bước sau — ví dụ `top_career_id` lấy từ Observation của `match_profile_to_careers` mới được dùng làm tham số cho `get_career_detail` ở bước kế. Khi Observation là lỗi (`"LỖI: Không tìm thấy nghề..."`), agent đọc được lỗi tường minh (không phải exception Python) nên tự chọn hành động khác trong lượt sau — kiểm chứng bằng test có kiểm soát (`ScriptedProvider`): tool trả lỗi ở career_id không tồn tại, agent tự đổi sang career_id hợp lệ khác ở bước tiếp theo rồi vẫn ra được Final Answer đúng.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Tách `run_react_agent` khỏi vòng lặp đồng bộ chặn (blocking) hiện tại — dùng hàng đợi async (asyncio/Celery) để xử lý nhiều phiên chat song song mà không phải mở 1 request HTTP giữ kết nối SSE suốt thời gian suy luận như `run_react_agent_stream` hiện tại.
- **Safety**: Hiện Guardrail mới chỉ có `MAX_ITERATIONS` chặn lặp vô tận. Có thể thêm 1 "Supervisor" nhẹ kiểm tra Action trước khi thực thi (ví dụ chặn agent gọi cùng 1 tool với cùng tham số lặp lại >2 lần — dấu hiệu bị kẹt logic), và validate `Final Answer` không chứa thông tin nghề nghiệp bịa ngoài `CAREER_DB`.
- **Performance**: Với 8 hướng nghề và 3 tool như hiện tại, không cần Vector DB. Nếu mở rộng lên hàng trăm nghề/tool, nên: (1) cache `provider.generate()` theo hash(prompt) để tránh gọi API trùng lặp khi test; (2) thêm cơ chế backoff-retry có độ trễ tăng dần cho lỗi 429 (hiện tại retry ngay lập tức, gây tốn quota nhanh khi rate-limit đã chạm).

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
