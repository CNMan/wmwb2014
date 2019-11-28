#!py -3
#encodding: utf-8

__all__ = (
    'load_wangma_wubi',
    'generate_jidian_wubi',
    'generate_qq_wubi',
    'generate_xiaoya_wubi',
    'generate_baidu_wubi',
    'generate_wubis',
)

import os
import os.path
import coders
import baiduphone

WUBI_SHORT1 = {
    '我' : 'q',
    '以' : 'c',
    '为' : 'o',
    '有' : 'e',
    '这' : 'p',
    '不' : 'i',
    '发' : 'v'
}

def load_wangma_wubi(version, name, fullcode_input, shortcut_input):
    ftab = coders.encode_fullcode_file(fullcode_input)
    stab = coders.encode_shortcut_file(shortcut_input)
    table = {}

    def add_pair(code, value):
        if code not in table:
            table[code] = []
        if value not in table[code]:
            table[code].append(value)

    for record in stab:
        add_pair(record.code, record.value)

    for record in ftab:
        if record.tag == 'char':
            # This mabiao error drives me crazy.
            if record.value == '三':
                record.flag = 6
            elif record.value == '著' and version == '06':
                record.flag = 6

            if record.flag & 0x1:
                c = record.code[ : 1]
                c = WUBI_SHORT1.get(record.value, c)
                add_pair(c, record.value)
            if record.flag & 0x2:
                add_pair(record.code[ : 2], record.value)
            if record.flag & 0x4:
                add_pair(record.code[ : 3], record.value)
        else:
            break

    for record in ftab:
        if record.tag in ('char', 'word', 'extended-char'):
            add_pair(record.code, record.value)

    return table, ftab, stab

def generate_jidian_wubi(table, output):
    with open(output, 'w', encoding='utf-16', newline='\r\n') as fout:
        for code in sorted(table):
            string = code
            for value in table[code]:
                try:
                    value.encode('gb2312')
                except UnicodeError:
                    value = '~' + value
                string += ' ' + value
            print(string, file=fout)

def generate_qq_wubi(table, output):
    with open(output, 'w', encoding='utf-16', newline='\r\n') as fout:
        for code in sorted(table):
            string = code
            for value in table[code]:
                string += ' ' + value
            print(string, file=fout)

def generate_xiaoya_wubi(table, output, name=None):
    with open(output, 'w', encoding='utf-16', newline='\r\n') as fout:
        if name is None:
            name = output
        print('[cmd:RefCode]', file=fout)
        print('[cmd:RemoveAll]', file=fout)
        print('[cmd:Info=%s]' % name, file=fout)
        for code in sorted(table):
            string = code
            for value in table[code]:
                string += ' ' + value
            print(string, file=fout)

def generate_baidu_wubi(table, output):
    with open(output, 'w', encoding='utf-16', newline='\r\n') as fout:
        for code in sorted(table):
            for value in reversed(table[code]):
                string = '%s\t%s' % (value, code)
                print(string, file=fout)

def generate_jidian_wubi_index(ftab, output):
    with open(output, 'w', encoding='ascii', newline='\r\n') as fout:
        mapping = {}
        for record in ftab:
            if record.tag == 'char':
                mapping[record.value] = record.code
        def key_function(value):
            return value.encode('gb18030')
        for value in sorted(mapping, key=key_function):
            print(mapping[value].ljust(4), end='', file=fout)

def generate_baidu_phone_wubi(table, output):
    with open(output, 'wb') as fout:
        file = baiduphone.File()
        for code in sorted(table):
            for value in table[code]:
                record = baiduphone.Record()
                record.value = value
                record.codes.append(code)
                file.records.append(record)
        bs = file.compile()
        fout.write(bs)

def generate_wubis():
    root = os.path.dirname(__file__)
    root = os.path.realpath(root)
    SRC = os.path.join(root, '../大一统2014原始CSV码表')
    DST = os.path.join(root, '../大一统2014原始码表 for %s/wmwb%s.txt')
    DST_INDEX = os.path.join(root, '../大一统2014原始码表 for %s/wmwb%s.freeime.dat')
    DST_PHONE = os.path.join(root, '../大一统2014原始码表 for %s/wmwb%s.def')
    VERSIONS = '06', '86', '98'
    NAMES = '新世纪五笔', '86-18030', '98五笔'
    for version, name in zip(VERSIONS, NAMES):
        fullcode_input = os.path.join(SRC, 'wmwb%sqm.dat.txt' % version)
        shortcut_input = os.path.join(SRC, 'wmwb%sjm.dat.txt' % version)
        table, ftab, stab = load_wangma_wubi(version, name, fullcode_input, shortcut_input)
        generate_jidian_wubi(table, DST % ('极点五笔', version))
        generate_qq_wubi(table, DST % ('QQ五笔', version))
        generate_xiaoya_wubi(table, DST % ('小鸭五笔', version), name)
        generate_baidu_wubi(table, DST % ('百度五笔', version))
        generate_jidian_wubi_index(ftab, DST_INDEX % ('极点五笔索引', version))
        generate_baidu_phone_wubi(table, DST_PHONE % ('百度手机五笔', version))
