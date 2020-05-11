import os, re, os.path

class FileUtils():
    
    def __init__(self):
        pass
    
    def removeFilesInDir(self, path, pattern):
        for root, dirs, files in os.walk(path):
            for file in filter(lambda x: re.match(pattern, x), files):
                os.remove(os.path.join(root, file))