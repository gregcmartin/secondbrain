"""Database interface for Second Brain."""

import sqlite3
import zlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog

from ..config import Config

logger = structlog.get_logger()


class Database:
    """SQLite database interface for Second Brain."""

    def __init__(self, db_path: Optional[Path] = None, config: Optional[Config] = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to database file. If None, uses default location.
            config: Configuration instance. If None, uses global config.
        """
        self.config = config or Config()
        self.db_path = db_path or (self.config.get_database_dir() / "memory.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database with schema."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Enable WAL mode for better concurrency and performance
        self.conn.execute("PRAGMA journal_mode = WAL")
        
        # Optimize SQLite settings
        self.conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes
        self.conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        self.conn.execute("PRAGMA temp_store = MEMORY")  # Use memory for temp tables
        
        # Load and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r") as f:
            schema = f.read()
        self.conn.executescript(schema)
        self.conn.commit()
        
        logger.info("database_initialized", db_path=str(self.db_path), wal_mode=True)

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # Compression helpers
    
    def _compress_text(self, text: str) -> bytes:
        """Compress text using zlib.
        
        Args:
            text: Text to compress
            
        Returns:
            Compressed bytes
        """
        return zlib.compress(text.encode('utf-8'), level=6)
    
    def _decompress_text(self, compressed: bytes) -> str:
        """Decompress text.
        
        Args:
            compressed: Compressed bytes
            
        Returns:
            Decompressed text
        """
        return zlib.decompress(compressed).decode('utf-8')

    # Frame operations
    
    def insert_frame(self, frame_data: Dict[str, Any]) -> str:
        """Insert a new frame record.
        
        Args:
            frame_data: Dictionary containing frame metadata
            
        Returns:
            frame_id of inserted frame
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO frames (
                frame_id, timestamp, window_title, app_bundle_id,
                app_name, file_path, file_size_bytes, screen_resolution
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            frame_data["frame_id"],
            frame_data["timestamp"],
            frame_data.get("window_title"),
            frame_data.get("app_bundle_id"),
            frame_data.get("app_name"),
            frame_data["file_path"],
            frame_data.get("file_size_bytes"),
            frame_data.get("screen_resolution"),
        ))
        self.conn.commit()
        
        logger.debug("frame_inserted", frame_id=frame_data["frame_id"])
        return frame_data["frame_id"]

    def get_frame(self, frame_id: str) -> Optional[Dict[str, Any]]:
        """Get frame by ID.
        
        Args:
            frame_id: Frame identifier
            
        Returns:
            Frame data dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM frames WHERE frame_id = ?", (frame_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_frames_by_timerange(
        self, start_timestamp: int, end_timestamp: int, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get frames within a time range.
        
        Args:
            start_timestamp: Start timestamp (Unix epoch)
            end_timestamp: End timestamp (Unix epoch)
            limit: Maximum number of frames to return
            
        Returns:
            List of frame dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM frames
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (start_timestamp, end_timestamp, limit))
        return [dict(row) for row in cursor.fetchall()]

    def get_frames_by_app(
        self, app_bundle_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get frames for a specific application.
        
        Args:
            app_bundle_id: Application bundle identifier
            limit: Maximum number of frames to return
            
        Returns:
            List of frame dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM frames
            WHERE app_bundle_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (app_bundle_id, limit))
        return [dict(row) for row in cursor.fetchall()]

    # Text block operations
    
    def insert_text_blocks(self, text_blocks: List[Dict[str, Any]]) -> int:
        """Insert multiple text blocks with compression.
        
        Args:
            text_blocks: List of text block dictionaries
            
        Returns:
            Number of blocks inserted
        """
        cursor = self.conn.cursor()
        
        # Prepare data with compression
        data_to_insert = []
        for block in text_blocks:
            text = block["text"]
            normalized = block.get("normalized_text")
            
            # Compress text if it's large enough to benefit (> 500 chars)
            text_compressed = None
            if len(text) > 500:
                text_compressed = self._compress_text(text)
                # Only use compression if it actually saves space
                if len(text_compressed) >= len(text.encode('utf-8')):
                    text_compressed = None
            
            data_to_insert.append((
                block["block_id"],
                block["frame_id"],
                text,
                normalized,
                text_compressed,
                block.get("confidence"),
                block.get("bbox", {}).get("x"),
                block.get("bbox", {}).get("y"),
                block.get("bbox", {}).get("width"),
                block.get("bbox", {}).get("height"),
                block.get("block_type"),
            ))
        
        cursor.executemany("""
            INSERT INTO text_blocks (
                block_id, frame_id, text, normalized_text, text_compressed, confidence,
                bbox_x, bbox_y, bbox_width, bbox_height, block_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data_to_insert)
        self.conn.commit()
        
        count = len(text_blocks)
        compressed_count = sum(1 for d in data_to_insert if d[4] is not None)
        logger.debug("text_blocks_inserted", count=count, compressed=compressed_count)
        return count

    def get_text_blocks_by_frame(self, frame_id: str) -> List[Dict[str, Any]]:
        """Get all text blocks for a frame.
        
        Args:
            frame_id: Frame identifier
            
        Returns:
            List of text block dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM text_blocks
            WHERE frame_id = ?
            ORDER BY bbox_y, bbox_x
        """, (frame_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_text_block(self, block_id: str) -> Optional[Dict[str, Any]]:
        """Get a single text block by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM text_blocks WHERE block_id = ?",
            (block_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_frames(
        self,
        limit: int = 500,
        app_bundle_id: Optional[str] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve frames with optional filtering."""
        sql = """
            SELECT *
            FROM frames
        """
        clauses: List[str] = []
        params: List[Any] = []

        if app_bundle_id:
            clauses.append("app_bundle_id = ?")
            params.append(app_bundle_id)

        if start_timestamp:
            clauses.append("timestamp >= ?")
            params.append(start_timestamp)

        if end_timestamp:
            clauses.append("timestamp <= ?")
            params.append(end_timestamp)

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    # Search operations
    
    def search_text(
        self,
        query: str,
        app_filter: Optional[str] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Full-text search across text blocks.
        
        Args:
            query: Search query
            app_filter: Optional app bundle ID filter
            start_timestamp: Optional start timestamp filter
            end_timestamp: Optional end timestamp filter
            limit: Maximum number of results
            
        Returns:
            List of search results with frame and text block data
        """
        # Build query with filters
        sql = """
            SELECT
                f.frame_id,
                f.timestamp,
                f.window_title,
                f.app_bundle_id,
                f.app_name,
                f.file_path,
                tb.block_id,
                tb.text,
                tb.confidence,
                tb.bbox_x,
                tb.bbox_y,
                tb.bbox_width,
                tb.bbox_height,
                bm25(text_blocks_fts) AS score
            FROM text_blocks_fts
            JOIN text_blocks tb ON text_blocks_fts.rowid = tb.rowid
            JOIN frames f ON tb.frame_id = f.frame_id
            WHERE text_blocks_fts MATCH ?
        """
        
        params: List[Any] = [query]
        
        if app_filter:
            sql += " AND f.app_bundle_id = ?"
            params.append(app_filter)
        
        if start_timestamp:
            sql += " AND f.timestamp >= ?"
            params.append(start_timestamp)
        
        if end_timestamp:
            sql += " AND f.timestamp <= ?"
            params.append(end_timestamp)
        
        sql += " ORDER BY score, f.timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        
        results = [dict(row) for row in cursor.fetchall()]
        logger.debug("text_search_completed", query=query, results=len(results))
        return results

    # Window tracking operations
    
    def update_window_tracking(
        self, app_bundle_id: str, app_name: str, timestamp: int
    ) -> None:
        """Update window tracking for an application.
        
        Args:
            app_bundle_id: Application bundle identifier
            app_name: Application name
            timestamp: Current timestamp
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO windows (app_bundle_id, app_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(app_bundle_id, app_name) DO UPDATE SET
                last_seen = ?
        """, (app_bundle_id, app_name, timestamp, timestamp, timestamp))
        self.conn.commit()

    def get_app_usage_stats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get application usage statistics.
        
        Args:
            limit: Maximum number of apps to return
            
        Returns:
            List of app usage statistics
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                w.app_bundle_id,
                w.app_name,
                w.first_seen,
                w.last_seen,
                COUNT(f.frame_id) as frame_count
            FROM windows w
            LEFT JOIN frames f ON w.app_bundle_id = f.app_bundle_id
            GROUP BY w.app_bundle_id, w.app_name
            ORDER BY frame_count DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # Maintenance operations
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        cursor = self.conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM frames")
        frame_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM text_blocks")
        text_block_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM windows")
        window_count = cursor.fetchone()[0]
        
        # Get database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        
        # Get oldest and newest frames
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM frames")
        oldest, newest = cursor.fetchone()
        
        return {
            "frame_count": frame_count,
            "text_block_count": text_block_count,
            "window_count": window_count,
            "database_size_bytes": db_size,
            "oldest_frame_timestamp": oldest,
            "newest_frame_timestamp": newest,
        }

    def cleanup_old_frames(self, retention_days: int) -> int:
        """Delete frames older than retention period.
        
        Args:
            retention_days: Number of days to retain
            
        Returns:
            Number of frames deleted
        """
        import time
        cutoff_timestamp = int(time.time()) - (retention_days * 86400)
        
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM frames WHERE timestamp < ?", (cutoff_timestamp,))
        deleted = cursor.rowcount
        self.conn.commit()
        
        logger.info("old_frames_cleaned", deleted=deleted, retention_days=retention_days)
        return deleted

    def vacuum(self) -> None:
        """Vacuum database to reclaim space."""
        self.conn.execute("VACUUM")
        logger.info("database_vacuumed")
    
    # Summary operations
    
    def insert_summary(self, summary_data: Dict[str, Any]) -> str:
        """Insert a summary record.
        
        Args:
            summary_data: Dictionary containing summary data
            
        Returns:
            summary_id of inserted summary
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO summaries (
                summary_id, start_timestamp, end_timestamp,
                summary_type, summary_text, frame_count, app_names
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            summary_data["summary_id"],
            summary_data["start_timestamp"],
            summary_data["end_timestamp"],
            summary_data["summary_type"],
            summary_data["summary_text"],
            summary_data.get("frame_count"),
            summary_data.get("app_names"),
        ))
        self.conn.commit()
        
        logger.debug("summary_inserted", summary_id=summary_data["summary_id"])
        return summary_data["summary_id"]
    
    def get_summaries_for_day(self, date: datetime) -> List[Dict[str, Any]]:
        """Get all summaries for a specific day.
        
        Args:
            date: Date to get summaries for
            
        Returns:
            List of summary dictionaries
        """
        start_ts = int(date.replace(hour=0, minute=0, second=0).timestamp())
        end_ts = int(date.replace(hour=23, minute=59, second=59).timestamp())
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM summaries
            WHERE start_timestamp >= ? AND end_timestamp <= ?
            ORDER BY start_timestamp ASC
            """,
            (start_ts, end_ts),
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_summary(self, summary_type: str = "hourly") -> Optional[Dict[str, Any]]:
        """Get the most recent summary of a given type.
        
        Args:
            summary_type: Type of summary to retrieve
            
        Returns:
            Summary dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM summaries
            WHERE summary_type = ?
            ORDER BY end_timestamp DESC
            LIMIT 1
        """, (summary_type,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
