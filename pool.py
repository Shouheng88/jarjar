#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
import logging, traceback

class PoolParser:
    def __init__(self):
        self.constants = {
            3: 4,
            4: 4,
            5: 8,
            6: 8,
            7: 2,
            8: 2,
            9: 4,
            10: 4,
            11: 4,
            12: 4,
            15: 3,
            16: 2,
            17: 4,
            18: 4,
            19: 2,
            20: 2
        }

    def parse(self, path: str) -> List[str]:
        '''Parse constant pool of class file with path.'''
        try:
            with open(path, 'rb') as fp:
                data = fp.read()
            constant_count = data[8] * 16 * 16 + data[9]
            cur_constant_index = 1
            index = 10
            sequences = {}
            classes_nums = []
            while cur_constant_index < constant_count:
                constant_code = data[index]
                if constant_code == 1:
                    char_length = data[index+1]*16*16+data[index+2]
                    char_start = index+3
                    char_end = char_start+char_length
                    # print(str(cur_constant_index) + '/' + str(constant_count) + ': ' + str(data[char_start:char_end], 'utf-8'))
                    sequences[cur_constant_index] = str(data[char_start:char_end], 'utf-8')
                    index = index + 2 + char_length + 1
                    cur_constant_index = cur_constant_index + 1
                elif constant_code == 5 or constant_code == 6:
                    # Special guideline for double and long type, see https://docs.oracle.com/javase/specs/jvms/se7/html/jvms-4.html#jvms-4.4.5
                    index = index + self.constants[constant_code] + 1
                    cur_constant_index = cur_constant_index + 2
                else:
                    # Get number of class in the constant pool.
                    if constant_code == 7:
                        classes_nums.append(data[index+1]*16*16+data[index+2])
                    index = index + self.constants[constant_code] + 1
                    cur_constant_index = cur_constant_index + 1
            return [sequences[num] for num in classes_nums]
        except BaseException as e:
            logging.error("Error while parsing constant pool:\n%s" % traceback.format_exc())
            print("Error while parsing constant pool for [%s]" % path)
            return []

if __name__ == "__main__":
    parser = PoolParser()
    ret = parser.parse('space/d0188fddda195add9dcbf7e91a74484c/unzip\com/ibm/icu/text/CharsetRecog_mbcs.class')
    for cls in ret:
        print(cls)
