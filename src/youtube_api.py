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
    Класс для работы с YouTube Data API v3
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
        Авторизация через OAuth 2.0
        
        Args:
            token_file: Путь к файлу с сохранёнными токенами
            
        Returns:
            True если авторизация успешна
        """
        creds = None
        
        # Проверяем существующий токен
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Если токена нет или он невалиден
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Ошибка обновления токена: {e}")
                    creds = None
            
            # Запускаем flow авторизации
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Файл credentials не найден: {self.credentials_file}\n"
                        "Создайте проект в Google Cloud Console и скачайте credentials."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Сохраняем токен
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Создаём service объект
        self.service = build(self.API_SERVICE_NAME, self.API_VERSION, credentials=creds)
        
        # Получаем информацию о канале
        self.channel_info = self._get_my_channel_info()
        
        return True
    
    def _get_my_channel_info(self) -> Dict:
        """Получение информации о текущем канале"""
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
        """Получение ID текущего канала"""
        if self.channel_info:
            return self.channel_info['id']
        return None
    
    def get_channel_title(self) -> Optional[str]:
        """Получение названия текущего канала"""
        if self.channel_info:
            return self.channel_info['snippet']['title']
        return None
    
    def get_subscriptions(self, max_results: int = 50) -> List[Dict]:
        """
        Получение списка подписок
        
        Args:
            max_results: Максимальное количество результатов за запрос
            
        Returns:
            Список подписок с информацией о каналах
        """
        if not self.service:
            raise RuntimeError("Не авторизован. Вызовите authenticate() сначала.")
        
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
        Получение последних видео с канала
        
        Args:
            channel_id: ID канала YouTube
            max_results: Максимальное количество видео
            
        Returns:
            Список видео с метаданными
        """
        if not self.service:
            raise RuntimeError("Не авторизован. Вызовите authenticate() сначала.")
        
        # Получаем uploads playlist ID
        request = self.service.channels().list(
            part='contentDetails',
            id=channel_id
        )
        response = request.execute()
        
        if not response['items']:
            return []
        
        uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Получаем видео из uploads playlist
        request = self.service.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=max_results
        )
        response = request.execute()
        
        video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]
        
        if not video_ids:
            return []
        
        # Получаем детальную информацию о видео
        videos_request = self.service.videos().list(
            part='snippet,contentDetails,statistics',
            id=','.join(video_ids)
        )
        videos_response = videos_request.execute()
        
        videos = []
        for item in videos_response.get('items', []):
            try:
                # Парсим ISO 8601 duration
                duration_iso = item['contentDetails'].get('duration', 'PT0S')
                
                # Проверяем на livestream (duration отсутствует или PT0S)
                if not duration_iso or duration_iso == 'PT0S':
                    duration_formatted = "LIVE"
                else:
                    duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
                    if duration_seconds == 0:
                        duration_formatted = "LIVE"
                    else:
                        duration_formatted = self._format_duration(duration_seconds)
            except (KeyError, ValueError, AttributeError):
                # Livestream или другой формат
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
        Получение последних видео со всех подписок
        
        Args:
            hours: За сколько часов получать видео
            max_videos_per_channel: Максимум видео с каждого канала
            
        Returns:
            Список видео с метаданными и информацией о канале
        """
        subscriptions = self.get_subscriptions()
        all_videos = []
        
        for sub in subscriptions:
            videos = self.get_channel_videos(
                sub['channel_id'], 
                max_results=max_videos_per_channel
            )
            
            # Добавляем информацию о канале к каждому видео
            for video in videos:
                video['channel_id'] = sub['channel_id']
                video['channel_name'] = sub['channel_name']
                video['channel_thumbnail'] = sub['thumbnail']
                all_videos.append(video)
        
        # Сортируем по дате публикации
        all_videos.sort(key=lambda x: x['published_at'], reverse=True)
        
        return all_videos
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Форматирование длительности видео"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def parse_published_date(date_str: str) -> datetime:
        """Парсинг даты публикации из ISO формата"""
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))


def setup_new_channel(channel_name: str, credentials_file: str = 'config/client_secrets.json') -> Dict:
    """
    Настройка нового личного канала (helper функция)
    
    Args:
        channel_name: Название для личного канала (например, "Технологии")
        credentials_file: Путь к client_secrets.json
        
    Returns:
        Словарь с информацией о канале
    """
    token_file = f'config/youtube_credentials/{channel_name.lower().replace(" ", "_")}_token.pickle'
    
    api = YouTubeAPI(credentials_file)
    
    print(f"\n=== Настройка канала: {channel_name} ===")
    print("Откроется браузер для авторизации...")
    
    api.authenticate(token_file)
    
    channel_info = {
        'name': channel_name,
        'youtube_channel_id': api.get_channel_id(),
        'youtube_channel_title': api.get_channel_title(),
        'token_file': token_file
    }
    
    print(f"✓ Авторизация успешна!")
    print(f"  YouTube канал: {channel_info['youtube_channel_title']}")
    print(f"  Channel ID: {channel_info['youtube_channel_id']}")
    
    return channel_info