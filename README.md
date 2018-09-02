# diff工具使用说明
## diff工具下载
```
git clone https://github.com/Maximillion2015/diff.git
```
## thrift文件打包模块--@张艺峰
**功能**:

获取该thrift文件引用的所有thrift文件，并打成jar包，存在目标路径下。

**代码调用**:

```
handler = thriftFileHandler(MainThriftPath, JarPath)
```

**命令**:

```
python handler/thriftFileHandler.py MainThriftPath JarPath
```
**参数说明**:

1. **MainThriftPath**：thrift文件的相对路径，如是diff目录平级的a目录下的b.thrift则为`/../../a/b.thrift`，如是diff目录下`c.thrift`，则为`/../c.thrift`。
2. **JarPath**：jar包存放的相对路径，如存放在diff目录平级的a目录下则为`/../../a`，如存放diff目录则为`/../`。

## 文件上传至tos模块--@张艺峰
**功能**:

将文件上传至tos中。

**命令**:

```
python script/upload.py -u UserName -l filepath1 filepath2 filepath3 ...
```
**参数说明**:

1. **UserName**:用户名，文件上传后的命名方式为`adtesttos_flow_UserName_FileName`。
2. **filepath**:上传文件的绝对路径。
