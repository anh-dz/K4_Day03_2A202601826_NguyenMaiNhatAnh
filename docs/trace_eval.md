# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*
*Chủ đề: Chatbot Định Hướng Sự Nghiệp*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Phải suy luận qua 3 bước phụ thuộc nhau: chấm trắc nghiệm RIASEC → xếp hạng nghề phù hợp → tra chi tiết nghề được chọn. Không thể gộp thành 1 bước suy luận ngôn ngữ đơn thuần. |
| 🛠️ **Tool Interaction** | `5/5` | Bắt buộc cần tính toán deterministic (similarity score theo khoảng cách vector RIASEC) mà LLM không nên tự "đoán" — sai lệch dễ dẫn đến gợi ý nghề sai. |
| 🔀 **Dynamic Decision** | `5/5` | Kết quả bước trước (holland_code, career_id phù hợp nhất) quyết định tham số gọi tool ở bước sau; nếu tool báo lỗi (vd. career_id không tồn tại) agent phải tự chọn hành động khác. |
| ⏳ **Long Horizon** | `3/5` | Quy trình hoàn chỉnh gồm 3 bước tool + có thể thêm bước tự sửa lỗi định dạng, không quá dài nhưng vẫn nhiều hơn 1 lượt hỏi-đáp. |
| **TỔNG ĐIỂM FIT** | **18/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT — Chatbot gốc không thể chấm điểm/match nghề một cách xác định (deterministic).** |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3 — "Tôi thích phân tích dữ liệu và giải quyết vấn đề logic, nghề nào phù hợp với tôi?")

### 🤖 Chatbot Baseline (không có tool):
* **Phản hồi**: Hỏi ngược lại người dùng về sở thích/điểm mạnh/tính cách một cách chung chung, không đưa ra con số hay xếp hạng cụ thể; tự nhận không có khả năng chấm trắc nghiệm xác định.
* **Nhận xét**: An toàn (không bịa dữ liệu), nhưng không giải quyết được nhu cầu match nghề có căn cứ — chỉ dừng ở tư vấn định tính.

### 🧠 ReAct Agent (có tool, trace thật thu được từ `gemini-3.5-flash`):

```
Thought: Người dùng đã cung cấp kết quả khảo sát RIASEC của mình. Tôi cần sử dụng
công cụ run_personality_assessment để chấm điểm và trích xuất profile_vector cùng
holland_code.
Action: run_personality_assessment[{"R": 2, "I": 4, "A": 3, "S": 2, "E": 4, "C": 2}]
Observation: {
  "profile_vector": {"R": 2, "I": 4, "A": 3, "S": 2, "E": 4, "C": 2},
  "top_traits": [["I", 4], ["E", 4], ["A", 3]],
  "holland_code": "IEA",
  "note": "Vector này có thể dùng làm input cho match_profile_to_careers."
}

Thought: Tôi cần sử dụng match_profile_to_careers với hồ sơ tính cách của người
dùng để tìm ra các nghề phù hợp nhất. Tôi sẽ chọn top 3 ngành nghề.
Action: match_profile_to_careers[{"R": 2, "I": 4, "A": 3, "S": 2, "E": 4, "C": 2}, 3]
Observation: {
  "top_k": 3,
  "matches": [
    {"career_id": "truyen_thong_bao_chi", "name": "Truyền thông - Báo chí", "similarity_percent": 83.33},
    {"career_id": "cntt", "name": "Công nghệ thông tin", "similarity_percent": 76.67},
    {"career_id": "kinh_te_kinh_doanh", "name": "Kinh tế - Kinh doanh - Quản trị", "similarity_percent": 73.33}
  ]
}

Thought: Ngành phù hợp nhất là "Truyền thông - Báo chí" (83.33%). Tôi sẽ lấy chi
tiết ngành này để tư vấn đầy đủ.
Action: get_career_detail["truyen_thong_bao_chi"]
Observation: {
  "id": "truyen_thong_bao_chi", "name": "Truyền thông - Báo chí",
  "description": "Sản xuất nội dung, quản lý thương hiệu và truyền tải thông tin tới công chúng.",
  "required_skills": ["Viết lách", "Kể chuyện", "Nắm bắt xu hướng", "Làm việc đa nền tảng"],
  "salary_range": "7 - 28 triệu VNĐ/tháng tùy vị trí và kinh nghiệm",
  "growth_outlook": "Cao, đặc biệt với truyền thông số và mạng xã hội."
}

Thought: Tôi đã có đủ thông tin để trả lời.
Final Answer: Dựa trên hồ sơ tính cách (mã Holland: IEA), nghề phù hợp nhất là
Truyền thông - Báo chí (83.33%) — sản xuất nội dung, quản lý thương hiệu, truyền
tải thông tin tới công chúng; kỹ năng cần: viết lách, kể chuyện, nắm bắt xu hướng...
```

