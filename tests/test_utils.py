"""
Tests for utilities (utils/)
"""

import pytest
from io import StringIO
import sys


@pytest.mark.unit
class TestViewStats:
    """Tests for utils/view_stats.py"""
    
    def test_view_channels_stats_empty(self, db, capsys):
        """Test statistics with empty DB"""
        # Import function
        # (in real tests it's better to refactor utils for testability)
        channels = db.get_all_personal_channels()
        assert len(channels) == 0
    
    def test_view_channels_stats_with_data(self, populated_db):
        """Test statistics with data"""
        db = populated_db['db']
        
        channels = db.get_all_personal_channels()
        assert len(channels) == 1
        
        videos = db.get_videos_by_personal_channel(channels[0]['id'])
        assert len(videos) == 1


@pytest.mark.unit
class TestManageSubscriptions:
    """Tests for utils/manage_subscriptions.py"""
    
    def test_view_inactive_subscriptions_none(self, populated_db):
        """Test: no inactive subscriptions"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        # All subscriptions are active
        all_subs = db.get_subscriptions_by_channel(channel_id, include_inactive=True)
        inactive = [s for s in all_subs if not s['is_active']]
        
        assert len(inactive) == 0
    
    def test_view_inactive_subscriptions_with_inactive(self, populated_db):
        """Test: there are inactive subscriptions"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        subscription_id = populated_db['subscription_id']
        
        # Deactivate subscription
        db.deactivate_subscription(subscription_id)
        
        # Check
        all_subs = db.get_subscriptions_by_channel(channel_id, include_inactive=True)
        inactive = [s for s in all_subs if not s['is_active']]
        
        assert len(inactive) == 1
        assert inactive[0]['channel_name'] == 'Test Subscription Channel'
    
    def test_delete_inactive_subscription(self, populated_db):
        """Test deleting inactive subscription from history"""
        db = populated_db['db']
        subscription_id = populated_db['subscription_id']
        
        # Deactivate
        db.deactivate_subscription(subscription_id)
        
        # Delete from history
        db.mark_subscription_deleted(subscription_id)
        
        # Check
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT deleted_by_user FROM subscriptions WHERE id = ?', (subscription_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result['deleted_by_user'] == 1


@pytest.mark.unit
class TestViewErrors:
    """Tests for utils/view_errors.py"""
    
    def test_view_errors_empty(self, db):
        """Test: no errors"""
        errors = db.get_unresolved_errors()
        assert len(errors) == 0
    
    def test_view_errors_with_data(self, populated_db):
        """Test: there are errors"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        # Log error
        db.log_sync_error(
            personal_channel_id=channel_id,
            subscription_id=None,
            channel_name='Test Channel',
            error_type='TEST_ERROR',
            error_message='Test error message'
        )
        
        errors = db.get_unresolved_errors()
        
        assert len(errors) == 1
        assert errors[0]['error_type'] == 'TEST_ERROR'
    
    def test_view_errors_by_channel(self, populated_db):
        """Test getting errors for specific channel"""
        db = populated_db['db']
        channel_id = populated_db['channel_id']
        
        # Add second channel
        channel2_id = db.add_personal_channel(
            name='Channel 2',
            youtube_channel_id='UC_2',
            oauth_token_path='token2.pickle'
        )
        
        # Log errors for different channels
        db.log_sync_error(channel_id, None, 'Ch1', 'ERROR1', 'Msg1')
        db.log_sync_error(channel2_id, None, 'Ch2', 'ERROR2', 'Msg2')
        
        # Get only for first channel
        errors_ch1 = db.get_unresolved_errors(channel_id)
        
        assert len(errors_ch1) == 1
        assert errors_ch1[0]['error_type'] == 'ERROR1'


@pytest.mark.integration
class TestUtilsIntegration:
    """Utilities integration tests"""
    
    def test_full_subscription_management_workflow(self, db):
        """Test full subscription management workflow"""
        # 1. Create channel
        channel_id = db.add_personal_channel(
            name='Test',
            youtube_channel_id='UC_test',
            oauth_token_path='token.pickle'
        )
        
        # 2. Add subscriptions
        sub1_id = db.add_subscription(channel_id, 'UC_sub1', 'Sub 1', 'thumb1.jpg')
        sub2_id = db.add_subscription(channel_id, 'UC_sub2', 'Sub 2', 'thumb2.jpg')
        
        # 3. Sync statuses (first subscription disappeared)
        stats = db.sync_subscriptions_status(channel_id, ['UC_sub2'])
        
        assert stats['deactivated'] == 1
        assert stats['unchanged'] == 1
        
        # 4. View inactive
        all_subs = db.get_subscriptions_by_channel(channel_id, include_inactive=True)
        inactive = [s for s in all_subs if not s['is_active']]
        
        assert len(inactive) == 1
        assert inactive[0]['youtube_channel_id'] == 'UC_sub1'
        
        # 5. Delete from history
        db.mark_subscription_deleted(sub1_id)
        
        # 6. Check
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT deleted_by_user FROM subscriptions WHERE id = ?', (sub1_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result['deleted_by_user'] == 1