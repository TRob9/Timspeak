"""
Timspeak Flask Web Application

Provides web interface for recording, transcribing, and cleaning dictation.
"""

from flask import Flask, render_template, request, jsonify
import yaml
import os
import sys
import threading
import pyperclip

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.audio_capture import AudioCapture
from adapters.stt.whisper_local import WhisperLocalAdapter
from adapters.stt.whisper_fast import WhisperFastAdapter
from adapters.stt.whisper_cloud import WhisperCloudAdapter
from adapters.stt.google_cloud import GoogleCloudAdapter
from adapters.stt.macos_speech import MacOSSpeechAdapter
from adapters.llm.litellm_adapter import LiteLLMAdapter


app = Flask(__name__)

# Global state
audio_capture = None
config = None
stt_adapters = {}
llm_adapters = {}
current_recording = None


def load_config():
    """Load configuration from config.yaml."""
    global config
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')

    if not os.path.exists(config_path):
        print("WARNING: config.yaml not found. Using config.yaml.example")
        config_path = config_path + '.example'

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def init_adapters():
    """Initialize all STT and LLM adapters."""
    global stt_adapters, llm_adapters, audio_capture

    # Initialize audio capture
    audio_config = config.get('audio', {})
    audio_capture = AudioCapture(
        sample_rate=audio_config.get('sample_rate', 16000),
        channels=audio_config.get('channels', 1),
        chunk_size=audio_config.get('chunk_size', 1024),
        device_index=audio_config.get('device_index')
    )

    # Initialize STT adapters
    stt_config = config.get('stt', {}).get('providers', {})
    cleaning_prompt = config.get('cleaning_prompt', '')

    adapter_classes = {
        'whisper_local': WhisperLocalAdapter,
        'whisper_fast': WhisperFastAdapter,
        'whisper_cloud': WhisperCloudAdapter,
        'google_cloud': GoogleCloudAdapter,
        'macos_speech': MacOSSpeechAdapter,
    }

    for name, adapter_class in adapter_classes.items():
        if name in stt_config:
            try:
                adapter = adapter_class(stt_config[name])
                if adapter.is_available() and adapter.enabled:
                    stt_adapters[name] = adapter
                    print(f"✓ STT adapter loaded: {adapter.get_name()}")
                else:
                    print(f"✗ STT adapter disabled or unavailable: {name}")
            except Exception as e:
                print(f"✗ Failed to load STT adapter {name}: {e}")

    # Initialize LLM adapters
    llm_config = config.get('llm', {}).get('providers', {})

    for provider_name, provider_config in llm_config.items():
        try:
            adapter = LiteLLMAdapter(provider_name, provider_config, cleaning_prompt)
            if adapter.is_available():
                llm_adapters[provider_name] = adapter
                print(f"✓ LLM adapter loaded: {adapter.get_name()}")
            else:
                print(f"✗ LLM adapter unavailable: {provider_name}")
        except Exception as e:
            print(f"✗ Failed to load LLM adapter {provider_name}: {e}")


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get current status and available adapters."""
    return jsonify({
        'stt_adapters': {name: adapter.get_name() for name, adapter in stt_adapters.items()},
        'llm_adapters': {name: adapter.get_name() for name, adapter in llm_adapters.items()},
        'default_stt': config.get('stt', {}).get('default', 'whisper_fast'),
        'default_llm': config.get('llm', {}).get('default', 'claude'),
        'is_recording': audio_capture.is_recording if audio_capture else False
    })


@app.route('/api/record/start', methods=['POST'])
def api_record_start():
    """Start recording audio."""
    try:
        if audio_capture.is_recording:
            return jsonify({'error': 'Already recording'}), 400

        audio_capture.start_recording()
        return jsonify({'success': True, 'message': 'Recording started'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/record/stop', methods=['POST'])
def api_record_stop():
    """Stop recording and process audio."""
    try:
        if not audio_capture.is_recording:
            return jsonify({'error': 'Not recording'}), 400

        # Get STT and LLM selections from request
        data = request.json or {}
        stt_name = data.get('stt_adapter', config.get('stt', {}).get('default'))
        llm_name = data.get('llm_adapter', config.get('llm', {}).get('default'))

        # Stop recording
        audio_data = audio_capture.stop_recording()

        if len(audio_data) == 0:
            return jsonify({'error': 'No audio recorded'}), 400

        # Start async processing
        def process_audio():
            global current_recording
            try:
                # Transcribe
                if stt_name not in stt_adapters:
                    raise ValueError(f"STT adapter '{stt_name}' not available")

                stt_adapter = stt_adapters[stt_name]
                original_text = stt_adapter.transcribe(audio_data, audio_capture.sample_rate)

                # Clean with LLM
                if llm_name not in llm_adapters:
                    raise ValueError(f"LLM adapter '{llm_name}' not available")

                llm_adapter = llm_adapters[llm_name]
                cleaned_text = llm_adapter.clean_text(original_text)

                # Copy to clipboard
                pyperclip.copy(cleaned_text)

                current_recording = {
                    'original': original_text,
                    'cleaned': cleaned_text,
                    'stt_used': stt_adapter.get_name(),
                    'llm_used': llm_adapter.get_name(),
                    'status': 'complete'
                }

            except Exception as e:
                current_recording = {
                    'error': str(e),
                    'status': 'error'
                }

        # Run in background thread
        thread = threading.Thread(target=process_audio, daemon=True)
        thread.start()

        return jsonify({'success': True, 'message': 'Processing audio...'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/result')
def api_result():
    """Get the latest processing result."""
    global current_recording
    if current_recording is None:
        return jsonify({'status': 'waiting'})
    return jsonify(current_recording)


@app.route('/api/clear', methods=['POST'])
def api_clear():
    """Clear the current result."""
    global current_recording
    current_recording = None
    return jsonify({'success': True})


def main():
    """Main entry point."""
    print("=" * 60)
    print("Timspeak - AI-Powered Dictation System")
    print("=" * 60)

    # Load configuration
    print("\nLoading configuration...")
    load_config()

    # Initialize adapters
    print("\nInitializing adapters...")
    init_adapters()

    if not stt_adapters:
        print("\n⚠️  WARNING: No STT adapters available!")
        print("Install at least one: pip install openai-whisper faster-whisper")

    if not llm_adapters:
        print("\n⚠️  WARNING: No LLM adapters available!")
        print("Configure API keys in config.yaml")

    # Start Flask server
    web_config = config.get('web', {})
    host = web_config.get('host', '127.0.0.1')
    port = web_config.get('port', 5000)
    debug = web_config.get('debug', False)

    print("\n" + "=" * 60)
    print(f"Starting web server at http://{host}:{port}")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()
