'''
Null Lottie provider
====================

A no-op fallback used when no functional Lottie provider is available.
It silently accepts all :class:`~kivy.core.lottie.LottieBase` calls and
produces no output, allowing application code that depends on
:class:`~kivy.core.lottie.Lottie` to import and run without errors.

.. versionadded:: 3.0.0
'''

__all__ = ('LottieNull',)

from kivy.core.lottie import LottieBase
from kivy.logger import Logger


class LottieNull(LottieBase):
    '''Lottie provider that does nothing.

    Used as a last-resort fallback when ``thorvg-python`` (or any other
    real provider) is not installed.  All DOM API methods return safe
    "no-op" values matching the documented return types of
    :class:`~kivy.core.lottie.LottieBase`.
    '''

    def load(self):
        Logger.warning(
            'LottieNull: no Lottie provider available; '
            f'<{self._filename}> will not be rendered. '
            'Install thorvg-python: pip install thorvg-python')

    # ------------------------------------------------------------------
    # Tier 1: Segments and markers (no-ops)
    # ------------------------------------------------------------------

    @property
    def markers(self):
        return []

    def play_segment(self, begin, end):
        pass

    def play_marker(self, name):
        pass

    # ------------------------------------------------------------------
    # Slot overrides (no-ops)
    # ------------------------------------------------------------------

    @property
    def slots(self):
        return frozenset()

    def apply_slot(self, slot_data):
        return None

    def reset_slot(self, slot_id=None):
        pass

    # ------------------------------------------------------------------
    # Tier 3: Rendering quality (no-op)
    # ------------------------------------------------------------------

    def set_quality(self, value):
        pass
