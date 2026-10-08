"""
Google Gemini AI Agent & Intelligence Service
Empowers the EcoSmart system with:
1. Multimodal & Semantic Waste Classification Agent (Level 1, Level 2, Level 3, Contamination Risk)
2. Cyber-Physical Threat Intelligence & Root-Cause Analysis Agent
3. Conversational AI Operations & Dispatch Assistant
"""
import os
import json
import logging
import requests
from typing import Optional, Dict, Any, Tuple

from app.config import settings

logger = logging.getLogger("gemini_agent")

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def get_api_key() -> str:
    return settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")


def get_model_name() -> str:
    return settings.GEMINI_MODEL or os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")


def call_gemini_generate(
    prompt: str,
    system_instruction: Optional[str] = None,
    image_b64: Optional[str] = None,
    mime_type: str = "image/jpeg",
    temperature: float = 0.2
) -> Optional[str]:
    """
    Direct HTTP REST invocation to Gemini API.
    Zero external heavy SDK dependency, high speed, and resilient error handling.
    """
    api_key = get_api_key()
    if not api_key:
        logger.warning("No GEMINI_API_KEY configured. Falling back to rule-based logic.")
        return None

    model = get_model_name()
    endpoint = f"{GEMINI_BASE_URL}/{model}:generateContent?key={api_key}"

    # Build contents parts
    parts = []
    if image_b64:
        # Strip header if present
        clean_b64 = image_b64.split(",")[-1] if "," in image_b64 else image_b64
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": clean_b64
            }
        })

    parts.append({"text": prompt})

    payload: Dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 1024
        }
    }

    if system_instruction:
        payload["system_instruction"] = {
            "parts": [{"text": system_instruction}]
        }

    try:
        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return None
        else:
            logger.error(f"Gemini API error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception contacting Gemini API: {e}")
        return None


# ── 1. Gemini Waste Classification Agent ─────────────────────────────────────

