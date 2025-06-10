from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class Criterion:
    """Represents an evaluation criterion"""
    name: str
    priority: int = 5  # 1-10, where 10 is highest priority
    description: str = ""
    
@dataclass
class CriteriaScore:
    """Represents a score for a specific criterion"""
    criterion: str
    score: int  # 0-10
    justification: str = ""
    
@dataclass
class CandidateScore:
    """Represents a candidate's evaluation scores"""
    candidate_name: str
    criteria_scores: Dict[str, int]  # Mapping of criterion name to score (0-10)
    overall_score: float  # Weighted overall score (0-100%)
    feedback: str = ""
    
@dataclass
class JobDescription:
    """Represents a job description"""
    title: str
    description: str
    criteria: List[Criterion] = field(default_factory=list)
    file_path: Optional[str] = None
    upload_date: datetime = field(default_factory=datetime.now)
    
@dataclass
class Resume:
    """Represents a candidate's resume"""
    candidate_name: str
    content: str
    file_path: str
    file_type: str
    upload_date: datetime = field(default_factory=datetime.now)
    sections: Dict[str, str] = field(default_factory=dict)
    
@dataclass
class EvaluationSession:
    """Represents a complete evaluation session"""
    session_id: str
    job_description: JobDescription
    criteria: List[str]
    priorities: Dict[str, int]
    resumes: Dict[str, Resume]
    results: Dict[str, CandidateScore] = field(default_factory=dict)
    creation_date: datetime = field(default_factory=datetime.now)
    
@dataclass
class EvaluationResult:
    """Represents the complete evaluation results"""
    session_id: str
    job_description: str
    criteria: List[Criterion]
    candidate_scores: List[CandidateScore]
    best_candidate: str = ""
    results_file: str = ""
    evaluation_date: datetime = field(default_factory=datetime.now)
