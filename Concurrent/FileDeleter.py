from Utils.FileUtils import FileUtils
from Concurrent.OurThread import OurThread
import time

class FileDeleterThread(OurThread):
    
    def __init__(self, name, path, pattern):
        super(FileDeleterThread, self).__init__()
        self.file_utils = FileUtils()
        self.name = name
        self.path = path
        self.pattern = pattern
        print(f"Init {self.name} thread")
    
    def run(self):
       # paths = ["./assets/audio/loquendo", "./assets/audio/streamings"]
        # pattern = "^\w+\.mp3$"
        self.file_utils.remove_files_in_dir(self.path, self.pattern)
            