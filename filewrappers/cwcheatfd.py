import struct

class WriteOnlyException(Exception):
    def __init__(self):
        super().__init__("The file descriptor is write only.")

class PermissionDenied(Exception):
    def __init__(self):
        super().__init__("Can only write to user memory.")

class CWCheatFileDescriptor():
    def __init__(self, file):
        if isinstance(file, str):
            self.file = open(file, "w")
        else:
            self.file = file
        self.virtual_address = 0
    
    def seek(self, add):
        self.virtual_address = add
        return add
    
    def read(self):
        raise WriteOnlyException
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        return self.file.close()
    
    def close(self):
        return self.file.close()
    
    def tell(self):
        return self.virtual_address
    
    def write(self, data):
        if isinstance(data, str):
            self.file.write(f"_C0 {data}\n")
        else:
            if self.virtual_address < 0x8800000:
                raise PermissionDenied
            while len(data)//4 > 0:
                word = data[:4]
                data = data[4:]
                add = hex(self.virtual_address-0x8800000).replace("0x", "")
                self.file.write(f'_L 0x2{add:0>7} {_to_word(word)}\n')
                self.virtual_address += 4
            while len(data)//2 > 0:
                short = data[:2]
                data = data[2:]
                add = hex(self.virtual_address-0x8800000).replace("0x", "")
                self.file.write(f'_L 0x1{add:0>7} {_to_short(short)}\n')
                self.virtual_address += 2
            while len(data) > 0:
                char = data[0]
                data = data[1:]
                add = hex(self.virtual_address-0x8800000).replace("0x", "")
                self.file.write(f'_L 0x0{add:0>7} {_to_byte(char)}\n')
                self.virtual_address += 1

def _to_word(word):
    return "0x"+"".join([f'{hex(x).replace("0x", ""):0>2}' for x in reversed(word)])

def _to_short(short):
    return "0x0000"+"".join([f'{hex(x).replace("0x", ""):0>2}' for x in reversed(short)])

def _to_byte(char):
    return "0x000000"+f'{hex(char).replace("0x", ""):0>2}'
