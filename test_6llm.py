from agents.llm_comparison import LLMComparisonEngine

e = LLMComparisonEngine()
print("Active models:", [l.name for l in e.llms])

result = e.compare(
    "M3", "vibration", 78, "Critical", 4, 240, 3,
    ["High incident frequency", "Multiple temp fixes", "Recent deterioration"]
)

print()
for r in result["results"]:
    status = "LIVE" if not r["is_demo"] else "DEMO"
    print(f"[{status}] {r['llm_name']}: quality={r['quality_score']}/100, latency={r['latency_ms']:.0f}ms, words={r['word_count']}")

print()
c = result["collective"]
print("Collective:", c["summary"])
print("Agreement:", c["agreement_level"])
print("Best from:", c["best_response_from"])
print("Top actions:", [(a, cnt) for a, cnt in c["top_actions"]])
