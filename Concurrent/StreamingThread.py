from Concurrent.OurThread import OurThread
from Utils.NetworkUtils import NetworkUtils

class StreamingThread(OurThread):
    
    def __init__(self, name):
        super(StreamingThread, self).__init__()
        print(f"Init {name} thread")
        self.network_utils = NetworkUtils()
        
    def setUrl(self, url):
        self.url = url
        
    def stop(self):
        self.network_utils.setStreamingFlag(False)
        
    def run(self):
        self.network_utils.setStreamingFlag(True)
        self.network_utils.startMp3StreamingDownload(self.url)