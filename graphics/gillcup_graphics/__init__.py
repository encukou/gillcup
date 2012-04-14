"""Shiny graphical flashiness for Gillcup
"""

__version__ = '0.2.0-alpha.0'
__version_info__ = (0, 2, 0, 'alpha', 0)

from gillcup_graphics.objects import (
    GraphicsObject, Layer, DecorationLayer, Rectangle, Sprite, Text)
from gillcup_graphics.effectlayer import EffectLayer
from gillcup_graphics.mainwindow import Window, RealtimeClock, run
