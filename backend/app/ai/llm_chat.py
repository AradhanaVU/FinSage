import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class FinancialCoachChat:
    def __init__(self):
        # Check for Gemini API key first (preferred)
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        self.provider = None
        self.client = None
        
        # Try Gemini first
        if self.gemini_key:
            try:
                # Try new google.genai package first
                try:
                    from google import genai
                    self.client = genai.Client(api_key=self.gemini_key)
                    # New API uses model names with 'models/' prefix
                    # Use gemini-2.5-flash (latest stable) or gemini-2.0-flash as fallback
                    self.model_name = 'models/gemini-2.5-flash'
                    self.provider = "gemini"
                    self.use_new_api = True
                    print(f"✓ Using Gemini API (google.genai) for chat features (gemini-2.5-flash)")
                except (ImportError, AttributeError) as e:
                    # Fall back to old package if new one not available
                    print(f"New API not available ({e}), trying old API...")
                    import google.generativeai as genai_old
                    genai_old.configure(api_key=self.gemini_key)
                    try:
                        self.client = genai_old.GenerativeModel('gemini-1.5-flash')
                        self.model_name = 'gemini-1.5-flash'
                    except:
                        self.client = genai_old.GenerativeModel('gemini-pro')
                        self.model_name = 'gemini-pro'
                    self.provider = "gemini"
                    self.use_new_api = False
                    print(f"✓ Using Gemini API (google.generativeai - deprecated) for chat features ({self.model_name})")
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}")
                import traceback
                traceback.print_exc()
                self.client = None
                self.use_new_api = False
        
        # Fall back to OpenAI if Gemini not available
        if not self.client and self.openai_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_key)
                self.provider = "openai"
                print("✓ Using OpenAI API for chat features")
            except Exception as e:
                print(f"Failed to initialize OpenAI: {e}")
                self.client = None
        
        if not self.client:
            print("Warning: No AI API key set. Chat features will be limited.")
            print("Set GEMINI_API_KEY or OPENAI_API_KEY in your .env file")
    
    def chat(self, message: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate a response to user's financial question using Gemini or OpenAI.
        """
        if not self.client:
            return self._fallback_response(message, context)
        
        # Build context for the LLM
        system_prompt = self._build_system_prompt(context)
        
        try:
            if self.provider == "gemini":
                result = self._chat_gemini(message, system_prompt)
                # If there's an error in the result, still return it so frontend can show it
                if "error" in result:
                    return result
                return result
            elif self.provider == "openai":
                return self._chat_openai(message, system_prompt)
        except Exception as e:
            error_msg = str(e)
            print(f"Error calling {self.provider} API: {error_msg}")
            return {
                "response": f"I encountered an error: {error_msg}. Falling back to basic responses.",
                "suggestions": ["Check API configuration", "Try again later"],
                "data": None,
                "error": error_msg
            }
    
    def _chat_gemini(self, message: str, system_prompt: str) -> Dict:
        """Chat using Gemini API."""
        # Combine system prompt and user message
        full_prompt = f"{system_prompt}\n\nUser question: {message}\n\nProvide a helpful, concise response:"
        
        try:
            if hasattr(self, 'use_new_api') and self.use_new_api:
                # Use new google.genai API
                # Try gemini-2.5-flash first, fall back to gemini-2.0-flash if needed
                try:
                    response = self.client.models.generate_content(
                        model='models/gemini-2.5-flash',
                        contents=full_prompt
                    )
                except Exception as e:
                    # Fall back to gemini-2.0-flash if 2.5 doesn't work
                    if '404' in str(e) or 'NOT_FOUND' in str(e):
                        print(f"Model gemini-2.5-flash not available, trying gemini-2.0-flash...")
                        response = self.client.models.generate_content(
                            model='models/gemini-2.0-flash',
                            contents=full_prompt
                        )
                    else:
                        raise
                # New API returns response.text directly
                ai_response = response.text.strip()
            else:
                # Use old google.generativeai API
                response = self.client.generate_content(full_prompt)
                ai_response = response.text.strip()
            
            # Check if response is empty
            if not ai_response:
                print("Warning: Gemini returned empty response")
                return self._fallback_response(message, None)
            
            # Check if response is just a greeting (might indicate API issue)
            if len(ai_response) < 50 and ("hello" in ai_response.lower() or "hi" in ai_response.lower()):
                print(f"Warning: Gemini returned very short response: {ai_response}")
            
            # Extract suggestions
            suggestions = self._extract_suggestions(ai_response)
            
            return {
                "response": ai_response,
                "suggestions": suggestions,
                "data": None
            }
        except Exception as e:
            error_msg = str(e)
            print(f"Gemini API error: {error_msg}")
            import traceback
            traceback.print_exc()
            # Return a user-friendly error message
            return {
                "response": f"I encountered an error with the AI service: {error_msg}. Please check your GEMINI_API_KEY in the backend .env file, or try again later.",
                "suggestions": ["Check API key configuration", "Try again in a moment", "Use fallback mode"],
                "data": None,
                "error": error_msg
            }
    
    def _chat_openai(self, message: str, system_prompt: str) -> Dict:
        """Chat using OpenAI API."""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        # Extract suggestions
        suggestions = self._extract_suggestions(ai_response)
        
        return {
            "response": ai_response,
            "suggestions": suggestions,
            "data": None
        }
    
    def _build_system_prompt(self, context: Optional[Dict]) -> str:
        """Build system prompt with user's financial context."""
        base_prompt = """You are a helpful financial coach AI assistant. You provide practical, 
        actionable financial advice. Be concise, friendly, and focus on actionable steps.
        
        When answering questions:
        - Provide specific, actionable advice
        - Use numbers and examples when relevant
        - Suggest concrete steps the user can take
        - Be encouraging and supportive
        """
        
        if context:
            context_str = "\n\nUser's Financial Context:\n"
            
            if context.get("current_balance"):
                context_str += f"- Current balance: ${context['current_balance']:.2f}\n"
            
            if context.get("monthly_income"):
                context_str += f"- Monthly income: ${context['monthly_income']:.2f}\n"
            
            if context.get("monthly_expenses"):
                context_str += f"- Monthly expenses: ${context['monthly_expenses']:.2f}\n"
            
            if context.get("goals"):
                context_str += f"- Active goals: {len(context['goals'])}\n"
                for goal in context.get("goals", [])[:3]:
                    context_str += f"  * {goal.get('name')}: ${goal.get('current_amount', 0):.2f} / ${goal.get('target_amount', 0):.2f}\n"
            
            if context.get("top_categories"):
                context_str += f"- Top spending categories: {', '.join(context['top_categories'][:3])}\n"
            
            base_prompt += context_str
        
        return base_prompt
    
    def _extract_suggestions(self, response: str) -> List[str]:
        """Extract actionable suggestions from the response."""
        suggestions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                suggestion = line.lstrip('-•*').strip()
                if len(suggestion) > 10:  # Filter out very short items
                    suggestions.append(suggestion)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _fallback_response(self, message: str, context: Optional[Dict]) -> Dict:
        """Fallback response when AI API is not available."""
        message_lower = message.lower()
        
        if "save" in message_lower or "saving" in message_lower:
            return {
                "response": "To save money, I recommend: 1) Track all expenses to identify spending patterns, 2) Create a budget and stick to it, 3) Reduce discretionary spending on non-essentials, 4) Set up automatic transfers to savings, 5) Review and cancel unused subscriptions.",
                "suggestions": [
                    "Track all expenses for a month",
                    "Create a monthly budget",
                    "Set up automatic savings transfers",
                    "Review and cancel unused subscriptions"
                ],
                "data": None
            }
        
        elif "retirement" in message_lower or "retire" in message_lower:
            return {
                "response": "For retirement planning: 1) Start saving early to benefit from compound interest, 2) Contribute to retirement accounts (401k, IRA), 3) Aim to save 15-20% of your income, 4) Diversify your investments, 5) Review your plan annually.",
                "suggestions": [
                    "Start contributing to a 401k or IRA",
                    "Aim to save 15-20% of income",
                    "Review retirement plan annually"
                ],
                "data": None
            }
        
        elif "budget" in message_lower:
            return {
                "response": "To create an effective budget: 1) Calculate your monthly income, 2) List all expenses, 3) Use the 50/30/20 rule (50% needs, 30% wants, 20% savings), 4) Track spending regularly, 5) Adjust as needed.",
                "suggestions": [
                    "Use the 50/30/20 budgeting rule",
                    "Track spending weekly",
                    "Adjust budget monthly based on actual spending"
                ],
                "data": None
            }
        
        else:
            return {
                "response": "I'm here to help with your financial questions! Try asking about: saving money, budgeting, retirement planning, investment strategies, or debt management. For more detailed advice, please provide your financial context.",
                "suggestions": [
                    "Ask about saving strategies",
                    "Get budgeting tips",
                    "Learn about retirement planning"
                ],
                "data": None
            }
