import threading

class OurThread(threading.Thread):
    
    def __init__(self):
        super(OurThread, self).__init__()
        
    def run(self):
        print("On super thread class")