import pyttsx3
import threading
import queue

# Global queue and worker thread
_speak_queue = queue.Queue()
_engine = pyttsx3.init()
_engine.setProperty('rate', 150)

# Try to select a female voice if available
voices = _engine.getProperty('voices')
for voice in voices:
    if "female" in voice.name.lower() or "zira" in voice.name.lower():
        _engine.setProperty('voice', voice.id)
        break

def _speech_worker():
    """Worker thread that processes text from the queue one by one."""
    while True:
        text = _speak_queue.get()  # Wait until something is in the queue
        if text is None:  # Shutdown signal
            break
        try:
            _engine.say(text)
            _engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            _speak_queue.task_done()

# Start worker thread
_worker_thread = threading.Thread(target=_speech_worker, daemon=True)
_worker_thread.start()

def speak(text):
    """Add text to the queue to be spoken sequentially."""
    _speak_queue.put(text)

def stop():
    """Stop the speech engine and worker thread."""
    _speak_queue.put(None)
    _worker_thread.join()
    _engine.stop()
