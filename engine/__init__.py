"""
Engine package containing sprite management, speech bubble renderer,
physics calculations, command routing, autonomy, and the main Mascot coordinator.
"""
from engine.sprite_manager import SpriteManager
from engine.speech_bubble import SpeechBubbleManager, create_bubble_image
from engine.physics import MascotPhysics
from engine.command_router import CommandRouter
from engine.autonomy import AutonomyManager
from engine.actions import MascotActions
from engine.context_menu import MascotContextMenu
from engine.mascot import Shimeji

__all__ = [
    "SpriteManager",
    "SpeechBubbleManager",
    "create_bubble_image",
    "MascotPhysics",
    "CommandRouter",
    "AutonomyManager",
    "MascotActions",
    "MascotContextMenu",
    "Shimeji"
]
