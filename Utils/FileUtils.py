from Utils.LoggerSaver import *
import os, re, os.path
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class FileUtils():
    
    @classmethod
    def remove_files_in_dir(cls, path, pattern):
        for root, dirs, files in os.walk(path):
            for file in filter(lambda x: re.match(pattern, x), files):                
                cls.delete_file(os.path.join(root, file))

    @classmethod
    def delete_file(cls, filename: str):
        for x in range(30):
            try:
                os.remove(filename)
                logger.debug(f'File deleted: {filename}')
                return True
            except PermissionError as e:
                if e.winerror == 32:  # File is in use
                    logger.debug(f'Can\'t delete file, it is currently in use: {filename}')
            except FileNotFoundError:
                logger.warning(f'Could not find delete {filename} as it was not found. Skipping.', exc_info=True)
                return False
            except Exception:
                log = f"Error trying to delete {filename}"
                logger.error(log, exc_info=True)
                LoggerSaver.save_log(log, WhatsappLogger())
                return False
        return False