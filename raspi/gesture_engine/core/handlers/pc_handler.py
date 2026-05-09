import webbrowser
from typing import Final

import pyautogui

from gesture_engine.log import get_logger

from ..matching import normalize_name

logger = get_logger(__name__)

SPOTIFY_URL: Final[str] = "https://open.spotify.com/"
YOUTUBE_URL: Final[str] = "https://www.youtube.com/"
BROWSER_URL: Final[str] = "https://www.google.com/"


def _open_url(url: str) -> bool:
    """Open a URL while keeping failures non-fatal for gesture processing.

    Args:
        url: Destination URL.

    Returns:
        `True` when browser launch succeeds, else `False`.
    """
    try:
        webbrowser.open_new_tab(url)
        return True
    except Exception as error:
        logger.error("Failed to open URL %s: %s", url, error)
        return False


def execute_pc_action(action_name: str) -> bool:
    """Execute PC-specific actions outside of generic routing code.

    Args:
        action_name: Raw or normalized action label from config.

    Returns:
        `True` when a supported action was executed successfully.
    """
    action_normalized = normalize_name(action_name)

    if action_normalized == "open spotify":
        return _open_url(SPOTIFY_URL)

    if action_normalized == "open youtube":
        return _open_url(YOUTUBE_URL)

    if action_normalized == "open browser":
        return _open_url(BROWSER_URL)

    if action_normalized == "close window":
        try:
            pyautogui.hotkey("alt", "f4")
            return True
        except Exception as error:
            logger.error("Failed to close active window: %s", error)
            return False

    if action_normalized == "left click":
        try:
            pyautogui.click()
            return True
        except Exception as error:
            logger.error("Failed to left click: %s", error)
            return False

    if action_normalized == "right click":
        try:
            pyautogui.rightClick()
            return True
        except Exception as error:
            logger.error("Failed to right click: %s", error)
            return False

    if action_normalized == "tab forward":
        try:
            pyautogui.hotkey("ctrl", "tab")
            return True
        except Exception as error:
            logger.error("Failed to tab forward: %s", error)
            return False

    if action_normalized == "tab backward":
        try:
            pyautogui.hotkey("ctrl", "shift", "tab")
            return True
        except Exception as error:
            logger.error("Failed to tab backward: %s", error)
            return False

    if action_normalized == "new tab":
        try:
            pyautogui.hotkey("ctrl", "t")
            return True
        except Exception as error:
            logger.error("Failed to open new tab: %s", error)
            return False

    if action_normalized == "close tab":
        try:
            pyautogui.hotkey("ctrl", "w")
            return True
        except Exception as error:
            logger.error("Failed to close tab: %s", error)
            return False

    if action_normalized == "task view":
        try:
            pyautogui.hotkey("win", "tab")
            return True
        except Exception as error:
            logger.error("Failed to open task view: %s", error)
            return False

    if action_normalized == "browser forward":
        try:
            pyautogui.hotkey("alt", "right")
            return True
        except Exception as error:
            logger.error("Failed to navigate browser forward: %s", error)
            return False

    if action_normalized == "browser back":
        try:
            pyautogui.hotkey("alt", "left")
            return True
        except Exception as error:
            logger.error("Failed to navigate browser back: %s", error)
            return False

    if action_normalized == "browser search":
        try:
            pyautogui.hotkey("ctrl", "l")
            return True
        except Exception as error:
            logger.error("Failed to focus browser search: %s", error)
            return False

    if action_normalized == "screenshot":
        try:
            pyautogui.hotkey("win", "shift", "s")
            return True
        except Exception as error:
            logger.error("Failed to take screenshot: %s", error)
            return False

    logger.warning("Unsupported PC action: %s", action_name)
    return False
