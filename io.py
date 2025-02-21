import os
from typing import Any, Dict, Optional, Tuple, Union

import torch
import torchaudio as ta
from loguru import logger
from numpy import ndarray
from torch import Tensor
from torchaudio import AudioMetaData

from df.logger import warn_once
from df.utils import download_file, get_cache_dir, get_git_root


def load_audio(
    audio_bytes: bytes, sr: Optional[int] = None, verbose=True, **kwargs
) -> Tuple[Tensor, AudioMetaData]:
    """Loads an audio buffer using torchaudio.

    Args:
        audio_bytes (bytes): Raw audio bytes.
        sr (int): Optionally resample audio to specified target sampling rate.
        **kwargs: Passed to torchaudio.load(). Depends on the backend. The resample method
            may be set via `method` which is passed to `resample()`.

    Returns:
        audio (Tensor): Audio tensor of shape [C, T], if channels_first=True (default).
        info (AudioMetaData): Meta data of the original audio file. Contains the original sr.
    """

    audio_tensor = torch.as_tensor(torch.frombuffer(audio_bytes, dtype=torch.float32).unsqueeze_(0))

    # Assuming the original sample rate is known or can be set
    orig_sr = 24000  # Set this to the original sample rate of the audio chunk

    # Proceed with existing logic for resampling if needed
    if sr is not None and orig_sr != sr:
        if verbose:
            warn_once(
                f"Audio sampling rate does not match model sampling rate ({orig_sr}, {sr}). "
                "Resampling..."
            )
        audio_tensor = resample(audio_tensor, orig_sr, sr, **kwargs)

    # Create AudioMetaData with dummy values for num_frames and num_channels
    num_frames = audio_tensor.size(1)
    num_channels = audio_tensor.size(0)
    info = AudioMetaData(num_frames=num_frames, num_channels=num_channels, bits_per_sample=32, encoding='PCM_S', sample_rate=48_000)

    return audio_tensor.contiguous(), info


def save_audio(
    file: str,
    audio: Union[Tensor, ndarray],
    sr: int,
    output_dir: Optional[str] = None,
    suffix: Optional[str] = None,
    log: bool = False,
    dtype=torch.int16,
):
    outpath = file
    if suffix is not None:
        file, ext = os.path.splitext(file)
        outpath = file + f"_{suffix}" + ext
    if output_dir is not None:
        outpath = os.path.join(output_dir, os.path.basename(outpath))
    if log:
        logger.info(f"Saving audio file '{outpath}'")
    audio = torch.as_tensor(audio)
    if audio.ndim == 1:
        audio.unsqueeze_(0)
    if dtype == torch.int16 and audio.dtype != torch.int16:
        audio = (audio * (1 << 15)).to(torch.int16)
    if dtype == torch.float32 and audio.dtype != torch.float32:
        audio = audio.to(torch.float32) / (1 << 15)
    ta.save(outpath, audio, sr)


try:
    from torchaudio.functional import resample as ta_resample
except ImportError:
    from torchaudio.compliance.kaldi import resample_waveform as ta_resample  # type: ignore


def get_resample_params(method: str) -> Dict[str, Any]:
    params = {
        "sinc_fast": {"resampling_method": "sinc_interp_hann", "lowpass_filter_width": 16},
        "sinc_best": {"resampling_method": "sinc_interpolation", "lowpass_filter_width": 64},
        "kaiser_fast": {
            "resampling_method": "kaiser_window",
            "lowpass_filter_width": 16,
            "rolloff": 0.85,
            "beta": 8.555504641634386,
        },
        "kaiser_best": {
            "resampling_method": "kaiser_window",
            "lowpass_filter_width": 16,
            "rolloff": 0.9475937167399596,
            "beta": 14.769656459379492,
        },
    }
    assert method in params.keys(), f"method must be one of {list(params.keys())}"
    return params[method]


def resample(audio: Tensor, orig_sr: int, new_sr: int, method="sinc_fast"):
    params = get_resample_params(method)
    return ta_resample(audio, orig_sr, new_sr, **params)


def get_test_sample(sr: int = 48000) -> Tensor:
    dir = get_git_root()
    file_path = os.path.join("assets", "clean_freesound_33711.wav")
    if dir is None:
        url = "https://github.com/Rikorose/DeepFilterNet/raw/main/" + file_path
        save_dir = get_cache_dir()
        path = download_file(url, save_dir)
    else:
        path = os.path.join(dir, file_path)
    sample, _ = load_audio(path, sr=sr)
    return sample