* **Nhận xét**: Hoàn thành nhiệm vụ nhờ kết hợp suy luận (chọn đúng thứ tự tool, tự đặt `top_k`) và công cụ deterministic (match/score không bị LLM "đoán"). Agent tự giải thích rõ vì sao chọn ngành xếp hạng #1 trước khi tra chi tiết.

---

## 🛡️ 3. KIỂM TRA GUARDRAIL (EDGE CASE — Test Case #5: "Cho tôi biết chi tiết về nghề Phi Hành Gia Vũ Trụ.")

Do đây là hành vi không xác định (phụ thuộc LLM có tuân theo định dạng hay không), nhóm test bằng **provider kịch bản có kiểm soát** (`ScriptedProvider` trong quá trình phát triển) để xác nhận 2 nhánh guardrail hoạt động đúng, độc lập với việc LLM thật có ổn định hay không:

### Nhánh A — Tool trả lỗi giữa chừng, Agent tự phục hồi:
```
Step 1: Action: get_career_detail["khong_ton_tai"]
        Observation: LỖI: Không tìm thấy nghề 'khong_ton_tai'. Nghề hỗ trợ: [...8 nghề...]
Step 2: Action: get_career_detail["cntt"]   <- agent tự chọn nghề hợp lệ khác
        Observation: {...chi tiết nghề CNTT...}
Step 3: Final Answer: Gợi ý nghề CNTT cho bạn.
```
✅ **PASS** — Tool báo lỗi rõ ràng (`"LỖI: ..."`, không crash), Agent đọc được lỗi và tự sửa hướng đi trong quota còn lại.

### Nhánh B — LLM không bao giờ theo đúng định dạng Thought/Action/Final Answer:
```
Step 1-5: (LLM không tuân theo định dạng bắt buộc): "toi khong biet phai lam gi ca"
🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa 5 bước. Ngắt lặp an toàn!
```
✅ **PASS** — Sau đúng `MAX_ITERATIONS` bước, vòng lặp dừng lại an toàn với thông báo rõ ràng, không lặp vô tận, không crash chương trình.

### Rủi ro thực tế phát hiện khi test với LLM thật (không phải lỗi code):
* LLM đôi khi viết tham số dạng `tool[key=value]` (keyword) thay vì `tool[value]` (positional) như prompt yêu cầu → đã vá bằng cách bóc `tên_biến=` trước khi parse (`_parse_tool_args` trong `src/app.py`).
* Vì gọi API không có stop-sequence, LLM đôi khi **tự bịa tiếp Observation/Final Answer giả** ngay sau khi viết Action thật trong cùng một lần sinh → đã vá bằng cách ưu tiên Action nếu xuất hiện trước Final Answer trong text, và cắt bỏ phần bịa phía sau trước khi đưa vào Observation thật + lịch sử hội thoại.
* `MAX_ITERATIONS` ban đầu để `3` (đúng bằng số bước happy-path) khiến không còn dư bước nào cho LLM tự sửa lỗi định dạng → nâng lên `5` (3 bước happy-path + 2 bước đệm).
