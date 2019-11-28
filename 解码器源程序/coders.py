#!py -3
#encodding: utf-8

__all__ = (
    'decode_radical_file',
    'encode_radical_folder',
    'decode_shortcut_file',
    'encode_shortcut_file',
    'decode_fullcode_file',
    'encode_fullcode_file',
    'decode_folder',
    'encode_folder',
)

import os
import os.path
import glob
import shutil
import csv
import header
import radical
import shortcut
import fullcode

def decode_radical_file(path, folder):
    with open(path, 'rb') as fin:
        table = radical.Table.read(fin)
    for record in table:
        name = folder + os.sep + record.code + '.bmp'
        with open(name, 'wb') as fout:
            fout.write(header.BMP_HEADER_DATA)
            fout.write(record.data)

def encode_radical_folder(folder):
    table = radical.Table()
    pattern = folder + os.sep + '[a-z]+[0-9][0-9].bmp'
    for name in glob.glob(pattern):
        with open(name, 'rb') as fin:
            bs = fin.read()
        if not bs.startswith(header.BMP_HEADER_DATA):
            print("`%s' is broken." % name, file=sys.stderr)
            continue
        record = radical.Record()
        record.code = name[-8 : -4]
        record.data = bs[len(header.BMP_HEADER_DATA) : ]
        table.add(record)
    return table

def decode_shortcut_file(input, output):
    with open(input, 'rb') as fin:
        table = shortcut.Table.read(fin)
    with open(output, 'w', encoding='utf-8-sig', newline='') as fout:
        writer = csv.writer(fout)
        for record in table:
            row = []
            row.append(record.code)
            row.append(record.value)
            writer.writerow(row)

def encode_shortcut_file(input):
    table = shortcut.Table()
    with open(input, 'r', encoding='utf-8-sig', newline='') as fin:
        reader = csv.reader(fin)
        for row in reader:
            record = shortcut.Record()
            record.code = row[0]
            record.value = row[1]
            table.add(record)
    return table

def decode_fullcode_file(input, output):
    with open(input, 'rb') as fin:
        table = fullcode.Table.read(fin)
    with open(output, 'w', encoding='utf-8-sig', newline='') as fout:
        writer = csv.writer(fout)
        for record in table:
            row = []
            row.append(record.tag)
            row.append(record.code)
            row.append(record.value)
            if record.tag == 'word':
                row.append(record.reading)
                row.append(record.length)
            elif record.tag in ('char', 'extended-char'):
                row.append(record.reading)
                row.append(record.reading2)
                row.append(record.decomposition)
                row.append(record.flag)
                row.append(record.tolerance)
                row.append(record.code6k)
            writer.writerow(row)

def encode_fullcode_file(input):
    table = fullcode.Table()
    with open(input, 'r', encoding='utf-8-sig', newline='') as fin:
        name = os.path.basename(input)
        reader = csv.reader(fin)
        for row in reader:
            record = fullcode.Record()
            record.tag = row[0]
            record.code = row[1]
            record.value = row[2]
            if record.tag == 'word':
                record.reading = row[3]
                record.length = row[4]
                if record.reading or record.length:
                    if len(record.reading.split()) != record.length:
                        print('%s: word-length: %s' % (name, record.value))
            elif record.tag in ('char', 'extended-char'):
                record.reading = row[3]
                record.reading2 = row[4]
                record.decomposition = row[5]
                record.flag = row[6]
                record.tolerance = row[7]
                record.code6k = row[8]
                code = ''.join(x[0] for x in record.decomposition.split())
                if code != record.code:
                    print('%s: char-decomposition: %s' % (name, record.code))
            table.add(record)
    return table

def decode_folder(src, dst):
    shutil.rmtree(dst, ignore_errors=True)
    os.mkdir(dst)
    for path in glob.glob(os.path.join(src, '*zg.dat')):
        target = os.path.join(dst, os.path.basename(path))
        os.mkdir(target)
        decode_radical_file(path, target)
    for input in glob.glob(os.path.join(src, '*jm.dat')):
        output = os.path.join(dst, os.path.basename(input) + '.txt')
        decode_shortcut_file(input, output)
    for input in glob.glob(os.path.join(src, '*qm.dat')):
        output = os.path.join(dst, os.path.basename(input) + '.txt')
        decode_fullcode_file(input, output)

def encode_folder(src, dst):
    shutil.rmtree(dst, ignore_errors=True)
    os.mkdir(dst)
    for folder in glob.glob(os.path.join(src, '*zg.dat')):
        path = os.path.join(dst, os.path.basename(folder))
        table = encode_radical_folder(folder)
        with open(path, 'wb') as fout:
            table.write(fout)
    for input in glob.glob(os.path.join(src, '*jm.dat.txt')):
        output = os.path.join(dst, os.path.basename(input)[ : -4])
        table = encode_shortcut_file(input)
        with open(output, 'wb') as fout:
            fout.write(header.HEADER_DATA)
            table.write(fout)
    for input in glob.glob(os.path.join(src, '*qm.dat.txt')):
        output = os.path.join(dst, os.path.basename(input)[ : -4])
        table = encode_fullcode_file(input)
        with open(output, 'wb') as fout:
            fout.write(header.HEADER_DATA)
            table.write(fout)
