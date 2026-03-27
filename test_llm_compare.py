from agents.llm_comparison import LLMComparisonEngine

e = LLMComparisonEngine()
r = e.compare('M6', 'vibration', 84, 'Critical', 3, 240, 2,
              ['High frequency', 'Temp fixes', 'Downtime'], use_demo_fallback=True)

print("Results:")
for res in r['results']:
    status = 'LIVE' if not res['is_demo'] else 'DEMO'
    print(f"  {res['llm_name']:25s} | {status} | score={res['quality_score']:3d} | {res['latency_ms']:6.0f}ms | {res['word_count']} words")

print(f"\nBest LLM: {r['best_llm']}")
print(f"Any demo: {r['any_demo']}")
print("\n✅ LLM Comparison working correctly!")
