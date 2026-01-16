"""Chat message parsing for extracting game state"""
import re
from typing import Tuple, Optional
from .state import EnhanceResult, GameState


# Regex patterns for parsing chat messages
PATTERNS = {
    # Success patterns - prioritize exact success messages
    "success": [
        r'\+(\d+)강.*성공',
        r'강화.*성공.*\+(\d+)',
        r'축하.*\+(\d+)강',
    ],
    # Maintain patterns - failed but level maintained
    "maintain": [
        r'실패.*유지',
        r'유지.*됩니다',
        r'레벨.*유지',
        r'강화.*실패(?!.*파괴)(?!.*부서)',
    ],
    # Destroy patterns - highest priority, must check first
    "destroy": [
        r'파괴',
        r'부서졌',
        r'부서',
        r'0강.*시작',
        r'처음.*시작',
    ],
    # Gold extraction
    "gold": r'(\d{1,3}(?:,\d{3})*)\s*(?:골드|원|G)',
    # Level extraction
    "level": r'\+(\d+)강',
    # Sell pattern
    "sell": r'판매.*(\d{1,3}(?:,\d{3})*)\s*원',
}


def normalize_text(text: str) -> str:
    """Normalize text for parsing"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might interfere
    text = text.strip()
    return text


def extract_gold(text: str) -> Optional[int]:
    """Extract gold amount from text"""
    match = re.search(PATTERNS["gold"], text)
    if match:
        gold_str = match.group(1).replace(",", "")
        try:
            return int(gold_str)
        except ValueError:
            pass
    return None


def extract_level(text: str) -> Optional[int]:
    """Extract level from text"""
    match = re.search(PATTERNS["level"], text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return None


def parse_enhance_result(text: str) -> Tuple[EnhanceResult, Optional[int]]:
    """
    Parse enhancement result from chat text.

    Returns:
        Tuple of (EnhanceResult, level if found)
    """
    text = normalize_text(text)

    # Check destroy first (highest priority)
    for pattern in PATTERNS["destroy"]:
        if re.search(pattern, text, re.IGNORECASE):
            return EnhanceResult.DESTROY, 0

    # Check success patterns
    for pattern in PATTERNS["success"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            level = None
            try:
                level = int(match.group(1))
            except (IndexError, ValueError):
                level = extract_level(text)
            return EnhanceResult.SUCCESS, level

    # Check maintain patterns
    for pattern in PATTERNS["maintain"]:
        if re.search(pattern, text, re.IGNORECASE):
            level = extract_level(text)
            return EnhanceResult.MAINTAIN, level

    return EnhanceResult.UNKNOWN, None


def parse_chat(text: str) -> Tuple[EnhanceResult, GameState]:
    """
    Parse chat text and extract game state.

    Returns:
        Tuple of (EnhanceResult, GameState)
    """
    result, level = parse_enhance_result(text)
    gold = extract_gold(text)

    state = GameState(
        level=level if level is not None else 0,
        gold=gold if gold is not None else 0,
    )

    return result, state


def is_sell_message(text: str) -> bool:
    """Check if text is a sell message"""
    return bool(re.search(PATTERNS["sell"], text, re.IGNORECASE))


def extract_sell_info(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract sell information from text.

    Returns:
        Tuple of (level sold, gold received)
    """
    text = normalize_text(text)

    level = extract_level(text)

    sell_match = re.search(PATTERNS["sell"], text)
    gold = None
    if sell_match:
        gold_str = sell_match.group(1).replace(",", "")
        try:
            gold = int(gold_str)
        except ValueError:
            pass

    return level, gold
