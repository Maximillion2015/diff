#! usr/bin/python
# -*- coding: UTF-8 -*-

import re, os
from pytos import tos

class thriftFileHandler:
    # originFilePath是原始thrift文件路径
    def __init__(self, outputPath=""):
        self._outputPath = outputPath


    def getAllPath(self, filePath):
        # 记录所有path
        allPath = set()


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


    def makePack(self, inputPath):

        pathList = self.getAllPath(inputPath)

        packDirName = str(inputPath.split('/')[-1].split('.')[0])
        os.environ['packDirName'] = packDirName
        os.system('mkdir $packDirName')
        for filePath in pathList:
            os.environ['filePath'] = str(filePath)
            os.system('cp $filePath ./$packDirName')

        os.environ['packName'] = packDirName + '.jar'
        os.system('jar cvf $packName ./$packDirName/*')
        # os.system('jar cvf $packName ./$packDirName/')

        os.environ['outputDir'] = str(self._outputPath)
        os.system('mv $packName $outputDir')
        os.system('mv ././$packDirName/* $outputDir')
        os.system('rm -rf ./$packDirName')

        # 申请的Bucket名字
        bucket = "adtesttos"
        # 申请的AccessKey
        accessKey = "SW7NH22ZE63DS2E09V0U"

        client = tos.TosClient(bucket, accessKey, cluster="default", timeout=10)
        tosKey = "adtesttos_flow_" + packDirName

        jarName = self._outputPath + packDirName + '.jar'
        with open(jarName) as f:
            client.put_object(tosKey, f.read())

        return tosKey


    def gen_thrift(self, thriftPath):
        self.makePack(thriftPath)

        with open(thriftPath, 'r') as f:
            # print f.read()
            # matchObj = re.match('service', f.read())
            pattern = re.compile(r'service\s(.*?)\s{')
            match =pattern.findall(f.read())


        return self.makePack(thriftPath), match







if __name__ == '__main__':
    # handler = thriftFileHandler("/../../idl/ad/tianchi.thrift", '/../')
    handler = thriftFileHandler('/Users/zhangyifeng/Desktop/')
    # pathList = handler.getAllPath()
    # print pathList
    # handler.gen_thrift("/Users/zhangyifeng/repos/py/idl/ad/tianchi.thrift")
    handler.gen_thrift("/Users/zhangyifeng/repos/py/idl/ad/tianchi.thrift")
    # handler.makePack()



