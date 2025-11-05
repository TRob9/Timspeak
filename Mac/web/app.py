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
import subprocess
import shutil

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
            # Check if explicitly disabled in config
            if not provider_config.get('enabled', True):
                print(f"✗ LLM adapter disabled in config: {provider_name}")
                continue

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


def check_ollama_installed():
    """Check if Ollama is installed."""
    return shutil.which('ollama') is not None


def setup_ollama_interactive():
    """Interactive setup for Ollama."""
    print("\n" + "=" * 60)
    print("🤖 OLLAMA SETUP")
    print("=" * 60)

    # Check if Ollama is installed
    if not check_ollama_installed():
        print("\n❌ Ollama is not installed.")
        print("\nTo install Ollama:")
        print("  • Download: https://ollama.ai/download")
        print("  • Or run: brew install ollama")
        print("\nAfter installing, restart Timspeak.")
        return False

    print("\n✓ Ollama is installed!")

    # Check if Ollama server is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                print(f"\n✓ Ollama server is running with {len(models)} model(s)")
                for model in models:
                    print(f"  • {model.get('name', 'unknown')}")

                print("\n🔧 Ollama is ready but config may need updating.")
                choice = input("\nUpdate config.yaml to use Ollama? (y/n): ").strip().lower()
                if choice == 'y':
                    update_config_for_ollama(models[0].get('name', 'llama2'))
                    return True
                return False
    except:
        pass

    # Ollama not running or no models
    print("\n⚠️  Ollama server is not running or no models installed.")
    print("\nAvailable models:")
    print("  1. llama3.2 (2GB) - Fast, good for most tasks")
    print("  2. llama3 (4.7GB) - Better quality")
    print("  3. mistral (4.1GB) - Great for coding/tech")
    print("  4. deepseek-r1:7b (7GB) - Reasoning model, great for complex tasks")
    print("  5. llama2 (3.8GB) - Older but reliable")

    choice = input("\nDownload a model? Enter 1-5 (or 'n' to skip): ").strip()

    models = {
        '1': 'llama3.2',
        '2': 'llama3',
        '3': 'mistral',
        '4': 'deepseek-r1:7b',
        '5': 'llama2'
    }

    if choice in models:
        model_name = models[choice]
        print(f"\n📥 Downloading {model_name}... (this may take a few minutes)")

        try:
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                check=True,
                capture_output=False,
                text=True
            )

            print(f"\n✓ Successfully downloaded {model_name}!")

            # Update config.yaml
            update_config_for_ollama(model_name)

            # Check if server is running
            print("\n🚀 Starting Ollama server...")
            print("NOTE: Ollama server will run in the background.")

            try:
                # Start ollama serve in background
                subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                # Give it a moment to start
                import time
                time.sleep(2)

                print("✓ Ollama server started!")
                return True

            except Exception as e:
                print(f"⚠️  Couldn't start Ollama server automatically: {e}")
                print("\nPlease open a NEW terminal and run:")
                print("  ollama serve")
                return False

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Failed to download model: {e}")
            return False

    return False


def update_config_for_ollama(model_name='llama3'):
    """Update config.yaml to use Ollama."""
    global config

    # Update in-memory config
    if 'llm' not in config:
        config['llm'] = {}
    if 'providers' not in config['llm']:
        config['llm']['providers'] = {}
    if 'ollama' not in config['llm']['providers']:
        config['llm']['providers']['ollama'] = {}

    config['llm']['default'] = 'ollama'
    config['llm']['providers']['ollama']['enabled'] = True
    config['llm']['providers']['ollama']['model'] = model_name
    config['llm']['providers']['ollama']['base_url'] = 'http://localhost:11434'

    # Write to file
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"\n✓ Updated config.yaml to use Ollama with {model_name}")
    except Exception as e:
        print(f"\n⚠️  Couldn't update config.yaml: {e}")
        print("Please manually update config.yaml:")
        print(f"  llm.default: ollama")
        print(f"  llm.providers.ollama.model: {model_name}")


