"""class ChatService:
    def generate_chat_response(self, customer_data, advisor_question):
        return {
            "status": "success",
            "answer": "Based on customer profile: Recommend asking about medical history, family coverage needs, and budget comfort levels for comprehensive insurance planning.",
            "model": "advisor-assistant",
            "question": advisor_question
        }

def get_chat_service():
    return ChatService()"""



class ChatService: #customer details
    def generate_chat_response(self, customer_data, advisor_question):
        age = customer_data.get('age', 0)
        medical = customer_data.get('medical_disclosures', [])
        coverage = customer_data.get('total_coverage', 0)
        budget = customer_data.get('premium_budget')
        family = customer_data.get('family_members_count', 0)
        name = customer_data.get('name', 'Customer')
        
        question_lower = advisor_question.lower()
        
        # Different answers based on SPECIFIC QUESTION
        #if else statements to check for keywords in the question and provide tailored advice 
        if 'additional information' in question_lower or 'what should i ask' in question_lower or 'what to ask' in question_lower:
            if age > 55 and medical:
                answer = f"For {name} (age {age}) with {', '.join(medical)}: Ask about disease duration, current medications, hospitalization history, and recent medical reports."
            elif age > 55:
                answer = f"For {name} (age {age}): Ask about medical history, current medications, recent hospitalizations, and existing health conditions."
            elif medical:
                answer = f"For {name} with {', '.join(medical)}: Ask about treatment duration, current medications, complications, and recent medical reports."
            elif coverage < 500000:
                answer = f"For {name} with ₹{coverage:,.0f} coverage: Ask about desired coverage amount, super top-up options, and portability."
            elif family > 0:
                answer = f"For {name} with {family} family members: Ask about floater coverage vs individual policies and dependent requirements."
            elif not budget:
                answer = f"For {name}: Ask about monthly and annual premium comfort levels."
            else:
                answer = f"For {name}: Ask about hospitalization history, medications, and desired coverage enhancements."
        
        elif 'how to approach' in question_lower or 'how should i' in question_lower or 'strategy' in question_lower:
            if age > 55:
                answer = f"Strategy for {name} (age {age}): Start with comprehensive health assessment. Focus on medical history and current treatments. Then discuss coverage needs."
            elif family > 0:
                answer = f"Strategy for {name}: Start by understanding family structure and coverage needs. Discuss floater vs individual options based on family situation."
            elif coverage < 500000:
                answer = f"Strategy for {name}: Lead with coverage gap analysis. Show comparison of current ₹{coverage:,.0f} vs recommended ₹10-15 lakhs coverage."
            else:
                answer = f"Strategy for {name}: Understand current coverage, identify gaps, then recommend appropriate enhancements."
        
        elif 'coverage' in question_lower or 'increase' in question_lower or 'why increase' in question_lower:
            if coverage < 500000:
                answer = f"For {name}: Current ₹{coverage:,.0f} is inadequate. Recommend increasing to ₹10-15 lakhs minimum. Discuss why: age {age}, family {family}, medical issues: {medical if medical else 'none'}. Super top-up covers catastrophic events."
            else:
                answer = f"For {name}: Current coverage ₹{coverage:,.0f} is decent. Consider critical illness rider for additional protection given age {age}."
        
        elif 'budget' in question_lower or 'premium' in question_lower or 'afford' in question_lower:
            if not budget:
                answer = f"For {name}: Budget not specified. Ask: 'What's your monthly comfort level?' Start with ₹2K-5K range. Then explore annual prepayment for discounts."
            else:
                answer = f"For {name}: Budget is ₹{budget}. Recommend plans within this budget that balance coverage and affordability."
        
        elif 'family' in question_lower or 'dependent' in question_lower or 'spouse' in question_lower:
            if family > 0:
                answer = f"For {name} with {family} family members: Discuss floater policy (one coverage for all, cheaper) vs individual policies (separate for each, flexible). Which suits better?"
            else:
                answer = f"For {name}: No family members recorded. Still recommend life insurance for income protection."
        
        elif 'medical' in question_lower or 'disease' in question_lower or 'health' in question_lower or 'disease' in question_lower:
            if medical:
                answer = f"For {name} with {', '.join(medical)}: Key questions: How long diagnosed? Current medications? Recent hospitalizations? Disease stable? This helps assess underwriting and premium."
            else:
                answer = f"For {name}: Ask about any pre-existing conditions, ongoing medications, recent hospitalizations, or chronic diseases. Important for underwriting."
        
        elif 'question' in question_lower or 'ask' in question_lower:
            answer = f"For {name} (age {age}, family {family}, coverage ₹{coverage:,.0f}): Ask about: medical history, family coverage needs, premium budget, desired coverage, and hospitalization history."
        
        else:
            # Fallback for any other question
            answer = f"For {name}: Based on profile - age {age}, family {family}, coverage ₹{coverage:,.0f}, medical {medical if medical else 'none'}, budget {budget if budget else 'not specified'} - I recommend discussing medical history, family coverage options, and coverage enhancements."
        
        return {
            "status": "success",
            "answer": answer,
            "model": "advisor-assistant",
            "question": advisor_question
        }

#Simple function that creates and returns a ChatService object
def get_chat_service():
    return ChatService()