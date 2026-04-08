import sys
import os
from unittest.mock import MagicMock
import types
import pytest
import math

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''

# Helper to ensure all parts of a module path exist as mock modules
def mock_deep_module(name):
    parts = name.split('.')
    for i in range(1, len(parts) + 1):
        mod_path = '.'.join(parts[:i])
        if mod_path not in sys.modules:
            m = types.ModuleType(mod_path)
            sys.modules[mod_path] = m
        if i > 1:
            parent = sys.modules['.'.join(parts[:i-1])]
            if isinstance(parent, types.ModuleType):
                setattr(parent, parts[i-1], sys.modules[mod_path])

mock_modules = [
    'google.cloud.firestore',
    'google.cloud.storage',
    'firebase_admin',
    'numpy',
    'reportlab.lib.pagesizes',
    'reportlab.lib.colors',
    'reportlab.lib.units',
    'reportlab.pdfgen.canvas',
    'reportlab.graphics',
    'pyloudnorm',
    'librosa',
    'soundfile',
    'mutagen.mp3',
    'mutagen.id3',
]

for mod in mock_modules:
    mock_deep_module(mod)

# Setup reportlab specifically
import reportlab.lib.pagesizes
reportlab.lib.pagesizes.letter = (612.0, 792.0)

import reportlab.pdfgen.canvas
import reportlab.pdfgen
reportlab.pdfgen.canvas = sys.modules['reportlab.pdfgen.canvas']
reportlab.pdfgen.canvas.Canvas = MagicMock()

# Setup numpy
import numpy as np
np.nan = float('nan')
np.inf = float('inf')
np.newaxis = None
np.isfinite = lambda x: math.isfinite(x)

class MockArray(list):
    @property
    def ndim(self):
        return 2 if len(self) > 0 and isinstance(self[0], list) else 1
    @property
    def shape(self):
        if self.ndim == 2:
            return (len(self), len(self[0]))
        return (len(self),)
    @property
    def T(self):
        return self.transpose()
    def transpose(self):
        if self.ndim == 2:
            return MockArray([list(i) for i in zip(*self)])
        return self
    def reshape(self, *args):
        return self
    def __getitem__(self, item):
        if isinstance(item, tuple):
            if len(item) == 2 and item[0] == slice(None) and item[1] is None:
                return MockArray([[i] for i in self])
        return super().__getitem__(item)

np.array = MagicMock(side_effect=lambda x, **kwargs: MockArray(x))

# Setup librosa
import librosa
librosa.load = MagicMock()

# Setup pyloudnorm
import pyloudnorm
pyloudnorm.Meter = MagicMock()

# Setup other mocks
import google.cloud.firestore
google.cloud.firestore.Client = MagicMock()
import google.cloud.storage
google.cloud.storage.Client = MagicMock()
import firebase_admin
firebase_admin.initialize_app = MagicMock()

# Mock pytest-mock fixture
@pytest.fixture
def mocker():
    from unittest import mock
    class Mocker:
        def patch(self, target, *args, **kwargs):
            p = mock.patch(target, *args, **kwargs)
            return p.start()
        def MagicMock(self, *args, **kwargs):
            return mock.MagicMock(*args, **kwargs)
    return Mocker()
