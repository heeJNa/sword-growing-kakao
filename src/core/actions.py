"""Game actions - enhance, sell, buy"""
import time
from typing import Optional
from ..automation.clipboard import type_to_chat, copy_chat_output
from ..automation.mouse import click_at
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES
from ..config.settings import Settings, DEFAULT_SETTINGS
from ..utils.logger import get_logger

logger = get_logger(__name__)


def enhance(coords: Coordinates = None, settings: Settings = None) -> None:
    """
    Execute enhancement command.

    Sends "/ㄱ" to the chat to trigger enhancement.

    Args:
        coords: Screen coordinates (uses default if None)
        settings: Settings configuration (uses default if None)
    """
    logger.debug("enhance() 호출됨")
    if coords is None:
        coords = DEFAULT_COORDINATES
        logger.debug("좌표: 기본값 사용")
    if settings is None:
        settings = DEFAULT_SETTINGS

    # Type enhancement command
    logger.info("강화 명령 전송: /ㄱ")
    type_to_chat("/ㄱ", coords)

    # Wait for response
    logger.debug(f"응답 대기: {settings.action_delay}초")
    time.sleep(settings.action_delay)
    logger.debug("enhance() 완료")


def sell(coords: Coordinates = None, settings: Settings = None) -> None:
    """
    Execute sell command.

    Sends "/판" to the chat to sell the current sword.

    Args:
        coords: Screen coordinates (uses default if None)
        settings: Settings configuration (uses default if None)
    """
    logger.debug("sell() 호출됨")
    if coords is None:
        coords = DEFAULT_COORDINATES
    if settings is None:
        settings = DEFAULT_SETTINGS

    # Type sell command
    logger.info("판매 명령 전송: /판")
    type_to_chat("/판", coords)

    # Wait for response
    logger.debug(f"응답 대기: {settings.action_delay}초")
    time.sleep(settings.action_delay)
    logger.debug("sell() 완료")


def buy_item(item_name: str, coords: Coordinates = None, settings: Settings = None) -> None:
    """
    Buy an item from the shop.

    Args:
        item_name: Name of item to buy (e.g., "방지권", "워프권")
        coords: Screen coordinates (uses default if None)
        settings: Settings configuration (uses default if None)
    """
    if coords is None:
        coords = DEFAULT_COORDINATES
    if settings is None:
        settings = DEFAULT_SETTINGS

    # Type buy command
    type_to_chat(f"/구매 {item_name}", coords)

    # Wait for response
    time.sleep(settings.action_delay)


def use_protection(coords: Coordinates = None, settings: Settings = None) -> None:
    """
    Use protection scroll (파괴방지권).

    Args:
        coords: Screen coordinates (uses default if None)
        settings: Settings configuration (uses default if None)
    """
    if coords is None:
        coords = DEFAULT_COORDINATES
    if settings is None:
        settings = DEFAULT_SETTINGS

    type_to_chat("/방지", coords)
    time.sleep(settings.action_delay)


def check_status(coords: Coordinates = None, settings: Settings = None) -> str:
    """
    Check current status by reading chat.

    Args:
        coords: Screen coordinates (uses default if None)
        settings: Settings configuration (uses default if None)

    Returns:
        Chat text content
    """
    logger.debug("check_status() 호출됨")
    if coords is None:
        coords = DEFAULT_COORDINATES
    if settings is None:
        settings = DEFAULT_SETTINGS

    # Read chat output
    logger.debug(f"채팅 출력 복사: ({coords.chat_output_x}, {coords.chat_output_y})")
    result = copy_chat_output(coords)
    logger.debug(f"복사된 텍스트 길이: {len(result)}자")
    return result


def check_inventory(coords: Coordinates = None, settings: Settings = None) -> None:
    """
    Check inventory.

    Args:
        coords: Screen coordinates (uses default if None)
        settings: Settings configuration (uses default if None)
    """
    if coords is None:
        coords = DEFAULT_COORDINATES
    if settings is None:
        settings = DEFAULT_SETTINGS

    type_to_chat("/인벤", coords)
    time.sleep(settings.action_delay)


def check_gold(coords: Coordinates = None, settings: Settings = None) -> None:
    """
    Check current gold.

    Args:
        coords: Screen coordinates (uses default if None)
        settings: Settings configuration (uses default if None)
    """
    if coords is None:
        coords = DEFAULT_COORDINATES
    if settings is None:
        settings = DEFAULT_SETTINGS

    type_to_chat("/골드", coords)
    time.sleep(settings.action_delay)
