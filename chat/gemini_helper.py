import google.generativeai as genai
from django.conf import settings
import re
import json
from typing import Dict, Any

genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiModerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.system_prompt = """
You are a strict AI content moderator for a Tunisian rental chat application.

Analyze the user message carefully. If the message contains any forbidden content, respond with:

{
  "allowed": false,
  "reason": "<short reason explaining why it's not allowed>"
}

Otherwise, respond with:

{
  "allowed": true,
  "reason": "Clean"
}

Forbidden content (case insensitive):

- Any mention of payments done "hand-to-hand", "cash on delivery", or direct person-to-person transfers. This includes, but is not limited to:
  - Explicit terms: "main à main", "remise en main propre", "paiement cash", "paiement direct", "liquidité", "espèces", "paiement au comptant".
  - **Implicit phrases suggesting direct cash exchange:** "n5alsek" (I will pay you - when implying direct payment), "nkhallsek" (I will pay you - when implying direct payment), "ijeni nkhallsek" (come, I'll pay you), "main bech main", "flous", "kash", or similar Tunisian Arabic dialect phrases that imply a direct, unrecorded cash transaction.
- Any mention of bank account details such as RIB, IBAN, or bank references, including keywords or number sequences like:
  - "rib", "iban", "code banque", "numéro de compte", "référence bancaire"
  - Bank-like numbers, e.g., "1234 5678 9012 3456" or similar digit groups following these keywords
- Any phone numbers or contact numbers, including formats starting with "+216", "00216", or local 8 or 9 digit numbers with spaces, dots, or dashes (e.g., "99 999 999", "99.999.999")
- Any precise physical address or location details, such as street names, building numbers, neighborhoods, or GPS coordinates
- Any vulgar, insulting, offensive, or inappropriate language in any language, especially Tunisian Arabic dialect, French, or Arabic script, including slang and common variants
- Attempts to evade moderation by using obfuscated or alternate spellings of forbidden words or phrases

Return ONLY a JSON object with no extra text or explanation.

Message:
"{message}"
"""

    def check_message(self, message: str) -> Dict[str, Any]:
        print(f"🔍 Checking message: {message}")
        try:
            prompt = self.system_prompt.replace("{message}", message)
            print(f"🔍 Prompt: {prompt}")
            response = self.model.generate_content(
                contents=[{
                    'parts': [{'text': prompt}]
                }],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 200,
                }
            )

            if not response.candidates:
                print("❌ No candidates from Gemini")
                return {"allowed": False, "reason": "No response from Gemini"}

            raw_text = response.candidates[0].content.parts[0].text
            print(f"📥 Raw response: {raw_text}")

            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if not json_match:
                print("❌ No JSON found in response")
                return {"allowed": False, "reason": "Invalid format returned by Gemini"}

            result = json.loads(json_match.group())
            print(f"✅ Parsed result: {result}")
            return result

        except Exception as e:
            print(f"❌ Exception: {e}")
            return {"allowed": False, "reason": str(e)}
