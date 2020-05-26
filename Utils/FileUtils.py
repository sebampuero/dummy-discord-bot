import os, re, os.path

class FileUtils():
    
    @classmethod
    def remove_files_in_dir(cls, path, pattern):
        for root, dirs, files in os.walk(path):
            for file in filter(lambda x: re.match(pattern, x), files):
                os.remove(os.path.join(root, file))

    @classmethod
    def save_file_in_dir(cls, path, file_name):
        pass