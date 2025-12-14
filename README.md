# NCM Converter

<p align="center">
  <img src="ncm_converter.ico" alt="NCM Converter Logo" width="100" height="100">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows-blue.svg" alt="Platform">
</p>

NCM 格式音频文件转换工具 / NCM Audio File Converter

## 简介 / Introduction

这是一个用于将网易云音乐的 NCM 格式音频文件转换为常见音频格式（如 MP3、FLAC）的工具。NCM 是网易云音乐使用的专有加密格式，此工具可以将其解密并转换为标准音频格式。

This is a tool for converting Netease Cloud Music's NCM format audio files to common audio formats (such as MP3, FLAC). NCM is a proprietary encrypted format used by Netease Cloud Music, and this tool can decrypt it and convert it to standard audio formats.

## 功能特性 / Features

- 批量转换 NCM 文件
- 支持多种输出格式（MP3、FLAC等）
- 跳过已存在的文件避免重复转换
- 可选择强制覆盖已存在的文件
- 显示转换进度和统计信息
- 支持中英文界面
- 命令行操作简便

- Batch convert NCM files
- Support multiple output formats (MP3, FLAC, etc.)
- Skip existing files to avoid duplicate conversion
- Option to force overwrite existing files
- Display conversion progress and statistics
- Support for Chinese and English interfaces
- Simple command-line operation

## 安装要求 / Requirements

- Python 3.6+
- 依赖包：`ncmdump==0.1.1`

## 安装 / Installation

1. 克隆或下载此仓库：
   ```bash
   git clone https://github.com/idk500/NCM_Converter.git
   cd NCM_Converter
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
   
   或者直接安装：
   ```bash
   pip install ncmdump==0.1.1
   ```

## 使用方法 / Usage

### 基本使用 / Basic Usage

```bash
python ncm_converter.py [输入文件夹] [输出文件夹]
```

### 参数说明 / Parameters

- `[输入文件夹]` - 包含.ncm文件的文件夹路径（默认为当前目录）
- `[输出文件夹]` - 转换后的文件输出路径（默认为./decode）

- `[input_folder]` - Folder path containing .ncm files (default: current directory)
- `[output_folder]` - Output folder path for converted files (default: ./decode)

### 可选参数 / Optional Arguments

- `--force` - 强制覆盖已存在的文件 / Force overwrite existing files
- `--version` - 显示版本信息 / Show version information
- `--about` - 显示关于信息 / Show about information

### 示例 / Examples

1. 转换当前目录下的所有.ncm文件到默认的decode文件夹：
   ```bash
   python ncm_converter.py
   ```

2. 转换指定文件夹中的.ncm文件到指定输出文件夹：
   ```bash
   python ncm_converter.py "C:/Music/NCM" "C:/Music/Converted"
   ```

3. 强制覆盖已存在的文件：
   ```bash
   python ncm_converter.py --force
   ```

## 构建可执行文件 / Build Executable

您可以使用 PyInstaller 将此脚本打包为独立的可执行文件：

```bash
pip install pyinstaller
pyinstaller ncm_converter.spec
```

生成的可执行文件将在 `dist` 文件夹中。

You can use PyInstaller to package this script into a standalone executable:

```bash
pip install pyinstaller
pyinstaller ncm_converter.spec
```

The generated executable will be in the `dist` folder.

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