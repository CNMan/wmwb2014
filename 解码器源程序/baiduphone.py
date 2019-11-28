#!py -3
#encoding: utf-8

__all__ = ('Record', 'File')

class Record:
    def __init__(self):
        self.__value = None
        self.__codes = []

    @property
    def value(self):
        return self.__value

    @property
    def codes(self):
        return self.__codes

    @value.setter
    def value(self, new_value):
        self.__value = new_value

    def __str__(self):
        string = str(self.__value)
        for code in self.__codes:
            string += ' ' + code
        return string

    def to_bytes(self):
        bs = bytearray()
        joined_codes = ' '.join(self.__codes)
        bs += len(joined_codes).to_bytes(1, 'little')
        bs += ((len(self.__value) + 1) * 2).to_bytes(1, 'little')
        bs += joined_codes.encode('ascii')
        bs += self.__value.encode('utf-16le')
        bs += b'\0\0'
        bs += b'\0\0\0\0'
        return bs

    @classmethod
    def read(cls, stream):
        try:
            value, codes = cls._read_record(stream)
            record = cls()
            record.__value = value
            record.__codes = codes
            return record
        except ValueError:
            return None

    @classmethod
    def _read_record(cls, stream):
        code_length = cls._read_byte(stream)
        value_length = cls._read_byte(stream)
        codes = cls._read_codes(stream, code_length)
        value = cls._read_value(stream, value_length)
        flag = cls._read_dword(stream)
        if flag:
            message = 'reserved flag must be zero'
            raise ValueError(message)
        return value, codes

    @classmethod
    def _read_codes(cls, stream, code_length):
        bs = stream.read(code_length)
        if len(bs) != code_length:
            message = 'bad code length'
            raise ValueError(message)
        string = bs.decode('ascii')
        codes = string.split()
        return codes

    @classmethod
    def _read_value(cls, stream, value_length):
        bs = stream.read(value_length)
        if len(bs) != value_length:
            message = 'bad value length'
            raise ValueError(message)
        value = bs.decode('utf-16le')
        return value.rstrip('\0')

    @classmethod
    def _read_byte(cls, stream):
        bs = stream.read(1)
        if len(bs) != 1:
            message = 'byte expected'
            raise ValueError(message)
        return int.from_bytes(bs, 'little')

    @classmethod
    def _read_dword(cls, stream):
        bs = stream.read(4)
        if len(bs) != 4:
            message = 'dword expected'
            raise ValueError(message)
        return int.from_bytes(bs, 'little')

class File:
    def __init__(self):
        self.__max_length = 4
        self.__offsets = []
        self.__records = []

    @property
    def max_length(self):
        return self.__max_length

    @max_length.setter
    def max_length(self, value):
        self.__max_length = value

    @property
    def records(self):
        return self.__records

    @classmethod
    def read(cls, stream):
        try:
            file = cls()
            file.__max_length = Record._read_byte(stream)
            for i in range(27):
                file.__offsets.append(Record._read_dword(stream))
            while True:
                record = Record.read(stream)
                if record is None:
                    break
                else:
                    file.__records.append(record)
            return file
        except ValueError:
            return None

    def __str__(self):
        string = ''
        string += 'MaxLength: %d' % self.__max_length
        string += '\nOffsets:'
        for i, offset in enumerate(self.__offsets):
            c = chr(ord('A') + i)
            string += '\n  %c -> 0x%08X' % (c, offset)
        string += '\nRecords:'
        for record in self.__records:
            string += '\n  %s' % record
        return string

    def compile(self):
        head = bytearray()
        body = bytearray()
        head += self.__max_length.to_bytes(1, 'little')
        prev_letter = ord('a') - 1
        for record in self.__records:
            while prev_letter < ord(record.codes[0][0]):
                prev_letter += 1
                head += len(body).to_bytes(4, 'little')
            body += record.to_bytes()
        while prev_letter <= ord('z'):
            prev_letter += 1
            head += len(body).to_bytes(4, 'little')
        return bytes(head + body)
