"""Quick test of all 4 LLM APIs"""
import sys
from agents.llm_comparison import OllamaLLM, GLMLLM, GeminiLLM, OpenAILLM

PROMPT = "In one sentence, what is the most common cause of industrial motor vibration?"

llms = [OllamaLLM(), GLMLLM(), GeminiLLM(), OpenAILLM()]

print("=" * 60)
print("🧠 LLM API CONNECTIVITY TEST")
print("=" * 60)

all_ok = True
for llm in llms:
    print(f"\n🔍 Testing {llm.name} ({llm.model_name})...")
    result = llm.query(PROMPT)
    if result['success']:
        preview = result['response'][:120].replace('\n', ' ')
        print(f"   ✅ OK  | {result['latency_ms']:.0f}ms")
        print(f"   Response: {preview}...")
    else:
        print(f"   ❌ FAIL | {result['error']}")
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✅ ALL 4 LLMs WORKING!")
else:
    print("⚠️  Some LLMs failed (see above). App will still work for successful ones.")
print("=" * 60)
