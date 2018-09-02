#! usr/bin/python
# -*- coding: UTF-8 -*-

import re, os, sys

class thriftFileHandler:
    # originFilePath是原始thrift文件路径
    def __init__(self, originFilePath="", outputPath=""):
        self._originFilePath = originFilePath
        self._outputPath = outputPath


    def getAllPath(self):
        # 记录所有path
        allPath = set()

        # 项目根路径的绝对路径
        absPath = os.path.abspath(".")
        filePath = os.path.normpath(absPath+self._originFilePath)


        pathStack = set([filePath])


        while len(pathStack) != 0:
            currentFilePath = pathStack.pop()
            allPath.add(currentFilePath)
            pathStack = pathStack | self.getFilePath(currentFilePath)

        return allPath


    def getFilePath(self, filePath):
        pathList = set()
        with open(filePath, 'r') as f:
            for line in f.readlines():
                matchObj = re.match('^include\s\"(.*)\"', line)
                if matchObj:
                    pathList.add(os.path.normpath(filePath + '/../' + matchObj.group(1)))

        return pathList


    def makePack(self):
        # 目标路径的绝对路径
        absPath = os.path.abspath(".")
        absOutputPath = os.path.normpath(absPath + self._outputPath)
        pathList = self.getAllPath()

        packDirName = str(self._originFilePath.split('/')[-1].split('.')[0])
        os.environ['packDirName'] = packDirName
        os.system('mkdir $packDirName')
        for filePath in pathList:
            os.environ['filePath'] = str(filePath)
            os.system('cp $filePath ./$packDirName')

        os.environ['packName'] = packDirName + '.jar'
        os.system('jar cvf $packName ./$packDirName/*')
        # os.system('jar cvf $packName ./$packDirName/')

        os.environ['outputDir'] = str(absOutputPath)
        os.system('mv $packName $outputDir')

        os.system('rm -rf $packDirName')



if __name__ == '__main__':
    # handler = thriftFileHandler("/../../idl/ad/tianchi.thrift", '/../')
    handler = thriftFileHandler(sys.argv[1], sys.argv[2])
    pathList = handler.getAllPath()
    print pathList
    handler.makePack()



