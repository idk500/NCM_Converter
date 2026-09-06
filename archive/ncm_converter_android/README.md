# NCM Converter Android

网易云音乐NCM格式音频文件转换器 - 安卓版

## 功能特点

- 自动嗅探网易云音乐下载路径
- 一键批量转换NCM文件
- Material Design风格界面
- 支持MP3、FLAC格式输出
- 显示转换进度和日志
- 跳过已存在文件

## 安装要求

- Python 3.8+
- Kivy 2.2+
- KivyMD 1.1+

## 本地开发

### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖（使用清华镜像加速）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple kivy[base] kivymd ncmdump==0.1.1 plyer
```

### 运行应用

```bash
cd ncm_converter_android
python main.py
```

## 构建APK

### 方法一：GitHub Actions自动构建

1. 将代码推送到GitHub仓库
2. 进入Actions标签
3. 等待构建完成
4. 下载APK文件

### 方法二：本地构建

需要使用WSL2或Linux环境：

```bash
# 安装WSL2
wsl --install -d Ubuntu-22.04

# 在WSL2中安装buildozer
pip install buildozer cython

# 构建
cd /mnt/e/Codes/NCM_Converter/ncm_converter_android
buildozer android debug
```

## 项目结构

```
ncm_converter_android/
├── main.py                 # 应用入口
├── requirements.txt        # Python依赖
├── buildozer.spec          # Buildozer配置
├── .github/
│   └── workflows/
│       └── build.yml       # GitHub Actions配置
├── app/
│   ├── __init__.py
│   ├── converter.py        # 转换核心逻辑
│   ├── path_sniffer.py     # 路径嗅探
│   └── utils.py            # 工具函数
├── ui/
│   ├── __init__.py
│   └── screens/
│       ├── __init__.py
│       └── main_screen.py  # 主界面
└── assets/
    └── icon.png            # 应用图标
```

## 注意事项

- 此工具仅用于个人学习和研究目的，请尊重版权
- Android 10+需要分区存储权限处理
- 首次构建时间较长（约15-30分钟)

## 许可证

本项目仅供个人学习和研究使用。
