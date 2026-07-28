import sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from app import run_react_agent_stream
from providers import get_llm_provider
provider = get_llm_provider()
answers = {"R": 5, "I": 5, "A": 5, "S": 5, "E": 5, "C": 5}
query = "Nghề nào phù hợp với tính cách của tôi?"

print("Simulating query:", query)
for event in run_react_agent_stream(query, provider, answers):
    print("EVENT:", event.strip())
