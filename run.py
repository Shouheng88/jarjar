#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, os
from time import sleep, time

from jarjar import JarJar

def config_logging(filename: str = 'app.log'):
    '''Config loggin library globaly.'''
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
    logging.basicConfig(filename=filename, filemode='a', level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.FileHandler(filename=filename, encoding='utf-8')

def _test_inner_class():
    cls = 'AAAA/BBB/CCC$DDD$EEE$FFF'
    pos = cls.rfind('$')
    while pos > 0:
        cls = cls[0:pos]
        print(cls)
        pos = cls.rfind('$')

if __name__ == "__main__":
    config_logging()
    # jarjar = JarJar()
    # jarjar.compress(['com.ibm.icu.text.CharsetDetector'], 'space/icu4j-50_2.jar', '.')
    while True:
        sleep(1)
        print('Tapping [%d] ...' % (int(time())), end='\r')
        os.system('adb shell input touchscreen swipe 2000 1000 2000 1000 100')
