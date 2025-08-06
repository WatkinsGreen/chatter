import os
import random
import glob
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class ConversationFlow:
    def __init__(self):
        self.conversations = {}  # conversation_id -> conversation_state
        
    def get_conversation_state(self, conversation_id: str) -> Dict[str, Any]:
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                'step': 'welcome',
                'wherami': None,
                'state': None,
                'issue_type': None,
                'customer': None,
                'environment': None,
                'performance_details': None,
                'completed_steps': []
            }
        return self.conversations[conversation_id]
    
    def update_conversation_state(self, conversation_id: str, updates: Dict[str, Any]):
        state = self.get_conversation_state(conversation_id)
        state.update(updates)
        
    def load_exclamation(self) -> str:
        """Load a random exclamation from /etc/exclamation.txt"""
        try:
            exclamation_path = os.path.join(os.path.dirname(__file__), 'etc', 'exclamation.txt')
            with open(exclamation_path, 'r') as f:
                exclamations = [line.strip() for line in f.readlines() if line.strip()]
            return random.choice(exclamations)
        except Exception as e:
            logger.error(f"Error loading exclamations: {e}")
            return "Wow"
    
    def load_joke(self) -> str:
        """Load a random joke from /etc/joke*.txt files"""
        try:
            etc_path = os.path.join(os.path.dirname(__file__), 'etc')
            joke_files = glob.glob(os.path.join(etc_path, 'joke*.txt'))
            if joke_files:
                selected_file = random.choice(joke_files)
                with open(selected_file, 'r') as f:
                    return f.read().strip()
            else:
                return "Why did the developer go broke? Because he used up all his cache!"
        except Exception as e:
            logger.error(f"Error loading jokes: {e}")
            return "Why did the developer go broke? Because he used up all his cache!"
    
    def process_message(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Process user message through the conversation flow"""
        state = self.get_conversation_state(conversation_id)
        current_step = state['step']
        user_message_lower = user_message.lower().strip()
        
        if current_step == 'welcome':
            return self._handle_welcome(conversation_id, user_message_lower)
        elif current_step == 'ask_state':
            return self._handle_state_question(conversation_id, user_message)
        elif current_step == 'ask_help_type':
            return self._handle_help_type(conversation_id, user_message_lower)
        elif current_step == 'ask_customer':
            return self._handle_customer(conversation_id, user_message)
        elif current_step == 'ask_environment':
            return self._handle_environment(conversation_id, user_message)
        elif current_step == 'ask_performance':
            return self._handle_performance(conversation_id, user_message)
        elif current_step in ['customer_process', 'env_process', 'performance_process']:
            return self._handle_detailed_process(conversation_id, user_message_lower, current_step)
        elif current_step == 'lunch_process':
            return self._handle_lunch_process(conversation_id, user_message_lower)
        else:
            # Default fallback
            return {
                'response': "I'm not sure where we are in our conversation. Let's start over! Where are you writing in from today, AMER or EMEA?",
                'suggestions': ['AMER', 'EMEA'],
                'use_traditional_flow': False
            }
    
    def _handle_welcome(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle the initial location question"""
        if 'amer' in user_message:
            self.update_conversation_state(conversation_id, {
                'wherami': 'AMER',
                'step': 'ask_state'
            })
            return {
                'response': "Great! Which state?",
                'suggestions': ['California', 'Texas', 'New York', 'Florida', 'Other'],
                'use_traditional_flow': False
            }
        elif 'emea' in user_message:
            self.update_conversation_state(conversation_id, {
                'wherami': 'EMEA',
                'step': 'ask_help_type'
            })
            return self._get_help_type_question()
        else:
            return {
                'response': "I didn't catch that! Please let me know - are you writing in from AMER or EMEA?",
                'suggestions': ['AMER', 'EMEA'],
                'use_traditional_flow': False
            }
    
    def _handle_state_question(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle the state question for AMER users"""
        self.update_conversation_state(conversation_id, {
            'state': user_message,
            'step': 'ask_help_type'
        })
        return self._get_help_type_question()
    
    def _get_help_type_question(self) -> Dict[str, Any]:
        """Return the help type question"""
        return {
            'response': "What can I help you with today:\n\n1. A specific customer\n2. A specific environment\n3. A generic performance issue\n4. Lunch",
            'suggestions': ['1. Customer', '2. Environment', '3. Performance', '4. Lunch'],
            'use_traditional_flow': False
        }
    
    def _handle_help_type(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle the help type selection"""
        if '1' in user_message or 'customer' in user_message:
            self.update_conversation_state(conversation_id, {
                'issue_type': 'customer',
                'step': 'ask_customer'
            })
            return {
                'response': "Which customer?",
                'suggestions': [],
                'use_traditional_flow': False
            }
        elif '2' in user_message or 'environment' in user_message:
            self.update_conversation_state(conversation_id, {
                'issue_type': 'environment',
                'step': 'ask_environment'
            })
            return {
                'response': "Which environment?",
                'suggestions': ['Production', 'Staging', 'Development', 'QA'],
                'use_traditional_flow': False
            }
        elif '3' in user_message or 'performance' in user_message:
            self.update_conversation_state(conversation_id, {
                'issue_type': 'performance',
                'step': 'ask_performance'
            })
            return {
                'response': "Tell me more...",
                'suggestions': [],
                'use_traditional_flow': False
            }
        elif '4' in user_message or 'lunch' in user_message:
            self.update_conversation_state(conversation_id, {
                'issue_type': 'lunch',
                'step': 'lunch_process'
            })
            return self._start_lunch_process(conversation_id)
        else:
            return {
                'response': "I didn't understand that. Please choose from the options:\n\n1. A specific customer\n2. A specific environment\n3. A generic performance issue\n4. Lunch",
                'suggestions': ['1. Customer', '2. Environment', '3. Performance', '4. Lunch'],
                'use_traditional_flow': False
            }
    
    def _handle_customer(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle customer specification"""
        self.update_conversation_state(conversation_id, {
            'customer': user_message,
            'step': 'customer_process'
        })
        return self._start_initial_response_process(conversation_id)
    
    def _handle_environment(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle environment specification"""
        self.update_conversation_state(conversation_id, {
            'environment': user_message,
            'step': 'env_process'
        })
        return self._start_initial_response_process(conversation_id)
    
    def _handle_performance(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle performance details"""
        self.update_conversation_state(conversation_id, {
            'performance_details': user_message,
            'step': 'performance_process'
        })
        return self._start_initial_response_process(conversation_id)
    
    def _start_initial_response_process(self, conversation_id: str) -> Dict[str, Any]:
        """Start the initial response process"""
        state = self.get_conversation_state(conversation_id)
        
        # Get exclamation and joke
        exclamation = self.load_exclamation()
        joke = self.load_joke()
        
        # Build response
        response = "My team says 'It's definitely not a database issue... but let me 2x check.'\n\n"
        response += f"{exclamation}. Your monitoring guys are good... there is a ton of data to check... it will take a bit. Here is a Dad joke while you wait:\n\n"
        response += f"{joke}\n\n"
        
        # Add location-specific food recommendations
        if state['wherami'] == 'AMER' and state.get('state'):
            state_name = state['state']
            url = f"http://10.10.4.6/dashboards/food/main.html?state={state_name}&top3"
            response += f"Staying PRODUCTIVE means you should keep energized with some sustenance. Try checking out one of these R365 customer locations: {url}"
        elif state['wherami'] == 'EMEA':
            response += "Oh. R365 does not have many customer locations in EMEA...yet. :)"
        
        return {
            'response': response,
            'suggestions': ['Continue with analysis', 'Ask more questions', 'Start over'],
            'use_traditional_flow': False
        }
    
    def _start_lunch_process(self, conversation_id: str) -> Dict[str, Any]:
        """Handle lunch process"""
        state = self.get_conversation_state(conversation_id)
        
        if state.get('state'):
            state_name = state['state']
            url = f"http://10.10.4.6/dashboards/food/main.html?state={state_name}"
            response = f"I am not fantastic with geography yet, so cannot narrow down a list to something close by. BUT.. here are all known R365 customer locations in: [{state_name}]({url})"
        else:
            response = "I am not fantastic with geography yet, so cannot narrow down a list to something close by. BUT.. here are all known R365 customer locations (please specify your state for better results)."
        
        return {
            'response': response,
            'suggestions': ['Show all locations', 'Start over'],
            'use_traditional_flow': False
        }
    
    def _handle_detailed_process(self, conversation_id: str, user_message: str, process_type: str) -> Dict[str, Any]:
        """Handle the detailed analysis processes"""
        state = self.get_conversation_state(conversation_id)
        
        if process_type == 'customer_process':
            if state.get('customer'):
                return {
                    'response': f"Looking for specific information about customer '{state['customer']}' in our monitoring data. Let me check recent alerts, performance metrics, and any known issues for this customer...\n\nWould you like me to focus on any specific time range or service?",
                    'suggestions': ['Last 24 hours', 'Last week', 'Specific service', 'All data'],
                    'use_traditional_flow': True,
                    'focus': f"customer {state['customer']}"
                }
        elif process_type == 'env_process':
            if state.get('environment'):
                return {
                    'response': f"Analyzing environment '{state['environment']}' in our monitoring data. Checking system health, recent deployments, and performance metrics...\n\nWhat specific aspect would you like me to investigate?",
                    'suggestions': ['Recent deployments', 'Error rates', 'Performance metrics', 'System health'],
                    'use_traditional_flow': True,
                    'focus': f"environment {state['environment']}"
                }
        elif process_type == 'performance_process':
            if state.get('performance_details'):
                return {
                    'response': f"Investigating performance issue: '{state['performance_details']}'. Analyzing metrics, error patterns, and correlations...\n\nWould you like me to look at any specific time period or component?",
                    'suggestions': ['Last hour', 'During business hours', 'Specific service', 'All components'],
                    'use_traditional_flow': True,
                    'focus': f"performance {state['performance_details']}"
                }
        
        return {
            'response': "Let me analyze that further. What specific details would you like me to investigate?",
            'suggestions': ['Show more details', 'Try different approach', 'Start over'],
            'use_traditional_flow': True
        }
    
    def _handle_lunch_process(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Continue handling lunch process"""
        return {
            'response': "Hope you find a great place for lunch! Anything else I can help you with?",
            'suggestions': ['Start new analysis', 'Customer issue', 'Environment check'],
            'use_traditional_flow': False
        }

# Global conversation flow instance
conversation_flow = ConversationFlow()