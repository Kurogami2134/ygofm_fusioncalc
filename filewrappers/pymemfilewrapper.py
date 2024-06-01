import win32api
import win32gui
import pyautogui
import psutil
from pymem import Pymem

class PymemFileDescriptor:
    def __init__(self, program_name, base_address = 0):
        self.file_pointer = 0
        self.base_address = base_address
        self.pm = None
        injected = False
        attempts = 0
        while not injected and attempts <= 3:
            try:
                self.pm = Pymem(program_name)
                injected = True
            except:
                attempts += 1

    def close(self):
        return True

    def seek(self, address):
        self.file_pointer = address
        return address

    def tell(self):
        return self.file_pointer
    
    def read(self, size):
        res = self.pm.read_bytes(self.base_address+self.file_pointer, size)
        self.seek(self.file_pointer+size)
        return res
    
    def write(self, data):
        res = self.pm.write_bytes(self.base_address+self.file_pointer, data, len(data))
        self.seek(self.file_pointer+len(data))
        return res
    
    def __exit__(self, *args):
        self.close()
    
    def __enter__(self):
        return self

class PSPRAMFileDescriptor(PymemFileDescriptor):
    def __init__(self):
        pywi = pyautogui.getWindowsWithTitle("PPSSPP")[0]
        wi = win32gui.FindWindow(None, pywi.title)
        retl = win32api.SendMessage(wi, 0x8000+0x3118, 0, 0)
        reth = win32api.SendMessage(wi, 0x8000+0x3118, 0, 1) << 32
        self.base_address = reth + retl
        self.file_pointer = 0
        injected = False
        while not injected:
            try:
                self.pm = Pymem("PPSSPPWindows64.exe")
                injected = True
            except:
                try:
                    self.pm = Pymem("PPSSPPWindows.exe")
                    injected = True
                except:
                    pass

class PSXRAMFileDescriptor(PymemFileDescriptor):
    def __init__(self, title, base_address):
        pywi = pyautogui.getWindowsWithTitle(title)[0]
        wi = win32gui.FindWindow(None, pywi.title)
        self.file_pointer = 0
        self.base_address = base_address
        injected = False
        while not injected:
            program_name = [x for x in psutil.process_iter() if "duckstation" in x.name()][0].name()
            try:
                self.pm = Pymem(program_name)
                injected = True
            except:
                pass