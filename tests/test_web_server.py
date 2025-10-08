"""
Unit tests for Web Server
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


@pytest.mark.unit
class TestStaticRoutes:
    """Tests for static file serving"""

    @patch('src.web_server.send_from_directory')
    @patch('src.web_server.app')
    def test_index_route_serves_frontend(self, mock_app, mock_send_from_directory):
        """Test that index route serves frontend/index.html"""
        from src.web_server import index

        # Mock the static folder and send_from_directory
        mock_app.static_folder = '/path/to/frontend'
        mock_send_from_directory.return_value = 'index.html content'

        # Call the function
        result = index()

        # Verify send_from_directory was called with correct parameters
        mock_send_from_directory.assert_called_once_with('/path/to/frontend', 'index.html')
        assert result == 'index.html content'


@pytest.mark.unit
class TestAPIEndpoints:
    """Tests for API endpoints"""

    def test_get_channels_success(self):
        """Test successful channels retrieval"""
        from src.web_server import app, db

        # Mock database responses
        mock_channels = [
            {'id': 1, 'name': 'Channel 1'},
            {'id': 2, 'name': 'Channel 2'}
        ]

        mock_videos = [
            {'id': 1, 'title': 'Video 1', 'published_at': '2025-01-01T00:00:00Z'},
            {'id': 2, 'title': 'Video 2', 'published_at': '2025-01-02T00:00:00Z'}
        ]

        mock_unwatched = [
            {'id': 1, 'title': 'Video 1', 'published_at': '2025-01-01T00:00:00Z'}
        ]

        mock_subs = [
            {'id': 1, 'channel_name': 'Sub 1'}
        ]

        with patch.object(db, 'get_all_personal_channels', return_value=mock_channels), \
             patch.object(db, 'get_videos_by_personal_channel') as mock_get_videos, \
             patch.object(db, 'get_subscriptions_by_channel', return_value=mock_subs):

            # Configure mocks for each channel
            mock_get_videos.side_effect = [
                mock_videos,  # videos for channel 1 (include_watched=True)
                mock_unwatched,  # unwatched for channel 1 (include_watched=False)
                mock_videos,  # videos for channel 2 (include_watched=True)
                mock_unwatched  # unwatched for channel 2 (include_watched=False)
            ]

            with app.test_client() as client:
                response = client.get('/api/channels')

                assert response.status_code == 200
                data = json.loads(response.data)

                assert data['success'] is True
                assert len(data['data']) == 2

                # Check that stats were added correctly
                assert 'stats' in data['data'][0]
                assert data['data'][0]['stats']['total_videos'] == 2
                assert data['data'][0]['stats']['unwatched_videos'] == 1
                assert data['data'][0]['stats']['subscriptions'] == 1

    def test_get_channels_database_error(self):
        """Test channels endpoint handles database errors"""
        from src.web_server import app, db

        with patch.object(db, 'get_all_personal_channels', side_effect=Exception('DB Error')):
            with app.test_client() as client:
                response = client.get('/api/channels')

                assert response.status_code == 500
                data = json.loads(response.data)

                assert data['success'] is False
                assert data['error'] == 'Internal server error'

    def test_get_channel_videos_success(self):
        """Test successful channel videos retrieval"""
        from src.web_server import app, db

        mock_videos = [
            {'id': 1, 'title': 'Video 1', 'published_at': '2025-01-02T00:00:00Z'},
            {'id': 2, 'title': 'Video 2', 'published_at': '2025-01-01T00:00:00Z'}
        ]

        with patch.object(db, 'get_videos_by_personal_channel', return_value=mock_videos):
            with app.test_client() as client:
                response = client.get('/api/channels/1/videos')

                assert response.status_code == 200
                data = json.loads(response.data)

                assert data['success'] is True
                assert len(data['data']) == 2

                # Check that videos are sorted by published_at (newest first)
                assert data['data'][0]['published_at'] == '2025-01-02T00:00:00Z'
                assert data['data'][1]['published_at'] == '2025-01-01T00:00:00Z'

    def test_get_channel_videos_include_watched_parameter(self):
        """Test channel videos with include_watched parameter"""
        from src.web_server import app, db

        mock_videos = [{'id': 1, 'title': 'Video 1'}]

        with patch.object(db, 'get_videos_by_personal_channel') as mock_get_videos:
            mock_get_videos.return_value = mock_videos

            with app.test_client() as client:
                # Test include_watched=true
                client.get('/api/channels/1/videos?include_watched=true')
                mock_get_videos.assert_called_with(1, include_watched=True)

                # Test include_watched=false
                client.get('/api/channels/1/videos?include_watched=false')
                mock_get_videos.assert_called_with(1, include_watched=False)

                # Test default (should be true)
                client.get('/api/channels/1/videos')
                mock_get_videos.assert_called_with(1, include_watched=True)

    def test_mark_video_watched_success(self):
        """Test successful video marking as watched"""
        from src.web_server import app, db

        with patch.object(db, 'mark_video_watched') as mock_mark_watched:
            with app.test_client() as client:
                response = client.post('/api/videos/1/watch')

                assert response.status_code == 200
                data = json.loads(response.data)

                assert data['success'] is True
                assert 'message' in data

                # Verify database was called
                mock_mark_watched.assert_called_once_with(1)

    def test_mark_video_watched_database_error(self):
        """Test video marking handles database errors"""
        from src.web_server import app, db

        with patch.object(db, 'mark_video_watched', side_effect=Exception('DB Error')):
            with app.test_client() as client:
                response = client.post('/api/videos/1/watch')

                assert response.status_code == 500
                data = json.loads(response.data)

                assert data['success'] is False
                assert data['error'] == 'Internal server error'

    def test_get_video_success(self):
        """Test successful video retrieval"""
        from src.web_server import app, db

        mock_video = {
            'id': 1,
            'title': 'Test Video',
            'youtube_video_id': 'test_123'
        }

        with patch.object(db, 'get_video_by_id', return_value=mock_video):
            with app.test_client() as client:
                response = client.get('/api/videos/1')

                assert response.status_code == 200
                data = json.loads(response.data)

                assert data['success'] is True
                assert data['data']['title'] == 'Test Video'

    def test_get_video_not_found(self):
        """Test video retrieval when video doesn't exist"""
        from src.web_server import app, db

        with patch.object(db, 'get_video_by_id', return_value=None):
            with app.test_client() as client:
                response = client.get('/api/videos/999')

                assert response.status_code == 404
                data = json.loads(response.data)

                assert data['success'] is False
                assert data['error'] == 'Video not found'

    def test_clear_watched_videos_success(self):
        """Test successful clearing of watched videos"""
        from src.web_server import app, db

        with patch.object(db, 'clear_watched_videos') as mock_clear:
            with app.test_client() as client:
                response = client.post('/api/channels/1/clear')

                assert response.status_code == 200
                data = json.loads(response.data)

                assert data['success'] is True
                assert 'message' in data

                # Verify database was called
                mock_clear.assert_called_once_with(1)

    def test_get_stats_success(self):
        """Test successful statistics retrieval"""
        from src.web_server import app, db

        mock_channels = [
            {'id': 1, 'name': 'Channel 1'},
            {'id': 2, 'name': 'Channel 2'}
        ]

        mock_videos = [
            {'id': 1, 'title': 'Video 1'},
            {'id': 2, 'title': 'Video 2'}
        ]

        mock_unwatched = [
            {'id': 1, 'title': 'Video 1'}
        ]

        mock_subs = [
            {'id': 1, 'channel_name': 'Sub 1'}
        ]

        with patch.object(db, 'get_all_personal_channels', return_value=mock_channels), \
             patch.object(db, 'get_videos_by_personal_channel') as mock_get_videos, \
             patch.object(db, 'get_subscriptions_by_channel', return_value=mock_subs):

            # Configure mocks for each channel
            mock_get_videos.side_effect = [
                mock_videos,  # videos for channel 1 (include_watched=True)
                mock_unwatched,  # unwatched for channel 1 (include_watched=False)
                mock_videos,  # videos for channel 2 (include_watched=True)
                mock_unwatched  # unwatched for channel 2 (include_watched=False)
            ]

            with app.test_client() as client:
                response = client.get('/api/stats')

                assert response.status_code == 200
                data = json.loads(response.data)

                assert data['success'] is True
                assert 'data' in data

                stats = data['data']
                assert stats['total_channels'] == 2
                assert stats['total_videos'] == 4  # 2 videos per channel
                assert stats['unwatched_videos'] == 2  # 1 unwatched per channel
                assert stats['total_subscriptions'] == 2  # 1 subscription per channel

    def test_get_errors_success(self):
        """Test successful errors retrieval"""
        from src.web_server import app, db

        mock_errors = [
            {
                'id': 1,
                'error_type': 'SYNC_ERROR',
                'error_message': 'Test error',
                'resolved': False
            }
        ]

        with patch.object(db, 'get_unresolved_errors', return_value=mock_errors):
            with app.test_client() as client:
                response = client.get('/api/errors')

                assert response.status_code == 200
                data = json.loads(response.data)

                assert data['success'] is True
                assert len(data['data']) == 1
                assert data['data'][0]['error_type'] == 'SYNC_ERROR'


