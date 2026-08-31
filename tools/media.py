from datetime import datetime
from pathlib import Path
import wave


VOICE_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "voice"
)

VOICE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def record_microphone(
    seconds=6,
):
    """
    Records microphone audio and returns:
        (wav_path, transcript)
    """

    import speech_recognition as sr

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.5,
        )

        audio = recognizer.listen(
            source,
            timeout=10,
            phrase_time_limit=seconds,
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    wav_path = (
        VOICE_DIR
        / f"voice_{timestamp}.wav"
    )

    wav_path.write_bytes(
        audio.get_wav_data()
    )

    transcript = ""

    try:

        transcript = recognizer.recognize_google(
            audio
        )

    except sr.UnknownValueError:

        transcript = ""

    except sr.RequestError as exc:

        transcript = (
            f"[Speech recognition unavailable: {exc}]"
        )

    return wav_path, transcript


def save_audio_copy(
    source,
    destination_dir,
):
    import shutil

    source_path = (
        Path(source)
        .expanduser()
        .resolve()
    )

    destination_dir = Path(
        destination_dir
    ).resolve()

    destination_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    target = (
        destination_dir
        / f"{stamp}_{source_path.name}"
    )

    shutil.copy2(
        source_path,
        target
    )

    return target