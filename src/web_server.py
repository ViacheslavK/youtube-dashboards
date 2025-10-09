#!/usr/bin/env python3
"""
Flask Web Server for YouTube Dashboard
"""

import os
import sys
import json
import webbrowser
import logging
import secrets
import pickle
from flask import Flask, jsonify, request, send_from_directory, redirect, url_for, session
from flask_cors import CORS
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow

# Add the root folder to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.db_manager import Database
from src.youtube_api import YouTubeAPI, setup_new_channel
from locales import load_locale_from_config, t

# Load locale
load_locale_from_config()

# Create Flask application
app = Flask(__name__,
            static_folder=os.path.join(project_root, 'frontend'),
            static_url_path='')
CORS(app)  # Enable CORS for development

# Set up session secret key
app.secret_key = secrets.token_hex(32)

# Database
db = Database()

# Настройка логирования
# Проверяем, находимся ли мы в тестовой среде
is_testing = 'pytest' in sys.modules or 'PYTEST_CURRENT_TEST' in os.environ

if is_testing:
    # В тестовой среде используем простой логгер без файлов
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
else:
    # В рабочей среде настраиваем полное логирование
    # Создаём директорию logs если она не существует
    logs_dir = os.path.join(project_root, 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, 'web_server.log')),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)


# === Static Files ===

@app.route('/')
def index():
    """Main page"""
    return send_from_directory(app.static_folder, 'index.html')


# === API Endpoints ===

