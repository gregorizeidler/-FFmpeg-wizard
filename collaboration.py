"""
Collaboration Features Module
Project sharing, comments, reviews, versioning.
"""

from typing import List, Dict, Optional
import json
import os
from datetime import datetime
import hashlib


class CollaborationManager:
    """Manages collaboration features."""
    
    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = projects_dir
        os.makedirs(projects_dir, exist_ok=True)
    
    def create_project(
        self,
        project_name: str,
        video_path: str,
        owner: str,
        description: Optional[str] = None
    ) -> str:
        """
        Create a new collaboration project.
        
        Args:
            project_name: Project name
            video_path: Path to video file
            owner: Owner username
            description: Optional description
        
        Returns:
            Project ID
        """
        project_id = hashlib.md5(f"{project_name}{owner}{datetime.now()}".encode()).hexdigest()[:8]
        
        project_data = {
            'id': project_id,
            'name': project_name,
            'description': description,
            'owner': owner,
            'created_at': datetime.now().isoformat(),
            'video_path': video_path,
            'versions': [],
            'comments': [],
            'collaborators': [owner],
            'status': 'draft'
        }
        
        project_path = os.path.join(self.projects_dir, f"{project_id}.json")
        with open(project_path, 'w') as f:
            json.dump(project_data, f, indent=2)
        
        return project_id
    
    def add_version(
        self,
        project_id: str,
        video_path: str,
        author: str,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Add a new version to project.
        
        Args:
            project_id: Project ID
            video_path: Path to edited video
            author: Author username
            notes: Optional version notes
        
        Returns:
            Version dictionary
        """
        project = self.get_project(project_id)
        if not project:
            return None
        
        version = {
            'id': len(project['versions']) + 1,
            'video_path': video_path,
            'author': author,
            'created_at': datetime.now().isoformat(),
            'notes': notes,
            'approved': False,
            'approved_by': None
        }
        
        project['versions'].append(version)
        self._save_project(project_id, project)
        
        return version
    
    def add_comment(
        self,
        project_id: str,
        author: str,
        text: str,
        timestamp: Optional[float] = None,
        version_id: Optional[int] = None
    ) -> Dict:
        """
        Add comment to project.
        
        Args:
            project_id: Project ID
            author: Comment author
            text: Comment text
            timestamp: Optional video timestamp
            version_id: Optional version ID
        
        Returns:
            Comment dictionary
        """
        project = self.get_project(project_id)
        if not project:
            return None
        
        comment = {
            'id': len(project['comments']) + 1,
            'author': author,
            'text': text,
            'timestamp': timestamp,
            'version_id': version_id,
            'created_at': datetime.now().isoformat(),
            'resolved': False
        }
        
        project['comments'].append(comment)
        self._save_project(project_id, project)
        
        return comment
    
    def approve_version(self, project_id: str, version_id: int, approver: str) -> bool:
        """
        Approve a version.
        
        Args:
            project_id: Project ID
            version_id: Version ID
            approver: Approver username
        
        Returns:
            Success status
        """
        project = self.get_project(project_id)
        if not project:
            return False
        
        for version in project['versions']:
            if version['id'] == version_id:
                version['approved'] = True
                version['approved_by'] = approver
                self._save_project(project_id, project)
                return True
        
        return False
    
    def add_collaborator(self, project_id: str, username: str) -> bool:
        """
        Add collaborator to project.
        
        Args:
            project_id: Project ID
            username: Username to add
        
        Returns:
            Success status
        """
        project = self.get_project(project_id)
        if not project:
            return False
        
        if username not in project['collaborators']:
            project['collaborators'].append(username)
            self._save_project(project_id, project)
        
        return True
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project data."""
        project_path = os.path.join(self.projects_dir, f"{project_id}.json")
        if os.path.exists(project_path):
            with open(project_path, 'r') as f:
                return json.load(f)
        return None
    
    def list_projects(self, username: Optional[str] = None) -> List[Dict]:
        """List all projects, optionally filtered by user."""
        projects = []
        
        for filename in os.listdir(self.projects_dir):
            if filename.endswith('.json'):
                project_path = os.path.join(self.projects_dir, filename)
                with open(project_path, 'r') as f:
                    project = json.load(f)
                    
                    if not username or username in project['collaborators']:
                        projects.append({
                            'id': project['id'],
                            'name': project['name'],
                            'owner': project['owner'],
                            'status': project['status'],
                            'versions_count': len(project['versions']),
                            'collaborators_count': len(project['collaborators'])
                        })
        
        return projects
    
    def _save_project(self, project_id: str, project_data: Dict):
        """Save project data."""
        project_path = os.path.join(self.projects_dir, f"{project_id}.json")
        with open(project_path, 'w') as f:
            json.dump(project_data, f, indent=2)

