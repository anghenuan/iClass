## 概述

这个仓库仅用于存储iClass项目开发的程序。
可以下载，GitHub Page仅用于预览，如需正式使用请克隆整个仓库后根据子文件夹中readme.md操作。
使用前请先安装node.js。

主页为RickBrowser中提取出来的网页，访问[这里](https://anghenuan.github.io/iClass/Homepage/)以使用。

### 对于工具，如何编译？

0、克隆此根目录

1、打开MSYS2 **MINGW64**终端

2、安装依赖库

3、进入程序根目录

4、依次运行：
```bash
qmake /*根目录下的.pro文件的文件名*/.pro
```

```bash
make
```

5、运行/release目录下的.exe文件。
