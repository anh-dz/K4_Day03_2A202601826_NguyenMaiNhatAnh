


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

# Các mục dưới đây là HƯỚNG NGHỀ NGHIỆP PHỔ BIẾN (ngành/nhóm nghề lớn),
# không phải job title cụ thể — phù hợp cho đối tượng học sinh THPT đang định hướng.
CAREER_DB = {
    "cntt": {
        "id": "cntt",
        "name": "Công nghệ thông tin",
        "description": "Xây dựng phần mềm, hệ thống, dữ liệu và các sản phẩm công nghệ số.",
        "required_skills": [
            "Lập trình",
            "Tư duy logic",
            "Giải quyết vấn đề",
            "Toán/Tin học",
            "Tự học công nghệ mới",
        ],
        "salary_range": "10 - 40 triệu VNĐ/tháng tùy vị trí và kinh nghiệm",
        "growth_outlook": "Rất cao, nhu cầu tăng mạnh nhờ chuyển đổi số và AI.",
        "education": "Phù hợp với CNTT, Khoa học máy tính, Kỹ thuật phần mềm hoặc tự học lập trình.",
        "riasec": {
            "R": 2,
            "I": 5,
            "A": 2,
            "S": 1,
            "E": 2,
            "C": 4,
        },
    },
    "kinh_te_kinh_doanh": {
        "id": "kinh_te_kinh_doanh",
        "name": "Kinh tế - Kinh doanh - Quản trị",
        "description": "Quản lý, vận hành, kinh doanh, tài chính và phát triển doanh nghiệp.",
        "required_skills": [
            "Giao tiếp",
            "Đàm phán",
            "Phân tích thị trường",
            "Lãnh đạo",
            "Tư duy chiến lược",
        ],
        "salary_range": "8 - 35 triệu VNĐ/tháng tùy vị trí và kinh nghiệm",
        "growth_outlook": "Ổn định, nhu cầu cao ở mọi ngành.",
        "education": "Phù hợp với Kinh tế, Quản trị kinh doanh, Tài chính - Ngân hàng.",
        "riasec": {
            "R": 1,
            "I": 2,
            "A": 2,
            "S": 3,
            "E": 5,
            "C": 4,
        },
    },
    "ky_thuat_cong_nghe": {
        "id": "ky_thuat_cong_nghe",
        "name": "Kỹ thuật - Công nghệ kỹ thuật",
        "description": "Thiết kế, chế tạo, vận hành máy móc, công trình và hệ thống kỹ thuật.",
        "required_skills": [
            "Tư duy kỹ thuật",
            "Toán/Vật lý",
            "Sử dụng phần mềm kỹ thuật (CAD...)",
            "Làm việc thực địa",
        ],
        "salary_range": "9 - 30 triệu VNĐ/tháng tùy vị trí và kinh nghiệm",
        "growth_outlook": "Cao, đặc biệt trong sản xuất, xây dựng, năng lượng.",
        "education": "Phù hợp với Cơ khí, Điện - Điện tử, Xây dựng, Kỹ thuật ô tô.",
        "riasec": {
            "R": 5,
            "I": 3,
            "A": 1,
            "S": 1,
            "E": 2,
            "C": 3,
        },
    },
    "y_suc_khoe": {
        "id": "y_suc_khoe",
        "name": "Y - Sức khỏe",
        "description": "Khám chữa bệnh, chăm sóc sức khỏe, dược phẩm và y tế cộng đồng.",
        "required_skills": [
            "Kiến thức y sinh",
            "Chịu áp lực cao",
            "Tỉ mỉ, cẩn thận",
            "Đồng cảm với người bệnh",
        ],
        "salary_range": "10 - 50 triệu VNĐ/tháng tùy chuyên khoa và kinh nghiệm",
        "growth_outlook": "Rất cao, nhu cầu ổn định lâu dài.",
        "education": "Phù hợp với Y đa khoa, Dược, Điều dưỡng, Y tế công cộng.",
        "riasec": {
            "R": 2,
            "I": 5,
            "A": 1,
            "S": 5,
            "E": 1,
            "C": 3,
        },
    },
    "su_pham_giao_duc": {
        "id": "su_pham_giao_duc",
        "name": "Sư phạm - Giáo dục",
        "description": "Giảng dạy, đào tạo và phát triển chương trình giáo dục các cấp.",
        "required_skills": [
            "Truyền đạt",
            "Kiên nhẫn",
            "Xây dựng giáo án",
            "Thấu hiểu tâm lý người học",
        ],
        "salary_range": "7 - 25 triệu VNĐ/tháng tùy cấp học và loại hình",
        "growth_outlook": "Ổn định, thêm cơ hội từ giáo dục trực tuyến/tư nhân.",
        "education": "Phù hợp với Sư phạm, Ngôn ngữ học, Tâm lý giáo dục.",
        "riasec": {
            "R": 1,
            "I": 3,
            "A": 2,
            "S": 5,
            "E": 2,
            "C": 2,
        },
    },
    "nghe_thuat_thiet_ke": {
        "id": "nghe_thuat_thiet_ke",
        "name": "Nghệ thuật - Thiết kế",
        "description": "Sáng tạo hình ảnh, sản phẩm, trải nghiệm thị giác cho thương hiệu và người dùng.",
        "required_skills": [
            "Tư duy thẩm mỹ",
            "Sử dụng phần mềm thiết kế",
            "Sáng tạo",
            "Kể chuyện bằng hình ảnh",
        ],
        "salary_range": "7 - 30 triệu VNĐ/tháng tùy portfolio và kinh nghiệm",
        "growth_outlook": "Tốt nếu có portfolio mạnh, đặc biệt trong ngành số.",
        "education": "Phù hợp với Thiết kế đồ họa, Mỹ thuật, Truyền thông đa phương tiện.",
        "riasec": {
            "R": 1,
            "I": 2,
            "A": 5,
            "S": 3,
            "E": 2,
            "C": 2,
        },
    },
    "luat": {
        "id": "luat",
        "name": "Luật",
        "description": "Tư vấn, soạn thảo, tranh tụng và bảo vệ quyền lợi pháp lý cho cá nhân/tổ chức.",
        "required_skills": [
            "Tư duy phản biện",
            "Phân tích văn bản",
            "Lập luận chặt chẽ",
            "Kiến thức pháp luật",
        ],
        "salary_range": "8 - 40 triệu VNĐ/tháng tùy lĩnh vực và kinh nghiệm",
        "growth_outlook": "Ổn định, tăng theo nhu cầu tuân thủ pháp lý của doanh nghiệp.",
        "education": "Phù hợp với Luật, Luật kinh tế, Luật quốc tế.",
        "riasec": {
            "R": 1,
            "I": 3,
            "A": 1,
            "S": 3,
            "E": 4,
            "C": 5,
        },
    },
    "truyen_thong_bao_chi": {
        "id": "truyen_thong_bao_chi",
        "name": "Truyền thông - Báo chí",
        "description": "Sản xuất nội dung, quản lý thương hiệu và truyền tải thông tin tới công chúng.",
        "required_skills": [
            "Viết lách",
            "Kể chuyện",
            "Nắm bắt xu hướng",
            "Làm việc đa nền tảng",
        ],
        "salary_range": "7 - 28 triệu VNĐ/tháng tùy vị trí và kinh nghiệm",
        "growth_outlook": "Cao, đặc biệt với truyền thông số và mạng xã hội.",
        "education": "Phù hợp với Báo chí, Truyền thông đa phương tiện, Quan hệ công chúng.",
        "riasec": {
            "R": 1,
            "I": 2,
            "A": 4,
            "S": 3,
            "E": 4,
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
            ("cntt",),
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
