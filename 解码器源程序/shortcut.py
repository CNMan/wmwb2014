#!py -3
#encodding: utf-8

__all__ = ('Record', 'Table')

import ctypes
import collections
import header

S1_BEGIN = 0
S1_END   = 24
S2_BEGIN = 30 + 1
S2_END   = 30 + 30 * 24 + 25
S3_BEGIN = 930 + 1
S3_END   = 930 + 900 * 24 + 30 * 24 + 25

class Record(ctypes.LittleEndianStructure):
    _fields_ = [('_index', ctypes.c_uint32),
                ('_value',  ctypes.c_byte * 4)]

    @property
    def code(self):
        index = self._index
        if S1_BEGIN <= index <= S1_END:
            offset = index - S1_BEGIN
            c1 = chr(ord('a') + offset)
            return c1
        if S2_BEGIN <= index <= S2_END:
            offset = index - S2_BEGIN
            c1 = chr(ord('a') + offset // 30)
            c2 = chr(ord('a') + offset % 30)
            return c1 + c2
        if S3_BEGIN <= index <= S3_END:
            offset = index - S3_BEGIN
            c1 = chr(ord('a') + offset // 900)
            c2 = chr(ord('a') + offset // 30 % 30)
            c3 = chr(ord('a') + offset % 30)
            return c1 + c2 + c3
        message = 'invalid index'
        raise ValueError(message)

    @code.setter
    def code(self, value):
        assert 1 <= len(value) <= 3
        assert value.islower()
        if len(value) == 1:
            n1 = ord(value[0]) - ord('a')
            index = S1_BEGIN + n1
        elif len(value) == 2:
            n1 = ord(value[0]) - ord('a')
            n2 = ord(value[1]) - ord('a')
            index = S2_BEGIN + 30 * n1 + n2
        else:
            n1 = ord(value[0]) - ord('a')
            n2 = ord(value[1]) - ord('a')
            n3 = ord(value[2]) - ord('a')
            index = S3_BEGIN + 900 * n1 + 30 * n2 + n3
        self._index = index

    @property
    def value(self):
        return bytes(self._value).rstrip(b'\0').decode('gb18030')

    @value.setter
    def value(self, value):
        self._value[:] = value.encode('gb18030').ljust(4, b'\0')

    @classmethod
    def read(cls, fin):
        bs = fin.read(ctypes.sizeof(cls))
        if bs:
            return cls.from_buffer_copy(bs)

    def write(self, fout):
        fout.write(self)

    def __str__(self):
        return self.code

class Table:
    def __init__(self):
        self._records = collections.defaultdict(list)

    def add(self, record):
        self._records[record.code].append(record)

    def remove(self, code):
        if code in self._records:
            del self._records[code]

    def clear(self):
        self._records.clear()

    def load(self, fin):
        head = fin.read(len(header.HEADER_DATA))
        if len(head) != len(header.HEADER_DATA):
            message = 'file is corrupt'
            raise ValueError(message)
        while True:
            record = Record.read(fin)
            if record:
                self.add(record)
            else:
                break

    @classmethod
    def read(cls, fin):
        table = cls()
        table.load(fin)
        return table

    def write(self, fout):
        for record in self:
            record.write(fout)

    def dump(self, fout=None):
        for record in self:
            print(record.code, file=fout)

    def __iter__(self):
        for code in sorted(self._records, key=lambda x: (len(x), x)):
            yield from self._records[code]
