from faster_whisper import WhisperModel
import io
import torch
import soundfile as sf
import numpy as np
import librosa

# Initialize model with optimized settings for real-time transcription
# Determine device: prefer CUDA, then MPS (Apple Silicon), then CPU
if torch.cuda.is_available():
    device = "cuda"
    compute_type = "float16"
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    device = "cpu"  # faster-whisper doesn't support MPS directly, use CPU with optimized settings
    compute_type = "int8"
else:
    device = "cpu"
    compute_type = "int8"

asr_model = WhisperModel("base", device=device, compute_type=compute_type)

def transcribe_audio(audio_bytes):
    """
    Transcribe audio bytes in real-time using faster-whisper.
    Processes audio directly from bytes without writing to disk.
    """
    # Load audio from bytes
    audio_io = io.BytesIO(audio_bytes)
    audio_data, sample_rate = sf.read(audio_io)
    
    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Resample to 16kHz if needed (Whisper expects 16kHz)
    if sample_rate != 16000:
        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
        sample_rate = 16000
    
    # Convert to float32 (required by VAD model)
    audio_data = audio_data.astype(np.float32)
    
    # Transcribe with real-time optimized settings
    segments, info = asr_model.transcribe(
        audio_data,
        beam_size=1,  # Smaller beam for faster inference
        language="en",  # Specify language for faster processing
        task="transcribe",
        vad_filter=True,  # Voice activity detection for better real-time performance
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    # Collect all transcribed text
    text_parts = []
    for segment in segments:
        text_parts.append(segment.text)
    
    return " ".join(text_parts).strip()