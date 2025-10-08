#!/usr/bin/env python3
"""
Flask Web Server для YouTube Dashboard
"""

import os
import sys
import json
import webbrowser
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Добавляем корневую папку в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.db_manager import Database
from locales import load_locale_from_config, t

# Загружаем локаль
load_locale_from_config()

# Создаём Flask приложение
app = Flask(__name__, 
            static_folder=os.path.join(project_root, 'frontend'),
            static_url_path='')
CORS(app)  # Разрешаем CORS для разработки

# База данных
db = Database()


# === Статические файлы ===

@app.route('/')
def index():
    """Главная страница"""
    return send_from_directory(app.static_folder, 'index.html')


# === API Endpoints ===

@app.route('/api/channels', methods=['GET'])
def get_channels():
    """Получить все личные каналы"""
    try:
        channels = db.get_all_personal_channels()
        
        # Добавляем статистику для каждого канала
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/channels/<int:channel_id>/videos', methods=['GET'])
def get_channel_videos(channel_id):
    """Получить видео для канала"""
    try:
        include_watched = request.args.get('include_watched', 'true').lower() == 'true'
        
        videos = db.get_videos_by_personal_channel(channel_id, include_watched=include_watched)
        
        # Сортируем по дате публикации (новые первыми)
        videos.sort(key=lambda x: x['published_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': videos
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/videos/<int:video_id>/watch', methods=['POST'])
def mark_video_watched(video_id):
    """Отметить видео как просмотренное"""
    try:
        db.mark_video_watched(video_id)
        
        return jsonify({
            'success': True,
            'message': t('videos.mark_watched')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/videos/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """Получить информацию о видео (включая authuser)"""
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/channels/<int:channel_id>/clear', methods=['POST'])
def clear_watched_videos(channel_id):
    """Очистить просмотренные видео для канала"""
    try:
        db.clear_watched_videos(channel_id)
        
        return jsonify({
            'success': True,
            'message': t('videos.clear_watched')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Получить общую статистику"""
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/errors', methods=['GET'])
def get_errors():
    """Получить нерешённые ошибки синхронизации"""
    try:
        errors = db.get_unresolved_errors()
        
        return jsonify({
            'success': True,
            'data': errors
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# === Запуск сервера ===

def load_config():
    """Загрузить конфигурацию"""
    config_path = os.path.join(project_root, 'config', 'settings.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'web_server_port': 8080, 'open_browser_on_start': True}


def main():
    """Запуск веб-сервера"""
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
    
    # Открываем браузер
    if open_browser:
        webbrowser.open(url)
    
    # Запускаем Flask
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