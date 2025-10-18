"""
Release notes service that parses git commits and generates release data
"""

import subprocess
import re
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Release:
    version: str
    date: str
    type: str  # major, minor, patch, hotfix
    summary: str
    features: List[str]
    improvements: List[str]
    fixes: List[str]
    technical: List[str]


def get_git_commits(days_back: int = 60) -> List[Dict[str, str]]:
    """Get git commits from the last N days"""
    try:
        # Get commits with hash, date, and message
        cmd = f"git log --pretty=format:'%h|%ad|%s' --date=short --since='{days_back} days ago'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Git command failed: {result.stderr}")
            return []
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|', 2)
                if len(parts) == 3:
                    commits.append({
                        'hash': parts[0],
                        'date': parts[1],
                        'message': parts[2]
                    })
        
        return commits
    except Exception as e:
        print(f"Error getting git commits: {e}")
        return []


def categorize_commit(message: str) -> tuple[str, str]:
    """Categorize a commit message and extract a clean description"""
    message_lower = message.lower()
    
    # Determine type
    if any(word in message_lower for word in ['fix', 'bug', 'error', 'issue', 'problem']):
        commit_type = 'fix'
    elif any(word in message_lower for word in ['add', 'implement', 'create', 'new', 'feature']):
        commit_type = 'feature'
    elif any(word in message_lower for word in ['improve', 'enhance', 'update', 'refactor', 'optimize']):
        commit_type = 'improvement'
    elif any(word in message_lower for word in ['migration', 'database', 'deploy', 'config', 'setup']):
        commit_type = 'technical'
    else:
        commit_type = 'improvement'  # default
    
    # Clean up the message
    clean_message = message
    
    # Remove common prefixes
    prefixes_to_remove = [
        r'^fix\s*:?\s*',
        r'^add\s*:?\s*',
        r'^implement\s*:?\s*',
        r'^create\s*:?\s*',
        r'^update\s*:?\s*',
        r'^improve\s*:?\s*',
        r'^enhance\s*:?\s*',
        r'^refactor\s*:?\s*',
        r'^configure\s*:?\s*',
        r'^setup\s*:?\s*',
    ]
    
    for prefix in prefixes_to_remove:
        clean_message = re.sub(prefix, '', clean_message, flags=re.IGNORECASE)
    
    # Capitalize first letter
    if clean_message:
        clean_message = clean_message[0].upper() + clean_message[1:]
    
    return commit_type, clean_message


def group_commits_by_date(commits: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Group commits by date"""
    grouped = {}
    for commit in commits:
        date = commit['date']
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(commit)
    return grouped


def generate_release_version(date: str, index: int) -> str:
    """Generate a version number based on date and index"""
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day
        
        # Create version like 2025.10.17.1
        return f"{year}.{month:02d}.{day:02d}.{index}"
    except:
        return f"v{index}"


def determine_release_type(commits: List[Dict[str, str]]) -> str:
    """Determine the overall release type based on commits"""
    types = []
    for commit in commits:
        commit_type, _ = categorize_commit(commit['message'])
        types.append(commit_type)
    
    # Count types
    type_counts = {}
    for t in types:
        type_counts[t] = type_counts.get(t, 0) + 1
    
    # Determine release type
    if type_counts.get('feature', 0) > 0:
        return 'minor'
    elif type_counts.get('fix', 0) > 2:
        return 'hotfix'
    elif type_counts.get('technical', 0) > 0:
        return 'patch'
    else:
        return 'patch'


def generate_release_summary(commits: List[Dict[str, str]]) -> str:
    """Generate a summary for the release based on commits"""
    if not commits:
        return "No changes"
    
    # Get the most significant commit
    main_commit = commits[0]
    _, clean_message = categorize_commit(main_commit['message'])
    
    if len(commits) == 1:
        return clean_message
    else:
        return f"{clean_message} and {len(commits) - 1} other changes"


def generate_releases(days_back: int = 60) -> List[Release]:
    """Generate release data from git commits"""
    commits = get_git_commits(days_back)
    
    if not commits:
        return []
    
    # Group commits by date
    grouped_commits = group_commits_by_date(commits)
    
    releases = []
    for date, date_commits in sorted(grouped_commits.items(), reverse=True):
        # Sort commits within the day by significance
        date_commits.sort(key=lambda x: (
            # Prioritize by type
            {'feature': 0, 'improvement': 1, 'fix': 2, 'technical': 3}.get(
                categorize_commit(x['message'])[0], 1
            ),
            x['message']  # Then alphabetically
        ))
        
        # Determine release type
        release_type = determine_release_type(date_commits)
        
        # Generate version
        version = generate_release_version(date, 1)
        
        # Generate summary
        summary = generate_release_summary(date_commits)
        
        # Categorize commits
        features = []
        improvements = []
        fixes = []
        technical = []
        
        for commit in date_commits:
            commit_type, clean_message = categorize_commit(commit['message'])
            
            if commit_type == 'feature':
                features.append(clean_message)
            elif commit_type == 'improvement':
                improvements.append(clean_message)
            elif commit_type == 'fix':
                fixes.append(clean_message)
            elif commit_type == 'technical':
                technical.append(clean_message)
        
        # Create release
        release = Release(
            version=version,
            date=date,
            type=release_type,
            summary=summary,
            features=features,
            improvements=improvements,
            fixes=fixes,
            technical=technical
        )
        
        releases.append(release)
    
    return releases


def get_latest_releases(limit: int = 20) -> List[Release]:
    """Get the latest releases"""
    return generate_releases(60)[:limit]
