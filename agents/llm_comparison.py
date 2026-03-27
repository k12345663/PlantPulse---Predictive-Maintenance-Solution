"""LLM Comparison Engine - Compare cloud Ollama models + Gemini + OpenAI"""

import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# API Keys — loaded from .env (never hardcode secrets)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


def build_maintenance_prompt(machine_id, issue_type, risk_score, risk_level,
                              recent_incidents, downtime_minutes, temp_fix_count,
                              top_factors):
    """Build the same prompt for all LLMs so comparison is fair"""
    return f"""You are an industrial maintenance expert AI assistant.

Machine: {machine_id}
Issue Type: {issue_type}
Risk Score: {risk_score}/100 ({risk_level})
Recent Incidents (7 days): {recent_incidents}
Total Downtime: {downtime_minutes} minutes
Temporary Fixes Applied: {temp_fix_count}
Key Risk Factors: {', '.join(top_factors[:3])}

Provide a structured maintenance recommendation with:
1. Root Cause Analysis (1-2 sentences)
2. Immediate Action (what to do in next 24 hours)
3. Long-term Fix (permanent solution)
4. Estimated Downtime for repair
5. Priority Level (Critical/High/Medium/Low)
6. Confidence in recommendation (%)

Keep response concise and practical. Use plain text, no markdown."""


