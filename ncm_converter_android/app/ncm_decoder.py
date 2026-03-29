"""
NCM文件解密模块 - 纯Python实现
基于 ncmdump 库的算法，用于Android兼容
"""
import os
import struct
from typing import Optional, Tuple, Callable


# AES密钥和IV（网易云音乐NCM格式）
AES_KEY = b"C284D70B33BF4D1D96A1B7C7A7E27B2D"
AES_IV = b"776B5F5D415076715A5F7A6B59534E4D"


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR加密/解密"""
    result = bytearray(len(data))
    key_len = len(key)
    for i, byte in enumerate(data):
        result[i] = byte ^ key[i % key_len]
    return bytes(result)


def _build_key_box(key: bytes) -> list:
    """构建密钥盒"""
    box = list(range(256))
    key_len = len(key)
    j = 0
    for i in range(256):
        j = (j + box[i] + key[i % key_len]) & 0xFF
        box[i], box[j] = box[j], box[i]
    return box


def _decrypt_core(data: bytes, key_box: list) -> bytes:
    """核心解密算法"""
    result = bytearray(len(data))
    box = key_box.copy()
    j = k = 0
    for i in range(len(data)):
        j = (j + 1) & 0xFF
        k = (k + box[j]) & 0xFF
        box[j], box[k] = box[k], box[j]
        result[i] = data[i] ^ box[(box[j] + box[k]) & 0xFF]
    return bytes(result)


class NCMDecoder:
    """NCM文件解码器"""
    
    def __init__(self, filepath: str):
        """
        初始化解码器
        :param filepath: NCM文件路径
        """
        self.filepath = filepath
        self._file = None  # type: ignore
        self._key_box = []  # type: list
        self._meta = {}  # type: dict
        self._audio_offset = 0
    
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def open(self):
        """打开文件并解析头部"""
        self._file = open(self.filepath, 'rb')
        self._parse_header()
    
    def close(self):
        """关闭文件"""
        if self._file:
            self._file.close()
            self._file = None
    
    def _parse_header(self):
        """解析NCM文件头部"""
        # 读取魔数
        magic = self._file.read(8)
        if magic != b'CTENFDAM':
            raise ValueError(f"Invalid NCM file: {self.filepath}")
        
        # 跳过2字节
        self._file.read(2)
        
        # 读取密钥数据长度
        key_len_bytes = self._file.read(4)
        key_len = struct.unpack('<I', key_len_bytes)[0]
        
        # 读取加密的密钥数据
        encrypted_key = self._file.read(key_len)
        
        # 解密密钥
        decrypted_key = _xor_bytes(encrypted_key, AES_KEY)
        
        # 构建密钥盒
        self._key_box = _build_key_box(decrypted_key)
        
        # 读取元数据长度
        meta_len_bytes = self._file.read(4)
        meta_len = struct.unpack('<I', meta_len_bytes)[0]
        
        # 读取元数据
        if meta_len > 0:
            encrypted_meta = self._file.read(meta_len)
            decrypted_meta = _xor_bytes(encrypted_meta, AES_IV)
            
            # 跳过第一个字节（可能是长度标记）
            if decrypted_meta[0] == 0x7F or decrypted_meta[0] < 0x20:
                decrypted_meta = decrypted_meta[1:]
            
            # 解析JSON元数据
            try:
                import json
                meta_str = decrypted_meta.decode('utf-8', errors='ignore')
                # 移除可能的垃圾字符
                meta_str = meta_str.strip('\x00').strip()
                if meta_str.startswith('{'):
                    self._meta = json.loads(meta_str)
                else:
                    self._meta = {'format': 'mp3'}
            except Exception:
                self._meta = {'format': 'mp3'}
        else:
            self._meta = {'format': 'mp3'}
        
        # 跳过CRC和图片等数据
        self._file.read(5)  # CRC32(4) + 未知(1)
        
        # 跳过图片数据
        img_len_bytes = self._file.read(4)
        img_len = struct.unpack('<I', img_len_bytes)[0]
        if img_len > 0:
            self._file.read(img_len)
        
        # 记录音频数据起始位置
        self._audio_offset = self._file.tell()
    
    def get_format(self) -> str:
        """获取音频格式"""
        if self._meta and 'format' in self._meta:
            return self._meta['format'].lower()
        return 'mp3'
    
    def get_metadata(self) -> dict:
        """获取元数据"""
        return self._meta or {}
    
    def decode(self, output_path: str, chunk_size: int = 8192) -> bool:
        """
        解码并保存到指定路径
        :param output_path: 输出文件路径
        :param chunk_size: 每次读取的块大小
        :return: 是否成功
        """
        if not self._file:
            raise RuntimeError("File not opened")
        
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 移动到音频数据起始位置
            self._file.seek(self._audio_offset)
            
            # 读取并解密音频数据
            with open(output_path, 'wb') as out_file:
                while True:
                    chunk = self._file.read(chunk_size)
                    if not chunk:
                        break
                    decrypted_chunk = _decrypt_core(chunk, self._key_box)
                    out_file.write(decrypted_chunk)
            
            return True
        except Exception as e:
            print(f"Decode error: {e}")
            return False


def decode_ncm(
    input_path: str,
    output_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    解码NCM文件
    :param input_path: 输入NCM文件路径
    :param output_path: 完整的输出文件路径（包含扩展名）
    :param output_dir: 输出目录（如果不指定output_path）
    :return: (成功与否, 输出路径, 错误信息)
    """
    try:
        with NCMDecoder(input_path) as decoder:
            # 确定输出路径
            if not output_path:
                name_without_ext = os.path.splitext(os.path.basename(input_path))[0]
                audio_format = decoder.get_format()
                if output_dir:
                    output_path = os.path.join(output_dir, f"{name_without_ext}.{audio_format}")
                else:
                    output_path = os.path.join(
                        os.path.dirname(input_path),
                        f"{name_without_ext}.{audio_format}"
                    )
            
            # 解码
            success = decoder.decode(output_path)
            if success:
                return True, output_path, None
            else:
                return False, None, "Decode failed"
    except Exception as e:
        return False, None, str(e)


