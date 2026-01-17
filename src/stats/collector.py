"""Statistics collector for tracking enhancement results"""
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from .models import SessionStats, LevelStats, EnhanceRecord
from ..core.state import EnhanceResult, GameState


class StatsCollector:
    """
    Collects and manages statistics for enhancement results.

    Tracks:
    - Per-level success/maintain/destroy rates
    - Session totals
    - Gold profit/loss
    - History of all enhancements
    """

    def __init__(self, stats_dir: str = None):
        self.stats_dir = Path(stats_dir) if stats_dir else Path.home() / ".sword-macro" / "stats"
        self.stats_dir.mkdir(parents=True, exist_ok=True)

        self.session: Optional[SessionStats] = None

    def start_session(self, starting_gold: int = 0) -> SessionStats:
        """
        Start a new statistics session.

        Args:
            starting_gold: Initial gold amount

        Returns:
            New SessionStats instance
        """
        self.session = SessionStats(
            start_time=datetime.now(),
            starting_gold=starting_gold,
            current_gold=starting_gold,
        )
        return self.session

    def end_session(self) -> Optional[SessionStats]:
        """
        End current session and save stats.

        Returns:
            Completed SessionStats or None if no session
        """
        if self.session is None:
            return None

        self.session.end_time = datetime.now()
        self.save_session(self.session)

        # Save cumulative level stats for persistence across restarts
        self.save_cumulative_level_stats()

        result = self.session
        self.session = None
        return result

    def record_enhance(self, level: int, result: EnhanceResult,
                       gold_before: int, gold_after: int) -> None:
        """
        Record an enhancement result.

        Args:
            level: Level before enhancement
            result: Enhancement result
            gold_before: Gold before enhancement
            gold_after: Gold after enhancement
        """
        if self.session is None:
            self.start_session(gold_before)

        self.session.record_enhance(level, result, gold_before, gold_after)

    def record_sell(self, gold_after: int) -> None:
        """
        Record a sell action.

        Args:
            gold_after: Gold after selling
        """
        if self.session:
            self.session.record_sell(gold_after)

    def get_level_stats(self, level: int) -> Optional[LevelStats]:
        """
        Get statistics for a specific level.

        Args:
            level: Level to get stats for

        Returns:
            LevelStats or None if no session
        """
        if self.session:
            return self.session.get_level_stats(level)
        return None

    def get_all_level_stats(self) -> dict:
        """
        Get all level statistics.

        Returns:
            Dictionary of level -> LevelStats
        """
        if self.session:
            return self.session.level_stats
        return {}

    def get_recent_history(self, count: int = 10) -> List[EnhanceRecord]:
        """
        Get recent enhancement history.

        Args:
            count: Number of records to return

        Returns:
            List of recent EnhanceRecords
        """
        if self.session:
            return self.session.history[-count:]
        return []

    def save_session(self, session: SessionStats) -> None:
        """
        Save session to file.

        Args:
            session: Session to save
        """
        # Create session directory
        sessions_dir = self.stats_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON summary
        json_path = sessions_dir / f"session_{session.session_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

        # Save CSV detail
        csv_path = sessions_dir / f"session_{session.session_id}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "level", "result", "gold_before", "gold_after", "gold_change"])
            for record in session.history:
                writer.writerow([
                    record.timestamp.isoformat(),
                    record.level,
                    record.result.value,
                    record.gold_before,
                    record.gold_after,
                    record.gold_change,
                ])

    def load_session(self, session_id: str) -> Optional[SessionStats]:
        """
        Load a session from file.

        Args:
            session_id: Session ID to load

        Returns:
            SessionStats or None if not found
        """
        json_path = self.stats_dir / "sessions" / f"session_{session_id}.json"
        if not json_path.exists():
            return None

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return SessionStats.from_dict(data)

    def list_sessions(self) -> List[str]:
        """
        List all saved session IDs.

        Returns:
            List of session IDs
        """
        sessions_dir = self.stats_dir / "sessions"
        if not sessions_dir.exists():
            return []

        sessions = []
        for f in sessions_dir.glob("session_*.json"):
            session_id = f.stem.replace("session_", "")
            sessions.append(session_id)

        return sorted(sessions, reverse=True)

    def get_cumulative_stats(self) -> dict:
        """
        Get cumulative statistics across all sessions.

        Returns:
            Dictionary with cumulative stats
        """
        cumulative = {
            "total_sessions": 0,
            "total_enhances": 0,
            "total_sells": 0,
            "total_profit": 0,
            "total_duration_minutes": 0,
            "level_stats": {},
        }

        for session_id in self.list_sessions():
            session = self.load_session(session_id)
            if session:
                cumulative["total_sessions"] += 1
                cumulative["total_enhances"] += session.total_enhances
                cumulative["total_sells"] += session.total_sells
                cumulative["total_profit"] += session.profit
                cumulative["total_duration_minutes"] += session.duration_minutes

                # Merge level stats
                for level, stats in session.level_stats.items():
                    if level not in cumulative["level_stats"]:
                        cumulative["level_stats"][level] = {
                            "success": 0,
                            "maintain": 0,
                            "destroy": 0,
                            "total": 0,
                        }
                    cumulative["level_stats"][level]["success"] += stats.success_count
                    cumulative["level_stats"][level]["maintain"] += stats.maintain_count
                    cumulative["level_stats"][level]["destroy"] += stats.destroy_count
                    cumulative["level_stats"][level]["total"] += stats.total_attempts

        return cumulative

    def save_cumulative_level_stats(self) -> None:
        """
        Save cumulative level stats to persistent storage.
        This is called automatically when session ends.
        """
        cumulative = self.get_cumulative_stats()
        cumulative_path = self.stats_dir / "cumulative_level_stats.json"

        with open(cumulative_path, "w", encoding="utf-8") as f:
            json.dump(cumulative["level_stats"], f, indent=2, ensure_ascii=False)

    def load_cumulative_level_stats(self) -> dict:
        """
        Load cumulative level stats from persistent storage.

        Returns:
            Dictionary of level -> {success, maintain, destroy, total}
        """
        cumulative_path = self.stats_dir / "cumulative_level_stats.json"

        if not cumulative_path.exists():
            return {}

        try:
            with open(cumulative_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert string keys to int
                return {int(k): v for k, v in data.items()}
        except (json.JSONDecodeError, ValueError):
            return {}

    def get_cumulative_level_stats_as_model(self) -> dict:
        """
        Get cumulative level stats as LevelStats model objects.
        This is useful for chart rendering.

        Returns:
            Dictionary of level -> LevelStats
        """
        raw_stats = self.load_cumulative_level_stats()
        result = {}

        for level, stats in raw_stats.items():
            level_stats = LevelStats(level=level)
            level_stats.success_count = stats.get("success", 0)
            level_stats.maintain_count = stats.get("maintain", 0)
            level_stats.destroy_count = stats.get("destroy", 0)
            level_stats.total_attempts = stats.get("total", 0)
            result[level] = level_stats

        return result
