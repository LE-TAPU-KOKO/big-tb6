import pytest
import os
import tempfile


def test_save_audio_to_wav_creates_valid_file():
    import numpy as np
    from tb_audio_tool import save_audio_to_wav

    sample_rate = 16000
    duration = 1
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16).tobytes()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name

    try:
        save_audio_to_wav(audio_data, sample_rate, temp_path)
        assert os.path.exists(temp_path)
        assert os.path.getsize(temp_path) > 44
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
