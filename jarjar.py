#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile, hashlib, traceback, time, logging, os, platform, shutil
from typing import List
from pool import *

class JarJar:
    def __init__(self) -> None:
        self.is_windows = platform.system().lower() == 'windows'

    def compress(self, classes: List[str], jar: str, output: str):
        '''
        - classes: classes used in jar.
        - jar: path of jar file.
        - output: path of compressed jar to store.
        '''
        self.jar_path = jar
        self.classes = classes
        self.output = os.path.abspath(output)
        self._unzip_jar()
        self.copy_to = 'space/final'
        # self._decompile_classes()
        # self._search_by_javap()
        self._search_by_read_constants()
        self._pack_classes()

    def _unzip_jar(self):
        '''Unzip the jar.'''
        print("Unzip jar ...")
        logging.info("Unzip jar ...")
        self.unzip_to = str(int(time.time()))
        try:
            with open(self.jar_path, 'rb') as fp:
                data = fp.read()
            self.unzip_to = hashlib.md5(data).hexdigest()
        except BaseException as e:
            logging.error("Error while reading the jar md5:\n%s" % traceback.format_exc())
            print("Error while reading the jar md5 [%s]" % self.jar_path)
        self.unzip_to = 'space/%s/unzip' % self.unzip_to
        if not os.path.exists(self.unzip_to):
            try:
                zipFile = zipfile.ZipFile(self.jar_path)
                zipFile.extractall(self.unzip_to)
                zipFile.close()
            except BaseException as e:
                logging.error("Error while unzip the jar:\n%s" % traceback.format_exc())
                print("Error while unzip the jar [%s]" % self.jar_path)
        else:
            logging.info("Unziped resources exists, ignore!")
            print("Unziped resources exists, ignore!")

    def _decompile_classes(self):
        '''Decompile all classes. Currently, we don't do decompile for all classes to save time usage.'''
        print("Decompile classes ...")
        logging.info("Decompile classes ...")
        classes = [self.unzip_to]
        decompiled_count = 0
        while len(classes) > 0:
            cur_path = classes.pop()
            if os.path.isdir(cur_path):
                cur_decompile_path = cur_path.replace('unzip', 'decompile')
                if not os.path.exists(cur_decompile_path):
                    os.mkdir(cur_decompile_path)
                classes.extend([os.path.join(cur_path, path) for path in os.listdir(cur_path)])
            elif cur_path.endswith('.class'):
                os.system('javap -c -p %s >> %s' % (cur_path, cur_path.replace('unzip', 'decompile')))
                decompiled_count = decompiled_count + 1
                print("JarJar >> ecompiled: %d" % decompiled_count, end = '\r')
        # space/d0188fddda195add9dcbf7e91a74484c/unzip/com/ibm/icu/text/CollatorServiceShimCollatorFactory.class
        # space/d0188fddda195add9dcbf7e91a74484c/unzip/com/ibm/icu/text/PluralRulesListBuilder.class

    def _search_by_javap(self):
        '''Deep search and decompile classes.'''
        print("Searching classes by javap ...")
        logging.info("Searching classes by javap ...")
        start = int(time.time())
        self.classes = [os.path.join(self.unzip_to, cls.replace('.', '/')) + '.class' for cls in self.classes]
        visits = []
        visits.extend(self.classes)
        count = 0
        while len(visits) > 0:
            count = count + 1
            cur_path = visits.pop()
            exists = os.path.exists(cur_path)
            logging.info("Searching under [%d][%s][%s]" % (count, str(exists), self._simplify_class_path(cur_path)))
            print("Searching under [%d][%s][%s]" % (count, str(exists), self._simplify_class_path(cur_path)), end='\r')
            # Ignore if the class file not exists.
            if not exists:
                self.classes.remove(cur_path)
                continue
            # Decompile and try to search methods.
            text = os.popen('javap -c -p %s' % self._get_class_path_according_to_system(cur_path)).read().strip()
            if text.find('错误') > 0 or len(text) == 0:
                logging.error("Error while decompiling [%s]" % (self._simplify_class_path(cur_path)))
                continue
            # Search in class text file.
            for line in text.splitlines():
                m_pos = line.find('// Method')
                if m_pos > 0:
                    method = line[(m_pos+10):].strip()
                    if method.find('.') > 0:
                        cls = method.split('.')[0]
                        self._handle_classes(cls, cur_path, visits)
        logging.info("Searching classes by javap done in [%d]" % (int(time.time())-start))
        print("Searching classes by javap done in [%d]" % (int(time.time())-start))

    def _search_by_read_constants(self):
        '''Search by parsing constants.'''
        print("Searching classes by parsing constant pool ...")
        logging.info("Searching classes by parsing constant pool ...")
        start = int(time.time())
        self.classes = [os.path.join(self.unzip_to, cls.replace('.', '/')) + '.class' for cls in self.classes]
        visits = []
        visits.extend(self.classes)
        count = 0
        parser = PoolParser()
        while len(visits) > 0:
            count = count + 1
            cur_path = visits.pop()
            exists = os.path.exists(cur_path)
            logging.info("Searching under [%d][%s][%s]" % (count, str(exists), self._simplify_class_path(cur_path)))
            print("Searching under [%d][%s][%s]" % (count, str(exists), self._simplify_class_path(cur_path)), end='\r')
            # Ignore if the class file not exists.
            if not exists:
                self.classes.remove(cur_path)
                continue
            # Parse classes from class constant pool.
            classes = parser.parse(cur_path)
            for cls in classes:
                self._handle_classes(cls, cur_path, visits)
        logging.info("Searching classes by parsing constant pool done in [%d]" % (int(time.time())-start))
        print("Searching classes by parsing constant pool done in [%d]" % (int(time.time())-start))

    def _handle_classes(self, cls: str, cur_path: str, visits: List[str]):
        '''Handle classes.'''
        pathes = [cls]
        # Handle if the class is an inner class.
        if cls.rfind('$') > 0:
            pos = cls.rfind('$')
            while pos > 0:
                cls = cls[0:pos]
                pathes.append(cls)
                pos = cls.rfind('$')
        for path in pathes:
            cls_path = os.path.join(self.unzip_to, path) + '.class'
            # Only search one class a time.
            if cls_path not in self.classes:
                self.classes.append(cls_path)
                visits.append(cls_path)
                logging.info("Found [%s] under [%s]" % (path, self._simplify_class_path(cur_path)))

    def _simplify_class_path(self, path: str) -> str:
        '''Simplify the class path.'''
        return path.replace(self.unzip_to + '/', '')

    def _get_class_path_according_to_system(self, path: str) -> str:
        '''Get class path according to file system.'''
        if self.is_windows:
            return path
        else:
            return path.replace('$', '\$')

    def _pack_classes(self):
        '''Packing casses.'''
        print("Packing classes ...")
        logging.info("Packing classes ...")
        if not os.path.exists(self.output):
            os.mkdir(self.output)
        self.classes = [self._simplify_class_path(self._get_class_path_according_to_system(cls)) for cls in self.classes]
        # Copy all filted classes to a directory.
        for cls in self.classes:
            dst = cls.replace(self.unzip_to, self.copy_to)
            par = os.path.dirname(dst)
            if not os.path.exists(par):
                os.makedirs(par)
            shutil.copyfile(cls, dst)
        # Get into the copied directory and use jar to package the directory.
        pack_command = 'cd %s && jar cvf %s/final.jar %s' % (self.copy_to, self.output, '.')
        logging.info("PACK COMMAND: %s" % pack_command)
        ret = os.popen(pack_command).read().strip()
