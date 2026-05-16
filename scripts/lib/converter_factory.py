"""
Registry and factory for target-format converters.

Provides a single entry point ``get_converter`` that maps short target
names to the correct Converter subclass instance.
"""

from scripts.lib.claude_code import ClaudeCodeConverter
from scripts.lib.opencode import OpencodeConverter
from scripts.lib.qwen import QwenConverter
from scripts.lib.gemini import GeminiConverter
from scripts.lib.pi import PiConverter
from scripts.lib.converter import Converter

_registry: dict[str, Converter] = {
    "claude": ClaudeCodeConverter(),
    "opencode": OpencodeConverter(),
    "qwen": QwenConverter(),
    "gemini": GeminiConverter(),
    "pi": PiConverter(),
}


def get_converter(shortname: str) -> Converter:
    """Return a Converter instance for the given target shortname.

    Args:
        shortname: One of ``"claude"``, ``"opencode"``, ``"qwen"``,
                   ``"gemini"``, ``"pi"``.

    Returns:
        A Converter instance whose type matches *shortname*.

    Raises:
        KeyError: If *shortname* is not a known target.
    """
    return _registry[shortname]
