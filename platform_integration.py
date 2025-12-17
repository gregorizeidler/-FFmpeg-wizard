"""
Platform Integration Module
Direct upload to YouTube, TikTok, Instagram, etc.
"""

from typing import Dict, Optional
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import json
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class PlatformUploader:
    """Handles uploads to various platforms."""
    
    def __init__(self):
        self.youtube_service = None
        self._init_youtube()
    
    def _init_youtube(self):
        """Initialize YouTube API client."""
        creds = None
        token_file = 'token.json'
        credentials_file = 'credentials.json'
        
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if os.path.exists(credentials_file):
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    print("YouTube credentials not found. Skipping YouTube integration.")
                    return
            
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        if creds:
            self.youtube_service = build('youtube', 'v3', credentials=creds)
    
    def upload_to_youtube(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        category_id: str = "22",  # People & Blogs
        privacy_status: str = "private"
    ) -> Optional[str]:
        """
        Upload video to YouTube.
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID
            privacy_status: 'private', 'unlisted', or 'public'
        
        Returns:
            Video ID or None
        """
        if not self.youtube_service:
            print("YouTube service not initialized. Please set up credentials.")
            return None
        
        try:
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }
            
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            insert_request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    print(f"Upload progress: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            print(f"Video uploaded successfully! ID: {video_id}")
            return video_id
            
        except Exception as e:
            print(f"Error uploading to YouTube: {e}")
            return None
    
    def schedule_youtube_upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        publish_at: str  # ISO 8601 format
    ) -> Optional[str]:
        """
        Schedule YouTube upload for later.
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            publish_at: ISO 8601 datetime string
        
        Returns:
            Video ID or None
        """
        if not self.youtube_service:
            return None
        
        try:
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': "22"
                },
                'status': {
                    'privacyStatus': 'private',
                    'publishAt': publish_at
                }
            }
            
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            insert_request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    print(f"Upload progress: {int(status.progress() * 100)}%")
            
            return response['id']
            
        except Exception as e:
            print(f"Error scheduling YouTube upload: {e}")
            return None
    
    def upload_to_tiktok(self, video_path: str, caption: str) -> bool:
        """
        Upload video to TikTok (requires TikTok API access).
        
        Args:
            video_path: Path to video file
            caption: Video caption
        
        Returns:
            Success status
        """
        # TikTok API integration would go here
        # Currently, TikTok API is limited and requires approval
        print("TikTok upload not yet implemented. TikTok API requires special approval.")
        return False
    
    def upload_to_instagram(self, video_path: str, caption: str) -> bool:
        """
        Upload video to Instagram (requires Instagram Graph API).
        
        Args:
            video_path: Path to video file
            caption: Video caption
        
        Returns:
            Success status
        """
        # Instagram Graph API integration would go here
        # Requires Facebook Developer account and app approval
        print("Instagram upload not yet implemented. Requires Instagram Graph API setup.")
        return False
    
    def get_upload_status(self, platform: str, video_id: str) -> Dict:
        """
        Get upload status for a video.
        
        Args:
            platform: Platform name ('youtube', etc.)
            video_id: Video ID
        
        Returns:
            Status dictionary
        """
        if platform == 'youtube' and self.youtube_service:
            try:
                response = self.youtube_service.videos().list(
                    part='status,snippet',
                    id=video_id
                ).execute()
                
                if response['items']:
                    video = response['items'][0]
                    return {
                        'status': video['status']['uploadStatus'],
                        'privacy': video['status']['privacyStatus'],
                        'title': video['snippet']['title']
                    }
            except Exception as e:
                print(f"Error getting upload status: {e}")
        
        return {'status': 'unknown'}


def export_for_platform(video_path: str, platform: str, output_path: Optional[str] = None) -> str:
    """
    Export video optimized for specific platform.
    
    Args:
        video_path: Input video path
        platform: Platform name ('youtube', 'instagram', 'tiktok', etc.)
        output_path: Optional output path
    
    Returns:
        Output video path
    """
    from compression import VideoCompressor
    
    compressor = VideoCompressor()
    
    if not output_path:
        name, ext = os.path.splitext(video_path)
        output_path = f"{name}_{platform}{ext}"
    
    compressor.compress_video(video_path, output_path, preset=platform)
    
    return output_path

