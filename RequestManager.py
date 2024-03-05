import time
import threading
from LockedFunction import LockedFunction
from typing import Callable

class RequestManager:
    def __init__(self, max_task : int = 5, period : float = 1.0, tasks = []):
        self.keepRunning = False
        self.loopingThread = None
        self.max_task = max_task
        self.period = period
        self.tasks = tasks[:]

    def execQuery(self, func : Callable, *params):
        # Initialize waitable function
        callable = LockedFunction(func, *params)

        # Add function to running loop
        self.tasks.append(callable)

        # Wait for function to finish
        result = callable.wait()

        # Check for exception and propagate exception if any
        if callable.exception is not None:
            raise callable.exception
        return result

    def start(self):
        if self.keepRunning:
            raise RuntimeError("Attempted to start looping thread while it is running")
        
        self.keepRunning = True
        self.loopingThread = threading.Thread(target=self.loop)
        self.loopingThread.start()

    def stop(self):
        if not self.keepRunning:
            raise RuntimeError("Attempted to stop looping thread while it was stopped")
        
        self.keepRunning = False
        self.loopingThread = None

    def getMaxTask(self) -> int:
        return self.max_task

    def setMaxTask(self, max_task : int):
        if max_task <= 0:
            raise ValueError(f"max_task shall be greater than 0 : got '{max_task}'")
        self.max_task = max_task

    def getPeriod(self) -> float:
        return self.period
    
    def setPeriod(self, period : float):
        self.period = period
    
    def loop(self):
        while self.keepRunning:
            tasks_to_run = self.tasks[:self.max_task]
            self.tasks = self.tasks[self.max_task:]

            for task in tasks_to_run:
                task.start()

            time.sleep(self.period)

    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.keepRunning:
            self.stop()
        
        #Propagate exception if any by returning False
        # See PEP343
        return False

#Test
if __name__ == "__main__":
    import concurrent.futures

    #Class for testing purpose
    class Server:
        def __init__(self, max_rate = 1/5):
            self.start = time.time()
            self.max_rate = max_rate
            self.queries = 0

        def query(self):
            self.queries += 1
            time.sleep(0.1)
            return self.getQueryPerSeconds()

        def getQueryPerSeconds(self):
            try:
                return self.queries / (time.time() - self.start)
            except ZeroDivisionError:
                return -1
                
    s = Server()
    with RequestManager() as rq:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(rq.execQuery, s.query) for _ in range(100)]

            for future in concurrent.futures.as_completed(futures):
                print(future.result())
