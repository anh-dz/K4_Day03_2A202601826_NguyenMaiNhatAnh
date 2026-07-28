


"""
🛠️ TOOL REGISTRY & SCHEMAS
Chủ đề: CHATBOT ĐỊNH HƯỚNG SỰ NGHIỆP

File: src/tools.py

Mục tiêu:
- Thiết kế tool deterministic cho ReAct Agent.
- Tool có contract rõ ràng: input, output, error semantics, side effect.
- Không để tool crash khi nhập sai dữ liệu.
- Error nghiệp vụ trả về chuỗi "LỖI: ..." để Agent đọc và xử lý tiếp.
- Chỉ giữ các tool phục vụ trực tiếp việc ĐỊNH HƯỚNG nghề nghiệp: chấm tính cách,
  match nghề phù hợp và xem chi tiết nghề được gợi ý.
"""

import json
from typing import Dict, Any


# ============================================================
# 📚 MOCK DATABASE
# ============================================================

CAREER_DB = {
    "ai_engineer": {
        "id": "ai_engineer",
        "name": "AI Engineer",
        "description": "Xây dựng, huấn luyện, triển khai và tối ưu các hệ thống AI/ML, LLM, chatbot và agent.",
        "required_skills": [
            "Python",
            "Machine Learning",
            "Deep Learning",
            "LLM",
            "Prompt Engineering",
            "SQL",
            "MLOps",
        ],
        "salary_range": "Junior: 15-25tr | Middle: 25-45tr | Senior: 45-80tr VNĐ/tháng",
        "growth_outlook": "Rất cao do nhu cầu ứng dụng AI trong doanh nghiệp tăng mạnh.",
        "education": "Nên có nền tảng CNTT, Khoa học dữ liệu, Toán tin hoặc tự học qua dự án thực tế.",
        "riasec": {
            "R": 1,
            "I": 5,
            "A": 2,
            "S": 2,
            "E": 2,
            "C": 3,
        },
    },
    "data_engineer": {
        "id": "data_engineer",
        "name": "Data Engineer",
        "description": "Thiết kế, xây dựng và vận hành hệ thống dữ liệu, ETL/ELT pipeline, Data Warehouse/Lakehouse.",
        "required_skills": [
            "SQL",
            "Python",
            "Airflow",
            "Spark",
            "Kafka",
            "ClickHouse",
            "Data Warehouse",
        ],
        "salary_range": "Junior: 12-20tr | Middle: 20-40tr | Senior: 40-70tr VNĐ/tháng",
        "growth_outlook": "Cao do doanh nghiệp ngày càng cần hạ tầng dữ liệu tốt để ra quyết định và ứng dụng AI.",
        "education": "Phù hợp với nền tảng CNTT, Hệ thống thông tin, Khoa học dữ liệu.",
        "riasec": {
            "R": 2,
            "I": 4,
            "A": 1,
            "S": 1,
            "E": 2,
            "C": 5,
        },
    },
    "backend_developer": {
        "id": "backend_developer",
        "name": "Backend Developer",
        "description": "Phát triển API, xử lý logic nghiệp vụ, làm việc với cơ sở dữ liệu và hệ thống phía server.",
        "required_skills": [
            "Java",
            "C#",
            "Python",
            "Go",
            "REST API",
            "Database",
            "Docker",
            "Microservices",
        ],
        "salary_range": "Junior: 10-18tr | Middle: 18-35tr | Senior: 35-60tr VNĐ/tháng",
        "growth_outlook": "Ổn định và cao vì hầu hết sản phẩm số đều cần backend.",
        "education": "Phù hợp với nền tảng CNTT, Kỹ thuật phần mềm hoặc tự học lập trình.",
        "riasec": {
            "R": 3,
            "I": 3,
            "A": 1,
            "S": 1,
            "E": 2,
            "C": 4,
        },
    },
    "business_analyst": {
        "id": "business_analyst",
        "name": "Business Analyst",
        "description": "Phân tích nghiệp vụ, làm cầu nối giữa khách hàng, người dùng và đội phát triển sản phẩm.",
        "required_skills": [
            "Requirement Analysis",
            "Communication",
            "BPMN",
            "UML",
            "SQL cơ bản",
            "Documentation",
        ],
        "salary_range": "Junior: 10-15tr | Middle: 15-30tr | Senior: 30-50tr VNĐ/tháng",
        "growth_outlook": "Tốt, đặc biệt trong công ty phần mềm, ERP, ngân hàng, bảo hiểm và chuyển đổi số.",
        "education": "Phù hợp với CNTT, Kinh tế, Quản trị kinh doanh hoặc người có tư duy hệ thống.",
        "riasec": {
            "R": 1,
            "I": 3,
            "A": 2,
            "S": 4,
            "E": 4,
            "C": 3,
        },
    },
    "ux_ui_designer": {
        "id": "ux_ui_designer",
        "name": "UX/UI Designer",
        "description": "Thiết kế trải nghiệm người dùng và giao diện cho website, mobile app, SaaS hoặc sản phẩm số.",
        "required_skills": [
            "Figma",
            "Design Thinking",
            "User Research",
            "Prototyping",
            "Design System",
        ],
        "salary_range": "Junior: 8-15tr | Middle: 15-28tr | Senior: 28-45tr VNĐ/tháng",
        "growth_outlook": "Tốt nếu có portfolio mạnh và hiểu sâu về sản phẩm.",
        "education": "Phù hợp với thiết kế, mỹ thuật, truyền thông hoặc người yêu thích sáng tạo sản phẩm.",
        "riasec": {
            "R": 1,
            "I": 2,
            "A": 5,
            "S": 3,
            "E": 2,
            "C": 2,
        },
    },
}