# ── Demo responses ────────────────────────────────────────────────────────────
_DEMO_RESPONSES = {
    "DeepSeek-V3 (Ollama)": {
        "vibration": """Root Cause Analysis: Bearing degradation combined with rotor imbalance is the root cause. The pattern of 3 temporary fixes without permanent resolution has accelerated wear progression beyond normal limits.

Immediate Action: Reduce operating load by 30% immediately. Schedule bearing inspection within 12 hours. Assign senior technician -- do not allow junior staff to operate machine until inspected.

Long-term Fix: Full bearing replacement with precision laser alignment. Install real-time vibration monitoring with automated alerts. Revise PM schedule to include monthly bearing checks.

Estimated Downtime: 4-6 hours for replacement and post-repair test run.

Priority Level: Critical

Confidence: 88%""",
        "overheating": """Root Cause Analysis: Cooling system degradation from fan blade wear and blocked ventilation paths has reduced heat dissipation capacity, causing progressive thermal buildup under normal load.

Immediate Action: Reduce machine load to 50% immediately. Measure motor winding temperature. If above 85 degrees C, shut down for inspection. Clean all ventilation grilles within 6 hours.

Long-term Fix: Replace cooling fan assembly. Clean motor internals. Install thermal monitoring relay with auto-shutdown at 90 degrees C. Schedule quarterly cooling system inspection.

Estimated Downtime: 3-5 hours.

Priority Level: High

Confidence: 85%"""
    },
    "GLM-5 (Ollama)": {
        "vibration": """Root Cause Analysis: Mechanical imbalance in rotating components, most likely bearing wear or shaft misalignment, exacerbated by repeated temporary fixes without addressing root cause.

Immediate Action: Perform vibration frequency analysis within 24 hours. Isolate machine if vibration exceeds 7mm/s RMS. Notify maintenance supervisor.

Long-term Fix: Complete bearing replacement with precision alignment. Install continuous vibration monitoring sensor. Update preventive maintenance interval to 500 hours.

Estimated Downtime: 5-8 hours including alignment verification.

Priority Level: Critical

Confidence: 83%""",
        "overheating": """Root Cause Analysis: Thermal stress from inadequate cooling, possibly due to fan degradation or blocked heat dissipation paths, causing insulation breakdown risk.

Immediate Action: Measure winding temperature immediately. If above 120 degrees C, shut down. Clean all cooling surfaces within 8 hours.

Long-term Fix: Replace cooling system components. Install thermal protection relay. Implement predictive thermal monitoring.

Estimated Downtime: 4-5 hours.

Priority Level: High

Confidence: 79%"""
    },
    "Gemini (Google)": {
        "vibration": """Root Cause Analysis: Progressive bearing degradation is the primary cause, with vibration amplitude increasing due to metal fatigue in the bearing races. The high number of temporary fixes suggests the root cause was never properly addressed.

Immediate Action: Immediately reduce operating speed by 20%. Schedule emergency bearing inspection within 24 hours. Document vibration readings every 2 hours until repair.

Long-term Fix: Full bearing replacement with upgraded sealed bearings. Implement oil analysis program. Install IoT vibration sensor for real-time monitoring. Review lubrication schedule.

Estimated Downtime: 6-8 hours for complete overhaul.

Priority Level: Critical

Confidence: 91%""",
        "overheating": """Root Cause Analysis: Thermal management failure due to combination of cooling fan degradation and possible winding insulation breakdown from repeated thermal cycling.

Immediate Action: Perform thermal imaging scan immediately. Reduce load to 50% capacity. Check all cooling pathways for blockages.

Long-term Fix: Replace cooling fan and thermal sensors. Rewind motor if insulation resistance below 1 megaohm. Install temperature monitoring with automatic shutdown.

Estimated Downtime: 4-12 hours depending on winding condition.

Priority Level: High

Confidence: 88%"""
    },
    "GPT-3.5 (OpenAI)": {
        "vibration": """Root Cause Analysis: The vibration issue stems from bearing wear and possible rotor imbalance. Multiple temporary fixes indicate a recurring problem that requires permanent resolution to prevent catastrophic failure.

Immediate Action: Stop machine for inspection within 24 hours. Perform vibration spectrum analysis to identify frequency signature. Check bearing clearances and lubrication.

Long-term Fix: Replace bearings with OEM-specified components. Perform dynamic balancing of rotor. Implement predictive maintenance program with monthly vibration checks.

Estimated Downtime: 4-6 hours.

Priority Level: Critical

Confidence: 85%""",
        "overheating": """Root Cause Analysis: Overheating caused by cooling system degradation and possibly increased friction from worn components, leading to excessive heat generation.

Immediate Action: Check motor temperature with thermal camera. Verify cooling fan operation. Clean heat exchanger surfaces within 12 hours.

Long-term Fix: Replace cooling fan and clean motor internals. Install temperature monitoring system. Review duty cycle and loading conditions.

Estimated Downtime: 3-5 hours.

Priority Level: High

Confidence: 80%"""
    },
    "MiniMax-M2 (Ollama)": {
        "vibration": """Root Cause Analysis: Bearing fatigue failure is the primary driver, with surface spalling on the inner race causing periodic impulse vibration. Repeated temporary fixes have allowed progressive damage to accumulate.

Immediate Action: Reduce machine speed by 25% and schedule bearing inspection within 12 hours. Use stethoscope or vibration pen to confirm bearing noise signature. Tag machine for priority repair.

Long-term Fix: Replace bearing set with upgraded sealed bearings rated for higher load. Perform laser shaft alignment post-replacement. Introduce oil analysis every 250 operating hours to catch early wear.

Estimated Downtime: 3-5 hours for bearing swap and alignment check.

Priority Level: Critical

Confidence: 89%""",
        "overheating": """Root Cause Analysis: Cooling system efficiency has dropped significantly, likely due to fan blade erosion and heat exchanger fouling, causing thermal accumulation beyond design limits.

Immediate Action: Immediately check motor surface temperature. If above 90 degrees C, reduce load by 40%. Inspect cooling fan blades for damage within 8 hours.

Long-term Fix: Full cooling system overhaul: replace fan, clean heat exchanger, verify thermal cutout settings. Add remote temperature monitoring.

Estimated Downtime: 4-6 hours.

Priority Level: High

Confidence: 84%"""
    },
    "Kimi-K2 (Ollama)": {
        "vibration": """Root Cause Analysis: The vibration signature is consistent with advanced bearing wear combined with possible coupling misalignment. Repeated temporary fixes have masked the deterioration, allowing secondary damage to develop in adjacent components.

Immediate Action: Isolate machine from production line within 24 hours. Conduct vibration frequency analysis to distinguish bearing fault from imbalance. Prepare replacement bearing kit before shutdown.

Long-term Fix: Replace bearings and coupling. Perform precision dynamic balancing. Install permanent vibration monitoring sensor with threshold alerts to prevent recurrence.

Estimated Downtime: 5-7 hours including post-repair verification run.

Priority Level: Critical

Confidence: 86%""",
        "overheating": """Root Cause Analysis: Thermal failure progression due to degraded cooling capacity and increased internal friction from worn components, creating a compounding heat generation cycle.

Immediate Action: Deploy portable cooling fan to motor housing immediately. Reduce production load to 60%. Schedule thermal camera inspection within 6 hours to map hot spots.

Long-term Fix: Replace cooling fan assembly and clean all ventilation paths. Install thermal protection relay with auto-shutdown. Review motor loading profile against nameplate rating.

Estimated Downtime: 3-5 hours.

Priority Level: High

Confidence: 81%"""
    },
    "Qwen3-Next-80B (Ollama)": {
        "vibration": """Root Cause Analysis: Advanced bearing fatigue with inner race spalling is the root cause, compounded by shaft misalignment that has increased radial load beyond design specification. Repeated temporary fixes have allowed secondary damage to propagate to adjacent components.

Immediate Action: Immediately reduce machine load by 25% and tag for priority inspection. Perform vibration frequency analysis to confirm bearing fault signature. Pre-order replacement bearing set and coupling before shutdown to minimize repair window.

Long-term Fix: Complete bearing and coupling replacement with precision laser alignment verification. Install continuous vibration monitoring with automated shutdown threshold. Revise lubrication schedule to monthly intervals and introduce oil analysis program.

Estimated Downtime: 5-7 hours including alignment verification and test run.

Priority Level: Critical

Confidence: 93%""",
        "overheating": """Root Cause Analysis: Compound thermal failure from cooling fan blade erosion reducing airflow by approximately 35%, combined with heat exchanger fouling and possible early-stage winding insulation degradation from repeated thermal cycling.

Immediate Action: Deploy portable cooling immediately. Perform thermal imaging scan to map hot spots. If winding temperature exceeds 90 degrees C, shut down for inspection. Clean all ventilation paths within 4 hours.

Long-term Fix: Full cooling system overhaul -- replace fan assembly, clean heat exchanger, test winding insulation resistance. Install thermal protection relay with auto-shutdown at 90 degrees C and remote temperature monitoring.

Estimated Downtime: 4-8 hours depending on winding condition.

Priority Level: High

Confidence: 91%"""
    }
}

