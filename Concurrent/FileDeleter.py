from Utils.FileUtils import FileUtils
from Concurrent.OurThread import OurThread
import time

class FileDeleterThread(OurThread):
    
    def __init__(self, name):
        super(FileDeleterThread, self).__init__()
        self.file_utils = FileUtils()
        self.name = name
        print(f"Init {self.name} thread")
    
    def run(self):
        while True:
            path = "./assets/audio/loquendo"
            pattern = "^\w+\.mp3$"
            self.file_utils.removeFilesInDir(path, pattern)
            time.sleep(86400)