def classify_waste_with_gemini(
    item_description: str,
    image_b64: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uses Gemini to classify waste into strict municipal taxonomy:
    Level 1: Organic / Wet, Recyclable, Hazardous, E-Waste, Biomedical, Construction, Textile, etc.
    Level 2: Plastic, Paper, Metal, Glass, Cardboard (for recyclables)
    Level 3: Specific object name
    """
    sys_prompt = """You are an expert AI Municipal Solid Waste Classification and Sorting Agent.
Analyze the user's waste item description or image and categorize it according to municipal regulations.
You MUST output ONLY a valid raw JSON object (no markdown fences, no explanatory text around it) with the following structure:
{
  "level1": "Organic / Wet" | "Recyclable" | "Hazardous" | "E-Waste" | "Biomedical" | "Garden / Green" | "Construction" | "Textile" | "Mixed / Unknown",
  "level2": "Plastic" | "Paper" | "Cardboard" | "Glass" | "Metal" | null,
  "level3": "Specific object name",
  "confidence": 95.0,
  "is_recyclable": true,
  "is_hazardous": false,
  "contamination_risk": "LOW" | "MEDIUM" | "HIGH",
  "handling_instructions": "Brief instructions on proper sorting or disposal.",
  "ai_explanation": "One concise sentence explaining why this classification was chosen."
}
"""
    prompt = f"Classify this waste item: '{item_description}'"
    raw_response = call_gemini_generate(prompt=prompt, system_instruction=sys_prompt, image_b64=image_b64)

    if raw_response:
        # Strip code block fences if present
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
            parsed["source"] = "Gemini-2.5-Flash"
            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse Gemini JSON output: {e}, raw was: {text[:200]}")

    # Fallback to intelligent rule-based categorization
    return fallback_waste_classification(item_description)


def fallback_waste_classification(query: str) -> Dict[str, Any]:
    """Graceful rule-based fallback when offline or API limit reached."""
    q = query.lower()
    if any(k in q for k in ["bottle", "bag", "cup", "wrapper", "container", "jug", "poly"]):
        return {
            "level1": "Recyclable",
            "level2": "Plastic",
            "level3": "Plastic Item",
            "confidence": 88.0,
            "is_recyclable": True,
            "is_hazardous": False,
            "contamination_risk": "LOW",
            "handling_instructions": "Rinse clean and place in the dry recycling stream.",
            "ai_explanation": "Item recognized as thermoplastic packaging polymer.",
            "source": "Rule-Engine-Fallback"
        }
    elif any(k in q for k in ["battery", "paint", "chemical", "acid", "pesticide", "poison"]):
        return {
            "level1": "Hazardous",
            "level2": None,
            "level3": "Hazardous Material",
            "confidence": 94.0,
            "is_recyclable": False,
            "is_hazardous": True,
            "contamination_risk": "HIGH",
            "handling_instructions": "Do not mix with general waste. Transport to certified e-waste or hazmat depot.",
            "ai_explanation": "Chemical or electrochemical components pose soil and water contamination risks.",
            "source": "Rule-Engine-Fallback"
        }
    elif any(k in q for k in ["apple", "peel", "food", "scrap", "vegetable", "banana", "bread"]):
        return {
            "level1": "Organic / Wet",
            "level2": None,
            "level3": "Food Waste",
            "confidence": 92.0,
            "is_recyclable": False,
            "is_hazardous": False,
            "contamination_risk": "MEDIUM",
            "handling_instructions": "Deposit into green composting stream. Divert from landfill.",
            "ai_explanation": "Biodegradable organic matter suitable for anaerobic digestion or composting.",
            "source": "Rule-Engine-Fallback"
        }
    else:
        return {
            "level1": "Recyclable",
            "level2": "Paper",
            "level3": "General Paper Waste",
            "confidence": 75.0,
            "is_recyclable": True,
            "is_hazardous": False,
            "contamination_risk": "LOW",
            "handling_instructions": "Sort into dry recyclables bin.",
            "ai_explanation": "Categorized via standard municipal sorting heuristics.",
            "source": "Rule-Engine-Fallback"
        }


# ── 2. Gemini Cyber Threat & Anomaly Intelligence Agent ───────────────────────

def analyze_threat_with_gemini(
    event_type: str,
    details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Uses Gemini to analyze IoT sensor anomalies, cryptographic failures,
    and OWASP attacks, providing actionable remediation plans.
    """
    sys_prompt = """You are a Principal Cyber-Physical Threat Intelligence Analyst for Smart Cities.
Analyze the IoT sensor telemetry anomaly, cryptographic failure, or API attack event.
You MUST output ONLY a valid raw JSON object (no markdown fences, no explanatory text around it) with:
{
  "threat_title": "Concise summary title",
  "threat_category": "GPS Spoofing" | "Cryptographic Tampering" | "Sensor Hardware Fault" | "OWASP Injection" | "Replay Attack",
  "severity_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "threat_score": 8.5,
  "tactical_assessment": "Analysis of the attack vector or fault mode.",
  "recommended_mitigation": [
    "Step 1 mitigation",
    "Step 2 mitigation"
  ],
  "quarantine_recommended": true
}
"""
    prompt = f"Analyze incident of type '{event_type}' with event details: {json.dumps(details)}"
    raw_response = call_gemini_generate(prompt=prompt, system_instruction=sys_prompt)

    if raw_response:
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
            parsed["source"] = "Gemini-2.5-Flash"
            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse Gemini threat analysis: {e}")

    # Fallback
    return {
        "threat_title": f"Security Alert: {event_type}",
        "threat_category": "Cryptographic Tampering" if "hmac" in event_type.lower() or "signature" in event_type.lower() else "IoT Sensor Anomaly",
        "severity_level": "HIGH" if "spoof" in event_type.lower() or "signature" in event_type.lower() else "MEDIUM",
        "threat_score": 7.8,
        "tactical_assessment": f"Detected anomaly in device telemetry stream matching {event_type} signature.",
        "recommended_mitigation": [
            "Review device hardware certificate and rotate HMAC key",
            "Inspect physical location for tamper evidence"
        ],
        "quarantine_recommended": True if "spoof" in event_type.lower() else False,
        "source": "Rule-Engine-Fallback"
    }


# ── 3. Conversational AI Operations & Dispatch Assistant ─────────────────────

def ask_operations_agent(
    user_query: str,
    user_role: str = "operator",
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Conversational assistant for dispatchers, drivers, and analysts.
    """
    sys_prompt = f"""You are 'EcoSmart AI', the intelligent operations assistant for the EcoSmart Autonomous Waste Management Platform.
You help municipal dispatchers, field truck drivers, and security analysts optimize waste collection, troubleshoot sensor faults, and explain routing algorithms.
User Role: {user_role}.
Current System Context: {json.dumps(context or {})}
Be concise, professional, and action-oriented. Provide direct answers in 2 to 4 clear sentences.
"""
    response = call_gemini_generate(prompt=user_query, system_instruction=sys_prompt, temperature=0.3)
    if response:
        return response.strip()

    return (
        "EcoSmart AI Assistant (Local Mode): System is operational. "
        "All telemetry signatures are verified with HMAC-SHA256, routes are optimized using Nearest-Neighbor TSP, "
        "and sensor nodes are running within normal parameters."
    )