def decode_ncm_with_callback(
    input_path: str,
    output_path_generator: Callable[[str, dict], str],
    skip_existing: bool = True
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    使用回调函数生成输出路径来解码NCM文件
    :param input_path: 输入NCM文件路径
    :param output_path_generator: 输出路径生成函数 (input_path, meta) -> output_path
    :param skip_existing: 是否跳过已存在的文件
    :return: (成功与否, 输出路径, 错误信息)
    """
    try:
        with NCMDecoder(input_path) as decoder:
            # 获取元数据
            meta = decoder.get_metadata()
            meta['format'] = decoder.get_format()
            
            # 生成输出路径
            output_path = output_path_generator(input_path, meta)
            
            # 检查是否已存在
            if skip_existing and os.path.exists(output_path):
                return True, output_path, "(skipped)"
            
            # 解码
            success = decoder.decode(output_path)
            if success:
                return True, output_path, None
            else:
                return False, None, "Decode failed"
    except Exception as e:
        return False, None, str(e)


# 兼容 ncmdump 库的接口
def dump(
    input_path: str,
    output_path_generator: Optional[Callable] = None,
    skip: bool = True
) -> Optional[str]:
    """
    兼容 ncmdump.dump 的接口
    :param input_path: 输入NCM文件路径
    :param output_path_generator: 输出路径生成函数
    :param skip: 是否跳过已存在的文件
    :return: 输出文件路径，失败返回None
    """
    try:
        with NCMDecoder(input_path) as decoder:
            meta = decoder.get_metadata()
            meta['format'] = decoder.get_format()
            
            if output_path_generator:
                output_path = output_path_generator(input_path, meta)
            else:
                name_without_ext = os.path.splitext(input_path)[0]
                output_path = f"{name_without_ext}.{meta['format']}"
            
            if skip and os.path.exists(output_path):
                return output_path
            
            success = decoder.decode(output_path)
            return output_path if success else None
    except Exception as e:
        print(f"Dump error: {e}")
        return None


# 测试代码
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ncm_decoder.py <ncm_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    success, output, error = decode_ncm(input_file)
    
    if success:
        print(f"Success: {output}")
    else:
        print(f"Failed: {error}")