def setup_stt_interactive():
    """Interactive setup for STT adapters."""
    global config

    print("\n" + "=" * 60)
    print("🎤 SPEECH-TO-TEXT SETUP")
    print("=" * 60)

    print("\nAvailable STT engines:")
    print("  1. macOS Speech Recognition (Fast, free, built-in)")
    print("  2. Whisper Tiny (Fast, 75MB, works offline)")
    print("  3. Whisper Base (Better quality, 145MB, works offline)")
    print("  4. Skip for now")

    choice = input("\nChoose an option (1-4): ").strip()

    if choice == '1':
        print("\n📥 Setting up macOS Speech Recognition...")
        print("Installing dependencies...")
        try:
            subprocess.run(
                ['pip', 'install', '-q', 'SpeechRecognition', 'pyobjc-framework-Speech'],
                check=True
            )
            print("✓ macOS Speech Recognition is ready!")

            # Update config
            if 'stt' not in config:
                config['stt'] = {}
            if 'providers' not in config['stt']:
                config['stt']['providers'] = {}
            if 'macos_speech' not in config['stt']['providers']:
                config['stt']['providers']['macos_speech'] = {}

            config['stt']['default'] = 'macos_speech'
            config['stt']['providers']['macos_speech']['enabled'] = True

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install: {e}")
            return False

    elif choice == '2' or choice == '3':
        model_size = 'tiny' if choice == '2' else 'base'
        model_mb = '75MB' if choice == '2' else '145MB'

        print(f"\n📥 Installing Whisper {model_size} ({model_mb})...")
        print("This will download the model on first use.")

        try:
            subprocess.run(
                ['pip', 'install', 'openai-whisper'],
                check=True
            )
            print(f"✓ Whisper {model_size} is ready!")

            # Update config
            if 'stt' not in config:
                config['stt'] = {}
            if 'providers' not in config['stt']:
                config['stt']['providers'] = {}
            if 'whisper_local' not in config['stt']['providers']:
                config['stt']['providers']['whisper_local'] = {}

            config['stt']['default'] = 'whisper_local'
            config['stt']['providers']['whisper_local']['enabled'] = True
            config['stt']['providers']['whisper_local']['model'] = model_size

            # Save config
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install: {e}")
            return False

    return False


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

    # Check what's missing and offer setup
    needs_setup = False

    if not stt_adapters:
        needs_setup = True
        # Try interactive STT setup
        if setup_stt_interactive():
            print("\n🔄 Reinitializing adapters with STT...")
            init_adapters()

        if not stt_adapters:
            print("\n⚠️  WARNING: No STT adapters available!")
            print("You'll need to install one manually later.")
    else:
        # Have STT but offer to add more
        print(f"\n✓ {len(stt_adapters)} STT adapter(s) loaded")
        choice = input("Add another STT engine? (y/n): ").strip().lower()
        if choice == 'y':
            if setup_stt_interactive():
                print("\n🔄 Reinitializing adapters...")
                init_adapters()

    if not llm_adapters:
        needs_setup = True
        # Try interactive Ollama setup
        if setup_ollama_interactive():
            print("\n🔄 Reinitializing adapters with Ollama...")
            init_adapters()

        if not llm_adapters:
            print("\n" + "=" * 60)
            print("⚠️  NO LLM ADAPTERS AVAILABLE!")
            print("=" * 60)
            print("\n📝 Alternative: Add API keys to config.yaml")
            print("   - Anthropic Claude: https://console.anthropic.com")
            print("   - OpenAI GPT: https://platform.openai.com")
            print("\n" + "=" * 60)
            input("\nPress Enter to continue (Timspeak will start but won't work until you set up an LLM)...")
            print()
    else:
        # Have LLM but offer to add more
        print(f"\n✓ {len(llm_adapters)} LLM adapter(s) loaded")
        choice = input("Add another LLM provider? (y/n): ").strip().lower()
        if choice == 'y':
            if setup_ollama_interactive():
                print("\n🔄 Reinitializing adapters...")
                init_adapters()

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
