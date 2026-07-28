# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thế Hải Đăng
- **Student ID**: 02A202601957
- **Date**: 28/07/2026

---

## I. Technical Contribution (15 Points)

Trong lab này, tôi đảm nhận vai trò Role 1 - Product Architect, tập trung vào việc định hình bài toán và xây dựng bộ test case làm tiêu chuẩn đánh giá cho cả chatbot và ReAct agent.

- **Modules Implemented**: file [config/test_cases.json](../../config/test_cases.json)
- **Code Highlights**: Tôi đã thiết kế 12 test case bao gồm 4 case đơn giản chỉ cần LLM trả lời trực tiếp, 5 case multi-step cần gọi tool như run_personality_assessment, match_profile_to_careers và get_career_detail, cùng 3 case edge case để kiểm tra guardrail và khả năng xử lý lỗi.
- **Documentation**: Bộ test case này đóng vai trò như acceptance criteria cho các thành viên Role 2, 3 và 4, giúp định hướng cách triển khai tool, prompt và vòng lặp ReAct cho phù hợp với mục tiêu bài toán.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Trong quá trình thử nghiệm, một số tình huống đầu tiên chưa đủ rõ về kỳ vọng đầu ra, đặc biệt là các câu hỏi về nghề không tồn tại hoặc dữ liệu RIASEC chưa đầy đủ. Điều này khiến agent có thể trả lời thiếu chính xác hoặc không tuân đúng guardrail.
- **Log Source**: Kết quả thực thi thử nghiệm và trace phản hồi từ app khi chạy các case kiểm thử.
- **Diagnosis**: Nguyên nhân không nằm ở LLM đơn thuần, mà ở chỗ test case ban đầu chưa nêu rõ yêu cầu về hành vi mong đợi như không bịa thông tin, không gọi tool giả, hoặc cần yêu cầu người dùng hoàn thiện dữ liệu trước khi phân tích.
- **Solution**: Tôi đã chỉnh lại bộ test case theo hướng rõ ràng hơn bằng cách phân loại theo mức độ ưu tiên, chỉ rõ tool nào nên được gọi và mô tả chính xác hành vi pass/fail cho từng trường hợp.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: ReAct agent có lợi thế hơn chatbot ở chỗ nó có thể suy luận theo chuỗi Thought → Action → Observation. Với những câu hỏi cần dùng tool như đánh giá tính cách hoặc tra cứu nghề nghiệp, agent thể hiện khả năng phân tích và điều hướng tốt hơn.
2. **Reliability**: Trong các câu hỏi đơn giản, chatbot thường phản hồi nhanh và tự nhiên hơn. Tuy nhiên, khi gặp câu hỏi phức tạp hoặc cần dữ liệu thực tế, agent có thể bị sai nếu tool hoặc prompt không được thiết kế tốt.
3. **Observation**: Việc có feedback từ observation giúp agent điều chỉnh bước tiếp theo thay vì chỉ đưa ra câu trả lời một lần, đây là điểm khác biệt lớn giữa chatbot và agent trong việc xử lý vấn đề nhiều bước.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Nên xây dựng hệ thống quản lý test case theo version và tự động hóa chạy kiểm thử để dễ mở rộng khi bài toán lớn hơn.
- **Safety**: Cần thêm validator để kiểm tra đầu vào và chặn các trường hợp agent trả lời không có căn cứ hoặc dùng tool sai mục đích.
- **Performance**: Có thể dùng một bộ scoring rubric chuẩn để đánh giá agent theo nhiều tiêu chí như độ chính xác, tính an toàn và hiệu quả thực hiện tool.

---

