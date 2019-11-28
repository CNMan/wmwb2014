#!py -3
#encodding: utf-8

__all__ = ('Record', 'Table')

import ctypes
import header

class Record(ctypes.LittleEndianStructure):
    _fields_ = [('_letter', ctypes.c_byte),
                ('_major', ctypes.c_byte),
                ('_minor', ctypes.c_byte),
                ('_reserved', ctypes.c_byte * 5),
                ('_data', ctypes.c_byte * 64)]

    @property
    def code(self):
        letter = chr(self._letter).lower()
        major = chr(self._major)
        minor = chr(self._minor)
        return '%c+%c%c' % (letter, major, minor)

    @code.setter
    def code(self, value):
        assert len(value) == 4
        assert 'a' <= value[0] <= 'z'
        assert value[1] == '+'
        assert '0' <= value[2] <= '9'
        assert '0' <= value[3] <= '9'
        self._letter = ord(value[0].upper())
        self._major = ord(value[2])
        self._minor = ord(value[3])

    @property
    def data(self):
        return bytes(self._data)

    @data.setter
    def data(self, value):
        assert len(value) == 64
        self._data[:] = value

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
        self._records = {}

    def add(self, record):
        self._records[record.code] = record

    def remove(self, code):
        if code in self._records:
            del self._records[code]

    def clear(self):
        self._records.clear()

    def load(self, fin):
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
        for code in sorted(self._records):
            record = self._records[code]
            record.write(fout)

    def dump(self, fout=None):
        for code in sorted(self._records):
            print(code, file=fout)

    def __iter__(self):
        return iter(self._records.values())
