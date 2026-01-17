"""Chat message parsing for extracting game state"""
import re
from dataclasses import dataclass
from typing import Tuple, Optional
from .state import EnhanceResult, GameState
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedMessage:
    """Parsed message data"""
    result: EnhanceResult
    level: Optional[int] = None
    gold: Optional[int] = None
    sword_name: Optional[str] = None
    gold_spent: int = 0
    gold_earned: int = 0
    prev_level: Optional[int] = None  # 강화 성공 시 이전 레벨


# ============================================================
# 정규식 패턴 (새로운 메시지 형식 기반)
# ============================================================

# 결과 타입 패턴
RESULT_PATTERNS = {
    # 성공: 〖✨강화 성공✨ +8 → +9〗
    "success": r'〖\s*✨?\s*강화\s*성공\s*✨?\s*\+(\d+)\s*→\s*\+(\d+)\s*〗',

    # 유지: 〖💦강화 유지💦〗
    "maintain": r'〖\s*💦?\s*강화\s*유지\s*💦?\s*〗',

    # 파괴: 〖💥강화 파괴💥〗
    "destroy": r'〖\s*💥?\s*강화\s*파괴\s*💥?\s*〗',

    # 판매: 〖검 판매〗
    "sell": r'〖\s*검\s*판매\s*〗',
}

# 골드 패턴
GOLD_PATTERNS = {
    # 남은 골드: 4,354,522,776G
    "remaining": r'(?:남은\s*골드|현재\s*보유\s*골드)\s*[:\s]*([0-9,]+)\s*G',

    # 사용 골드: -5,000G
    "spent": r'사용\s*골드\s*[:\s]*-?([0-9,]+)\s*G',

    # 획득 골드: +80G
    "earned": r'획득\s*골드\s*[:\s]*\+?([0-9,]+)\s*G',
}

# 검 패턴
SWORD_PATTERNS = {
    # 획득 검: [+9] 영원한 혈맥의 검
    "acquired": r'(?:획득\s*검|새로운\s*검\s*획득)\s*[:\s]*\[?\+?(\d+)\]?\s*(.+?)(?:\n|$)',

    # 『[+2] 과속의 몽둥이』의 레벨이 유지
    "maintained": r'『\[?\+?(\d+)\]?\s*(.+?)』',

    # 일반 검 이름 추출
    "general": r'\[\+(\d+)\]\s*(.+?)(?:\s*검|\s*의\s*검|』|$)',
}


def parse_gold(text: str) -> int:
    """Parse gold string to integer"""
    return int(text.replace(",", ""))


def extract_remaining_gold(text: str) -> Optional[int]:
    """Extract remaining gold from text"""
    match = re.search(GOLD_PATTERNS["remaining"], text)
    if match:
        return parse_gold(match.group(1))
    return None


def extract_spent_gold(text: str) -> int:
    """Extract spent gold from text"""
    match = re.search(GOLD_PATTERNS["spent"], text)
    if match:
        return parse_gold(match.group(1))
    return 0


def extract_earned_gold(text: str) -> int:
    """Extract earned gold from text"""
    match = re.search(GOLD_PATTERNS["earned"], text)
    if match:
        return parse_gold(match.group(1))
    return 0


