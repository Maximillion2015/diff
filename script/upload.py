# -*- coding: utf-8 -*-

import argparse
import tos

# 申请的Bucket名字
bucket = "adtesttos"
# 申请的AccessKey
accessKey = "SW7NH22ZE63DS2E09V0U"

client = tos.TosClient(bucket, accessKey, cluster="default", timeout=10)


def parse_args():
    # 输入格式： python upload.py -l file1Path file2Path file3Path ...
    parser = argparse.ArgumentParser(
        description='上传文件至tos')
    parser.add_argument('-u', '--user', type=str, help='<Required> user name', required=True)
    parser.add_argument('-l', '--list', type=str, nargs='+', help='<Required> file path', required=True)
    args = parser.parse_args()
    return args

def getFileFullName(filePath, user = 'default'):
    return 'adtesttos_flow_' + user + '_' + filePath.split('/')[-1]


def uploadFile(paths, user = 'default'):
    # print paths, user
    for path in paths:
        with open(path) as f:
            client.put_object(getFileFullName(path, user), f.read())


if __name__ == '__main__':
    paths = parse_args()._get_kwargs()[0][1]
    user = parse_args()._get_kwargs()[1][1]
    uploadFile(paths, user)
