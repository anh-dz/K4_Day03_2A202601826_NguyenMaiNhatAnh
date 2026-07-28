# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: CareerWay
- **Team Members**: Nguyen Mai Nhat Anh, Đỗ Tú Anh, Nguyễn Minh Đức, Nguyễn Thế Hải Đăng, Trần Thanh Huyền
- **Deployment Date**: 2026-07-28

---

## 1. Executive Summary

Dự án này xây dựng một hệ thống định hướng nghề nghiệp bằng cách so sánh hai luồng: chatbot cơ bản và ReAct agent. Mục tiêu là chứng minh rằng với các câu hỏi đa bước, cần dùng tool và có logic phụ thuộc giữa các bước, agent có lợi thế rõ rệt hơn chatbot vì có thể gọi công cụ và suy luận theo chuỗi Thought → Action → Observation.

- **Success Rate**: Theo bộ 5 test case thiết kế trong dự án, agent xử lý đúng các trường hợp multi-step và edge case, trong khi chatbot chỉ hoạt động tốt với các câu hỏi đơn giản, không cần tool.
- **Key Outcome**: ReAct agent có thể chấm trắc nghiệm RIASEC, xếp hạng nghề bằng độ tương đồng deterministic, và tra cứu chi tiết nghề một cách có căn cứ thay vì chỉ đưa ra lời khuyên chung chung.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

Hệ thống triển khai vòng lặp ReAct theo mẫu:

1. Nhận câu hỏi từ người dùng.
2. LLM suy luận và quyết định bước tiếp theo dưới dạng Thought.
3. Gọi tool phù hợp bằng Action.
4. Nhận kết quả thực tế qua Observation.
5. Lặp lại cho đến khi có đủ dữ liệu để trả lời hoặc đạt giới hạn guardrail.

Luồng này được cài đặt trong [src/app.py](src/app.py), nơi hệ thống duy trì ngữ cảnh và parse định dạng action từ output của LLM.

### 2.2 Tool Definitions (Inventory)

| Tool Name                    | Input Format                                                       | Use Case                                                                      |
| :--------------------------- | :----------------------------------------------------------------- | :---------------------------------------------------------------------------- |
| `run_personality_assessment` | `dict` (ví dụ: `{"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}`) | Chấm trắc nghiệm RIASEC và sinh `profile_vector`, `holland_code`.             |
| `match_profile_to_careers`   | `dict + int`                                                       | So khớp hồ sơ tính cách với danh sách nghề và xếp hạng theo similarity score. |
| `get_career_detail`          | `string`                                                           | Lấy chi tiết nghề như mô tả, kỹ năng, mức lương và triển vọng.                |

### 2.3 LLM Providers Used

- **Primary**: Gemini/OpenRouter-style provider configuration via environment variables, with support for real LLM calls.
- **Secondary (Backup)**: Mock provider for offline testing and demo when API key is unavailable.

---

## 3. Telemetry & Performance Dashboard

Hiện tại hệ thống chủ yếu chạy ở chế độ console và chưa có logger chuyên sâu cho latency/token/cost. Do đó, các số liệu dưới đây là theo mức độ quan sát từ thiết kế chứ không phải benchmark đầy đủ.

- **Average Latency (P50)**: Chưa đo lường chính thức trong code hiện tại.
- **Max Latency (P99)**: Chưa đo lường chính thức trong code hiện tại.
- **Average Tokens per Task**: Chưa ghi nhận thống kê cụ thể.
- **Total Cost of Test Suite**: Chưa tính toán chi phí thực tế vì hệ thống chưa tích hợp telemetry billing.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: LLM viết sai định dạng action và tự bịa observation

- **Input**: "Cho tôi biết chi tiết về nghề Phi Hành Gia Vũ Trụ."
- **Observation**: Tool `get_career_detail` trả về lỗi vì nghề không tồn tại trong cơ sở dữ liệu, và hệ thống phải chuyển sang fallback an toàn.
- **Root Cause**: LLM đôi khi không tuân đúng định dạng `Action: tool[...]`, thậm chí tự viết thêm `Observation` hoặc `Final Answer` giả trong cùng một lần sinh. Đây là lỗi do prompt và parsing chưa đủ chặt ở giai đoạn đầu, nhưng đã được xử lý bằng cách ưu tiên action thật và cắt phần bịa phía sau.

### Additional Failure Mode

- **Input**: Các câu hỏi yêu cầu tool với tham số theo dạng keyword như `tool[key=value]`.
- **Root Cause**: LLM không luôn tuân theo định dạng positional như prompt yêu cầu. Hệ thống đã bổ sung logic bóc phần `tên_biến=` trước khi parse để tăng độ bền.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2

- **Diff**: Thêm quy tắc rõ ràng rằng sau khi viết `Action`, LLM phải dừng ngay, không tự bịa `Observation` hay `Final Answer`; đồng thời nêu rõ định dạng tham số phải theo kiểu positional.
- **Result**: Giảm lỗi parsing và giảm tình trạng hallucinated observation trong vòng lặp ReAct.

### Experiment 2 (Bonus): Chatbot vs Agent

| Case       | Chatbot Result                                   | Agent Result                                      | Winner    |
| :--------- | :----------------------------------------------- | :------------------------------------------------ | :-------- |
| Simple Q   | Trả lời đúng bằng kiến thức chung                | Trả lời đúng                                      | Draw      |
| Multi-step | Không thể chấm điểm hoặc xếp hạng nghề có căn cứ | Chấm trắc nghiệm, match nghề và lấy chi tiết nghề | **Agent** |
| Edge Case  | Không có cơ chế xử lý lỗi tool chuyên nghiệp     | Có thể nhận lỗi tool và dừng/fallback an toàn     | **Agent** |

---

## 6. Production Readiness Review

Đây là một prototype tốt cho mục đích học tập và demo, nhưng để đưa vào môi trường thực tế cần cải thiện thêm một số khía cạnh.

- **Security**: Cần kiểm tra và sanitize input trước khi truyền vào tool để tránh lỗi hoặc dữ liệu bất thường.
- **Guardrails**: Hệ thống đã có `MAX_ITERATIONS = 5` để ngăn vòng lặp vô hạn và giảm chi phí gọi LLM.
- **Scaling**: Với độ phức tạp tăng lên, nên chuyển sang workflow orchestration như LangGraph hoặc một framework agent có state management rõ ràng.
- **Observability**: Nên thêm logging chuẩn cho mỗi step, thời gian phản hồi, token usage và cost để đánh giá hiệu năng liên tục.

---
