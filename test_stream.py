import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from app import run_react_agent_stream
from providers import get_llm_provider
from dotenv import load_dotenv

load_dotenv()

provider = get_llm_provider()
answers = {"R": 2, "I": 5, "A": 3, "S": 2, "E": 1, "C": 4}
query = "Nghề nào phù hợp với tính cách của tôi?"

print("Simulating query:", query)
for event in run_react_agent_stream(query, provider, answers):
    print("EVENT:", event.strip())
