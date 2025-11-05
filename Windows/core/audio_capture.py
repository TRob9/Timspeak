"""
Audio Capture Module

Handles recording audio from microphone using sounddevice.
"""

import sounddevice as sd
import numpy as np
from typing import Optional, Callable
import threading
import queue


class AudioCapture:
    """Manages audio recording from microphone."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 chunk_size: int = 1024, device_index: Optional[int] = None):
        """
        Initialize audio capture.

        Args:
            sample_rate: Sample rate in Hz (default 16000 for Whisper)
            channels: Number of audio channels (1 for mono, 2 for stereo)
            chunk_size: Size of audio chunks to process
            device_index: Device index to use (None for default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device_index = device_index

        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recorded_chunks = []
        self.stream = None

    def list_devices(self):
        """
        List all available audio devices.

        Returns:
            List of available audio devices
        """
        return sd.query_devices()

    def start_recording(self):
        """Start recording audio from the microphone."""
        if self.is_recording:
            raise RuntimeError("Already recording")

        self.is_recording = True
        self.recorded_chunks = []

        # Start audio stream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            blocksize=self.chunk_size,
            device=self.device_index,
            callback=self._audio_callback
        )
        self.stream.start()

    def stop_recording(self) -> np.ndarray:
        """
        Stop recording and return the recorded audio.

        Returns:
            NumPy array of recorded audio samples (float32)
        """
        if not self.is_recording:
            raise RuntimeError("Not currently recording")

        self.is_recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Combine all recorded chunks into a single array
        if len(self.recorded_chunks) == 0:
            return np.array([], dtype=np.float32)

        audio_data = np.concatenate(self.recorded_chunks, axis=0)

        # Flatten to 1D if mono
        if self.channels == 1 and len(audio_data.shape) > 1:
            audio_data = audio_data.flatten()

        return audio_data

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback function for audio stream (called in a separate thread).

        Args:
            indata: Incoming audio data
            frames: Number of frames
            time_info: Time information
            status: Stream status
        """
        if status:
            print(f"Audio callback status: {status}")

        if self.is_recording:
            # Make a copy of the data and store it
            self.recorded_chunks.append(indata.copy())

    def get_volume_level(self) -> float:
        """
        Get current audio volume level (for visualization).

        Returns:
            Volume level as RMS (0.0 to 1.0 typically)
        """
        if len(self.recorded_chunks) > 0:
            latest_chunk = self.recorded_chunks[-1]
            rms = np.sqrt(np.mean(latest_chunk**2))
            return float(rms)
        return 0.0

    def cleanup(self):
        """Clean up audio resources."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.recorded_chunks = []
