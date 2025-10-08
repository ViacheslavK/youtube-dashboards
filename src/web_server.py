#!/usr/bin/env python3
"""
Flask Web Server for YouTube Dashboard
"""

import os
import sys
import json
import webbrowser
import logging
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Add the root folder to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.db_manager import Database
from locales import load_locale_from_config, t

# Load locale
load_locale_from_config()

# Create Flask application
app = Flask(__name__, 
            static_folder=os.path.join(project_root, 'frontend'),
            static_url_path='')
CORS(app)  # Enable CORS for development

# Database
db = Database()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, 'logs', 'web_server.log')),
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