@pytest.mark.unit
class TestConfiguration:
    """Tests for configuration loading"""

    def test_load_config_file_exists(self):
        """Test loading config when file exists"""
        from src.web_server import load_config

        config_data = {
            'web_server_port': 9000,
            'open_browser_on_start': False
        }

        with patch('src.web_server.project_root', '/test/path'), \
             patch('builtins.open', create=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(config_data)

            result = load_config()

            assert result['web_server_port'] == 9000
            assert result['open_browser_on_start'] is False

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist"""
        from src.web_server import load_config

        with patch('src.web_server.project_root', '/test/path'), \
             patch('builtins.open', side_effect=FileNotFoundError()):
            result = load_config()

            assert result['web_server_port'] == 8080
            assert result['open_browser_on_start'] is True


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling and logging"""

    @patch('src.web_server.logger')
    def test_database_error_logging(self, mock_logger):
        """Test that database errors are properly logged"""
        from src.web_server import app, db

        with patch.object(db, 'get_all_personal_channels', side_effect=Exception('Test DB Error')):
            with app.test_client() as client:
                client.get('/api/channels')

                # Verify error was logged
                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args[0]
                assert 'Error in get_channels: Test DB Error' in call_args[0]
                # Check that exc_info was passed as keyword argument
                assert 'exc_info' in mock_logger.error.call_args[1]
                assert mock_logger.error.call_args[1]['exc_info'] is True

    @patch('src.web_server.logger')
    def test_all_endpoints_log_errors(self, mock_logger):
        """Test that all endpoints properly log errors"""
        from src.web_server import app, db

        # Test each endpoint individually with proper mocking
        test_cases = [
            ('GET', '/api/channels', 'get_all_personal_channels'),
            ('GET', '/api/channels/1/videos', 'get_videos_by_personal_channel'),
            ('POST', '/api/videos/1/watch', 'mark_video_watched'),
            ('GET', '/api/videos/1', 'get_video_by_id'),
            ('POST', '/api/channels/1/clear', 'clear_watched_videos'),
            ('GET', '/api/stats', 'get_all_personal_channels'),
            ('GET', '/api/errors', 'get_unresolved_errors')
        ]

        for method, endpoint, db_method in test_cases:
            mock_logger.reset_mock()

            with patch.object(db, db_method, side_effect=Exception(f'Error for {endpoint}')):
                with app.test_client() as client:
                    if method == 'GET':
                        client.get(endpoint)
                    else:
                        client.post(endpoint)

                    # Verify each endpoint logs errors
                    mock_logger.error.assert_called_once()
                    call_args = mock_logger.error.call_args[0]
                    assert 'Error in' in call_args[0]


@pytest.mark.unit
class TestMainFunction:
    """Tests for main server function"""

    @patch('src.web_server.webbrowser.open')
    @patch('src.web_server.app.run')
    @patch('src.web_server.load_config')
    @patch('src.web_server.print')
    @patch('builtins.open', create=True)
    def test_main_function_with_browser(self, mock_file, mock_print, mock_load_config, mock_app_run, mock_webbrowser):
        """Test main function opens browser when configured"""
        from src.web_server import main

        mock_load_config.return_value = {
            'web_server_port': 9000,
            'open_browser_on_start': True
        }

        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps({})

        # Mock KeyboardInterrupt to exit cleanly
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            main()

            # Verify browser was opened
            mock_webbrowser.assert_called_once_with('http://localhost:9000')

            # Verify app.run was called with correct parameters
            mock_app_run.assert_called_once_with(
                host='0.0.0.0',
                port=9000,
                debug=False,
                threaded=True
            )

    @patch('src.web_server.webbrowser.open')
    @patch('src.web_server.app.run')
    @patch('src.web_server.load_config')
    @patch('src.web_server.print')
    def test_main_function_without_browser(self, mock_print, mock_load_config, mock_app_run, mock_webbrowser):
        """Test main function doesn't open browser when disabled"""
        from src.web_server import main

        mock_load_config.return_value = {
            'web_server_port': 8080,
            'open_browser_on_start': False
        }

        # Mock KeyboardInterrupt to exit cleanly
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            main()

            # Verify browser was NOT opened
            mock_webbrowser.assert_not_called()

            # Verify app.run was called with correct parameters
            mock_app_run.assert_called_once_with(
                host='0.0.0.0',
                port=8080,
                debug=False,
                threaded=True
            )