# ============================================================
# 🧩 HELPER FUNCTIONS
# ============================================================

def _safe_json(data: Any) -> str:
    """
    Chuyển dữ liệu Python sang JSON string an toàn, hỗ trợ tiếng Việt.
    """
    return json.dumps(data, ensure_ascii=False, indent=2)


def _normalize_text(text: str) -> str:
    """
    Chuẩn hóa text về lowercase và strip.
    """
    return str(text).strip().lower()


def _find_career_id(value: str) -> str:
    """
    Tìm career_id từ id hoặc tên nghề.
    """
    key = _normalize_text(value)

    for career_id, career in CAREER_DB.items():
        name = _normalize_text(career["name"])

        if key == career_id:
            return career_id

        if key == name:
            return career_id

        if key in name or name in key:
            return career_id

    return ""


# ============================================================
# 🔧 TOOLS
# ============================================================

def run_personality_assessment(answers: Dict[str, int]) -> str:
    """
    Chấm điểm trắc nghiệm định hướng nghề nghiệp theo rubric RIASEC self-built.

    Name:
        run_personality_assessment

    Purpose:
        Dùng khi người dùng trả lời bộ câu hỏi tính cách/sở thích.
        Không dùng để tra cứu thông tin nghề cụ thể.

    Input schema:
        answers (dict): Dictionary gồm các key thuộc R, I, A, S, E, C.
                        Giá trị là điểm từ 1 đến 5.
                        Ví dụ: {"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}

    Output schema:
        str: JSON string chứa vector RIASEC, top_traits và holland_code.

    Error semantics:
        Nếu thiếu input, sai kiểu dữ liệu hoặc điểm ngoài 1-5 -> trả về "LỖI: ...".

    Side effect:
        Read-only, không thay đổi trạng thái.

    Example:
        >>> run_personality_assessment({"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4})
    """
    try:
        if not isinstance(answers, dict):
            return "LỖI: answers phải là dict. Ví dụ: {'R': 2, 'I': 5, 'A': 3, 'S': 2, 'E': 1, 'C': 4}."

        traits = ["R", "I", "A", "S", "E", "C"]
        vector = {}

        for trait in traits:
            score = answers.get(trait, 0)

            if not isinstance(score, int):
                return f"LỖI: Điểm của '{trait}' phải là số nguyên từ 1 đến 5."

            if score < 0 or score > 5:
                return f"LỖI: Điểm của '{trait}' phải nằm trong khoảng 0 đến 5."

            vector[trait] = score

        ranked = sorted(vector.items(), key=lambda x: x[1], reverse=True)
        holland_code = "".join([item[0] for item in ranked[:3]])

        result = {
            "profile_vector": vector,
            "top_traits": ranked[:3],
            "holland_code": holland_code,
            "note": "Vector này có thể dùng làm input cho match_profile_to_careers.",
        }

        return _safe_json(result)

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi chấm trắc nghiệm tính cách ({e})."


