"""Game actions - enhance, sell, buy"""
import time
from typing import Optional
from ..automation.clipboard import type_to_chat, copy_chat_output
from ..automation.mouse import click_at
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES
from ..config.settings import Settings, DEFAULT_SETTINGS


def enhance(coords: Coordinates = None, settings: Settings = None) -> None:
    """
    Execute enhancement command.

    Sends "/ㄱ" to the chat to trigger enhancement.

    Args:
        coords: Screen coordinates (uses default if None)
        settings: Settings configuration (uses default if None)
    """
    if coords is None:
        coords = DEFAULT_COORDINATES
    if settings is None:
        settings = DEFAULT_SETTINGS

    # Type enhancement command
    type_to_chat("/ㄱ", coords)

    # Wait for response
    time.sleep(settings.action_delay)


def sell(coords: Coordinates = None, settings: Settings = None) -> None:
    """
    Execute sell command.

    Sends "/판" to the chat to sell the current sword.

    Args:
        coords: Screen coordinates (uses default if None)
        settings: Settings configuration (uses default if None)
    """
    if coords is None:
        coords = DEFAULT_COORDINATES
    if settings is None:
        settings = DEFAULT_SETTINGS

    # Type sell command
    type_to_chat("/판", coords)

    # Wait for response
    time.sleep(settings.action_delay)


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
    if coords is None:
        coords = DEFAULT_COORDINATES
    if settings is None:
        settings = DEFAULT_SETTINGS

    # Read chat output
    return copy_chat_output(coords)


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
