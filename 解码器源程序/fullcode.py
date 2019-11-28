#!py -3
#encodding: utf-8

__all__ = ('Record', 'Table')

import ctypes
import collections
import header

MAPPING_FROM_TAG_TO_STRING = {
    0: 'null',
    1: 'char',
    2: 'extended-char',
    4: 'word',
    8: 'variable',
    16: 'symbol'
}

MAPPING_FROM_STRING_TO_TAG = {
    'null': 0,
    'char': 1,
    'extended-char': 2,
    'word': 4,
    'variable': 8,
    'symbol': 16
}

class BaseData(ctypes.LittleEndianStructure):
    pass

class CharData(BaseData):
    _fields_ = [('_value', ctypes.c_byte * 4),
                ('_decomposition', ctypes.c_byte * (2 * 4)),
                ('_reading', ctypes.c_byte * (6 * 7)),
                ('_flag', ctypes.c_uint16),
                ('_tolerance', ctypes.c_byte * (4 * 3)),
                ('_code6k', ctypes.c_byte * 5),
                ('_reading2', ctypes.c_byte * 223)]

class WordData(BaseData):
    _fields_ = [('_length', ctypes.c_byte),
                ('_reserved', ctypes.c_byte * (7 + 16 * 2)),
                ('_value', ctypes.c_byte * (2 * 32)),
                ('_reading', ctypes.c_byte * (6 * 32))]

class StringData(BaseData):
    _fields_ = [('_value', ctypes.c_byte * 296)]

class DataVariant(ctypes.Union):
    _fields_ = [('_c', CharData),
                ('_w', WordData),
                ('_s', StringData)]

class Record(ctypes.LittleEndianStructure):
    _fields_ = [('_tag', ctypes.c_uint32),
                ('_code',  ctypes.c_byte * 4),
                ('_u', DataVariant)]

    @property
    def tag(self):
        return MAPPING_FROM_TAG_TO_STRING[self._tag]

    @tag.setter
    def tag(self, value):
        self._tag = MAPPING_FROM_STRING_TO_TAG[value]

    @property
    def code(self):
        return bytes(self._code).rstrip(b' ').decode()

    @code.setter
    def code(self, value):
        self._code[:] = value.encode().ljust(4, b' ')

    @property
    def value(self):
        assert self.tag in ('char', 'extended-char', 'word', 'variable', 'symbol')
        tag = self.tag
        if tag in ('char', 'extended-char'):
            value = self._u._c._value
        elif tag == 'word':
            value = self._u._w._value
        elif tag in ('variable', 'symbol'):
            value = self._u._s._value
        return bytes(value).rstrip(b'\0').decode('gb18030')

    @value.setter
    def value(self, value):
        assert self.tag in ('char', 'extended-char', 'word', 'variable', 'symbol')
        bs = value.encode('gb18030')
        tag = self.tag
        if tag in ('char', 'extended-char'):
            self._u._c._value[:] = bs.ljust(4, b'\0')
        elif tag == 'word':
            self._u._w._value[:] = bs.ljust(2 * 32, b'\0')
        elif tag in ('variable', 'symbol'):
            self._u._s._value[:] = bs.ljust(296, b'\0')

    @property
    def decomposition(self):
        assert self.tag in ('char', 'extended-char')
        dec = bytes(self._u._c._decomposition).rstrip(b'\0')
        res = ''
        for i, c in zip(dec[::2], dec[1::2]):
            if res:
                res += ' '
            res += '%c+%02d' % (c, i)
        return res

    @decomposition.setter
    def decomposition(self, value):
        assert self.tag in ('char', 'extended-char')
        bs = []
        for item in value.split():
            c, i = item.split('+')
            bs.append(int(i))
            bs.append(ord(c))
        bs = bytes(bs)
        self._u._c._decomposition[:] = bs.ljust(2 * 4, b'\0')

    @property
    def flag(self):
        assert self.tag in ('char', 'extended-char')
        return int(self._u._c._flag)

    @flag.setter
    def flag(self, value):
        assert self.tag in ('char', 'extended-char')
        self._u._c._flag = int(value)

    @property
    def length(self):
        assert self.tag == 'word'
        return int(self._u._w._length)

    @length.setter
    def length(self, value):
        assert self.tag == 'word'
        self._u._w._length = int(value)

    @property
    def reading(self):
        assert self.tag in ('char', 'extended-char', 'word')
        if self.tag == 'word':
            reading = self._u._w._reading
        else:
            reading = self._u._c._reading
        bs = bytes(reading)
        res = ''
        for i in range(0, len(bs), 6):
            major = ''.join(map(chr, bs[i : i + 2]))
            minor = ''.join(map(chr, bs[i + 2 : i + 6]))
            if major == '\0\0' and minor == '\0\0\0\0':
                break
            if res:
                res += ' '
            res += major.rstrip('\0') + '+' + minor.rstrip('\0')
        return res

    @reading.setter
    def reading(self, value):
        assert self.tag in ('char', 'extended-char', 'word')
        bs = b''
        for item in value.split():
            major, minor = item.split('+')
            bs += major.ljust(2, '\0').encode()
            bs += minor.ljust(4, '\0').encode()
        if self.tag == 'word':
            self._u._w._reading[:] = bs.ljust(6 * 32, b'\0')
        else:
            self._u._c._reading[:] = bs.ljust(6 * 7, b'\0')

    @property
    def reading2(self):
        assert self.tag in ('char', 'extended-char')
        reading = self._u._c._reading2
        bs = bytes(reading)
        bs = bs.rstrip(b'\0').split(b',')
        res = map(lambda x: x.decode(), bs)
        return ' '.join(res)

    @reading2.setter
    def reading2(self, value):
        assert self.tag in ('char', 'extended-char')
        string = ','.join(value.split())
        self._u._c._reading2[:] = string.encode().ljust(223, b'\0')

    @property
    def tolerance(self):
        assert self.tag in ('char', 'extended-char')
        bs = bytes(self._u._c._tolerance)
        res = ''
        for i in range(0, len(bs), 4):
            part = ''.join(map(chr, bs[i : i + 4]))
            if part == '\0\0\0\0':
                break
            if res:
                res += ' '
            res += part.rstrip('\0')
        return res

    @tolerance.setter
    def tolerance(self, value):
        assert self.tag in ('char', 'extended-char')
        bs = b''
        for item in value.split():
            bs += item.encode().ljust(4, b'\0')
        self._u._c._tolerance[:] = bs.ljust(4 * 3, b'\0')

    @property
    def code6k(self):
        assert self.tag in ('char', 'extended-char')
        bs = bytes(self._u._c._code6k).rstrip(b'\0')
        return ' '.join(map(str, bs))

    @code6k.setter
    def code6k(self, value):
        assert self.tag in ('char', 'extended-char')
        ints = map(int, value.split())
        bs = bytes(ints).ljust(5, b'\0')
        self._u._c._code6k[:] = bs

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
        self._records = []

    def add(self, record):
        self._records.append(record)

    def clear(self):
        del self._records[:]

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
        return iter(self._records)
