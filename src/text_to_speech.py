from gtts import gTTS
import io
import numpy as np
import librosa
import asyncio

async def synthesize_speech(text, lang='en', slow=False):
    """
    Synthesize speech from text using Google Text-to-Speech (gTTS).

    Args:
        text: Text to convert to speech
        lang: Language code (default: 'en')
        slow: Whether to speak slowly (default: False)

    Returns:
        numpy array of audio data (float32, 16kHz sample rate)
    """
    # Run the synchronous speech synthesis in a thread pool
    audio_data = await asyncio.to_thread(_synthesize_speech_sync, text, lang, slow)
    return audio_data

def _synthesize_speech_sync(text, lang='en', slow=False):
    """Synchronous helper function for speech synthesis."""
    # Generate speech using gTTS
    tts = gTTS(text=text, lang=lang, slow=slow)

    # Save to BytesIO buffer
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    # Load MP3 directly using librosa (handles conversion internally)
    # librosa will resample to sr=16000 by default, or you can specify
    audio_data, sample_rate = librosa.load(audio_buffer, sr=16000, mono=True)

    # Convert to float32 numpy array (matching the expected format)
    return audio_data.astype(np.float32)
