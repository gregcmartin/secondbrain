"""Streamlit UI for Second Brain - Daily summaries and visual timeline."""

import streamlit as st
from datetime import datetime, timedelta, time
from pathlib import Path
import sqlite3
from typing import List, Dict, Any
import os

# Import config system
from second_brain.config import get_config

# Page config
st.set_page_config(
    page_title="Second Brain - Daily Review",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .summary-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
    }
    .stat-box {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .timeline-frame {
        border: 2px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.3s;
    }
    .timeline-frame:hover {
        border-color: #667eea;
        transform: scale(1.05);
    }
    .timeline-frame.selected {
        border-color: #667eea;
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
    }
</style>
""", unsafe_allow_html=True)


class SecondBrainUI:
    """Streamlit UI for Second Brain."""
    
    def __init__(self):
        """Initialize UI."""
        self.db_path = Path.home() / "Library/Application Support/second-brain/database/memory.db"
        self.frames_dir = Path.home() / "Library/Application Support/second-brain/frames"
        self.conn = None
        
    def connect_db(self):
        """Connect to database."""
        if not self.db_path.exists():
            st.error("Database not found. Please start Second Brain first.")
            st.stop()
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
    
    def get_daily_stats(self, date: datetime) -> Dict[str, Any]:
        """Get statistics for a specific day."""
        start_ts = int(date.replace(hour=0, minute=0, second=0).timestamp())
        end_ts = int(date.replace(hour=23, minute=59, second=59).timestamp())
        
        cursor = self.conn.cursor()
        
        # Get frame count
        cursor.execute("""
            SELECT COUNT(*) as count FROM frames
            WHERE timestamp BETWEEN ? AND ?
        """, (start_ts, end_ts))
        frame_count = cursor.fetchone()['count']
        
        # Get text block count
        cursor.execute("""
            SELECT COUNT(*) as count FROM text_blocks tb
            JOIN frames f ON tb.frame_id = f.frame_id
            WHERE f.timestamp BETWEEN ? AND ?
        """, (start_ts, end_ts))
        text_count = cursor.fetchone()['count']
        
        # Get app usage
        cursor.execute("""
            SELECT app_name, COUNT(*) as count
            FROM frames
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY app_name
            ORDER BY count DESC
            LIMIT 5
        """, (start_ts, end_ts))
        top_apps = [dict(row) for row in cursor.fetchall()]
        
        # Get total text length
        cursor.execute("""
            SELECT SUM(LENGTH(text)) as total_chars
            FROM text_blocks tb
            JOIN frames f ON tb.frame_id = f.frame_id
            WHERE f.timestamp BETWEEN ? AND ?
        """, (start_ts, end_ts))
        total_chars = cursor.fetchone()['total_chars'] or 0
        
        return {
            'frame_count': frame_count,
            'text_count': text_count,
            'top_apps': top_apps,
            'total_chars': total_chars,
        }
    
    def get_frames_for_day(self, date: datetime, app_filter: str = None, start_time=None, end_time=None, preview_per_hour: int = 10) -> Dict[int, List[Dict[str, Any]]]:
        """Get frames for a specific day with filtering and lazy loading.

        Args:
            date: Date to query
            app_filter: Optional app name to filter by
            start_time: Start time (datetime.time object)
            end_time: End time (datetime.time object)
            preview_per_hour: Number of frames to load per hour as preview

        Returns:
            Dict mapping hour -> list of frames (limited to preview_per_hour)
        """
        # Ensure we have time objects, not datetime
        if start_time is None:
            start_time = time(0, 0)
        elif isinstance(start_time, datetime):
            start_time = start_time.time()

        if end_time is None:
            end_time = time(23, 59, 59)
        elif isinstance(end_time, datetime):
            end_time = end_time.time()

        # Get date object from datetime
        if isinstance(date, datetime):
            date_obj = date.date()
        else:
            date_obj = date

        start_dt = datetime.combine(date_obj, start_time)
        end_dt = datetime.combine(date_obj, end_time)
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())

        cursor = self.conn.cursor()

        # Build query with optional app filter
        query = """
            SELECT * FROM frames
            WHERE timestamp BETWEEN ? AND ?
        """
        params = [start_ts, end_ts]

        if app_filter and app_filter != "All":
            query += " AND app_name = ?"
            params.append(app_filter)

        query += " ORDER BY timestamp ASC"

        cursor.execute(query, params)
        all_frames = [dict(row) for row in cursor.fetchall()]

        # Group by hour and limit to preview
        frames_by_hour = {}
        for frame in all_frames:
            hour = datetime.fromtimestamp(frame['timestamp']).hour
            if hour not in frames_by_hour:
                frames_by_hour[hour] = {'frames': [], 'total': 0}

            frames_by_hour[hour]['total'] += 1
            if len(frames_by_hour[hour]['frames']) < preview_per_hour:
                frames_by_hour[hour]['frames'].append(frame)

        return frames_by_hour

    def get_apps_for_day(self, date: datetime) -> List[str]:
        """Get list of apps used on a specific day."""
        start_ts = int(date.replace(hour=0, minute=0, second=0).timestamp())
        end_ts = int(date.replace(hour=23, minute=59, second=59).timestamp())

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT app_name FROM frames
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY app_name
        """, (start_ts, end_ts))

        return [row[0] for row in cursor.fetchall()]
    
    def get_text_for_frame(self, frame_id: str) -> List[Dict[str, Any]]:
        """Get text blocks for a frame."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM text_blocks
            WHERE frame_id = ?
        """, (frame_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def render_settings_panel(self):
        """Render the settings panel with full config sync.
        
        This panel reads from and writes to the config system bidirectionally.
        """
        config = get_config()
        
        # Initialize session state for settings
        if 'settings_changed' not in st.session_state:
            st.session_state['settings_changed'] = False
        
        st.subheader("⚙️ Settings")
        
        # Create tabs for different settings categories
        tab1, tab2, tab3 = st.tabs(["Capture", "Search", "Storage"])
        
        with tab1:
            st.markdown("#### Capture Settings")
            
            # Smart capture toggles
            st.markdown("**Smart Capture:**")
            
            # Enable frame deduplication
            enable_frame_diff = config.get("capture.enable_frame_diff", True)
            new_frame_diff = st.checkbox(
                "Skip duplicate frames",
                value=enable_frame_diff,
                help="Automatically skip frames that haven't changed"
            )
            if new_frame_diff != enable_frame_diff:
                config.set("capture.enable_frame_diff", new_frame_diff)
                config.save()
                st.success(f"Frame deduplication {'enabled' if new_frame_diff else 'disabled'}")
            
            # Frame similarity threshold
            if new_frame_diff:
                similarity_threshold = config.get("capture.similarity_threshold", 0.95)
                new_threshold = st.slider(
                    "Similarity threshold",
                    min_value=0.80,
                    max_value=0.99,
                    value=float(similarity_threshold),
                    step=0.01,
                    help="How similar frames need to be to be considered duplicates (higher = more strict)"
                )
                if new_threshold != similarity_threshold:
                    config.set("capture.similarity_threshold", new_threshold)
                    config.save()
                    st.success(f"Threshold updated to {new_threshold}")
            
            st.markdown("---")
            st.markdown("**Adaptive FPS:**")
            
            # Enable adaptive FPS
            enable_adaptive_fps = config.get("capture.enable_adaptive_fps", True)
            new_adaptive_fps = st.checkbox(
                "Auto-adjust FPS based on activity",
                value=enable_adaptive_fps,
                help="Automatically reduce FPS when idle (smart power saving)"
            )
            if new_adaptive_fps != enable_adaptive_fps:
                config.set("capture.enable_adaptive_fps", new_adaptive_fps)
                config.save()
                st.success(f"Adaptive FPS {'enabled' if new_adaptive_fps else 'disabled'}")
            
            # Idle threshold
            if new_adaptive_fps:
                idle_threshold = config.get("capture.idle_threshold_seconds", 30.0)
                new_idle = st.slider(
                    "Idle detection threshold (seconds)",
                    min_value=10.0,
                    max_value=120.0,
                    value=float(idle_threshold),
                    step=5.0,
                    help="Seconds of inactivity before considered idle"
                )
                if new_idle != idle_threshold:
                    config.set("capture.idle_threshold_seconds", new_idle)
                    config.save()
                    st.success(f"Idle threshold updated to {new_idle}s")
            
            st.markdown("---")
            st.markdown("**Image Settings:**")
            
            # Format setting
            current_format = config.get("capture.format", "png")
            new_format = st.selectbox(
                "Image format",
                options=["png", "webp", "jpg"],
                index=["png", "webp", "jpg"].index(current_format),
                help="PNG: lossless, larger; WebP: balanced; JPG: smaller, lossy"
            )
            if new_format != current_format:
                config.set("capture.format", new_format)
                config.save()
                st.success(f"Format updated to {new_format}")
            
            # BEGIN_DEEPSEEK_OCR
            # OCR Engine selection (currently Apple Vision only, DeepSeek commented for future)
            # FUTURE: Uncomment when DeepSeek OCR is production-ready
            # current_ocr_engine = config.get("ocr.engine", "apple")
            # new_ocr_engine = st.selectbox(
            #     "OCR Engine",
            #     options=["apple", "deepseek"],
            #     index=["apple", "deepseek"].index(current_ocr_engine),
            #     help="Apple Vision: fast, free, local (default)\nDeepSeek: cutting-edge, local, requires MLX (experimental)"
            # )
            # if new_ocr_engine != current_ocr_engine:
            #     config.set("ocr.engine", new_ocr_engine)
            #     config.save()
            #     st.success(f"OCR engine updated to {new_ocr_engine}")
            # END_DEEPSEEK_OCR
            
            # Quality setting
            current_quality = config.get("capture.quality", 85)
            new_quality = st.slider(
                "Image quality (for WebP/JPG)",
                min_value=50,
                max_value=100,
                value=int(current_quality),
                step=5,
                help="Higher quality = larger files but better image preservation"
            )
            if new_quality != current_quality:
                config.set("capture.quality", new_quality)
                config.save()
                st.success(f"Quality updated to {new_quality}")
            
            # Max disk usage
            current_max_disk = config.get("capture.max_disk_usage_gb", 100)
            new_max_disk = st.number_input(
                "Max disk usage (GB)",
                min_value=10,
                max_value=1000,
                value=int(current_max_disk),
                step=10,
                help="Maximum disk space to use for captured frames"
            )
            if new_max_disk != current_max_disk:
                config.set("capture.max_disk_usage_gb", new_max_disk)
                config.save()
                st.success(f"Max disk usage updated to {new_max_disk} GB")
        
        with tab2:
            st.markdown("#### Search Settings")
            
            # Embeddings enabled
            embeddings_enabled = config.get("embeddings.enabled", True)
            new_embeddings_enabled = st.checkbox(
                "Enable semantic search (embeddings)",
                value=embeddings_enabled,
                help="Enable vector embeddings for semantic search"
            )
            if new_embeddings_enabled != embeddings_enabled:
                config.set("embeddings.enabled", new_embeddings_enabled)
                config.save()
                status = "enabled" if new_embeddings_enabled else "disabled"
                st.success(f"Semantic search {status}")
            
            # Reranker setting
            reranker_enabled = config.get("embeddings.reranker_enabled", False)
            new_reranker_enabled = st.checkbox(
                "Enable search result reranking",
                value=reranker_enabled,
                help="Use AI-powered reranking to improve search result relevance (requires BAAI/bge-reranker-large model - 2.24 GB download on first use)"
            )
            if new_reranker_enabled != reranker_enabled:
                config.set("embeddings.reranker_enabled", new_reranker_enabled)
                config.save()
                if new_reranker_enabled:
                    st.info("ℹ️ Reranker model (2.24 GB) will download on first search. This improves relevance significantly.")
                    st.success("Reranking enabled")
                else:
                    st.success("Reranking disabled")
            
            # Embedding model info
            if embeddings_enabled:
                embedding_model = config.get("embeddings.model", "sentence-transformers/all-MiniLM-L6-v2")
                st.caption(f"Embedding model: {embedding_model}")
        
        with tab3:
            st.markdown("#### Storage Settings")
            
            # Retention days
            current_retention = config.get("storage.retention_days", 90)
            new_retention = st.number_input(
                "Data retention (days)",
                min_value=7,
                max_value=365,
                value=int(current_retention),
                step=7,
                help="How long to keep captured data before automatic deletion"
            )
            if new_retention != current_retention:
                config.set("storage.retention_days", new_retention)
                config.save()
                st.success(f"Retention updated to {new_retention} days")
            
            # Compression
            compression_enabled = config.get("storage.compression", True)
            new_compression = st.checkbox(
                "Enable compression",
                value=compression_enabled,
                help="Compress text blocks and metadata for faster I/O"
            )
            if new_compression != compression_enabled:
                config.set("storage.compression", new_compression)
                config.save()
                st.success(f"Compression {'enabled' if new_compression else 'disabled'}")
        
        st.markdown("---")
        
        # Reset options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save All Settings", use_container_width=True):
                config.save()
                st.success("✅ All settings saved")
        
        with col2:
            if st.button("🔄 Reset to Defaults", use_container_width=True, type="secondary"):
                config.reset_all()
                st.success("✅ Settings reset to defaults")
                st.rerun()
    
    def get_summaries_for_day(self, date: datetime) -> List[Dict[str, Any]]:
        """Get AI-generated summaries for a specific day.
        
        Args:
            date: Date to get summaries for
            
        Returns:
            List of summary dictionaries
        """
        start_ts = int(date.replace(hour=0, minute=0, second=0).timestamp())
        end_ts = int(date.replace(hour=23, minute=59, second=59).timestamp())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM summaries
            WHERE start_timestamp >= ? AND end_timestamp <= ?
            ORDER BY start_timestamp ASC
        """, (start_ts, end_ts))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def run(self):
        """Run the Streamlit app."""
        self.connect_db()
        
        # Header
        st.markdown('<div class="main-header">🧠 Second Brain</div>', unsafe_allow_html=True)
        st.markdown("### Your Visual Memory Timeline")
        
        # Sidebar - Date selection
        with st.sidebar:
            st.header("📅 Select Date")
            selected_date = st.date_input(
                "Date",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
            selected_datetime = datetime.combine(selected_date, datetime.min.time())
            
            st.markdown("---")
            
            # Render settings panel with full config management (collapsible)
            with st.expander("⚙️ Settings", expanded=False):
                self.render_settings_panel()
            
            st.markdown("---")
            st.caption("💡 Changes are saved immediately")
        
        # Get stats for selected day
        stats = self.get_daily_stats(selected_datetime)
        
        # UI-only settings (not persisted to config)
        show_summary = st.sidebar.checkbox("Show AI Summary", value=True, help="Display AI-generated summaries if available")
        frames_per_row = st.sidebar.slider("Frames per row", 2, 6, 4, help="How many frames to display per row in timeline")

        # Filters
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filters")

        # App filter
        available_apps = self.get_apps_for_day(selected_datetime)
        app_filter = st.sidebar.selectbox(
            "Filter by App",
            options=["All"] + available_apps,
            index=0,
            help="Filter frames by application"
        )

        # Time range filter with proper time picker
        st.sidebar.subheader("Time Range")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_time = st.time_input("Start Time", value=time(0, 0))
        with col2:
            end_time = st.time_input("End Time", value=time(23, 59, 59))

        # Preview limit control - up to 1000 frames per hour
        preview_limit = st.sidebar.number_input(
            "Frames per hour (max)",
            min_value=5,
            max_value=1000,
            value=10,
            step=5,
            help="Number of frames to display per hour. Set to 1000 to see all frames."
        )
        
        # Summary cards - show AI-generated summaries from database
        if show_summary and stats['frame_count'] > 0:
            summaries = self.get_summaries_for_day(selected_datetime)
            
            if summaries:
                for summary in summaries:
                    start_time = datetime.fromtimestamp(summary['start_timestamp'])
                    end_time = datetime.fromtimestamp(summary['end_timestamp'])
                    
                    st.markdown(f"""
                    <div class="summary-card">
                        <h2>🤖 AI Summary - {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}</h2>
                        <p style="font-size: 1.1rem; line-height: 1.6;">{summary['summary_text']}</p>
                        <p style="font-size: 0.9rem; opacity: 0.8; margin-top: 1rem;">
                            📊 {summary['frame_count']} frames analyzed
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("💡 AI summaries will appear here once generated (hourly). Keep Second Brain running to generate summaries automatically.")
        
        # Stats row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-box">
                <h3 style="color: #667eea; margin: 0;">📸 {stats['frame_count']}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #666;">Frames Captured</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-box">
                <h3 style="color: #667eea; margin: 0;">📝 {stats['text_count']}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #666;">Text Blocks</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-box">
                <h3 style="color: #667eea; margin: 0;">💬 {stats['total_chars']:,}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #666;">Characters</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-box">
                <h3 style="color: #667eea; margin: 0;">🎯 {len(stats['top_apps'])}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #666;">Apps Used</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Top apps
        if stats['top_apps']:
            st.subheader("📊 Top Applications")
            for app in stats['top_apps']:
                st.progress(
                    app['count'] / stats['frame_count'],
                    text=f"{app['app_name']}: {app['count']} frames"
                )
        
        st.markdown("---")

        # Timeline
        st.subheader("🎬 Visual Timeline")

        # Get filtered frames (lazy loaded with preview limit)
        frames_by_hour = self.get_frames_for_day(
            selected_datetime,
            app_filter=app_filter,
            start_time=start_time,
            end_time=end_time,
            preview_per_hour=preview_limit
        )

        if not frames_by_hour:
            st.info(f"No frames found for selected filters")
            return

        # Display timeline by hour
        for hour in sorted(frames_by_hour.keys()):
            hour_data = frames_by_hour[hour]
            hour_frames = hour_data['frames']
            total_frames = hour_data['total']
            showing_count = len(hour_frames)

            # Header shows total frames and how many are displayed
            header = f"⏰ {hour:02d}:00 - {hour:02d}:59 ({total_frames} frames"
            if showing_count < total_frames:
                header += f", showing {showing_count})"
            else:
                header += ")"

            with st.expander(header, expanded=(hour == datetime.now().hour)):
                # Display frames in grid
                cols = st.columns(frames_per_row)
                for idx, frame in enumerate(hour_frames):
                    col_idx = idx % frames_per_row

                    with cols[col_idx]:
                        # Get frame image path
                        frame_path = self.frames_dir / frame['file_path']

                        if frame_path.exists():
                            # Display thumbnail
                            st.image(
                                str(frame_path),
                                caption=f"{datetime.fromtimestamp(frame['timestamp']).strftime('%H:%M:%S')} - {frame['app_name']}",
                                use_container_width=True
                            )

                            # Show details on click
                            if st.button(f"View Details", key=f"btn_{frame['frame_id']}"):
                                st.session_state['selected_frame'] = frame['frame_id']
                                st.rerun()

                # Show "more available" message if there are more frames
                if showing_count < total_frames:
                    st.info(f"💡 {total_frames - showing_count} more frames available in this hour. Adjust filters or increase preview limit to see more.")
        
        # Selected frame details - using container to force visibility
        if 'selected_frame' in st.session_state:
            # Scroll target
            st.markdown('<a id="frame-details"></a>', unsafe_allow_html=True)

            frame_details_container = st.container()

            with frame_details_container:
                st.markdown("---")
                st.subheader("🔍 Frame Details")

                frame_id = st.session_state['selected_frame']

                # Get frame data
                cursor = self.conn.cursor()
                cursor.execute("SELECT * FROM frames WHERE frame_id = ?", (frame_id,))
                frame = dict(cursor.fetchone())

                # Get text blocks to calculate confidence
                text_blocks = self.get_text_for_frame(frame_id)
                avg_confidence = None
                if text_blocks:
                    confidences = [block['confidence'] for block in text_blocks if block.get('confidence')]
                    if confidences:
                        avg_confidence = sum(confidences) / len(confidences)

                col1, col2 = st.columns([1, 1])

                with col1:
                    # Display full image
                    frame_path = self.frames_dir / frame['file_path']
                    if frame_path.exists():
                        st.image(str(frame_path), use_container_width=True)

                with col2:
                    # Display metadata with confidence at top
                    st.markdown(f"**Time**: {datetime.fromtimestamp(frame['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"**Application**: {frame['app_name']}")
                    st.markdown(f"**Window**: {frame['window_title']}")
                    st.markdown(f"**Resolution**: {frame['screen_resolution']}")
                    if avg_confidence is not None:
                        st.markdown(f"**Confidence**: {avg_confidence:.1%}")

                    st.markdown("---")

                    # Display OCR text
                    if text_blocks:
                        st.markdown("**Extracted Text:**")
                        for block in text_blocks:
                            with st.expander(f"Text Block ({block['block_type']})", expanded=True):
                                st.text(block['text'])
                    else:
                        st.info("No text extracted for this frame")


def main():
    """Main entry point."""
    ui = SecondBrainUI()
    ui.run()


if __name__ == "__main__":
    main()
