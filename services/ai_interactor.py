"""
AI Interaction Module
"""

import dashscope
import json
import re
import time
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from services.config import Config
from exceptions.project_exceptions import AIInteractionError
# Removed direct import of UIProjectAgent to avoid circular import

if TYPE_CHECKING:
    from agents.application import UIProjectAgent

class AIInteractor:
    def __init__(self, api_key: Optional[str] = None):
        self.config = Config()
        if api_key:
            self.config.api_key = api_key
        self.messages: List[Dict[str, str]] = []
        self.agent: UIProjectAgent  # Use string annotation to avoid circular import

    def set_agent(self, agent):
        """Set agent reference to call actual actions"""
        self.agent = agent

    def ask_with_react(self, prompt: str) -> str:
        """
        Interact with AI using ReAct strategy
        """
        try:
            dashscope.api_key = self.config.api_key
            self.messages.append({"role": "user", "content": prompt})
            
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                try:
                    response = dashscope.Generation.call(
                        model=self.config.model_name,
                        messages=self.messages,
                        stream=True,
                        result_format='message'
                    )

                    content = ""
                    for resp in response:
                        if resp.status_code == 200 and hasattr(resp, 'output') and resp.output and 'choices' in resp.output:
                            if resp.output['choices'] and len(resp.output['choices']) > 0:
                                choice = resp.output['choices'][0]
                                if 'message' in choice and choice['message']:
                                    delta = choice['message'].get('content', '')
                                    if delta:
                                        content += delta
                        elif resp.status_code != 200:
                            raise AIInteractionError(
                                f"API call failed: status_code={resp.status_code}, "
                                f"code={getattr(resp, 'code', 'N/A')}, "
                                f"message={getattr(resp, 'message', 'N/A')}"
                            )
                    
                    self.messages.append({"role": "assistant", "content": content.strip()})
                    
                    # Check if it contains Thought process
                    thought_match = re.search(r'Thought:\s*(.*?)(?:\n(?:Action|Final Answer):|$)', content, re.DOTALL | re.IGNORECASE)
                    if thought_match:
                        thought = thought_match.group(1).strip()
                        if thought:
                            print(f"Thought: {thought}")

                    # Check if it contains Final Answer, if so, return the final answer directly
                    final_answer_match = re.search(r'Final Answer:\s*(.*)', content, re.DOTALL)
                    if final_answer_match:
                        # Extract content after Final Answer as the final result
                        final_answer = final_answer_match.group(1).strip()
                        return final_answer
                    
                    # Check if it contains Action, support multiple formats such as "Action: FUNCTION(args)" or "Action: FUNCTION (args)"
                    action_match = re.search(r'Action:\s*(\w+)\s*\((.*?)\)', content, re.IGNORECASE)
                    if action_match:
                        action = action_match.group(1)
                        action_input = action_match.group(2).strip('\"')
                        
                        # Execute Action and get Observation
                        observation = self.dispatch_action(action, action_input)
                        
                        # Add Observation to the conversation
                        observation_message = f"Observation: {observation}"
                        # print(observation_message)  # Add print for debugging
                        self.messages.append({"role": "user", "content": observation_message})
                        
                        iteration += 1
                    else:
                        # No more Action, check if it contains Final Answer line, if so, extract content after it
                        # This is to handle the case where AI may not strictly follow the format but gives the answer in the last line
                        lines = content.strip().split('\n')
                        final_answer_found = False
                        final_answer_lines = []
                        
                        for line in lines:
                            if line.startswith('Final Answer:'):
                                final_answer_found = True
                                # Extract content after "Final Answer:" (if any)
                                possible_answer = line[13:].strip()  # 13 is the length of "Final Answer:"
                                if possible_answer:
                                    final_answer_lines.append(possible_answer)
                            elif final_answer_found:
                                # After finding the Final Answer line, all subsequent lines are considered part of the answer
                                final_answer_lines.append(line)
                        
                        if final_answer_found:
                            final_answer = '\n'.join(final_answer_lines).strip()
                            return final_answer
                        
                        # If there is no Final Answer line either, log warning and try to extract useful information from content
                        print("Warning: AI response did not follow ReAct format, neither Action nor Final Answer identifier found")
                        
                        # Try to extract possible file list from content (for file list generation scenario)
                        # This is a heuristic method to extract useful information from non-standard format
                        potential_files = []
                        for line in lines:
                            # Enhanced heuristic check if it looks like a file path or valid result
                            cleaned_line = line.strip()
                            if (cleaned_line and 
                                # Check if it contains path separators and extensions, or looks like a reasonable answer
                                (('.' in cleaned_line and ('/' in cleaned_line or '\\' in cleaned_line)) or 
                                 # Or it's valid content that doesn't start with specific ReAct keywords
                                 not cleaned_line.startswith(('Thought:', 'Action:', 'Observation:', 'Final Answer:')) and 
                                 len(cleaned_line) > 0)):
                                potential_files.append(cleaned_line)
                        
                        if potential_files:
                            print("Possible file list extracted from non-standard format")
                            return '\n'.join(potential_files)
                        else:
                            # If no useful information can be extracted, return the entire content
                            print("Cannot extract useful information from non-standard format, returning full content")
                            return content.strip()
                
                except Exception as e:
                    print(f"Error calling AI interface: {str(e)}")
                    # Implement retry mechanism
                    if iteration < self.config.max_retries - 1:
                        wait_time = 2 ** iteration  # Exponential backoff
                        print(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        iteration += 1
                        continue
                    else:
                        raise AIInteractionError(f"AI interface call failed, retried {self.config.max_retries} times: {str(e)}")
            
            # After reaching maximum iterations, try to extract Final Answer
            final_content = self.messages[-1]["content"] if self.messages else ""
            final_answer_match = re.search(r'Final Answer:\s*(.*)', final_content, re.DOTALL)
            if final_answer_match:
                final_answer = final_answer_match.group(1).strip()
                return final_answer
            else:
                # If Final Answer is not found, try other ways to extract answer
                lines = final_content.strip().split('\n')
                final_answer_found = False
                final_answer_lines = []
                
                for line in lines:
                    if line.startswith('Final Answer:'):
                        final_answer_found = True
                        possible_answer = line[13:].strip()
                        if possible_answer:
                            final_answer_lines.append(possible_answer)
                    elif final_answer_found:
                        final_answer_lines.append(line)
                
                if final_answer_found:
                    final_answer = '\n'.join(final_answer_lines).strip()
                    return final_answer
                
                # Last resort: issue warning and return full content
                print("Warning: Maximum iterations reached but Final Answer identifier not found, returning full content")
                return final_content.strip()
        
        except Exception as e:
            raise AIInteractionError(f"AI interaction failed: {str(e)}")

    def dispatch_action(self, action: str, action_input: str) -> str:
        """
        Execute specific Action and return result
        """
        # If there is an agent reference, call the actual action implementation in agent
        if self.agent:
            # Parse parameters
            args: List[str] = []
            if action_input:
                # Try to parse parameters, support quoted parameters
                try:
                    import csv
                    from io import StringIO
                    # Use csv module to handle potentially quoted parameters
                    reader = csv.reader(StringIO(action_input), delimiter=',', quotechar='"')
                    # Get parameters from all rows and merge (usually only one row)
                    for row in reader:
                        args.extend([arg.strip() for arg in row])
                except Exception as e:
                    # If CSV parsing fails, use simple comma splitting
                    print(f"Parameter parsing warning: CSV parsing failed, using simple splitting: {e}")
                    args = [arg.strip() for arg in action_input.split(',')]
            
            # Call the actual action implementation in agent
            try:
                result = self.agent.execute_action(action, args)
                return result
            except Exception as e:
                return f"Error executing {action} operation: {str(e)}"
        else:
            # If there is no agent reference, return simulated response
            return f"Executed {action} operation with input: {action_input}"
    
    def rollback_last_interaction(self):
        """
        Remove the most recent user question and AI answer, used when user rejects AI suggestions
        """
        if len(self.messages) >= 2:
            # Remove the last two messages (AI's answer and user's question)
            self.messages.pop()  # AI's answer
            self.messages.pop()  # User's question
