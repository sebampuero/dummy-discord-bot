import os, re, os.path
import logging

class FileUtils():
    
    @classmethod
    def remove_files_in_dir(cls, path, pattern):
        for root, dirs, files in os.walk(path):
            for file in filter(lambda x: re.match(pattern, x), files):
                os.remove(os.path.join(root, file))

    @classmethod
    def delete_file(cls, filename: str):
        for x in range(30):
            try:
                os.remove(filename)
                logging.debug(f'File deleted: {filename}')
                return True
            except PermissionError as e:
                if e.winerror == 32:  # File is in use
                    logging.debug(f'Can\'t delete file, it is currently in use: {filename}')
            except FileNotFoundError:
                logging.warning(f'Could not find delete {filename} as it was not found. Skipping.', exc_info=True)
                return False
            except Exception:
                logging.error(f"Error trying to delete {filename}", exc_info=True)
                return False
        return False