"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_stream(self, prompt: str, system_prompt: str = ""):
        """Sinh kết quả dạng stream (yield chunks)"""
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def _build_config(self):
        """
        Các model Gemini "thinking" (2.5/3.x flash trở lên) mặc định dành 1 phần
        max_output_tokens cho suy luận ẩn (không hiển thị). Nếu không giới hạn rõ,
        với prompt dài (scratchpad ReAct tích lũy nhiều bước) model có thể dùng hết
        token cho "thinking" và trả về response.text RỖNG — làm ReAct Agent tốn oan
        1 bước Guardrail mỗi lần gặp. Tắt thinking (budget=0) và đặt max_output_tokens
        đủ lớn để ưu tiên trả lời đúng định dạng Thought/Action ngắn gọn, xác định.
        """
        from google.genai import types

        # Các model "-lite" không có thinking để tắt -> gửi thinking_config sẽ bị
        # API từ chối với lỗi 400 INVALID_ARGUMENT. Chỉ áp dụng cho model "thinking" thật.
        if "lite" in self.model_name.lower():
            return types.GenerateContentConfig(max_output_tokens=2048)

        try:
            return types.GenerateContentConfig(
                max_output_tokens=2048,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
        except Exception:
            # Model/SDK version không hỗ trợ thinking_config -> vẫn giới hạn max_output_tokens
            return types.GenerateContentConfig(max_output_tokens=2048)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            config = self._build_config()

            # Gemini đôi khi trả về response rỗng với finish_reason MALFORMED_RESPONSE
            # (lỗi tạm thời/không xác định phía Google, không lặp lại theo prompt cố định).
            # Thử lại vài lần trước khi báo lỗi, để không lãng phí bước Guardrail của ReAct Agent.
            last_error = None
            for attempt in range(3):
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
                if response.text:
                    return response.text
                finish_reason = response.candidates[0].finish_reason if response.candidates else None
                last_error = finish_reason

            return f"[Gemini Error]: Model trả về câu trả lời rỗng sau 3 lần thử (finish_reason={last_error})."
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_stream(self, prompt: str, system_prompt: str = ""):
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            yield "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
            return
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            config = self._build_config()

            # Giống generate(): nếu cả stream không có chunk nào (response rỗng do lỗi tạm
            # thời MALFORMED_RESPONSE phía Google), thử lại tối đa 3 lần trước khi báo lỗi.
            for attempt in range(3):
                response = client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
                got_any_chunk = False
                for chunk in response:
                    if chunk.text:
                        got_any_chunk = True
                        yield chunk.text
                if got_any_chunk:
                    return
            return
        except Exception as e:
            yield f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_stream(self, prompt: str, system_prompt: str = ""):
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            yield "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
            return
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"

    def generate_stream(self, prompt: str, system_prompt: str = ""):
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            yield "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
            return
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            with client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"

    def generate_stream(self, prompt: str, system_prompt: str = ""):
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            yield "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
            return
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": True
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, stream=True, timeout=30)
            if res.status_code == 200:
                for line in res.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                import json
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except:
                                pass
            else:
                yield f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            yield f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()

        # Đã có Observation chứa profile_vector (bước 1 đã chạy) -> kết luôn cho demo offline gọn.
        if "observation" in text and "profile_vector" in text:
            return (
                "Thought: Tôi đã có đủ thông tin để trả lời.\n"
                "Final Answer: (Mock) Dựa trên hồ sơ tính cách, nghề phù hợp nhất với bạn là Công nghệ thông tin."
            )

        if "tính cách" in text or "riasec" in text or "phù hợp" in text:
            return (
                "Thought: Cần chấm trắc nghiệm RIASEC để hiểu tính cách người dùng.\n"
                "Action: run_personality_assessment[{'R': 2, 'I': 5, 'A': 3, 'S': 2, 'E': 1, 'C': 4}]"
            )
        return "🤖 [Mock Provider]: Phản hồi giả lập offline cho bài test."

    def generate_stream(self, prompt: str, system_prompt: str = ""):
        import time
        result = self.generate(prompt, system_prompt)
        for word in result.split(" "):
            yield word + " "
            time.sleep(0.05)


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
