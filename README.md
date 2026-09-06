# NCM Converter

<p align="center">
  <img src="ncm_converter.ico" alt="NCM Converter Logo" width="100" height="100">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows-blue.svg" alt="Windows">
  <img src="https://img.shields.io/badge/Platform-macOS-lightgrey.svg" alt="macOS">
  <img src="https://img.shields.io/badge/Platform-Android-green.svg" alt="Android">
</p>

NCM 格式音频文件转换工具 / NCM Audio File Converter

## 简介 / Introduction

这是一个用于将网易云音乐的 NCM 格式音频文件转换为常见音频格式（如 MP3、FLAC）的工具。

**所有平台共用同一套经过验证的解密核心**（`ncmdump==0.1.1` + pycryptodome + mutagen）：
桌面端直接运行 Python；Android 端通过 [Chaquopy](https://chaquo.com/chaquopy/) 在应用内嵌入
同一个 Python 核心，不存在第二份算法实现。格式规范见 [docs/ncm-format.md](docs/ncm-format.md)。

All platforms share one proven decryption core. Desktop runs plain Python; Android embeds
the very same Python core via Chaquopy.

## 平台 / Platforms

| 平台 | 形态 | 状态 |
|---|---|---|
| Windows | `ncm_converter.exe`（CLI，PyInstaller 打包） | ✅ 与此前一致 |
| macOS | `.app` 外壳 + CLI（`dist/NCM_Converter-macos.zip`） | ✅ 已验证 |
| Android | APK（Kotlin + Jetpack Compose + 内嵌 Python） | ✅ 已验证 |
| 鸿蒙 NEXT | — | 暂不支持 |

## 使用方法 / Usage

### Windows / macOS（命令行）

```bash
python ncm_converter.py [输入文件夹] [输出文件夹] [--force]
# 或直接运行可执行文件
ncm_converter [输入文件夹] [输出文件夹]
```

macOS 的 `.app`：双击会在 Terminal 中打开交互界面；带参数启动等价于 CLI。
**Gatekeeper 提示**：应用未做公证签名，首次打开请**右键 → 打开**，
或在 Terminal 执行 `xattr -cr "/Applications/NCM Converter.app"`。

### Android

1. 「选择文件」从任意位置多选 .ncm，或「选择文件夹」授权网易云下载目录（下次免选）；
2. 默认输出到系统 `Music/NCM_Converted/`（无需任何存储权限，音乐类应用可直接看到），
   也可「自定义文件夹」；
3. 点「开始转换」，支持批量、进度、跳过已存在文件、完成通知。

> 系统限制：Android 15 不允许对**顶级** Download 文件夹做整树授权（"Can't use this folder"
> 为系统行为）；请选择其子文件夹（网易云的下载目录通常是 `netease/cloudmusic/Music`，不受影响），
> 或使用「选择文件」。

## 本地构建 / Build

```bash
# Windows exe（与之前一致）
pyinstaller ncm_converter.spec

# macOS：CLI + .app + zip
./macos/build_macos.sh

# Android APK（需 Android SDK/NDK + JDK 17；Chaquopy 会自动处理 Python 依赖）
cd android_app && ./gradlew assembleDebug
```

发布产物由 GitHub Actions 自动构建（tag `v*` 触发），Android 支持通过
`APK_KEYSTORE_BASE64` 等 secrets 注入正式签名，缺省回退 debug 签名（仍可安装）。

## 开发说明 / Development

- 测试夹具：`scripts/make_test_ncm.py` 按规范**逆向加密**生成合成 .ncm（无需版权音乐），
  并自动用真实 ncmdump 库做字节级往返校验；
- Android 端到端验证：SAF 选目录 → 转换 → `Music/NCM_Converted` 输出与参考逐字节一致；
- 早期两版 Android 移植（Kivy / 原生 Kotlin）的算法实现有误，已归档至 `archive/` 仅供查阅；
- 修复/打包的 CI 工作流：`.github/workflows/{build_android,release}.yml`。

## 注意事项 / Notes

- 此工具仅用于个人学习和研究目的，请尊重版权。
- 请确保您有权转换这些.ncm文件。
- 转换过程不会修改原始.ncm文件。

- This tool is for personal learning and research purposes only. Please respect copyright.
- Please ensure you have the right to convert these .ncm files.
- The conversion process will not modify the original .ncm files.

## 许可证 / License

本项目仅供个人学习和研究使用。

This project is for personal learning and research use only.

## 作者 / Author

[idk500](https://github.com/idk500/)
