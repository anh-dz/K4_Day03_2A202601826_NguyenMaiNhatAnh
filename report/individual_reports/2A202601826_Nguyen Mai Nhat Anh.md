# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Mai Nhat Anh
- **Student ID**: 2A202601826
- **Date**: 28/07/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implemented**: 
  - `src/providers.py` ([GeminiProvider](file:///Users/nhatanh245/Documents/Project/K4_Day03_2A202601826_NguyenMaiNhatAnh/src/providers.py#L31)): Integrated streaming capability (`generate_stream`) across LLM providers including Gemini, Mock, OpenAI, Anthropic, and OpenRouter to yield tokens step-by-step.
  - `src/app.py` ([run_react_agent_stream](file:///Users/nhatanh245/Documents/Project/K4_Day03_2A202601826_NguyenMaiNhatAnh/src/app.py#L190)): Refactored the core ReAct agent execution loop to support Server-Sent Events (SSE) streaming. Implemented a smart buffering system that hides internal reasoning (`Thought` / `Action` blocks) and only begins streaming text when the `Final Answer` is detected.
  - `src/server.py` ([/api/chat](file:///Users/nhatanh245/Documents/Project/K4_Day03_2A202601826_NguyenMaiNhatAnh/src/server.py#L29)): Rewrote the backend API handler to stream response tokens dynamically using Flask's `stream_with_context`.
  - `ui/index.html` ([fetchAIResponse](file:///Users/nhatanh245/Documents/Project/K4_Day03_2A202601826_NguyenMaiNhatAnh/ui/index.html#L430)): Replaced static JSON parsing with a real-time SSE stream reader, utilizing `Marked.js` for markdown rendering and `DOMPurify` to ensure safe, cross-site scripting (XSS)-free HTML rendering.
  - `src/prompts.py` ([REACT_SYSTEM_PROMPT](file:///Users/nhatanh245/Documents/Project/K4_Day03_2A202601826_NguyenMaiNhatAnh/src/prompts.py#L22)): Added short-circuit guidelines to optimize token usage when the user asks irrelevant questions, bypassing tool execution. Disabled automated deep searches by removing the `get_career_detail` tool from default prompts to mitigate Gemini API quota exhaustion.
  
- **Code Highlights**:
  - **Self-Healing Fallback Parser** in `_parse_llm_action` and `run_react_agent_stream`:
    ```python
    # FALLBACK TỰ ĐỘNG CHỮA LỖI (SELF-HEALING) NẾU LLM QUÊN GHI "Final Answer:"
    if not action_match and len(text.strip()) > 10:
        fallback_text = re.sub(r"^Thought:\s*", "", text.strip(), flags=re.IGNORECASE)
        return {"type": "final_answer", "content": fallback_text}
    ```
  - **SSE Streaming Integration** in `/api/chat`:
    ```python
    @app.route('/api/chat', methods=['POST'])
    def chat():
        data = request.json or {}
        message = data.get('message', '')
        answers = data.get('answers', None)
        return Response(stream_with_context(run_react_agent_stream(message, provider, answers)), mimetype='text/event-stream')
    ```

- **Documentation**: 
  The ReAct loop executes inside `run_react_agent_stream`. Whenever the LLM outputs an `Action: tool_name[args]`, it suspends generation, runs the local Python function from `src/tools.py`, appends the result as an `Observation`, and feeds it back into the prompt. Once a `Final Answer:` is reached or the self-healing fallback detects regular text, the stream is closed with a `{"done": true}` token.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: 
  The agent frequently crashed with the message: `"Hệ thống đã đạt giới hạn tối đa 5 bước suy luận. Xin vui lòng thử lại."` when users requested detail on a recommended career, or when the LLM answered without using the strictly required `Final Answer:` tag.

- **Log Source**: 
  Found in [.system_generated/tasks/task-315.log](file:///Users/nhatanh245/.gemini/antigravity-ide/brain/eb3f49fc-de68-42be-b359-2c26f21e716b/.system_generated/tasks/task-315.log):
  ```
  --- 🔄 Vòng lặp ReAct Stream (Step 1/5) ---
  Action: match_profile_to_careers[...]
  --- 🔄 Vòng lặp ReAct Stream (Step 2/5) ---
  Action: get_career_detail[kinh_te_kinh_doanh]
  --- 🔄 Vòng lặp ReAct Stream (Step 3/5) ---
  Action: get_career_detail[y_suc_khoe]
  --- 🔄 Vòng lặp ReAct Stream (Step 4/5) ---
  Action: get_career_detail[luat]
  --- 🔄 Vòng lặp ReAct Stream (Step 5/5) ---
  🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa 5 bước.
  ```

- **Diagnosis**: 
  The LLM was trying to be too thorough by executing multiple tool calls sequentially: querying matched careers, and then making separate queries to get details for *every* career returned. This quickly consumed 4 out of the 5 allowed `MAX_ITERATIONS` steps. Any subsequent step trying to formulate the final answer or recover from formatting issues was cut short by the 5-step safety guardrail.

- **Solution**: 
  1. Increased the `MAX_ITERATIONS` safety ceiling from 5 to 10 in `src/prompts.py` to give the agent more headroom.
  2. Implemented the self-healing fallback parser in `src/app.py` to intercept and stream replies that are missing the `Final Answer:` prefix but do not call any tool.
  3. Removed `get_career_detail` from the available tools list in the system prompt to prevent the agent from performing expensive automated sub-queries, forcing it to use its general reasoning for descriptions instead.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1. **Reasoning**: The `Thought` block acts as the agent's internal monologue/scratchpad. It allows the model to decompose the user's intent into logical steps (e.g., "I need to run the personality test first, then match careers, then format the response") before selecting a tool. Baseline chatbots try to jump straight to the conclusion, resulting in hallucinated RIASEC scores and made-up career alignments.
2. **Reliability**: ReAct Agents perform *worse* when users ask simple chit-chat or out-of-domain questions (e.g., "hi", "weather", or "give me windows 10 key"). Without prompt guardrails, the agent gets confused by the automatically injected survey scores and starts invoking tools (assessment, matching) on a greeting, consuming unnecessary tokens and rate limits.
3. **Observation**: Observations serve as real-world feedback loops. When a tool outputs `"LỖI: answers phải là dict"`, the agent reads this in the observation block and uses its next `Thought` to correct the parameter format, illustrating the self-correcting behavior of ReAct.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Move tool executions to an asynchronous background task worker (e.g., Celery with Redis) so long-running database matches or API lookups do not block the active Flask server thread.
- **Safety**: Introduce structured output validation (e.g., using `Pydantic` or `Instructor`) on the raw `Action` parameters to guarantee valid JSON structures before calling the tools, preventing execution-level code errors.
- **Performance**: Implement semantic caching (e.g., using a Vector DB like Milvus/Qdrant) to cache Holland score mappings. If another user answers the survey with similar traits, the agent can retrieve the career list instantly from the cache, avoiding LLM calls entirely.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
