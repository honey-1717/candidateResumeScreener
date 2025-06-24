import requests
import json
from dotenv import load_dotenv
from config import GOOGLE_API_KEY, GEMINI_API_URL, GEMINI_MODEL

# Load environment variables
load_dotenv()

class LLMClient:
    """Client for interacting with Language Model APIs"""
    
    def __init__(self):
        """
        Initialize the LLM client
        """
        self.api_key = GOOGLE_API_KEY
        self.api_url = GEMINI_API_URL # This URL already specifies the model
    
    def generate_text(self, prompt_text: str, temperature: float = 0.5, max_tokens: int = 2048):
        """
        Generates text using the configured Gemini model via direct HTTP request.
        """
        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        # Add API key to URL
        url_with_key = f"{self.api_url}?key={self.api_key}"

        try:
            response = requests.post(url_with_key, headers=headers, data=json.dumps(data))
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            response_json = response.json()
            
            if "candidates" in response_json and len(response_json["candidates"]) > 0:
                if "content" in response_json["candidates"][0] and "parts" in response_json["candidates"][0]["content"] and len(response_json["candidates"][0]["content"]["parts"]) > 0:
                    return response_json["candidates"][0]["content"]["parts"][0]["text"]
            
            # Handle cases where the expected response structure is missing
            error_message = "LLM response missing expected content. Full response: " + json.dumps(response_json)
            print(f"Error: {error_message}") # Log for debugging
            return f"Error: Could not extract text from LLM response. {error_message}"

        except requests.exceptions.RequestException as e:
            print(f"Error during LLM API request: {e}") # Log for debugging
            return f"Error: API request failed - {str(e)}"
        except json.JSONDecodeError as e:
            print(f"Error decoding LLM JSON response: {e}. Response text: {response.text}") # Log for debugging
            return f"Error: Could not decode LLM response - {str(e)}"
        except KeyError as e:
            print(f"KeyError accessing LLM response: {e}. Response JSON: {json.dumps(response_json if 'response_json' in locals() else 'N/A')}") # Log for debugging
            return f"Error: Unexpected LLM response structure - {str(e)}"

# This function is specifically for the 1-pager anonymization
def anonymize_text_with_llm(resume_text: str) -> str:
    """
    Anonymizes resume text using an LLM, keeping only the first name
    and replacing other PII with the placeholder "[REDACTED]".
    The output will be formatted using Markdown for better organization.
    """
    prompt = f"""
    You are an expert HR assistant. Your task is to process the following resume text.

    **Overall Goal:** Create a clean, organized, and anonymized 1-page summary suitable for unbiased screening.

    **Instructions for Anonymization:**
    1.  **Identify the candidate's full name.**
    2.  **Output ONLY the candidate's first name on the very first line, formatted as a Level 1 Markdown heading (e.g., `# John`).** This is the only Level 1 heading.
    3.  **Replace ALL other Personally Identifiable Information (PII) with the placeholder "[REDACTED]".** This includes:
        -   Surnames/Last Names (after the first name has been extracted for the first line).
        -   Phone numbers.
        -   Email addresses.
        -   Specific physical addresses (street, city, state, zip code). Generic regions like "[REDACTED] Area" are acceptable if location context is important for a role, but specific city/state should be redacted.
        -   Social media profile URLs (e.g., LinkedIn, GitHub, personal websites).
        -   Any other direct contact details.
    4.  **Do NOT use the first name as a placeholder for other PII.** Use "[REDACTED]".

    **Instructions for Formatting (Output in Markdown):**
    1.  **First Name:** The first line MUST be `# FirstName`.
    2.  **Main Sections:** Use `##` for major section headings (e.g., `## Professional Summary`, `## Experience`, `## Education`, `## Skills`, `## Projects`).
    3.  **Sub-headings/Titles:** Use `###` for job titles, company names, or degree names within sections (e.g., `### Software Engineer at [REDACTED] Company`).
    4.  **Course Information (Education Section):**
        -   Keep course lists brief. Focus on the degree and institution (anonymized if necessary, e.g., "[REDACTED] University").
        -   If specific courses are mentioned, list only general subject areas or very high-level course names (e.g., "Advanced Algorithms", "Data Structures").
        -   **Redact any overly specific, niche, or potentially identifying course titles or lengthy descriptions.** Replace with "[REDACTED]" or omit.
    5.  **Bullet Points:** Use `-` for list items (e.g., job responsibilities, skills lists). Ensure clean, concise bullet points.
    6.  **Paragraphs:** Ensure clear line breaks between paragraphs for readability.
    7.  **No Markdown in Content:** The Markdown symbols (`#`, `##`, `###`, `-`) are ONLY for structuring. Do NOT include these symbols *within* the text content of paragraphs or bullet points.
    8.  **Preserve Professional Content:** Ensure all relevant professional content (experience details, education summaries, skills, project descriptions) remains intact and is not altered or removed, except for the PII.
    9.  **Maintain Logical Flow:** Keep the logical flow and order of the original resume.
    10. **Conciseness:** Aim for a summary that fits well on a single page when formatted. Remove redundant phrases or overly verbose descriptions if possible without losing meaning.

    Resume Text to Anonymize and Format:
    ---
    {resume_text}
    ---

    Anonymized and Formatted Resume Text (Markdown):
    """
    
    client = LLMClient()
    # Give enough tokens for the original text + Markdown formatting + [REDACTED]
    anonymized_text = client.generate_text(prompt, temperature=0.15, max_tokens=len(resume_text) * 2 + 500) # Slightly more tokens, lower temp for precision

    if anonymized_text.startswith("Error:"):
        print(f"Anonymization Error: {anonymized_text}")
        return "Error during anonymization. Could not process resume." 
        
    return anonymized_text