_DEMO_LATENCIES = {
    "GLM-5 (Ollama)":           5100,
    "DeepSeek-V3 (Ollama)":     9200,
    "Gemini (Google)":           890,
    "GPT-3.5 (OpenAI)":         1540,
    "MiniMax-M2 (Ollama)":      6800,
    "Kimi-K2 (Ollama)":         7200,
    "Qwen3-Next-80B (Ollama)":  11500,
}


# ── LLM Classes ───────────────────────────────────────────────────────────────

def _get_ollama_available_models():
    """Return set of model names currently pulled in Ollama"""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            return {m["name"] for m in resp.json().get("models", [])}
    except Exception:
        pass
    return set()


def _ollama_query(model_name, prompt, timeout=20):
    """Shared Ollama query helper — 20s timeout so slow models fail fast to demo"""
    start = time.time()
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=timeout
        )
        elapsed = (time.time() - start) * 1000
        if resp.status_code == 200:
            text = resp.json().get("response", "").strip()
            return {"success": True, "response": text, "latency_ms": elapsed, "error": None}
        return {"success": False, "response": "", "latency_ms": elapsed,
                "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "response": "",
                "latency_ms": (time.time() - start) * 1000,
                "error": "Ollama not running"}
    except Exception as e:
        return {"success": False, "response": "",
                "latency_ms": (time.time() - start) * 1000, "error": str(e)}


