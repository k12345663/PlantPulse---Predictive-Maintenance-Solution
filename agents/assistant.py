import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

class AIAssistantAgent:
    """Natural language interface for maintenance queries"""
    
    def __init__(self, log_analyzer, failure_predictor, scheduler):
        self.log_analyzer = log_analyzer
        self.failure_predictor = failure_predictor
        self.scheduler = scheduler
        self.llm_provider = os.getenv('LLM_PROVIDER', 'ollama')  # Default to Ollama
        
        # Initialize LLM client
        if self.llm_provider == 'ollama':
            # Ollama local setup
            self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            self.ollama_model = os.getenv('OLLAMA_MODEL', 'kimi-k2.5:cloud')
            self.client = 'ollama'
            print(f"🤖 Using Kimi-K2 (cloud): {self.ollama_model}")
        elif self.llm_provider == 'openai':
            try:
                import openai
                self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                self.model = 'gpt-3.5-turbo'
            except:
                self.client = None
        elif self.llm_provider == 'gemini':
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
                self.client = genai.GenerativeModel('gemini-pro')
            except:
                self.client = None
        else:
            self.client = None
    
    def answer_query(self, question):
        """Answer natural language questions about maintenance"""
        
        # Determine query type and gather context
        context = self._gather_context(question)
        
        # If no LLM available, use rule-based responses
        if self.client is None:
            return self._rule_based_answer(question, context)
        
        # Use LLM for natural language response
        return self._llm_answer(question, context)
    
    def _gather_context(self, question):
        """Gather relevant context based on question"""
        question_lower = question.lower()
        context = {}
        
        # Check if asking about specific machine
        machines = self.log_analyzer.df['machine_id'].unique()
        mentioned_machine = None
        for machine in machines:
            if machine.lower() in question_lower:
                mentioned_machine = machine
                break
        
        if mentioned_machine:
            context['machine'] = mentioned_machine
            context['machine_history'] = self.log_analyzer.get_machine_history(mentioned_machine)
            context['risk_info'] = self.failure_predictor.calculate_risk_score(mentioned_machine)
        
        # Get overall risk data
        context['all_risks'] = self.failure_predictor.get_all_risk_scores()
        context['high_risk'] = self.failure_predictor.get_high_risk_machines()
        
        # Get schedule
        context['schedule'] = self.scheduler.generate_schedule()
        
        return context
    
    def _rule_based_answer(self, question, context):
        """Provide rule-based answers when LLM is not available"""
        question_lower = question.lower()
        
        # High risk machines query
        if 'high risk' in question_lower or 'likely to fail' in question_lower:
            high_risk = context['high_risk']
            if not high_risk:
                return "No machines currently at high risk."
            
            response = f"**High Risk Machines ({len(high_risk)}):**\n\n"
            for machine in high_risk[:5]:
                response += f"- **{machine['machine_id']}**: Risk Score {machine['risk_score']}/100\n"
                response += f"  - {', '.join(machine['factors'][:2])}\n\n"
            return response
        
        # Specific machine query
        if context.get('machine'):
            machine = context['machine']
            risk = context['risk_info']
            history = context['machine_history']
            
            response = f"**Machine {machine} Analysis:**\n\n"
            response += f"- **Risk Score:** {risk['risk_score']}/100 ({risk['risk_level']})\n"
            response += f"- **Total Incidents:** {history['total_incidents']}\n"
            response += f"- **Total Downtime:** {history['total_downtime']} minutes\n"
            response += f"- **Temporary Fixes:** {history['temporary_fix_count']}\n\n"
            
            if risk['factors']:
                response += "**Risk Factors:**\n"
                for factor in risk['factors']:
                    response += f"- {factor}\n"
            
            return response
        
        # Schedule query
        if 'schedule' in question_lower or 'when' in question_lower:
            schedule = context['schedule']
            if not schedule:
                return "No maintenance currently scheduled."
            
            response = f"**Upcoming Maintenance Schedule ({len(schedule)} machines):**\n\n"
            for item in schedule[:5]:
                response += f"**{item['machine_id']}** - {item['scheduled_time']}\n"
                response += f"- Priority: {item['priority']}\n"
                response += f"- {item['reason']}\n\n"
            return response
        
        # Default response
        return "I can help you with:\n- High risk machine analysis\n- Specific machine history\n- Maintenance schedules\n- Failure predictions"
    
    def _llm_answer(self, question, context):
        """Use LLM to generate natural language answer"""
        
        # Build prompt with context
        prompt = self._build_prompt(question, context)
        
        try:
            if self.llm_provider == 'ollama':
                # Use Ollama local API
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    return response.json()['response']
                else:
                    print(f"Ollama error: {response.status_code}")
                    return self._rule_based_answer(question, context)
            
            elif self.llm_provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an AI maintenance assistant. Provide clear, concise answers based on the data provided."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            
            elif self.llm_provider == 'gemini':
                response = self.client.generate_content(prompt)
                return response.text
        
        except Exception as e:
            print(f"LLM error: {e}")
            return self._rule_based_answer(question, context)
    
    def _build_prompt(self, question, context):
        """Build prompt with relevant context"""
        prompt = f"Question: {question}\n\n"
        prompt += "Context:\n"
        
        if context.get('machine'):
            machine = context['machine']
            risk = context['risk_info']
            prompt += f"\nMachine {machine}:\n"
            prompt += f"- Risk Score: {risk['risk_score']}/100\n"
            prompt += f"- Risk Factors: {', '.join(risk['factors'])}\n"
        
        if context.get('high_risk'):
            prompt += f"\nHigh Risk Machines: {len(context['high_risk'])}\n"
            for m in context['high_risk'][:3]:
                prompt += f"- {m['machine_id']}: {m['risk_score']}/100\n"
        
        prompt += "\nProvide a clear, professional answer based on this data."
        return prompt
