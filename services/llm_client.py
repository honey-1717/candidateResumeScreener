import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMClient:
    """Client for interacting with Language Model APIs"""
    
    def __init__(self, api_key=None):
        """
        Initialize the LLM client
        
        Args:
            api_key (str, optional): API key for Google PaLM. If not provided, 
                                     will use Hugging Face's free API.
        """
        self.api_key = api_key
        
        # If API key is provided, use Google PaLM API
        if self.api_key:
            self.api_type = "google"
            self.api_url = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText"
        # Otherwise use Hugging Face API (free tier with rate limits)
        else:
            self.api_type = "huggingface"
            self.api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    
    def generate_text(self, prompt, max_retries=3, retry_delay=5):
        """
        Generate text using the LLM API
        
        Args:
            prompt (str): The prompt to send to the LLM
            max_retries (int, optional): Maximum number of retries. Defaults to 3.
            retry_delay (int, optional): Delay between retries in seconds. Defaults to 5.
            
        Returns:
            str: The generated text
        """
        if self.api_type == "google":
            return self._generate_with_google(prompt, max_retries, retry_delay)
        else:
            return self._generate_with_huggingface(prompt, max_retries, retry_delay)
    
    def _generate_with_google(self, prompt, max_retries=3, retry_delay=5):
        """Generate text using Google PaLM API"""
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": self.api_key
        }
        
        payload = {
            "prompt": {
                "text": prompt
            },
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.95,
            "candidate_count": 1,
            "max_output_tokens": 1024,
            "safety_settings": [
                {"category": "HARM_CATEGORY_DEROGATORY", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_TOXICITY", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_VIOLENCE", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUAL", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_MEDICAL", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
            ]
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url, 
                    headers=headers, 
                    params=params,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        return result['candidates'][0]['output']
                    return ""
                
                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        print(f"Rate limited. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return "Error: Rate limit exceeded. Please try again later."
                
                # Handle other errors
                error_msg = f"Error: API returned status code {response.status_code}"
                try:
                    error_details = response.json()
                    if 'error' in error_details:
                        error_msg += f" - {error_details['error']['message']}"
                except:
                    pass
                return error_msg
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                return f"Error: {str(e)}"
        
        return "Error: Failed to generate text after multiple attempts."
    
    def _generate_with_huggingface(self, prompt, max_retries=3, retry_delay=5):
        """Generate text using Hugging Face Inference API"""
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.7,
                "top_p": 0.95,
                "do_sample": True
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get("generated_text", "").strip()
                    return ""
                
                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        print(f"Rate limited. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return "Error: Rate limit exceeded. Please try again later."
                
                # Handle other errors
                return f"Error: API returned status code {response.status_code}"
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                return f"Error: {str(e)}"
        
        return "Error: Failed to generate text after multiple attempts."
