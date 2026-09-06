# NCM 文件格式规范（经 ncmdump 0.1.1 源码逐行验证）

> 上游 [nondanee/ncmdump](https://github.com/nondanee/ncmdump) 已被屏蔽（HTTP 451），
> 本文按本仓库 venv 内实际安装的 `ncmdump==0.1.1`（PyPI）`core.py` 逐行核实，
> 是本项目所有平台的权威算法依据。历史移植失败均源于未按此规范实现密钥推导。

## 总览

NCM = 自定义容器：头部明文 + 密钥/元数据加密段 + 变体 RC4 流加密的音频负载。
派生密钥链必须包含 **AES-128-ECB** 步骤——只做 XOR 的实现解不出正确的 RC4 密钥。

固定密钥（hex）：
- `core_key = 687A4852416D736F356B496E62617857`（ASCII `hzHRAmso5kInbaxW`）
- `meta_key = 2331346C6A6B5F215C5D2630553C2728`（ASCII `#14ljk_!\]&0U<'(`）

## 布局（按 ncmdump 0.1.1 读取顺序）

| 偏移 | 长度 | 内容 |
|---|---|---|
| 0 | 8 | 魔数 `CTENFDAM`（hex `4354454E4644414D`） |
| 8 | 2 | 跳过 |
| 10 | 4 | key 段长度 `key_length`（u32 LE） |
| 14 | `key_length` | key 数据（见下） |
| — | 4 | meta 段长度 `meta_length`（u32 LE；可为 0） |
| — | `meta_length` | meta 数据（见下） |
| — | 5 | 跳过 |

> ⚠️ **0.1.1 没有 crc32 字段。** 网上流传的格式文档多写"meta 后有 4 字节 crc32 + 5 字节间隔"，
> 与本版本源码不符（源码仅 `seek(5, 1)`）。按文档实现的解析会整体错位 4 字节。

| 偏移 | 长度 | 内容 |
|---|---|---|
| — | 4 | `image_space`（u32 LE，封面预留总空间） |
| — | 4 | `image_size`（u32 LE，封面实际字节数） |
| — | `image_size` | 封面原始字节（PNG/JPEG，写入目标文件作为专辑图） |
| — | `image_space - image_size` | 封面预留填充 |
| — | 剩余全部 | 音频数据（变体 RC4 加密，见下） |

## 密钥段解密（两条必须走的链）

```
key_bytes ^= 0x64（逐字节）
key_bytes = AES-128-ECB-decrypt(key_bytes, core_key)
key_bytes = unpad_pkcs7(key_bytes, 16)
rc4_key   = key_bytes[17:]        # 前 17 字节是 "neteasecloudmusic"
```

## 元数据段解密

```
meta_bytes ^= 0x63（逐字节）
identifier  = meta_bytes.decode('utf-8')      # "163 key(Don't modify):<base64>"，写入输出文件的 comment/description
meta_bytes  = base64.b64decode(meta_bytes[22:])
meta_bytes  = AES-128-ECB-decrypt(meta_bytes, meta_key)
meta_bytes  = unpad_pkcs7(meta_bytes, 16)
meta_json   = json.loads(meta_bytes[6:])      # 前 6 字节是 "music:"
```

`meta_json` 关键字段：`format`（`mp3`/`flac`，决定输出扩展名）、`musicName`、`album`、
`artist`（`[[名字, id], …]`）。`meta_length == 0` 时按文件大小猜格式（>16MiB → flac）。

## 音频负载：变体 RC4

标准 RC4 KSA 构建 S 盒（256 字节），但 PRGA 改为生成 256 字节**重复**密钥流：

```
stream[i] = S[(S[i] + S[(i + S[i]) & 0xFF]) & 0xFF]   # i ∈ [0, 256)
keystream = bytes(stream * (len(data) // 256 + 1))[1 : 1 + len(data)]
                                              # ⚠️ 注意：从第 2 字节开始取（偏移 [1:]）
audio = data XOR keystream
```

两个高频踩坑点：**密钥推导缺 AES-ECB 步骤**、**密钥流偏移 [1:]**。见
`scripts/make_test_ncm.py`（按本规范逆向加密的往返测试夹具）。

## 标签回写（ncmdump 使用 mutagen，非格式本身）

- MP3：EasyMP3 写 `title=meta.musicName`、`album`、`artist='/'.join(artist[0])`、
  `comment=identifier`；封面为 ID3 `APIC`（type 6）。
- FLAC：`title/album/artist` 同上，`description=identifier`；封面为 FLAC `Picture`（type 3）。