class MiniMaxOllamaLLM:
    name = "MiniMax-M2 (Ollama)"
    model_name = "minimax-m2.7:cloud"
    color = "#E91E63"

    def query(self, prompt):
        return _ollama_query(self.model_name, prompt)


class KimiOllamaLLM:
    name = "Kimi-K2 (Ollama)"
    model_name = "kimi-k2.5:cloud"
    color = "#00BCD4"

    def query(self, prompt):
        return _ollama_query(self.model_name, prompt)


class DeepSeekOllamaLLM:
    name = "DeepSeek-V3 (Ollama)"
    model_name = "deepseek-v3.2:cloud"
    color = "#FF5722"

    def query(self, prompt):
        return _ollama_query(self.model_name, prompt)


class GLMOllamaLLM:
    name = "GLM-5 (Ollama)"
    model_name = "glm-5:cloud"
    color = "#9C27B0"

    def query(self, prompt):
        return _ollama_query(self.model_name, prompt)


class Qwen3Next80bOllamaLLM:
    name = "Qwen3-Next-80B (Ollama)"
    model_name = "qwen3-next:80b-cloud"
    color = "#00796B"

    def query(self, prompt):
        return _ollama_query(self.model_name, prompt)


class GeminiLLM:
    name = "Gemini (Google)"
    model_name = "gemini-2.0-flash"
    color = "#FF9800"

    def query(self, prompt):
        start = time.time()
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent",
                params={"key": GEMINI_API_KEY},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7}
                },
                timeout=30
            )
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return {"success": True, "response": text, "latency_ms": elapsed, "error": None}
            return {"success": False, "response": "", "latency_ms": elapsed,
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "response": "",
                    "latency_ms": (time.time() - start) * 1000, "error": str(e)}


class OpenAILLM:
    name = "GPT-3.5 (OpenAI)"
    model_name = "gpt-3.5-turbo"
    color = "#4CAF50"

    def query(self, prompt):
        start = time.time()
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are an industrial maintenance expert."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500, "temperature": 0.7
                },
                timeout=30
            )
            elapsed = (time.time() - start) * 1000
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                return {"success": True, "response": text, "latency_ms": elapsed, "error": None}
            return {"success": False, "response": "", "latency_ms": elapsed,
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "response": "",
                    "latency_ms": (time.time() - start) * 1000, "error": str(e)}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_demo_response(llm_name, issue_type):
    issue_key = issue_type.lower() if issue_type.lower() in ["vibration", "overheating"] else "vibration"
    # Fallback to DeepSeek if model not found in demo responses
    fallback = _DEMO_RESPONSES["DeepSeek-V3 (Ollama)"]
    return _DEMO_RESPONSES.get(llm_name, fallback).get(issue_key, fallback["vibration"])


# ── Main Engine ───────────────────────────────────────────────────────────────

