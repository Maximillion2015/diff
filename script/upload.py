import argparse
import tos

# 申请的Bucket名字
bucket = "tostest"
# 申请的AccessKey
accessKey = "BG8DFYMLM6U44P9KX755"

client = tos.TosClient(bucket, accessKey, cluster="default", timeout=10)


def parse_args():
    # 输入格式： python upload.py -l file1Path file2Path file3Path ...
    parser = argparse.ArgumentParser(
        description='上传文件至tos')
    parser.add_argument('-l', '--list', type=str, nargs='+', help='<Required> file path', required=True)
    args = parser.parse_args()
    return args

def getFileFullName(filePath, user = 'zhangyifeng'):
    return 'adtesttos' + user + filePath.split('/')[-1]


def uploadFile(args, user = 'zhangyifeng'):
    for path in args:
        with open(path) as f:
            client.put_object(getFileFullName(path, user), f.readline())


if __name__ == '__main__':
    args = parse_args()._get_kwargs()[0][1]
    uploadFile(args)

