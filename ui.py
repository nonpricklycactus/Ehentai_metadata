#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI dialogs for E-hentai metadata plugin."""

from __future__ import (unicode_literals, division, absolute_import, print_function)

try:
    from qt.core import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                         QLineEdit, QPushButton, QDialogButtonBox)
except ImportError:
    from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                  QLineEdit, QPushButton, QDialogButtonBox)

import re
from typing import Optional

__license__ = 'GPL v3'
__copyright__ = '2026, nonpricklycactus'


class AccurateLabelDialog(QDialog):
    """Dialog for entering E-hentai gallery URL for accurate tag fetching."""
    
    URL_PATTERN = re.compile(
        r'https?://(?:e-hentai\.org|exhentai\.org)/g/\d+/[a-f0-9]+/?'
    )
    
    def __init__(self, parent=None):
        super(AccurateLabelDialog, self).__init__(parent)
        self.setWindowTitle(_('Accurate Label - Enter Gallery URL'))
        self.setMinimumWidth(500)
        self._url = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # URL input row
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel(_('Gallery URL:')))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('https://e-hentai.org/g/123456/abcdef123/')
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _validate_and_accept(self):
        url = self.url_input.text().strip()
        if not url:
            return
        if not self.URL_PATTERN.match(url):
            # Invalid URL - could show error message here
            return
        self._url = url
        self.accept()
    
    def get_url(self) -> Optional[str]:
        """Return the entered URL if dialog was accepted."""
        return self._url


def _(text):
    """Placeholder for translation function."""
    return text
