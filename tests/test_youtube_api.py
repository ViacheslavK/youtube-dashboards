"""
Tests for YouTube API (with mocks)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.youtube_api import YouTubeAPI


@pytest.fixture
def mock_credentials():
    """Mock for credentials"""
    creds = Mock()
    creds.valid = True
    creds.expired = False
    return creds


@pytest.fixture
def youtube_api():
    """Creates YouTube API instance without real authentication"""
    api = YouTubeAPI('fake_credentials.json')
    api.service = Mock()  # Mock the service
    return api


@pytest.mark.api
class TestYouTubeAPIBasics:
    """Basic YouTube API tests"""
    
    @patch('src.youtube_api.build')
    @patch('src.youtube_api.pickle')
    @patch('os.path.exists')
    def test_authenticate_with_existing_token(self, mock_exists, mock_pickle, mock_build):
        """Test authentication with existing token"""
        # Set up mocks
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle.load.return_value = mock_creds
        
        api = YouTubeAPI('fake_credentials.json')
        
        with patch('builtins.open', create=True):
            result = api.authenticate('fake_token.pickle')
        
        assert result is True
        mock_build.assert_called_once()
    
    def test_get_channel_id(self, youtube_api):
        """Test getting channel ID"""
        youtube_api.channel_info = {'id': 'UC_test_123'}
        
        channel_id = youtube_api.get_channel_id()
        
        assert channel_id == 'UC_test_123'
    
    def test_get_channel_title(self, youtube_api):
        """Test getting channel title"""
        youtube_api.channel_info = {
            'snippet': {'title': 'Test Channel'}
        }
        
        title = youtube_api.get_channel_title()
        
        assert title == 'Test Channel'


@pytest.mark.api
class TestGetSubscriptions:
    """Subscription retrieval tests"""
    
    def test_get_subscriptions(self, youtube_api):
        """Test getting subscription list"""
        # Mock API response
        mock_response = {
            'items': [
                {
                    'snippet': {
                        'resourceId': {'channelId': 'UC_sub1'},
                        'title': 'Subscription 1',
                        'thumbnails': {'default': {'url': 'thumb1.jpg'}},
                        'description': 'Description 1'
                    }
                },
                {
                    'snippet': {
                        'resourceId': {'channelId': 'UC_sub2'},
                        'title': 'Subscription 2',
                        'thumbnails': {'default': {'url': 'thumb2.jpg'}},
                        'description': 'Description 2'
                    }
                }
            ]
        }
        
        # Set up mock
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        youtube_api.service.subscriptions().list.return_value = mock_request
        
        subscriptions = youtube_api.get_subscriptions(max_results=50)
        
        assert len(subscriptions) == 2
        assert subscriptions[0]['channel_id'] == 'UC_sub1'
        assert subscriptions[0]['channel_name'] == 'Subscription 1'
        assert subscriptions[1]['channel_id'] == 'UC_sub2'
    
    def test_get_subscriptions_pagination(self, youtube_api):
        """Test pagination when getting subscriptions"""
        # First page
        mock_response_page1 = {
            'items': [
                {
                    'snippet': {
                        'resourceId': {'channelId': 'UC_sub1'},
                        'title': 'Sub 1',
                        'thumbnails': {'default': {'url': 'thumb1.jpg'}},
                        'description': 'Desc 1'
                    }
                }
            ],
            'nextPageToken': 'token_page2'
        }
        
        # Second page
        mock_response_page2 = {
            'items': [
                {
                    'snippet': {
                        'resourceId': {'channelId': 'UC_sub2'},
                        'title': 'Sub 2',
                        'thumbnails': {'default': {'url': 'thumb2.jpg'}},
                        'description': 'Desc 2'
                    }
                }
            ]
        }
        
        # Set up mocks for pagination
        mock_request1 = Mock()
        mock_request1.execute.return_value = mock_response_page1
        
        mock_request2 = Mock()
        mock_request2.execute.return_value = mock_response_page2
        
        youtube_api.service.subscriptions().list.side_effect = [mock_request1, mock_request2]
        
        subscriptions = youtube_api.get_subscriptions()
        
        assert len(subscriptions) == 2


@pytest.mark.api
class TestGetChannelVideos:
    """Tests for getting videos from channel"""
    
    def test_get_channel_videos(self, youtube_api):
        """Test getting videos from channel"""
        # Mock for getting uploads playlist ID
        mock_channel_response = {
            'items': [{
                'contentDetails': {
                    'relatedPlaylists': {'uploads': 'UU_uploads_123'}
                }
            }]
        }
        
        # Mock for getting videos from playlist
        mock_playlist_response = {
            'items': [{
                'contentDetails': {'videoId': 'video_123'}
            }]
        }
        
        # Mock for getting video details
        mock_videos_response = {
            'items': [{
                'id': 'video_123',
                'snippet': {
                    'title': 'Test Video',
                    'description': 'Test Description',
                    'thumbnails': {'medium': {'url': 'thumb.jpg'}},
                    'publishedAt': '2025-01-15T10:00:00Z'
                },
                'contentDetails': {
                    'duration': 'PT10M30S'
                },
                'statistics': {
                    'viewCount': '1000'
                }
            }]
        }
        
        # Set up mocks
        mock_channel_request = Mock()
        mock_channel_request.execute.return_value = mock_channel_response
        
        mock_playlist_request = Mock()
        mock_playlist_request.execute.return_value = mock_playlist_response
        
        mock_videos_request = Mock()
        mock_videos_request.execute.return_value = mock_videos_response
        
        youtube_api.service.channels().list.return_value = mock_channel_request
        youtube_api.service.playlistItems().list.return_value = mock_playlist_request
        youtube_api.service.videos().list.return_value = mock_videos_request
        
        videos = youtube_api.get_channel_videos('UC_test', max_results=10)
        
        assert len(videos) == 1
        assert videos[0]['video_id'] == 'video_123'
        assert videos[0]['title'] == 'Test Video'
        assert videos[0]['duration'] == '10:30'
        assert videos[0]['view_count'] == 1000
    
    def test_get_channel_videos_with_livestream(self, youtube_api):
        """Test processing livestream (without duration)"""
        mock_channel_response = {
            'items': [{
                'contentDetails': {
                    'relatedPlaylists': {'uploads': 'UU_uploads_123'}
                }
            }]
        }
        
        mock_playlist_response = {
            'items': [{
                'contentDetails': {'videoId': 'livestream_123'}
            }]
        }
        
        # Livestream without duration
        mock_videos_response = {
            'items': [{
                'id': 'livestream_123',
                'snippet': {
                    'title': 'Livestream',
                    'thumbnails': {'medium': {'url': 'thumb.jpg'}},
                    'publishedAt': '2025-01-15T10:00:00Z'
                },
                'contentDetails': {},  # No duration
                'statistics': {}
            }]
        }
        
        mock_channel_request = Mock()
        mock_channel_request.execute.return_value = mock_channel_response
        
        mock_playlist_request = Mock()
        mock_playlist_request.execute.return_value = mock_playlist_response
        
        mock_videos_request = Mock()
        mock_videos_request.execute.return_value = mock_videos_response
        
        youtube_api.service.channels().list.return_value = mock_channel_request
        youtube_api.service.playlistItems().list.return_value = mock_playlist_request
        youtube_api.service.videos().list.return_value = mock_videos_request
        
        videos = youtube_api.get_channel_videos('UC_test')
        
        assert len(videos) == 1
        assert videos[0]['duration'] == 'LIVE'


@pytest.mark.api
class TestHelperMethods:
    """Tests for helper methods"""
    
    def test_format_duration_hours(self):
        """Test formatting duration with hours"""
        duration = YouTubeAPI._format_duration(3661)  # 1:01:01
        assert duration == '1:01:01'
    
    def test_format_duration_minutes(self):
        """Test formatting duration without hours"""
        duration = YouTubeAPI._format_duration(630)  # 10:30
        assert duration == '10:30'
    
    def test_format_duration_seconds(self):
        """Test formatting short videos"""
        duration = YouTubeAPI._format_duration(45)  # 0:45
        assert duration == '0:45'
    
    def test_parse_published_date(self):
        """Test parsing publication date"""
        date_str = '2025-01-15T10:30:00Z'
        parsed = YouTubeAPI.parse_published_date(date_str)
        
        assert parsed.year == 2025
        assert parsed.month == 1
        assert parsed.day == 15
        assert parsed.hour == 10
        assert parsed.minute == 30