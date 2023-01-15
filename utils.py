import time
import math
import random
import numpy as np

def getGUID():
    sectionLength: float = time.time()
    id = ""
    for c in "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx":
        r: int = math.floor((sectionLength + random.random() * 16) % 16)
        sectionLength: int = math.floor(sectionLength / 16)
        _guid = c
        if c in {'x', 'y'}:
            _guid: str = np.base_repr(int(r if c=="x" else (r & 7) | 8), base=16)
        id += _guid
    return id.lower()