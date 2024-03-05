import threading

class LockedFunction:
    def __init__(self, func, *params):
        self.func = func
        self.lock = threading.Lock() #Semaphore
        self.params = params
        self.result = None
        self.exception = None
        self.thread = threading.Thread(target=self.exec)

        #Ensure that lock is locked for upcoming wait() call
        self.lock.acquire(blocking=False)
        
    def exec(self):
        try:
            self.result = self.func(*self.params)
        except Exception as e:
            self.exception = e
        finally:
            self.lock.release()

    def wait(self):
        self.lock.acquire()
        return self.result

    def start(self):
        self.thread.start()