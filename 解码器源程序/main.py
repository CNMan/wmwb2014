#!py -3
#encodding: utf-8

import sys
import os
import os.path

def decode_wmwb2014():
    root = os.path.dirname(__file__)
    root = os.path.realpath(root)
    if root not in sys.path:
        sys.path.append(root)
    import coders
    SRC = os.path.join(root, '../大一统2014原始二进制码表')
    DST = os.path.join(root, '../大一统2014原始CSV码表')
    coders.decode_folder(SRC, DST)

def encode_wmwb2014():
    root = os.path.dirname(__file__)
    root = os.path.realpath(root)
    if root not in sys.path:
        sys.path.append(root)
    import coders
    SRC = os.path.join(root, '../大一统2014原始CSV码表')
    DST = os.path.join(root, '../大一统2014原始二进制码表2')
    coders.encode_folder(SRC, DST)

def create_tables():
    root = os.path.dirname(__file__)
    root = os.path.realpath(root)
    if root not in sys.path:
        sys.path.append(root)
    import tables
    tables.generate_wubis()

def main():
    #decode_wmwb2014()
    #encode_wmwb2014()
    create_tables()

if __name__ == '__main__':
    main()
