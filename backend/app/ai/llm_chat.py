import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
import httpx

load_dotenv()


class FinancialCoachChat:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.provider = None
        self.client = None
        self.use_new_api = False
        self.use_rest = False
        self.model_name = None

        if self.gemini_key:
            # Prefer REST on Windows — avoids Errno 22 / broken google package installs.
            self.provider = "gemini"
            self.use_rest = True
            self.model_name = "gemini-2.5-flash"
            self.client = True  # truthy so chat() proceeds
            print(f"Using Gemini REST API for chat ({self.model_name})")

        if not self.client and self.openai_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_key)
                self.provider = "openai"
                print("Using OpenAI API for chat features")
            except Exception as e:
                print(f"Failed to initialize OpenAI: {e}")
                self.client = None

        if not self.client:
            print("Warning: No AI API key set. Chat features will be limited.")
            print("Set GEMINI_API_KEY or OPENAI_API_KEY in your .env file")

    def chat(self, message: str, context: Optional[Dict] = None) -> Dict:
        if not self.client:
            return self._fallback_response(message, context)

        system_prompt = self._build_system_prompt(context)

        try:
            if self.provider == "gemini":
                return self._chat_gemini(message, system_prompt)
            if self.provider == "openai":
                return self._chat_openai(message, system_prompt)
            return self._fallback_response(message, context)
        except Exception as e:
            error_msg = str(e)
            print(f"Error calling {self.provider} API: {error_msg}")
            return {
                "response": (
                    "I couldn't reach the AI service right now, so I'm using basic "
                    f"guidance instead. ({error_msg})"
                ),
                "suggestions": [
                    "Check GEMINI_API_KEY in backend/.env",
                    "Confirm the backend is on the same port as VITE_API_URL",
                    "Try again in a moment",
                ],
                "data": None,
                "error": error_msg,
            }

    def _chat_gemini(self, message: str, system_prompt: str) -> Dict:
        full_prompt = (
            f"{system_prompt}\n\nUser question: {message}\n\n"
            "Provide a helpful, concise response:"
        )

        models_to_try = [
            self.model_name,
            "gemini-2.5-flash",
            "gemini-flash-latest",
            "gemini-2.5-flash-lite",
        ]
        last_error = None
        ai_response = None

        for model in models_to_try:
            if not model:
                continue
            try:
                ai_response = self._gemini_rest(model, full_prompt)
                if ai_response:
                    self.model_name = model
                    break
            except Exception as e:
                last_error = e
                print(f"Gemini model {model} failed: {e}")

        if not ai_response:
            if last_error:
                raise last_error
            return self._fallback_response(message, None)

        return {
            "response": ai_response,
            "suggestions": self._extract_suggestions(ai_response),
            "data": None,
        }

    def _gemini_rest(self, model: str, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800},
        }
        with httpx.Client(timeout=45.0) as client:
            res = client.post(url, params={"key": self.gemini_key}, json=payload)
            res.raise_for_status()
            data = res.json()

        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError(data.get("error", {}).get("message") or "Empty Gemini response")
        parts = candidates[0].get("content", {}).get("parts") or []
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned empty text")
        return text

    def _chat_openai(self, message: str, system_prompt: str) -> Dict:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        ai_response = response.choices[0].message.content
        return {
            "response": ai_response,
            "suggestions": self._extract_suggestions(ai_response),
            "data": None,
        }

    def _build_system_prompt(self, context: Optional[Dict]) -> str:
        prompt = (
            "You are FinSage, a helpful AI financial coach. Provide practical, "
            "actionable advice. Be concise and encouraging. Do not give formal "
            "investment advice; remind users to do their own research when relevant."
        )
        if not context:
            return prompt

        prompt += "\n\nUser financial context:\n"
        if context.get("current_balance") is not None:
            prompt += f"- Current balance: ${context['current_balance']:.2f}\n"
        if context.get("monthly_income") is not None:
            prompt += f"- Monthly income: ${context['monthly_income']:.2f}\n"
        if context.get("monthly_expenses") is not None:
            prompt += f"- Monthly expenses: ${context['monthly_expenses']:.2f}\n"
        if context.get("goals"):
            prompt += "- Goals:\n"
            for goal in context["goals"][:5]:
                prompt += (
                    f"  - {goal.get('name')}: ${goal.get('current_amount', 0):.2f} / "
                    f"${goal.get('target_amount', 0):.2f}\n"
                )
        if context.get("top_categories"):
            prompt += f"- Top spending categories: {', '.join(context['top_categories'][:3])}\n"
        return prompt

    def _extract_suggestions(self, response: str) -> List[str]:
        suggestions = []
        lines = response.split("\n")
        for line in lines:
            cleaned = line.strip()
            if cleaned.startswith(("-", "*", "•")) or (
                len(cleaned) > 2 and cleaned[0].isdigit() and cleaned[1] in ".)"
            ):
                suggestion = cleaned.lstrip("-*•0123456789.) ").strip()
                if suggestion and len(suggestion) > 10:
                    suggestions.append(suggestion)
        return suggestions[:3] if suggestions else [
            "Review your top spending categories",
            "Set a savings goal for this month",
            "Ask about a specific budget category",
        ]

    def _fallback_response(self, message: str, context: Optional[Dict]) -> Dict:
        lower = (message or "").lower()
        if any(w in lower for w in ("save", "saving", "budget")):
            text = (
                "Start by listing your top 3 expense categories and cutting 10% from "
                "the largest discretionary one this month. Automate a transfer to savings "
                "on payday so it happens before you spend."
            )
        elif any(w in lower for w in ("debt", "loan", "credit")):
            text = (
                "List debts by interest rate, pay minimums on all, then put extra toward "
                "the highest-rate balance. Avoid new revolving debt while you catch up."
            )
        elif any(w in lower for w in ("invest", "stock", "retirement")):
            text = (
                "Build an emergency fund first (3–6 months of expenses), then contribute "
                "regularly to diversified low-cost funds. Consistency beats timing."
            )
        else:
            text = (
                "I can help with budgeting, debt payoff, savings goals, and spending "
                "patterns. Ask about a specific number or category for tighter advice."
            )
            if context and context.get("top_categories"):
                text += f" Your top categories lately: {', '.join(context['top_categories'][:3])}."

        return {
            "response": text,
            "suggestions": [
                "How can I cut my largest expense?",
                "Am I on track for my goals?",
                "What's a simple monthly budget?",
            ],
            "data": None,
        }
