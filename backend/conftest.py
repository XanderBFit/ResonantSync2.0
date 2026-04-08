import sys
import os
from unittest.mock import MagicMock

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''

# Mock dependencies that might be missing in some environments
mock_modules = [
    'google',
    'google.cloud',
    'google.cloud.firestore',
    'google.cloud.storage',
    'firebase_admin',
    'numpy',
    'librosa',
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.pdfgen',
    'mutagen',
    'mutagen.mp3',
    'mutagen.id3',
    'ffmpeg',
    'pyloudnorm',
    'soundfile',
]

for module in mock_modules:
    # Use a real-ish Mock for numpy if it doesn't exist
    if module == 'numpy':
        import math
        mock_np = MagicMock()
        mock_np.newaxis = None
        mock_np.inf = float('inf')
        mock_np.nan = float('nan')
        mock_np.isfinite.side_effect = lambda x: math.isfinite(float(x)) if not isinstance(x, MagicMock) else True
        mock_np.round = round
        def mock_array(x):
            class MockArray(MagicMock):
                pass

            def create_mock_array(shape):
                m = MockArray()
                m.shape = shape
                m.ndim = len(shape)
                def getitem(key):
                    if key is None:
                        return create_mock_array((1,) + m.shape)
                    if isinstance(key, tuple):
                        new_shape = []
                        it = iter(m.shape)
                        for k in key:
                            if k is None:
                                new_shape.append(1)
                            elif k is Ellipsis:
                                for s in it:
                                    new_shape.append(s)
                            elif isinstance(k, slice):
                                try:
                                    next(it)
                                    new_shape.append(3) # dummy
                                except StopIteration: pass
                            else:
                                try: next(it)
                                except StopIteration: pass
                        for s in it:
                            new_shape.append(s)
                        return create_mock_array(tuple(new_shape))
                    return m
                m.__getitem__.side_effect = getitem
                m.__eq__.side_effect = lambda o: m.shape == o if isinstance(o, tuple) else True
                return m

            if isinstance(x, list) and len(x) > 0 and isinstance(x[0], list):
                m = create_mock_array((len(x), len(x[0])))
                m.T = create_mock_array((len(x[0]), len(x)))
            else:
                m = create_mock_array((len(x),))
            m.__array__ = lambda *args, **kwargs: x
            return m
        mock_np.array.side_effect = mock_array
        sys.modules[module] = mock_np
    else:
        sys.modules[module] = MagicMock()

# Set up specific mocks for reportlab to avoid import errors
import reportlab.lib.pagesizes
reportlab.lib.pagesizes.letter = (612, 792)

import mutagen.id3
mutagen.id3.ID3NoHeaderError = type('ID3NoHeaderError', (Exception,), {})
