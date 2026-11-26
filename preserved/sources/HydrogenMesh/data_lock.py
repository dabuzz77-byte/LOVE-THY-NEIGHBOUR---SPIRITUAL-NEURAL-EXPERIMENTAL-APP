"""Prevent two studio instances from writing the same rolling history."""
import os
from pathlib import Path

class DataLock:
    def __init__(self,path):
        self.handle=Path(path).open('a+b');self.closed=False
        if self.handle.seek(0,2)==0:self.handle.write(b'0');self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.handle.close();self.closed=True
            raise OSError('Another Hydrogen Mesh instance is using this data folder. Close it before reopening.')
    def close(self):
        if self.closed:return
        self.closed=True;self.handle.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.handle.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(self.handle,fcntl.LOCK_UN)
        finally:self.handle.close()
