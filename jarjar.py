#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile, hashlib, traceback, time, logging, os
from typing import List

class JarJar:
    def __init__(self) -> None:
        pass

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
        # self._decompile_classes()
        self._search()
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

    def _search(self):
        '''Deep search and decompile classes.'''
        print("Searching classes ...")
        logging.info("Searching classes ...")
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
            text = os.popen('javap -c -p %s' % cur_path.replace('$', '\$')).read().strip()
            if text.find('错误') > 0:
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
        return path.removeprefix(self.unzip_to + '/')

    def _pack_classes(self):
        '''Packing casses.'''
        print("Packing classes ...")
        logging.info("Packing classes ...")
        self.classes = [self._simplify_class_path(cls.replace('$', '\$')) for cls in self.classes]
        pack_command = 'cd %s && jar cvf %s/final.jar %s ' % (self.unzip_to, self.output, ' '.join(self.classes))
        logging.info("PACK COMMAND: %s" % pack_command)
        os.system(pack_command)