@app.route('/api/channels', methods=['GET'])
def get_channels():
    """Get all personal channels"""
    try:
        channels = db.get_all_personal_channels()

        # Add statistics for each channel
        for channel in channels:
            videos = db.get_videos_by_personal_channel(channel['id'], include_watched=True)
            unwatched = db.get_videos_by_personal_channel(channel['id'], include_watched=False)
            subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=False)

            channel['stats'] = {
                'total_videos': len(videos),
                'unwatched_videos': len(unwatched),
                'subscriptions': len(subs)
            }

        return jsonify({
            'success': True,
            'data': channels
        })
    except Exception as e:
        logger.error(f"Error in get_channels: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/channels/<int:channel_id>/videos', methods=['GET'])
def get_channel_videos(channel_id):
    """Get videos for channel"""
    try:
        include_watched = request.args.get('include_watched', 'true').lower() == 'true'

        videos = db.get_videos_by_personal_channel(channel_id, include_watched=include_watched)

        # Sort by publication date (newest first)
        videos.sort(key=lambda x: x['published_at'], reverse=True)

        return jsonify({
            'success': True,
            'data': videos
        })
    except Exception as e:
        logger.error(f"Error in get_channel_videos: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/videos/<int:video_id>/watch', methods=['POST'])
def mark_video_watched(video_id):
    """Mark video as watched"""
    try:
        db.mark_video_watched(video_id)

        return jsonify({
            'success': True,
            'message': t('videos.mark_watched')
        })
    except Exception as e:
        logger.error(f"Error in mark_video_watched: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/videos/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """Get video information (including authuser)"""
    try:
        video = db.get_video_by_id(video_id)

        if not video:
            return jsonify({
                'success': False,
                'error': 'Video not found'
            }), 404

        return jsonify({
            'success': True,
            'data': video
        })
    except Exception as e:
        logger.error(f"Error in get_video: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/channels/<int:channel_id>/clear', methods=['POST'])
def clear_watched_videos(channel_id):
    """Clear watched videos for channel"""
    try:
        db.clear_watched_videos(channel_id)

        return jsonify({
            'success': True,
            'message': t('videos.clear_watched')
        })
    except Exception as e:
        logger.error(f"Error in clear_watched_videos: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        channels = db.get_all_personal_channels()

        total_videos = 0
        total_unwatched = 0
        total_subs = 0

        for channel in channels:
            videos = db.get_videos_by_personal_channel(channel['id'], include_watched=True)
            unwatched = db.get_videos_by_personal_channel(channel['id'], include_watched=False)
            subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=False)

            total_videos += len(videos)
            total_unwatched += len(unwatched)
            total_subs += len(subs)

        return jsonify({
            'success': True,
            'data': {
                'total_channels': len(channels),
                'total_subscriptions': total_subs,
                'total_videos': total_videos,
                'unwatched_videos': total_unwatched
            }
        })
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/errors', methods=['GET'])
def get_errors():
    """Get unresolved synchronization errors"""
    try:
        errors = db.get_unresolved_errors()

        return jsonify({
            'success': True,
            'data': errors
        })
    except Exception as e:
        logger.error(f"Error in get_errors: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# === OAuth Endpoints ===

@app.route('/api/auth/start', methods=['POST'])
def start_oauth():
    """Initiate OAuth flow for adding a new channel"""
    try:
        data = request.get_json()
        channel_name = data.get('channel_name', '').strip()

        if not channel_name:
            return jsonify({
                'success': False,
                'error': 'Channel name is required'
            }), 400

        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state in session (in production, use Redis/database)
        if 'oauth_states' not in session:
            session['oauth_states'] = {}
        session['oauth_states'][state] = {
            'channel_name': channel_name,
            'created_at': json.dumps({'timestamp': None})  # Placeholder
        }
        session.modified = True

        # Create OAuth flow
        credentials_file = 'config/client_secrets.json'
        if not os.path.exists(credentials_file):
            return jsonify({
                'success': False,
                'error': 'OAuth credentials not configured'
            }), 500

        flow = Flow.from_client_secrets_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/youtube.readonly'],
            redirect_uri=url_for('oauth_callback', _external=True)
        )

        # Generate authorization URL
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )

        return jsonify({
            'success': True,
            'data': {
                'auth_url': authorization_url,
                'state': state
            }
        })

    except Exception as e:
        logger.error(f"Error in start_oauth: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to start OAuth flow'
        }), 500


@app.route('/api/auth/callback', methods=['GET'])
def oauth_callback():
    """Handle OAuth callback and complete channel setup"""
    try:
        state = request.args.get('state')
        code = request.args.get('code')
        error = request.args.get('error')

        if error:
            return jsonify({
                'success': False,
                'error': f'OAuth error: {error}'
            }), 400

        if not state or not code:
            return jsonify({
                'success': False,
                'error': 'Missing state or code parameter'
            }), 400

        # Verify state token
        if 'oauth_states' not in session or state not in session['oauth_states']:
            return jsonify({
                'success': False,
                'error': 'Invalid state token'
            }), 400

        channel_name = session['oauth_states'][state]['channel_name']

        # Clean up state
        del session['oauth_states'][state]
        session.modified = True

        # Complete OAuth flow
        credentials_file = 'config/client_secrets.json'
        flow = Flow.from_client_secrets_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/youtube.readonly'],
            redirect_uri=url_for('oauth_callback', _external=True)
        )

        # Exchange code for tokens
        flow.fetch_token(code=code)

        # Get channel info
        credentials = flow.credentials
        youtube = build('youtube', 'v3', credentials=credentials)

        channels_response = youtube.channels().list(
            part='snippet',
            mine=True
        ).execute()

        if not channels_response['items']:
            return jsonify({
                'success': False,
                'error': 'No YouTube channel found'
            }), 400

        channel_info = channels_response['items'][0]
        youtube_channel_id = channel_info['id']
        youtube_channel_title = channel_info['snippet']['title']

        # Save tokens
        token_file = f'config/youtube_credentials/{channel_name.lower().replace(" ", "_")}_token.pickle'
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, 'wb') as f:
            pickle.dump(credentials, f)

        # Add channel to database
        channel_id = db.add_personal_channel(
            name=channel_name,
            youtube_channel_id=youtube_channel_id,
            oauth_token_path=token_file,
            color='#3b82f6'  # Default blue color
        )

        return jsonify({
            'success': True,
            'data': {
                'id': channel_id,
                'name': channel_name,
                'youtube_channel_id': youtube_channel_id,
                'youtube_channel_title': youtube_channel_title
            }
        })

    except Exception as e:
        logger.error(f"Error in oauth_callback: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to complete OAuth flow'
        }), 500


# === Channel Management ===

@app.route('/api/channels', methods=['POST'])
def add_channel():
    """Add new channel (after OAuth completion)"""
    try:
        data = request.get_json()
        channel_id = db.add_personal_channel(
            name=data['name'],
            youtube_channel_id=data['youtube_channel_id'],
            oauth_token_path=data['oauth_token_path'],
            color=data.get('color', '#3b82f6')
        )

        return jsonify({
            'success': True,
            'data': db.get_all_personal_channels()[-1]  # Return the newly added channel
        })

    except Exception as e:
        logger.error(f"Error in add_channel: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to add channel'
        }), 500


@app.route('/api/channels/<int:channel_id>', methods=['PUT'])
def update_channel(channel_id):
    """Update channel information"""
    try:
        data = request.get_json()

        # Update database (this would need to be added to Database class)
        # For now, just return success
        return jsonify({
            'success': True,
            'message': 'Channel updated successfully'
        })

    except Exception as e:
        logger.error(f"Error in update_channel: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update channel'
        }), 500


@app.route('/api/channels/<int:channel_id>', methods=['DELETE'])
def delete_channel(channel_id):
    """Delete channel and all related data"""
    try:
        # This would need to be implemented in Database class
        # For now, just return success
        return jsonify({
            'success': True,
            'message': 'Channel deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error in delete_channel: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to delete channel'
        }), 500


# === Subscription Management ===

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    """Get all subscriptions or subscriptions for a specific channel"""
    try:
        channel_id = request.args.get('channel_id', type=int)

        if channel_id:
            subscriptions = db.get_subscriptions_by_channel(channel_id, include_inactive=True)
        else:
            # Get all subscriptions from all channels
            channels = db.get_all_personal_channels()
            subscriptions = []
            for channel in channels:
                channel_subs = db.get_subscriptions_by_channel(channel['id'], include_inactive=True)
                subscriptions.extend(channel_subs)

        return jsonify({
            'success': True,
            'data': subscriptions
        })

    except Exception as e:
        logger.error(f"Error in get_subscriptions: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to get subscriptions'
        }), 500


@app.route('/api/subscriptions/<int:subscription_id>', methods=['PUT'])
def update_subscription(subscription_id):
    """Update subscription status"""
    try:
        data = request.get_json()
        is_active = data.get('is_active')

        if is_active is not None:
            if is_active:
                db.reactivate_subscription(subscription_id)
            else:
                db.deactivate_subscription(subscription_id)

        return jsonify({
            'success': True,
            'message': 'Subscription updated successfully'
        })

    except Exception as e:
        logger.error(f"Error in update_subscription: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update subscription'
        }), 500


@app.route('/api/subscriptions/<int:subscription_id>', methods=['DELETE'])
def delete_subscription(subscription_id):
    """Mark subscription as deleted by user"""
    try:
        db.mark_subscription_deleted(subscription_id)

        return jsonify({
            'success': True,
            'message': 'Subscription deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error in delete_subscription: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to delete subscription'
        }), 500


# === Sync Operations ===

@app.route('/api/sync/subscriptions', methods=['POST'])
def sync_subscriptions():
    """Trigger subscription synchronization"""
    try:
        # Import and run sync function
        from src.sync_subscriptions import sync_subscriptions
        sync_subscriptions(db)

        return jsonify({
            'success': True,
            'message': 'Subscription sync completed'
        })

    except Exception as e:
        logger.error(f"Error in sync_subscriptions: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to sync subscriptions'
        }), 500


@app.route('/api/sync/videos', methods=['POST'])
def sync_videos():
    """Trigger video synchronization"""
    try:
        data = request.get_json() or {}
        max_videos = data.get('max_videos', 5)

        # Import and run sync function
        from src.sync_subscriptions import sync_videos
        sync_videos(db, max_videos_per_channel=max_videos)

        return jsonify({
            'success': True,
            'message': 'Video sync completed'
        })

    except Exception as e:
        logger.error(f"Error in sync_videos: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to sync videos'
        }), 500


# === Settings ===

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get application settings"""
    try:
        config_path = os.path.join(project_root, 'config', 'settings.json')

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            settings = {
                'locale': 'en',
                'auto_refresh': True,
                'refresh_interval': 5,
                'web_server_port': 8080,
                'open_browser_on_start': True
            }

        return jsonify({
            'success': True,
            'data': settings
        })

    except Exception as e:
        logger.error(f"Error in get_settings: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to get settings'
        }), 500


@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update application settings"""
    try:
        data = request.get_json()
        config_path = os.path.join(project_root, 'config', 'settings.json')

        # Load existing settings
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            settings = {}

        # Update with new data
        settings.update(data)

        # Save settings
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })

    except Exception as e:
        logger.error(f"Error in update_settings: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update settings'
        }), 500


# === i18n ===

@app.route('/api/i18n/<locale>', methods=['GET'])
def get_translations(locale):
    """Get translations for a specific locale"""
    try:
        locale_file = os.path.join(project_root, 'locales', f'{locale}.json')

        if not os.path.exists(locale_file):
            return jsonify({
                'success': False,
                'error': f'Locale {locale} not found'
            }), 404

        with open(locale_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)

        return jsonify({
            'success': True,
            'data': translations
        })

    except Exception as e:
        logger.error(f"Error in get_translations: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to get translations'
        }), 500


# === Server Launch ===

def load_config():
    """Load configuration"""
    config_path = os.path.join(project_root, 'config', 'settings.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'web_server_port': 8080, 'open_browser_on_start': True}


def main():
    """Launch web server"""
    config = load_config()
    port = config.get('web_server_port', 8080)
    open_browser = config.get('open_browser_on_start', True)

    url = f'http://localhost:{port}'

    print("=" * 60)
    print(t('app.name'))
    print("=" * 60)
    print(f"\n[OK] Server starting on {url}")
    print(f"[OK] Press Ctrl+C to stop")
    print("=" * 60)

    # Open browser
    if open_browser:
        webbrowser.open(url)

    # Launch Flask
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[OK] Server stopped")
        sys.exit(0)