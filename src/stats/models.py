"""Statistics data models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from ..core.state import EnhanceResult


@dataclass
class LevelStats:
    """Statistics for a specific enhancement level"""
    level: int
    success_count: int = 0
    maintain_count: int = 0
    destroy_count: int = 0
    total_attempts: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0-1)"""
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts

    @property
    def maintain_rate(self) -> float:
        """Calculate maintain rate (0-1)"""
        if self.total_attempts == 0:
            return 0.0
        return self.maintain_count / self.total_attempts

    @property
    def destroy_rate(self) -> float:
        """Calculate destroy rate (0-1)"""
        if self.total_attempts == 0:
            return 0.0
        return self.destroy_count / self.total_attempts

    def record(self, result: EnhanceResult) -> None:
        """Record an enhancement result"""
        self.total_attempts += 1
        if result == EnhanceResult.SUCCESS:
            self.success_count += 1
        elif result == EnhanceResult.MAINTAIN:
            self.maintain_count += 1
        elif result == EnhanceResult.DESTROY:
            self.destroy_count += 1

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "level": self.level,
            "success_count": self.success_count,
            "maintain_count": self.maintain_count,
            "destroy_count": self.destroy_count,
            "total_attempts": self.total_attempts,
            "success_rate": self.success_rate,
            "maintain_rate": self.maintain_rate,
            "destroy_rate": self.destroy_rate,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LevelStats":
        """Create from dictionary"""
        return cls(
            level=data.get("level", 0),
            success_count=data.get("success_count", 0),
            maintain_count=data.get("maintain_count", 0),
            destroy_count=data.get("destroy_count", 0),
            total_attempts=data.get("total_attempts", 0),
        )


@dataclass
class EnhanceRecord:
    """Record of a single enhancement attempt"""
    timestamp: datetime
    level: int
    result: EnhanceResult
    gold_before: int
    gold_after: int

    @property
    def gold_change(self) -> int:
        """Calculate gold change"""
        return self.gold_after - self.gold_before

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "result": self.result.value,
            "gold_before": self.gold_before,
            "gold_after": self.gold_after,
            "gold_change": self.gold_change,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnhanceRecord":
        """Create from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            level=data["level"],
            result=EnhanceResult(data["result"]),
            gold_before=data["gold_before"],
            gold_after=data["gold_after"],
        )


@dataclass
class SessionStats:
    """Statistics for a single session"""
    session_id: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_enhances: int = 0
    total_sells: int = 0
    starting_gold: int = 0
    current_gold: int = 0
    max_level_reached: int = 0
    level_stats: Dict[int, LevelStats] = field(default_factory=dict)
    history: List[EnhanceRecord] = field(default_factory=list)

    def __post_init__(self):
        if not self.session_id:
            self.session_id = self.start_time.strftime("%Y%m%d_%H%M%S")

    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def duration_minutes(self) -> float:
        """Get session duration in minutes"""
        return self.duration_seconds / 60

    @property
    def profit(self) -> int:
        """Calculate total profit"""
        return self.current_gold - self.starting_gold

    @property
    def roi_percent(self) -> float:
        """Calculate ROI percentage"""
        if self.starting_gold == 0:
            return 0.0
        return (self.profit / self.starting_gold) * 100

    @property
    def profit_per_enhance(self) -> float:
        """Calculate average profit per enhancement"""
        if self.total_enhances == 0:
            return 0.0
        return self.profit / self.total_enhances

    @property
    def total_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_success = sum(s.success_count for s in self.level_stats.values())
        total_attempts = sum(s.total_attempts for s in self.level_stats.values())
        if total_attempts == 0:
            return 0.0
        return total_success / total_attempts

    def get_level_stats(self, level: int) -> LevelStats:
        """Get or create stats for a level"""
        if level not in self.level_stats:
            self.level_stats[level] = LevelStats(level=level)
        return self.level_stats[level]

    def record_enhance(self, level: int, result: EnhanceResult,
                       gold_before: int, gold_after: int) -> None:
        """Record an enhancement result"""
        # Update level stats
        stats = self.get_level_stats(level)
        stats.record(result)

        # Update session totals
        self.total_enhances += 1
        self.current_gold = gold_after

        # Track max level
        if result == EnhanceResult.SUCCESS:
            new_level = level + 1
            if new_level > self.max_level_reached:
                self.max_level_reached = new_level

        # Add to history
        record = EnhanceRecord(
            timestamp=datetime.now(),
            level=level,
            result=result,
            gold_before=gold_before,
            gold_after=gold_after,
        )
        self.history.append(record)

    def record_sell(self, gold_after: int) -> None:
        """Record a sell action"""
        self.total_sells += 1
        self.current_gold = gold_after

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "total_enhances": self.total_enhances,
            "total_sells": self.total_sells,
            "starting_gold": self.starting_gold,
            "current_gold": self.current_gold,
            "profit": self.profit,
            "roi_percent": self.roi_percent,
            "max_level_reached": self.max_level_reached,
            "total_success_rate": self.total_success_rate,
            "level_stats": {
                str(k): v.to_dict() for k, v in self.level_stats.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionStats":
        """Create from dictionary"""
        stats = cls(
            session_id=data.get("session_id", ""),
            start_time=datetime.fromisoformat(data["start_time"]),
            total_enhances=data.get("total_enhances", 0),
            total_sells=data.get("total_sells", 0),
            starting_gold=data.get("starting_gold", 0),
            current_gold=data.get("current_gold", 0),
            max_level_reached=data.get("max_level_reached", 0),
        )

        if data.get("end_time"):
            stats.end_time = datetime.fromisoformat(data["end_time"])

        level_stats_data = data.get("level_stats", {})
        for level_str, level_data in level_stats_data.items():
            level = int(level_str)
            stats.level_stats[level] = LevelStats.from_dict(level_data)

        return stats
