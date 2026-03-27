# 使用说明

[English](usage.md) | **中文**

## 使用agentsight监测Claude Code的命令行参数

使用源代码编译成功后，agentsight二进制程序生成位置在当前目录下的collector/target/release/目录下，进入源代码的根目录，然后执行如下命令来测试：

```sh
sudo ./collector/target/release/agentsight ssl --http-parser --http-filter "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=" --ssl-filter "data=0\r\n\r\n"
```

```sh
sudo ./collector/target/release/agentsight agent -c "claude" --http-parser --http-filter "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=" --ssl-filter "data=0\r\n\r\n"
```

```sh
sudo ./collector/target/release/agentsight agent -c claude --http-filter "request.path_prefix=/v1/rgstr | response.status_code=202 | request.method=HEAD | response.body=" --ssl-filter "data=0\r\n\r\n|data.type=binary"
```
