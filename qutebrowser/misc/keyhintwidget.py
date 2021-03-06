# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2016 Ryan Roden-Corrent (rcorre) <ryan@rcorre.net>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Small window that pops up to show hints for possible keystrings.

When a user inputs a key that forms a partial match, this shows a small window
with each possible completion of that keystring and the corresponding command.
It is intended to help discoverability of keybindings.
"""

import html

from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt

from qutebrowser.config import config, style
from qutebrowser.utils import objreg, utils


class KeyHintView(QLabel):

    """The view showing hints for key bindings based on the current key string.

    Attributes:
        _win_id: Window ID of parent.
        _enabled: If False, do not show the window at all

    Signals:
        reposition_keyhint: Emitted when this widget should be resized.
    """

    STYLESHEET = """
        QLabel {
            font: {{ font['keyhint'] }};
            color: {{ color['keyhint.fg'] }};
            background-color: {{ color['keyhint.bg'] }};
            padding: 6px;
            border-top-right-radius: 6px;
        }
    """

    reposition_keyhint = pyqtSignal()

    def __init__(self, win_id, parent=None):
        super().__init__(parent)
        self.setTextFormat(Qt.RichText)
        self._win_id = win_id
        self.set_enabled()
        cfg = objreg.get('config')
        cfg.changed.connect(self.set_enabled)
        style.set_register_stylesheet(self)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.hide()

    def __repr__(self):
        return utils.get_repr(self, win_id=self._win_id)

    @config.change_filter('ui', 'show-keyhints')
    def set_enabled(self):
        """Update self._enabled when the config changed."""
        self._enabled = config.get('ui', 'show-keyhints')
        if not self._enabled:
            self.hide()

    def showEvent(self, e):
        """Adjust the keyhint size when it's freshly shown."""
        self.reposition_keyhint.emit()
        super().showEvent(e)

    @pyqtSlot(str)
    def update_keyhint(self, modename, prefix):
        """Show hints for the given prefix (or hide if prefix is empty).

        Args:
            prefix: The current partial keystring.
        """
        if not prefix or not self._enabled:
            self.hide()
            return

        self.show()
        suffix_color = html.escape(config.get('colors', 'keyhint.fg.suffix'))

        text = ''
        keyconf = objreg.get('key-config')
        # this is only fired in normal mode
        for key, cmd in keyconf.get_bindings_for(modename).items():
            # for now, special keys can't be part of keychains, so ignore them
            is_special_binding = key.startswith('<') and key.endswith('>')
            if key.startswith(prefix) and not is_special_binding:
                text += (
                    "<tr>"
                    "<td>{}</td>"
                    "<td style='color: {}'>{}</td>"
                    "<td style='padding-left: 2ex'>{}</td>"
                    "</tr>"
                ).format(
                    html.escape(prefix),
                    suffix_color,
                    html.escape(key[len(prefix):]),
                    html.escape(cmd)
                )
        text = '<table>{}</table>'.format(text)

        self.setText(text)
        self.adjustSize()
        self.reposition_keyhint.emit()