def extract_sword_info(text: str, result_type: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Extract sword level and name from text.

    Returns:
        Tuple of (level, name)
    """
    # 성공/판매 시 획득 검
    if result_type in ("success", "sell"):
        match = re.search(SWORD_PATTERNS["acquired"], text)
        if match:
            level = int(match.group(1))
            name = match.group(2).strip()
            return level, name

    # 유지 시 검 정보
    if result_type == "maintain":
        match = re.search(SWORD_PATTERNS["maintained"], text)
        if match:
            level = int(match.group(1))
            name = match.group(2).strip()
            return level, name

    # 일반 패턴
    match = re.search(SWORD_PATTERNS["general"], text)
    if match:
        level = int(match.group(1))
        name = match.group(2).strip()
        return level, name

    return None, None


def parse_message(text: str) -> ParsedMessage:
    """
    Parse a chat message and extract all game information.

    Args:
        text: Raw chat message text

    Returns:
        ParsedMessage with all extracted data
    """
    logger.debug(f"메시지 파싱 시작 (길이: {len(text)}자)")

    # 성공 체크
    success_match = re.search(RESULT_PATTERNS["success"], text)
    if success_match:
        prev_level = int(success_match.group(1))
        new_level = int(success_match.group(2))
        gold = extract_remaining_gold(text)
        gold_spent = extract_spent_gold(text)
        _, sword_name = extract_sword_info(text, "success")

        logger.info(f"파싱 결과: 성공 ({prev_level}→{new_level}강), gold={gold}, sword={sword_name}")
        return ParsedMessage(
            result=EnhanceResult.SUCCESS,
            level=new_level,
            prev_level=prev_level,
            gold=gold,
            gold_spent=gold_spent,
            sword_name=sword_name,
        )

    # 유지 체크
    if re.search(RESULT_PATTERNS["maintain"], text):
        level, sword_name = extract_sword_info(text, "maintain")
        gold = extract_remaining_gold(text)
        gold_spent = extract_spent_gold(text)

        logger.info(f"파싱 결과: 유지 (level={level}), gold={gold}, sword={sword_name}")
        return ParsedMessage(
            result=EnhanceResult.MAINTAIN,
            level=level,
            gold=gold,
            gold_spent=gold_spent,
            sword_name=sword_name,
        )

    # 파괴 체크
    if re.search(RESULT_PATTERNS["destroy"], text):
        gold = extract_remaining_gold(text)
        gold_spent = extract_spent_gold(text)

        logger.info(f"파싱 결과: 파괴, gold={gold}")
        return ParsedMessage(
            result=EnhanceResult.DESTROY,
            level=0,
            gold=gold,
            gold_spent=gold_spent,
            sword_name=None,  # 파괴 시 검 없음
        )

    # 판매 체크
    if re.search(RESULT_PATTERNS["sell"], text):
        gold = extract_remaining_gold(text)
        gold_earned = extract_earned_gold(text)
        level, sword_name = extract_sword_info(text, "sell")

        logger.info(f"파싱 결과: 판매, gold={gold}, earned={gold_earned}, new_sword={sword_name}")
        return ParsedMessage(
            result=EnhanceResult.UNKNOWN,  # 판매는 별도 처리
            level=level if level is not None else 0,
            gold=gold,
            gold_earned=gold_earned,
            sword_name=sword_name,
        )

    # 알 수 없음 - 기존 패턴으로 시도
    logger.debug("새 패턴 매칭 실패, 기존 패턴으로 시도")
    return _parse_legacy(text)


def _parse_legacy(text: str) -> ParsedMessage:
    """Legacy parsing for backward compatibility"""
    # 기존 패턴들
    legacy_patterns = {
        "destroy": [r'파괴', r'부서졌', r'부서', r'0강.*시작'],
        "success": [r'\+(\d+)강.*성공', r'강화.*성공.*\+(\d+)'],
        "maintain": [r'실패.*유지', r'유지.*됩니다', r'레벨.*유지'],
        "gold": r'(\d{1,3}(?:,\d{3})*)\s*(?:골드|원|G)',
    }

    # 파괴 체크
    for pattern in legacy_patterns["destroy"]:
        if re.search(pattern, text, re.IGNORECASE):
            gold_match = re.search(legacy_patterns["gold"], text)
            gold = parse_gold(gold_match.group(1)) if gold_match else None
            return ParsedMessage(result=EnhanceResult.DESTROY, level=0, gold=gold)

    # 성공 체크
    for pattern in legacy_patterns["success"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            level = int(match.group(1))
            gold_match = re.search(legacy_patterns["gold"], text)
            gold = parse_gold(gold_match.group(1)) if gold_match else None
            return ParsedMessage(result=EnhanceResult.SUCCESS, level=level, gold=gold)

    # 유지 체크
    for pattern in legacy_patterns["maintain"]:
        if re.search(pattern, text, re.IGNORECASE):
            gold_match = re.search(legacy_patterns["gold"], text)
            gold = parse_gold(gold_match.group(1)) if gold_match else None
            return ParsedMessage(result=EnhanceResult.MAINTAIN, gold=gold)

    return ParsedMessage(result=EnhanceResult.UNKNOWN)


def parse_chat(text: str) -> Tuple[EnhanceResult, GameState]:
    """
    Parse chat text and extract game state.

    This is the main entry point for parsing.

    Returns:
        Tuple of (EnhanceResult, GameState)
    """
    parsed = parse_message(text)

    state = GameState(
        level=parsed.level if parsed.level is not None else 0,
        gold=parsed.gold if parsed.gold is not None else 0,
        sword_name=parsed.sword_name or "",
        gold_spent=parsed.gold_spent,
        gold_earned=parsed.gold_earned,
    )

    return parsed.result, state


def is_sell_message(text: str) -> bool:
    """Check if text is a sell message"""
    return bool(re.search(RESULT_PATTERNS["sell"], text))


def parse_sell_message(text: str) -> Tuple[int, int, str]:
    """
    Parse sell message.

    Returns:
        Tuple of (gold_earned, remaining_gold, new_sword_name)
    """
    gold_earned = extract_earned_gold(text)
    remaining_gold = extract_remaining_gold(text) or 0
    _, sword_name = extract_sword_info(text, "sell")

    return gold_earned, remaining_gold, sword_name or ""


# ============================================================
# 하위 호환성 유지 함수들
# ============================================================

def normalize_text(text: str) -> str:
    """Normalize text for parsing"""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_gold(text: str) -> Optional[int]:
    """Extract gold amount from text (legacy)"""
    return extract_remaining_gold(text)


def extract_level(text: str) -> Optional[int]:
    """Extract level from text (legacy)"""
    match = re.search(r'\+(\d+)강', text)
    if match:
        return int(match.group(1))
    return None


def parse_enhance_result(text: str) -> Tuple[EnhanceResult, Optional[int]]:
    """Parse enhancement result from chat text (legacy)"""
    parsed = parse_message(text)
    return parsed.result, parsed.level


def extract_sell_info(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Extract sell information from text (legacy)"""
    gold_earned, remaining_gold, _ = parse_sell_message(text)
    level, _ = extract_sword_info(text, "sell")
    return level, gold_earned


# ============================================================
# 프로필 파싱
# ============================================================

@dataclass
class ProfileInfo:
    """Parsed profile information"""
    name: Optional[str] = None
    gold: Optional[int] = None
    level: Optional[int] = None
    sword_name: Optional[str] = None


def parse_profile(text: str) -> Optional[ProfileInfo]:
    """
    Parse profile message to extract current state.

    Expected format:
    ⚔️ [프로필]
    ● 이름: @김희준
    ● 보유 골드: 4,354,050,506 G
    ● 보유 검: [+9] 생명의 근원 검

    Returns:
        ProfileInfo or None if not a profile message
    """
    # Check if this is a profile message
    if "[프로필]" not in text and "프로필" not in text:
        return None

    logger.debug("프로필 메시지 파싱 시작")

    profile = ProfileInfo()

    # Extract name: ● 이름: @김희준
    name_match = re.search(r'이름\s*:\s*@?(\S+)', text)
    if name_match:
        profile.name = name_match.group(1)
        logger.debug(f"이름: {profile.name}")

    # Extract gold: ● 보유 골드: 4,354,050,506 G
    gold_match = re.search(r'보유\s*골드\s*:\s*([0-9,]+)\s*G', text)
    if gold_match:
        profile.gold = parse_gold(gold_match.group(1))
        logger.debug(f"보유 골드: {profile.gold:,}")

    # Extract sword: ● 보유 검: [+9] 생명의 근원 검
    sword_match = re.search(r'보유\s*검\s*:\s*\[\+(\d+)\]\s*(.+?)(?:\n|$)', text)
    if sword_match:
        profile.level = int(sword_match.group(1))
        profile.sword_name = sword_match.group(2).strip()
        logger.debug(f"보유 검: +{profile.level} {profile.sword_name}")

    logger.info(f"프로필 파싱 완료: level={profile.level}, gold={profile.gold:,} G" if profile.gold else f"프로필 파싱 완료: level={profile.level}")

    return profile
