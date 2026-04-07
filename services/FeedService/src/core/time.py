import time
from ..core.logger import logger as log

def timer(func) :
    def decorator(*args, **kwargs) : 
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            log.info(f"Execution time of {func.__name__} : {end_time - start_time} seconds")
            return result
    return decorator