"""Tests for database layer."""

import pytest
import tempfile
from pathlib import Path

from src.second_brain.database import Database


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    db = Database(db_path=db_path)
    yield db
    
    db.close()
    db_path.unlink(missing_ok=True)


def test_database_initialization(temp_db):
    """Test database initializes with schema."""
    stats = temp_db.get_database_stats()
    
    assert stats["frame_count"] == 0
    assert stats["text_block_count"] == 0
    assert stats["window_count"] == 0


def test_insert_frame(temp_db):
    """Test inserting a frame."""
    frame_data = {
        "frame_id": "test-frame-1",
        "timestamp": 1234567890,
        "window_title": "Test Window",
        "app_bundle_id": "com.test.app",
        "app_name": "Test App",
        "file_path": "2025/10/26/test.png",
        "file_size_bytes": 1024000,
        "screen_resolution": "1920x1080",
    }
    
    frame_id = temp_db.insert_frame(frame_data)
    assert frame_id == "test-frame-1"
    
    # Verify frame was inserted
    frame = temp_db.get_frame("test-frame-1")
    assert frame is not None
    assert frame["window_title"] == "Test Window"


def test_insert_text_blocks(temp_db):
    """Test inserting text blocks."""
    # First insert a frame
    frame_data = {
        "frame_id": "test-frame-1",
        "timestamp": 1234567890,
        "window_title": "Test Window",
        "app_bundle_id": "com.test.app",
        "app_name": "Test App",
        "file_path": "2025/10/26/test.png",
        "file_size_bytes": 1024000,
        "screen_resolution": "1920x1080",
    }
    temp_db.insert_frame(frame_data)
    
    # Insert text blocks
    text_blocks = [
        {
            "block_id": "block-1",
            "frame_id": "test-frame-1",
            "text": "Hello world",
            "normalized_text": "hello world",
            "confidence": 0.95,
            "bbox": {"x": 100, "y": 200, "width": 300, "height": 50},
            "block_type": "prose",
        }
    ]
    
    count = temp_db.insert_text_blocks(text_blocks)
    assert count == 1
    
    # Verify text blocks were inserted
    blocks = temp_db.get_text_blocks_by_frame("test-frame-1")
    assert len(blocks) == 1
    assert blocks[0]["text"] == "Hello world"


def test_search_text(temp_db):
    """Test full-text search."""
    # Insert test data
    frame_data = {
        "frame_id": "test-frame-1",
        "timestamp": 1234567890,
        "window_title": "Test Window",
        "app_bundle_id": "com.test.app",
        "app_name": "Test App",
        "file_path": "2025/10/26/test.png",
        "file_size_bytes": 1024000,
        "screen_resolution": "1920x1080",
    }
    temp_db.insert_frame(frame_data)
    
    text_blocks = [
        {
            "block_id": "block-1",
            "frame_id": "test-frame-1",
            "text": "Python programming tutorial",
            "normalized_text": "python programming tutorial",
            "confidence": 0.95,
            "bbox": {"x": 100, "y": 200, "width": 300, "height": 50},
            "block_type": "prose",
        }
    ]
    temp_db.insert_text_blocks(text_blocks)
    
    # Search for text
    results = temp_db.search_text("python")
    assert len(results) > 0
    assert "python" in results[0]["text"].lower()


def test_window_tracking(temp_db):
    """Test window tracking."""
    temp_db.update_window_tracking(
        "com.test.app",
        "Test App",
        1234567890
    )
    
    stats = temp_db.get_app_usage_stats()
    assert len(stats) > 0
    assert stats[0]["app_name"] == "Test App"


def test_cleanup_old_frames(temp_db):
    """Test cleaning up old frames."""
    # Insert old frame
    frame_data = {
        "frame_id": "old-frame",
        "timestamp": 1000000000,  # Very old timestamp
        "window_title": "Old Window",
        "app_bundle_id": "com.test.app",
        "app_name": "Test App",
        "file_path": "2001/09/09/old.png",
        "file_size_bytes": 1024000,
        "screen_resolution": "1920x1080",
    }
    temp_db.insert_frame(frame_data)
    
    # Clean up frames older than 1 day
    deleted = temp_db.cleanup_old_frames(retention_days=1)
    assert deleted > 0
    
    # Verify frame was deleted
    frame = temp_db.get_frame("old-frame")
    assert frame is None
