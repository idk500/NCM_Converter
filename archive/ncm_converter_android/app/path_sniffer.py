"""
路径嗅探模块
自动检测网易云音乐下载路径和默认音乐输出路径
"""
import os
from typing import List, Tuple, Optional


# 网易云音乐可能的路径（按优先级排序）
NETEASE_PATHS = [
    '/storage/emulated/0/netease/cloudmusic/Music/',
    '/storage/emulated/0/Android/data/com.netease.cloudmusic/files/Music/',
    '/sdcard/netease/cloudmusic/Music/',
    '/storage/emulated/0/Music/网易云音乐/',
    '/sdcard/Music/网易云音乐/',
    '/storage/emulated/0/Download/网易云音乐/',
    '/sdcard/Download/网易云音乐/',
]

# 默认输出路径
OUTPUT_PATHS = [
    '/storage/emulated/0/Music/NCM_Converted/',
    '/sdcard/Music/NCM_Converted/',
]


class PathSniffer:
    """路径嗅探器"""
    
    @staticmethod
    def path_exists(path: str) -> bool:
        """检查路径是否存在"""
        return os.path.exists(path) and os.path.isdir(path)
    
    @staticmethod
    def get_ncm_count(path: str) -> int:
        """获取路径中的NCM文件数量"""
        if not PathSniffer.path_exists(path):
            return 0
        try:
            return len([f for f in os.listdir(path) if f.lower().endswith('.ncm')])
        except Exception:
            return 0
    
    @staticmethod
    def get_total_size_mb(path: str) -> float:
        """获取路径中NCM文件总大小（MB）"""
        if not PathSniffer.path_exists(path):
            return 0
        try:
            total_size = 0
            for f in os.listdir(path):
                if f.lower().endswith('.ncm'):
                    filepath = os.path.join(path, f)
                    total_size += os.path.getsize(filepath)
            return total_size / (1024 * 1024)
        except Exception:
            return 0
    
    @staticmethod
    def find_netease_path() -> Tuple[Optional[str], int]:
        """
        查找网易云音乐下载路径
        :return: (路径, NCM文件数量) 如果未找到返回 (None, 0)
        """
        best_path = None
        best_count = 0
        
        for path in NETEASE_PATHS:
            if PathSniffer.path_exists(path):
                count = PathSniffer.get_ncm_count(path)
                if count > 0:
                    if count > best_count:
                        best_path = path
                        best_count = count
        
        return best_path, best_count
    
    @staticmethod
    def get_default_output_path() -> str:
        """获取默认输出路径"""
        for path in OUTPUT_PATHS:
            # 返回第一个可用的父目录
            parent = os.path.dirname(path.rstrip('/'))
            if PathSniffer.path_exists(parent):
                return path
        
        # 默认返回第一个选项
        return OUTPUT_PATHS[0]
    
    @staticmethod
    def get_all_netease_paths() -> List[Tuple[str, int]]:
        """
        获取所有包含NCM文件的网易云音乐路径
        :return: [(路径, NCM文件数量), ...]
        """
        result = []
        for path in NETEASE_PATHS:
            if PathSniffer.path_exists(path):
                count = PathSniffer.get_ncm_count(path)
                if count > 0:
                    result.append((path, count))
        return result
    
    @staticmethod
    def sniff() -> dict:
        """
        执行路径嗅探
        :return: {
            'input_path': 最佳输入路径,
            'input_count': NCM文件数量,
            'input_size_mb': NCM文件总大小,
            'output_path': 默认输出路径,
            'all_paths': 所有可用路径
        }
        """
        input_path, input_count = PathSniffer.find_netease_path()
        output_path = PathSniffer.get_default_output_path()
        all_paths = PathSniffer.get_all_netease_paths()
        
        input_size_mb = 0
        if input_path:
            input_size_mb = PathSniffer.get_total_size_mb(input_path)
        
        return {
            'input_path': input_path,
            'input_count': input_count,
            'input_size_mb': input_size_mb,
            'output_path': output_path,
            'all_paths': all_paths
        }


# 桌面测试用
if __name__ == '__main__':
    # 测试当前目录
    test_paths = [
        './test_ncm/',
        '.',
    ]
    
    print("=== 路径嗅探测试 ===")
    for path in test_paths:
        if os.path.exists(path):
            count = PathSniffer.get_ncm_count(path)
            size = PathSniffer.get_total_size_mb(path)
            print(f"路径: {path}")
            print(f"  NCM文件数: {count}")
            print(f"  总大小: {size:.2f}MB")
