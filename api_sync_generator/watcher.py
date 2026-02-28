import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .config import GeneratorConfig
from .extractor import extract_schema
from .parser import parse_schema
from .generator import generate_code

class BackendChangeHandler(FileSystemEventHandler):
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.last_run = time.time()
        
    def _run_generator(self):
        print("\nChange detected! Regenerating API client...")
        try:
            schema = extract_schema(self.config)
            parsed_data = parse_schema(schema, self.config)
            generate_code(parsed_data, self.config)
            print("Successfully regenerated APIs.")
        except Exception as e:
            print(f"Failed to regenerate APIs: {e}")

    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Debounce
        current_time = time.time()
        if current_time - self.last_run < 2:
            return
            
        if event.src_path.endswith(".py"):
            self.last_run = current_time
            self._run_generator()

def start_watcher(config: GeneratorConfig):
    # Run once at startup
    handler = BackendChangeHandler(config)
    handler._run_generator()
    
    observer = Observer()
    path_to_watch = os.getcwd() # Watch the current backend directory
    observer.schedule(handler, path_to_watch, recursive=True)
    
    print(f"\nWatching {path_to_watch} for Python changes...")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping watch mode.")
    observer.join()