def get_career_detail(career_id: str) -> str:
    """
    Lấy chi tiết một nghề theo career_id.

    Name:
        get_career_detail

    Purpose:
        Dùng khi người dùng muốn xem chi tiết nghề vừa được định hướng/gợi ý:
        mô tả, kỹ năng, lương, triển vọng.

    Input schema:
        career_id (str): ID hoặc tên nghề.
                         Ví dụ: "ai_engineer", "AI Engineer".

    Output schema:
        str: JSON string chứa thông tin chi tiết nghề.

    Error semantics:
        Nếu không tìm thấy career_id -> "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> get_career_detail("ai_engineer")
    """
    try:
        found_id = _find_career_id(career_id)

        if not found_id:
            return f"LỖI: Không tìm thấy nghề '{career_id}'. Nghề hỗ trợ: {list(CAREER_DB.keys())}."

        return _safe_json(CAREER_DB[found_id])

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi lấy chi tiết nghề nghiệp ({e})."


def match_profile_to_careers(profile_vector: Dict[str, int], top_k: int = 3) -> str:
    """
    Match hồ sơ người dùng với danh sách nghề bằng similarity score.

    Name:
        match_profile_to_careers

    Purpose:
        Dùng khi đã có vector đặc điểm người dùng và cần xếp hạng nghề phù hợp.
        Đây là logic tính toán deterministic, không để LLM tự đoán điểm match.

    Input schema:
        profile_vector (dict): Vector RIASEC, ví dụ {"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}
        top_k (int): Số nghề muốn trả về.

    Output schema:
        str: JSON string chứa ranked list nghề phù hợp.

    Error semantics:
        Nếu vector sai định dạng hoặc top_k không hợp lệ -> "LỖI: ...".

    Side effect:
        Read-only.

    Example:
        >>> match_profile_to_careers({"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}, 3)
    """
    try:
        if not isinstance(profile_vector, dict):
            return "LỖI: profile_vector phải là dict."

        if not isinstance(top_k, int) or top_k <= 0:
            return "LỖI: top_k phải là số nguyên dương."

        traits = ["R", "I", "A", "S", "E", "C"]

        for trait in traits:
            if trait not in profile_vector:
                return f"LỖI: profile_vector thiếu trait '{trait}'."

            if not isinstance(profile_vector[trait], int):
                return f"LỖI: Giá trị của trait '{trait}' phải là số nguyên."

        matches = []

        for career_id, career in CAREER_DB.items():
            career_vector = career["riasec"]

            distance = 0
            for trait in traits:
                distance += abs(profile_vector[trait] - career_vector[trait])

            max_distance = 5 * len(traits)
            similarity = round((1 - distance / max_distance) * 100, 2)

            matches.append({
                "career_id": career_id,
                "name": career["name"],
                "similarity_percent": similarity,
                "reason": f"Phù hợp với nhóm đặc điểm nổi bật của nghề {career['name']}.",
            })

        matches = sorted(matches, key=lambda item: item["similarity_percent"], reverse=True)

        return _safe_json({
            "top_k": top_k,
            "matches": matches[:top_k],
        })

    except Exception as e:
        return f"LỖI: Xảy ra lỗi khi match hồ sơ với nghề nghiệp ({e})."


# ============================================================
# 📋 TOOL REGISTRY
# ============================================================

AVAILABLE_TOOLS = {
    "run_personality_assessment": run_personality_assessment,
    "match_profile_to_careers": match_profile_to_careers,
    "get_career_detail": get_career_detail,
}


# ============================================================
# ✅ SELF-TEST
# Chạy: python src/tools.py
# ============================================================

if __name__ == "__main__":
    test_cases = [
        (
            "run_personality_assessment",
            ({"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4},),
            "Chấm RIASEC hợp lệ",
        ),
        (
            "run_personality_assessment",
            ("sai input",),
            "Input sai kiểu dữ liệu",
        ),
        (
            "match_profile_to_careers",
            ({"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}, 3),
            "Match profile với nghề",
        ),
        (
            "get_career_detail",
            ("ai_engineer",),
            "Lấy chi tiết nghề",
        ),
        (
            "get_career_detail",
            ("phi_hanh_gia",),
            "Nghề không tồn tại",
        ),
    ]

    passed = 0

    for tool_name, args, description in test_cases:
        try:
            result = AVAILABLE_TOOLS[tool_name](*args)

            assert isinstance(result, str)
            assert len(result) > 0

            print(f"✅ PASS | {tool_name}{args} | {description}")
            print(f"   -> {result[:160]}...\n")

            passed += 1

        except Exception as e:
            print(f"❌ FAIL | {tool_name}{args} | {description}")
            print(f"   Crash: {e}\n")

    print(f"KẾT QUẢ: {passed}/{len(test_cases)} test PASS")
