import os
import textwrap
import scipy
import ffmpeg
import numpy as np
import time
from functools import wraps


def clear_screen():
    """Clears the console screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_transcript(text):
    """Prints formatted transcript text."""
    wrapper = textwrap.TextWrapper(width=60)
    for line in wrapper.wrap(text="".join(text)):
        print(line)


def format_time(s):
    """Convert seconds (float) to SRT time format."""
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    seconds = int(s % 60)
    milliseconds = int((s - int(s)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def create_srt_file(segments, output_file):
    return
    with open(output_file, 'w', encoding='utf-8') as srt_file:
        segment_number = 1
        for segment in segments:
            start_time  = format_time(float(segment['start']))
            end_time = format_time(float(segment['end']))
            text = segment['text']

            srt_file.write(f"{segment_number}\n")
            srt_file.write(f"{start_time} --> {end_time}\n")
            srt_file.write(f"{text}\n\n")

            segment_number += 1


def resample(file: str, sr: int = 16000):
    """
    # https://github.com/openai/whisper/blob/7858aa9c08d98f75575035ecd6481f462d66ca27/whisper/audio.py#L22
    Open an audio file and read as mono waveform, resampling as necessary,
    save the resampled audio

    Args:
        file (str): The audio file to open
        sr (int): The sample rate to resample the audio if necessary

    Returns:
        resampled_file (str): The resampled audio file
    """
    try:
        # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
        # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
        out, _ = (
            ffmpeg.input(file, threads=0)
            .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=sr)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e
    np_buffer = np.frombuffer(out, dtype=np.int16)

    resampled_file = f"{file.split('.')[0]}_resampled.wav"
    scipy.io.wavfile.write(resampled_file, sr, np_buffer.astype(np.int16))
    return resampled_file




def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"* Function '{func.__name__}' executed in {execution_time:.4f} seconds")
        print(f"*** Result: {result}")
        return result
    return wrapper

LANGUAGE_CODE_TO_ID_MAPPING = {
    "en": 50259,
    "zh": 50260,
    "de": 50261,
    "es": 50262,
    "ru": 50263,
    "ko": 50264,
    "fr": 50265,
    "ja": 50266,
    "pt": 50267,
    "tr": 50268,
    "pl": 50269,
    "ca": 50270,
    "nl": 50271,
    "ar": 50272,
    "sv": 50273,
    "it": 50274,
    "id": 50275,
    "hi": 50276,
    "fi": 50277,
    "vi": 50278,
    "he": 50279,
    "uk": 50280,
    "el": 50281,
    "ms": 50282,
    "cs": 50283,
    "ro": 50284,
    "da": 50285,
    "hu": 50286,
    "ta": 50287,
    "no": 50288,
    "th": 50289,
    "ur": 50290,
    "hr": 50291,
    "bg": 50292,
    "lt": 50293,
    "la": 50294,
    "mi": 50295,
    "ml": 50296,
    "cy": 50297,
    "sk": 50298,
    "te": 50299,
    "fa": 50300,
    "lv": 50301,
    "bn": 50302,
    "sr": 50303,
    "az": 50304,
    "sl": 50305,
    "kn": 50306,
    "et": 50307,
    "mk": 50308,
    "br": 50309,
    "eu": 50310,
    "is": 50311,
    "hy": 50312,
    "ne": 50313,
    "mn": 50314,
    "bs": 50315,
    "kk": 50316,
    "sq": 50317,
    "sw": 50318,
    "gl": 50319,
    "mr": 50320,
    "pa": 50321,
    "si": 50322,
    "km": 50323,
    "sn": 50324,
    "yo": 50325,
    "so": 50326,
    "af": 50327,
    "oc": 50328,
    "ka": 50329,
    "be": 50330,
    "tg": 50331,
    "sd": 50332,
    "gu": 50333,
    "am": 50334,
    "yi": 50335,
    "lo": 50336,
    "uz": 50337,
    "fo": 50338,
    "ht": 50339,
    "ps": 50340,
    "tk": 50341,
    "nn": 50342,
    "mt": 50343,
    "sa": 50344,
    "lb": 50345,
    "my": 50346,
    "bo": 50347,
    "tl": 50348,
    "mg": 50349,
    "as": 50350,
    "tt": 50351,
    "haw": 50352,
    "ln": 50353,
    "ha": 50354,
    "ba": 50355,
    "jw": 50356,
    "su": 50357,
    "yue": 50358
}


def get_language_token(language):
    return LANGUAGE_CODE_TO_ID_MAPPING.get(language, 50259)