import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Dict, Optional
from datetime import datetime, timezone
import isodate


class YouTubeAPI:
    """
    Class for working with the YouTube Data API v3
    """
    
    SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'
    
    def __init__(self, credentials_file: str = 'config/client_secrets.json'):
        self.credentials_file = credentials_file
        self.service = None
        self.channel_info = None
    
    def authenticate(self, token_file: str) -> bool:
        """
        Authenticates via OAuth 2.0.

        Args:
            token_file: Path to the file with saved tokens.

        Returns:
            True if authentication is successful.
        """
        creds = None

        # Check for an existing token
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

        # If there is no token or it is invalid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    creds = None
            
            # Start the authorization flow
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Create a project in the Google Cloud Console and download the credentials."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the token
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

        # Create the service object
        self.service = build(self.API_SERVICE_NAME, self.API_VERSION, credentials=creds)

        # Get channel information
        self.channel_info = self._get_my_channel_info()

        return True
    
    def _get_my_channel_info(self) -> Dict:
        """Gets information about the current channel."""
        if not self.service:
            return None
        
        request = self.service.channels().list(
            part='snippet,contentDetails',
            mine=True
        )
        response = request.execute()
        
        if response['items']:
            return response['items'][0]
        return None
    
    def get_channel_id(self) -> Optional[str]:
        """Gets the ID of the current channel."""
        if self.channel_info:
            return self.channel_info['id']
        return None
    
    def get_channel_title(self) -> Optional[str]:
        """Gets the title of the current channel."""
        if self.channel_info:
            return self.channel_info['snippet']['title']
        return None
    
    def get_subscriptions(self, max_results: int = 50) -> List[Dict]:
        """
        Gets a list of subscriptions.

        Args:
            max_results: The maximum number of results per request.

        Returns:
            A list of subscriptions with channel information.
        """
        if not self.service:
            raise RuntimeError("Not authorized. Call authenticate() first.")
        
        subscriptions = []
        next_page_token = None
        
        while True:
            request = self.service.subscriptions().list(
                part='snippet',
                mine=True,
                maxResults=max_results,
                pageToken=next_page_token
            )
            
            response = request.execute()
            
            for item in response.get('items', []):
                subscription = {
                    'channel_id': item['snippet']['resourceId']['channelId'],
                    'channel_name': item['snippet']['title'],
                    'thumbnail': item['snippet']['thumbnails']['default']['url'],
                    'description': item['snippet']['description']
                }
                subscriptions.append(subscription)
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return subscriptions
    
    def get_channel_videos(self, channel_id: str, max_results: int = 10) -> List[Dict]:
        """
        Gets recent videos from a channel.

        Args:
            channel_id: The YouTube channel ID.
            max_results: The maximum number of videos to retrieve.

        Returns:
            A list of videos with metadata.
        """
        if not self.service:
            raise RuntimeError("Not authorized. Call authenticate() first.")

        # Get the uploads playlist ID
        request = self.service.channels().list(
            part='contentDetails',
            id=channel_id
        )
        response = request.execute()

        if not response['items']:
            return []

        uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Get videos from the uploads playlist
        request = self.service.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=max_results
        )
        response = request.execute()

        video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]

        if not video_ids:
            return []

        # Get detailed information about the videos
        videos_request = self.service.videos().list(
            part='snippet,contentDetails,statistics',
            id=','.join(video_ids)
        )
        videos_response = videos_request.execute()

        videos = []
        for item in videos_response.get('items', []):
            try:
                # Parse ISO 8601 duration
                duration_iso = item['contentDetails'].get('duration', 'PT0S')

                # Check for livestream (duration is missing or PT0S)
                if not duration_iso or duration_iso == 'PT0S':
                    duration_formatted = "LIVE"
                else:
                    duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
                    if duration_seconds == 0:
                        duration_formatted = "LIVE"
                    else:
                        duration_formatted = self._format_duration(duration_seconds)
            except (KeyError, ValueError, AttributeError):
                # Livestream or other format
                duration_formatted = "LIVE"

            video = {
                'video_id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet'].get('description', ''),
                'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                'published_at': item['snippet']['publishedAt'],
                'duration': duration_formatted,
                'view_count': int(item['statistics'].get('viewCount', 0))
            }
            videos.append(video)

        return videos
    
    def get_latest_videos_from_subscriptions(self, hours: int = 24, 
                                             max_videos_per_channel: int = 5) -> List[Dict]:
        """
        Gets the latest videos from all subscriptions.

        Args:
            hours: How many hours back to get videos from.
            max_videos_per_channel: The maximum number of videos from each channel.

        Returns:
            A list of videos with metadata and channel information.
        """
        subscriptions = self.get_subscriptions()
        all_videos = []

        for sub in subscriptions:
            videos = self.get_channel_videos(
                sub['channel_id'], 
                max_results=max_videos_per_channel
            )

            # Add channel information to each video
            for video in videos:
                video['channel_id'] = sub['channel_id']
                video['channel_name'] = sub['channel_name']
                video['channel_thumbnail'] = sub['thumbnail']
                all_videos.append(video)

        # Sort by publication date
        all_videos.sort(key=lambda x: x['published_at'], reverse=True)

        return all_videos
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Formats the video duration."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def parse_published_date(date_str: str) -> datetime:
        """Parses the publication date from ISO format."""
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))


def setup_new_channel(channel_name: str, credentials_file: str = 'config/client_secrets.json') -> Dict:
    """
    Sets up a new personal channel (helper function).

    Args:
        channel_name: The name for the personal channel (e.g., "Technology").
        credentials_file: The path to client_secrets.json.

    Returns:
        A dictionary with channel information.
    """
    token_file = f'config/youtube_credentials/{channel_name.lower().replace(" ", "_")}_token.pickle'

    api = YouTubeAPI(credentials_file)

    print(f"\n=== Setting up channel: {channel_name} ===")
    print("A browser will open for authorization...")

    api.authenticate(token_file)

    channel_info = {
        'name': channel_name,
        'youtube_channel_id': api.get_channel_id(),
        'youtube_channel_title': api.get_channel_title(),
        'token_file': token_file
    }

    print(f"✓ Authorization successful!")
    print(f"  YouTube channel: {channel_info['youtube_channel_title']}")
    print(f"  Channel ID: {channel_info['youtube_channel_id']}")

    return channel_info