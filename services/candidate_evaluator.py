from services.llm_client import LLMClient
from config import GOOGLE_API_KEY, GEMINI_API_URL, GEMINI_MODEL

class CandidateEvaluator:
    """Service for evaluating candidates based on job criteria"""
    
    def __init__(self, api_key=None):
        """
        Initialize the candidate evaluator
        
        Args:
            api_key (str, optional): API key for LLM service
        """
        self.api_key = api_key or GOOGLE_API_KEY
    
    def evaluate_candidates(self, job_description, criteria, priorities, resumes):
        """
        Evaluate candidates based on job description, criteria, and priorities
        
        Args:
            job_description (str): The job description text
            criteria (list): List of evaluation criteria
            priorities (dict): Dictionary mapping criteria to priority values (1-10)
            resumes (dict): Dictionary mapping candidate names to resume texts
            
        Returns:
            dict: Evaluation results for each candidate
        """
        print(f"Evaluating all {len(resumes)} candidates together for better comparison")
        
        # First, evaluate all candidates together for direct comparison
        comparative_scores = self._evaluate_all_resumes(job_description, criteria, list(resumes.items()))
        
        results = {}
        for candidate, resume_text in resumes.items():
            criteria_scores, justifications = self._get_detailed_evaluation(
                job_description, 
                criteria, 
                resume_text,
                comparative_scores.get(candidate, {})
            )
            
            # Calculate weighted score
            total_priority = sum(priorities.values())
            weighted_score = 0
            
            for criterion, score in criteria_scores.items():
                criterion_priority = priorities[criterion]
                weighted_score += (score * criterion_priority) / total_priority
            
            # Convert to percentage
            overall_score = (weighted_score / 10) * 100
            
            results[candidate] = {
                'criteria_scores': criteria_scores,
                'justifications': justifications,
                'overall_score': overall_score
            }
        
        return results
    
    def _evaluate_all_resumes(self, job_description, criteria, candidate_resumes):
        """
        Evaluate all resumes together for direct comparison
        
        Args:
            job_description (str): The job description text
            criteria (list): List of evaluation criteria
            candidate_resumes (list): List of (candidate_name, resume_text) tuples
            
        Returns:
            dict: Dictionary mapping candidate names to scores for each criterion
        """
        import requests
        import json
        
        # Prepare candidate information
        candidates_info = []
        for candidate_name, resume_text in candidate_resumes:
            # Truncate resume text if too long
            max_length = 2000  # Shorter to accommodate multiple resumes
            truncated_resume = resume_text[:max_length] + "..." if len(resume_text) > max_length else resume_text
            candidates_info.append(f"Candidate: {candidate_name}\nResume:\n{truncated_resume}\n\n")
        
        candidates_text = "\n".join(candidates_info)
        
        url = GEMINI_API_URL
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": self.api_key
        }
        
        prompt = f"""
        You are an expert resume screener. Evaluate and compare the following candidates for a job position.
        
        Job Description:
        {job_description}
        
        Evaluation Criteria:
        {', '.join(criteria)}
        
        Candidates:
        {candidates_text}
        
        For each candidate, evaluate them on each criterion on a scale of 0-10 (where 10 is perfect match).
        Consider how candidates compare to each other for each criterion.It must give a score for each criterion.
        if criteria is mandatory, score must be 10.if criteria is preferred, score must be 8.if criteria is optional, score can be between 4 and .
        
        Format your response as:
        
        CANDIDATE: [Candidate Name]
        [Criterion 1]: [Score 0-10]
        [Criterion 2]: [Score 0-10]
        ...
        
        Repeat for each candidate. Be objective and fair in your comparative assessment.
        """
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    response_text = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Parse the response to extract scores for each candidate
                    comparative_scores = {}
                    current_candidate = None
                    
                    for line in response_text.strip().split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line.startswith('CANDIDATE:'):
                            current_candidate = line.split('CANDIDATE:')[1].strip()
                            comparative_scores[current_candidate] = {}
                        elif current_candidate and ':' in line:
                            parts = line.split(':', 1)
                            criterion = parts[0].strip()
                            
                            # Find the matching criterion from our list
                            matching_criterion = None
                            for c in criteria:
                                if c.lower() in criterion.lower() or criterion.lower() in c.lower():
                                    matching_criterion = c
                                    break
                            
                            if matching_criterion:
                                try:
                                    score_text = parts[1].strip()
                                    # Extract the first number found in the score text
                                    score_match = score_text.split()[0]
                                    score = int(float(score_match))
                                    comparative_scores[current_candidate][matching_criterion] = min(10, max(0, score))
                                except (ValueError, IndexError):
                                    comparative_scores[current_candidate][matching_criterion] = 5
                    
                    return comparative_scores
            
            # If API call fails, return empty dict
            return {}
        except Exception as e:
            print(f"Error in comparative evaluation: {str(e)}")
            return {}
    
    def _get_detailed_evaluation(self, job_description, criteria, resume_text, comparative_scores=None):
        """
        Get detailed evaluation with justifications for a single resume
        
        Args:
            job_description (str): The job description text
            criteria (list): List of evaluation criteria
            resume_text (str): The resume text
            comparative_scores (dict): Pre-computed scores from comparative evaluation
            
        Returns:
            tuple: (scores, justifications) for each criterion
        """
        import requests
        import json
        
        # Truncate resume text if too long to avoid API limits
        max_length = 4000
        if len(resume_text) > max_length:
            resume_text = resume_text[:max_length] + "..."
        
        url = GEMINI_API_URL
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": self.api_key
        }
        
        # Include comparative scores in the prompt if available
        comparative_info = ""
        if comparative_scores:
            comparative_info = "Based on comparative analysis, you've already assigned these scores:\n"
            for criterion, score in comparative_scores.items():
                comparative_info += f"{criterion}: {score}/10\n"
            comparative_info += "\nPlease provide detailed justifications for these scores."
        
        prompt = f"""
        You are an expert resume screener. Evaluate the following resume against the job description and criteria.
        
        Job Description:
        {job_description}
        
        Resume:
        {resume_text}
        
        {comparative_info}
        
        Evaluate the candidate on each of the following criteria on a scale of 0-10 (where 10 is perfect match):
        {', '.join(criteria)}
        
        For each criterion, provide:
        1. A score from 0-10
        2. A detailed justification (2-3 sentences) explaining why you gave this score
        
        Format your response EXACTLY as follows for each criterion:
        
        CRITERION: [Name of Criterion]
        SCORE: [Score 0-10]
        JUSTIFICATION: [Your detailed justification]
        
        Repeat this format for each criterion. Be specific and detailed in your justifications.
        """
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    response_text = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Parse the response to extract scores and justifications
                    scores = {}
                    justifications = {}
                    
                    # Use comparative scores as a starting point if available
                    if comparative_scores:
                        scores = comparative_scores.copy()
                    
                    # Split by criterion sections
                    sections = response_text.split("CRITERION:")
                    
                    for section in sections:
                        if not section.strip():
                            continue
                            
                        lines = section.strip().split('\n')
                        criterion_line = lines[0].strip()
                        
                        # Find the criterion that best matches
                        matched_criterion = None
                        for c in criteria:
                            if c.lower() in criterion_line.lower() or criterion_line.lower() in c.lower():
                                matched_criterion = c
                                break
                        
                        if not matched_criterion:
                            continue
                            
                        # Extract score
                        score = scores.get(matched_criterion, 0)  # Use existing score if available
                        for line in lines:
                            if "SCORE:" in line:
                                try:
                                    score_text = line.split("SCORE:")[1].strip()
                                    score = int(float(score_text))
                                    scores[matched_criterion] = min(10, max(0, score))
                                except (ValueError, IndexError):
                                    scores[matched_criterion] = score
                                break
                        
                        # Extract justification
                        justification = ""
                        justification_started = False
                        for line in lines:
                            if "JUSTIFICATION:" in line:
                                justification = line.split("JUSTIFICATION:")[1].strip()
                                justification_started = True
                            elif justification_started and line.strip() and "CRITERION:" not in line and "SCORE:" not in line:
                                justification += " " + line.strip()
                        
                        justifications[matched_criterion] = justification
                    
                    # Ensure all criteria have scores and justifications
                    for criterion in criteria:
                        if criterion not in scores:
                            scores[criterion] = 5
                        if criterion not in justifications:
                            justifications[criterion] = "No specific justification provided."
                    
                    return scores, justifications
            
            # If API call fails, return default scores and justifications
            return {criterion: 5 for criterion in criteria}, {criterion: "Unable to evaluate due to API error." for criterion in criteria}
        except Exception as e:
            print(f"Error evaluating resume: {str(e)}")
            return {criterion: 5 for criterion in criteria}, {criterion: f"Error during evaluation: {str(e)}" for criterion in criteria}
    
    def generate_feedback(self, job_description, resume_text, criteria_scores):
        """
        Generate detailed feedback for a candidate using Gemini API
        
        Args:
            job_description (str): The job description text
            resume_text (str): The resume text
            criteria_scores (dict): Dictionary of criteria scores
            
        Returns:
            str: Detailed feedback for the candidate
        """
        import requests
        import json
        
        # Truncate texts if too long
        max_length = 2000
        if len(job_description) > max_length:
            job_description = job_description[:max_length] + "..."
        if len(resume_text) > max_length:
            resume_text = resume_text[:max_length] + "..."
        
        # Format criteria scores for the prompt
        criteria_scores_text = "\n".join([f"{criterion}: {score}/10" for criterion, score in criteria_scores.items()])
        
        url = GEMINI_API_URL
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": self.api_key
        }
        
        prompt = f"""
        You are an expert resume reviewer. Generate constructive feedback for a candidate based on their resume and how it matches the job description.
        
        Job Description:
        {job_description}
        
        Resume:
        {resume_text}
        
        Evaluation Scores:
        {criteria_scores_text}
        
        Provide the following feedback:
        1. 3 key strengths of the candidate for this role
        2. 3 areas for improvement or missing qualifications
        3. Overall assessment of fit for the role
        
        Format your response in a professional and constructive manner.
        """
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            return "Unable to generate feedback at this time."
        except Exception as e:
            print(f"Error generating feedback: {str(e)}")
            return "Unable to generate feedback at this time."
