import os
import csv
import json
from datetime import datetime
from typing import List, Dict, Any

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Check if a file has an allowed extension
    
    Args:
        filename (str): The filename to check
        allowed_extensions (set): Set of allowed file extensions
        
    Returns:
        bool: True if file has an allowed extension, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def create_directories(directories: List[str]) -> None:
    """
    Create directories if they don't exist
    
    Args:
        directories (list): List of directory paths to create
    """
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def save_results_to_csv(results: List[tuple], priorities: Dict[str, int], output_file: str) -> None:
    """
    Save evaluation results to CSV file
    
    Args:
        results (list): List of (candidate, result) tuples
        priorities (dict): Dictionary mapping criteria to priority values
        output_file (str): Path to output CSV file
    """
    if not results:
        return
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Get all criteria from the first result
    criteria = list(results[0][1]['criteria_scores'].keys())
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header row
        header = ['Candidate', 'Overall Score (%)'] + [f"{c} (Priority: {priorities[c]})" for c in criteria]
        writer.writerow(header)
        
        # Write data rows
        for candidate, result in results:
            row = [
                candidate, 
                f"{result['overall_score']:.2f}"
            ]
            
            for criterion in criteria:
                row.append(result['criteria_scores'][criterion])
            
            writer.writerow(row)

def save_session(session_data: Dict[str, Any], output_dir: str, session_id: str) -> str:
    """
    Save session data to JSON file
    
    Args:
        session_data (dict): Session data to save
        output_dir (str): Directory to save the file
        session_id (str): Session ID
        
    Returns:
        str: Path to the saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{session_id}_{timestamp}.json"
    file_path = os.path.join(output_dir, filename)
    
    # Convert datetime objects to strings
    session_data_copy = {}
    for key, value in session_data.items():
        if isinstance(value, datetime):
            session_data_copy[key] = value.isoformat()
        else:
            session_data_copy[key] = value
    
    # Save to file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(session_data_copy, f, indent=2)
    
    return file_path

def load_session(file_path: str) -> Dict[str, Any]:
    """
    Load session data from JSON file
    
    Args:
        file_path (str): Path to the session file
        
    Returns:
        dict: Session data
    """
    if not os.path.exists(file_path):
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        int: File size in bytes
    """
    return os.path.getsize(file_path)

def get_file_extension(file_path: str) -> str:
    """
    Get file extension
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: File extension (lowercase, without dot)
    """
    return os.path.splitext(file_path)[1].lower().lstrip('.')

def list_files(directory: str, extensions: List[str] = None) -> List[str]:
    """
    List files in a directory, optionally filtered by extension
    
    Args:
        directory (str): Directory to list files from
        extensions (list, optional): List of extensions to filter by
        
    Returns:
        list: List of file paths
    """
    if not os.path.exists(directory):
        return []
    
    files = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            if extensions is None or get_file_extension(file_path) in extensions:
                files.append(file_path)
    
    return files