class LLMComparisonEngine:
    """Compare all cloud LLMs on the same maintenance prompt"""

    def __init__(self):
        # Cloud API models (always included, fall back to demo if quota issues)
        cloud_api = [GeminiLLM(), OpenAILLM()]

        # Ollama cloud models — always included, demo fallback handles failures
        ollama_cloud = [
            MiniMaxOllamaLLM(),
            KimiOllamaLLM(),
            GLMOllamaLLM(),
            DeepSeekOllamaLLM(),
            Qwen3Next80bOllamaLLM(),
        ]

        # Ollama models first, then cloud APIs
        self.llms = ollama_cloud + cloud_api

    def compare_instant(self, machine_id, issue_type, risk_score, risk_level,
                        recent_incidents, downtime_minutes, temp_fix_count, top_factors):
        """
        Return demo responses instantly (< 100ms) — no API calls.
        Used for the fast demo mode in the UI.
        """
        prompt = build_maintenance_prompt(
            machine_id, issue_type, risk_score, risk_level,
            recent_incidents, downtime_minutes, temp_fix_count, top_factors
        )
        results = []
        for llm in self.llms:
            response_text = _get_demo_response(llm.name, issue_type)
            results.append({
                "llm_name":   llm.name,
                "model_name": llm.model_name,
                "color":      llm.color,
                "success":    True,
                "response":   response_text,
                "latency_ms": _DEMO_LATENCIES.get(llm.name, 2000),
                "error":      None,
                "is_demo":    True,
                "word_count": len(response_text.split()),
                "char_count": len(response_text),
            })

        for r in results:
            r["quality_score"] = self._score_response(r["response"])

        best_llm   = self._pick_best(results)
        collective = self._generate_collective_recommendation(results, machine_id, issue_type, risk_level)

        return {
            "prompt":     prompt,
            "machine_id": machine_id,
            "issue_type": issue_type,
            "risk_score": risk_score,
            "results":    results,
            "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "best_llm":   best_llm,
            "any_demo":   True,
            "collective": collective,
            "mode":       "instant",
        }

    def compare(self, machine_id, issue_type, risk_score, risk_level,
                recent_incidents, downtime_minutes, temp_fix_count, top_factors,
                use_demo_fallback=True):
        """Run all LLMs in parallel and return comparison"""

        prompt = build_maintenance_prompt(
            machine_id, issue_type, risk_score, risk_level,
            recent_incidents, downtime_minutes, temp_fix_count, top_factors
        )

        # ── Query all LLMs in parallel ────────────────────────────────────────
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def query_llm(llm):
            result = llm.query(prompt)
            if not result["success"] and use_demo_fallback:
                result = {
                    "success": True,
                    "response": _get_demo_response(llm.name, issue_type),
                    "latency_ms": _DEMO_LATENCIES.get(llm.name, 2000),
                    "error": None,
                    "is_demo": True
                }
            else:
                result["is_demo"] = False
            return llm, result

        raw_results = {}
        with ThreadPoolExecutor(max_workers=len(self.llms)) as executor:
            futures = {executor.submit(query_llm, llm): llm for llm in self.llms}
            for future in as_completed(futures):
                llm, result = future.result()
                raw_results[llm.name] = (llm, result)

        # Preserve original order
        results = []
        for llm in self.llms:
            llm_obj, result = raw_results[llm.name]
            results.append({
                "llm_name":   llm_obj.name,
                "model_name": llm_obj.model_name,
                "color":      llm_obj.color,
                "success":    result["success"],
                "response":   result["response"],
                "latency_ms": result["latency_ms"],
                "error":      result["error"],
                "is_demo":    result.get("is_demo", False),
                "word_count": len(result["response"].split()) if result["response"] else 0,
                "char_count": len(result["response"]) if result["response"] else 0,
            })

        for r in results:
            r["quality_score"] = self._score_response(r["response"]) if r["success"] else 0

        best_llm = self._pick_best(results)
        collective = self._generate_collective_recommendation(results, machine_id, issue_type, risk_level)

        return {
            "prompt":      prompt,
            "machine_id":  machine_id,
            "issue_type":  issue_type,
            "risk_score":  risk_score,
            "results":     results,
            "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "best_llm":    best_llm,
            "any_demo":    any(r.get("is_demo") for r in results),
            "collective":  collective,
            "mode":        "live",
        }

    def _score_response(self, text):
        """Score a response on 5 criteria (0-100 total)"""
        if not text:
            return 0
        score = 0
        t = text.lower()
        if any(w in t for w in ["cause", "root", "reason", "due to", "because"]):
            score += 20
        if any(w in t for w in ["immediate", "24 hour", "urgent", "now", "asap", "right away"]):
            score += 20
        if any(w in t for w in ["long-term", "permanent", "replace", "overhaul", "preventive"]):
            score += 20
        if any(w in t for w in ["priority", "critical", "high", "confidence", "%"]):
            score += 20
        wc = len(text.split())
        if wc >= 80:
            score += 20
        elif wc >= 40:
            score += 10
        return score

    def _pick_best(self, results):
        """Pick best LLM by quality (70%) + speed (30%)"""
        successful = [r for r in results if r["success"] and r["quality_score"] > 0]
        if not successful:
            return None
        max_lat = max(r["latency_ms"] for r in successful) or 1
        for r in successful:
            r["_combined"] = r["quality_score"] * 0.7 + (1 - r["latency_ms"] / max_lat) * 100 * 0.3
        return max(successful, key=lambda x: x["_combined"])["llm_name"]

    def _generate_collective_recommendation(self, results, machine_id, issue_type, risk_level):
        """
        Synthesize all LLM responses into one collective recommendation.
        Extracts the most agreed-upon points across all models.
        """
        successful = [r for r in results if r["success"] and r["response"]]
        if not successful:
            return None

        # Count keyword votes across all responses
        all_text = " ".join(r["response"].lower() for r in successful)

        # Priority vote — what do most models say?
        priority_votes = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in successful:
            t = r["response"].lower()
            for p in priority_votes:
                if f"priority level: {p}" in t or f"priority: {p}" in t:
                    priority_votes[p] += 1
        agreed_priority = max(priority_votes, key=priority_votes.get).title()
        priority_agreement = int((priority_votes[agreed_priority.lower()] / len(successful)) * 100)

        # Confidence vote — average confidence %
        import re
        confidences = []
        for r in successful:
            match = re.search(r"confidence[:\s]+(\d+)%", r["response"].lower())
            if match:
                confidences.append(int(match.group(1)))
        avg_confidence = int(sum(confidences) / len(confidences)) if confidences else 75

        # Common action keywords
        action_keywords = {
            "replace bearing":    all_text.count("bearing"),
            "shaft alignment":    all_text.count("alignment"),
            "cooling fan":        all_text.count("cooling fan"),
            "vibration analysis": all_text.count("vibration"),
            "thermal inspection": all_text.count("thermal"),
            "shut down":          all_text.count("shut down") + all_text.count("shutdown"),
            "reduce load":        all_text.count("reduce load") + all_text.count("reduce machine"),
        }
        top_actions = sorted(action_keywords.items(), key=lambda x: x[1], reverse=True)
        top_actions = [(a, c) for a, c in top_actions if c > 0][:3]

        # Average quality score
        avg_quality = int(sum(r["quality_score"] for r in successful) / len(successful))

        # Best response text (highest quality score)
        best_response = max(successful, key=lambda x: x["quality_score"])

        # Agreement level
        scores = [r["quality_score"] for r in successful]
        score_variance = max(scores) - min(scores)
        if score_variance <= 20:
            agreement_level = "High Agreement"
        elif score_variance <= 40:
            agreement_level = "Moderate Agreement"
        else:
            agreement_level = "Mixed Opinions"

        return {
            "agreed_priority":      agreed_priority,
            "priority_agreement":   priority_agreement,
            "avg_confidence":       avg_confidence,
            "avg_quality_score":    avg_quality,
            "agreement_level":      agreement_level,
            "models_agreed":        len(successful),
            "top_actions":          top_actions,
            "best_response_from":   best_response["llm_name"],
            "best_response_text":   best_response["response"],
            "summary": (
                f"Based on {len(successful)} AI models, the collective recommendation for "
                f"{machine_id} ({issue_type}) is {agreed_priority} priority with "
                f"{avg_confidence}% average confidence. "
                f"{agreement_level} across all models."
            )
        }
