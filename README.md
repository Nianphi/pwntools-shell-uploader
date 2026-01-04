# pwntools-shell-uploader

基于 Python pwntools 的反弹 Shell 文件上传工具

通过 Base64 分块在受限 Shell 环境中传输较大文件

## 依赖环境

- Python ≥ 3.7
- pwntools

安装 pwntools：

```
pip install pwntools
```

## 使用方法

### 一、仅监听反弹 Shell（不上传文件）

```
python pwntools-shell-uploader.py -p 1234
```

- 监听 `1234` 端口
- 等待反弹 Shell
- 连接成功后直接进入交互式 Shell

------

### 二、监听并上传文件

```
python pwntools-shell-uploader.py -p 1234 -f ./tool -r /tmp/tools/tool
```

参数说明：

| 参数 | 说明         |
| ---- | ------------ |
| `-p` | 本地监听端口 |
| `-f` | 本地文件路径 |
| `-r` | 远端保存路径 |

上传速度受 Shell 稳定性影响，可自行调整：

```
time.sleep(0.01)
```

