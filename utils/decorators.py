import time
from functools import wraps
import logging

def timer_decorator(func):
    """
    Decorator to measure and log the execution time of a function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.debug(f"Execution time for {func.__name__}: {end_time - start_time:.2f} seconds")
        return result
    return wrapper