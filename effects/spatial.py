import sys
from typing import Optional, Union
import logging as _logging

_LOGGER = _logging.getLogger(__name__)
# -------------------------------------------------------------------------
class SpatialEffects:
    def __init__(self):
        pass

    @classmethod
    def sine_warp(cls, text: str, amplitude: float = 3.0, frequency: float = 1.0) -> str:
        """Shift each row horizontally by a sine offset based on its row index."""
        # Implement here
        _LOGGER.info('sine_warp called with params: %s', (amplitude, frequency))
        return ''
    
    @classmethod
    def perspective_tilt(cls, text: str, strength: float = 0.3, direction: str = 'top') -> str:
        """Fake perspective/vanishing-point effect by scaling row widths."""
        # Implement here
        _LOGGER.info('perspective_tilt called with params: %s', (strength, direction))
        return ''
    
    @classmethod
    def shear(cls, text: str, amount: float = 0.5, direction: str = 'right') -> str:
        """Italic/oblique shear — each row offset horizontally by amount * row_idx."""
        # Implement here
        _LOGGER.info('shear called with params: %s', (amount, direction))
        return ''
