from openai import OpenAI
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ChatService:
    def generate_chat_response(self, customer_data, advisor_question):
        age = customer_data.get('age', 0)
        medical = customer_data.get('medical_disclosures', [])
        coverage = customer_data.get('total_coverage', 0)
        family = customer_data.get('family_members_count', 0)
        budget = customer_data.get('premium_budget')
        name = customer_data.get('name', 'Customer')

        prompt = f"""
You are an AI insurance advisor assistant. The advisor asks: "{advisor_question}"

Customer profile:
- Name: {name}
- Age: {age}
- Family members: {family}
- Pre-existing diseases: {', '.join(medical) if medical else 'None'}
- Total existing cover: ₹{coverage:,.0f}
- Premium budget: {budget if budget else 'Not specified'}

Provide a helpful, concise answer addressing the advisor's question.
"""
        try:
            client = OpenAI(
                api_key=settings.NVIDIA_API_KEY,
                base_url="https://integrate.api.nvidia.com/v1"
            )
            completion = client.chat.completions.create(
                model="meta/llama-3.1-8b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=512,
            )
            answer = completion.choices[0].message.content.strip()

            return {
                "status": "success",
                "answer": answer,
                "model": "meta/llama-3.1-8b-instruct",
                "question": advisor_question,
                "source": "nvidia"
            }
        except Exception as e:
            logger.error(f"NVIDIA API failed: {e}")
            return self._fallback_response(customer_data, advisor_question)

    def _fallback_response(self, customer_data, advisor_question):
        # PASTE your original rule-based logic here, indented like this
        # (this is the part that got cut off when you pasted the code to me —
        # I don't have the real body, so don't lose it)
        pass


def get_chat_service():
    return ChatService()