"""
NCM转换核心逻辑
复用PC版的转换功能
"""
import os
import time
from ncmdump import dump


class ConversionResult:
    """转换结果"""
    def __init__(self, success: bool, input_file: str, output_file: str = None, 
                 error: str = None, size_mb: float = 0, elapsed_time: float = 0):
        self.success = success
        self.input_file = input_file
        self.output_file = output_file
        self.error = error
        self.size_mb = size_mb
        self.elapsed_time = elapsed_time


class NCMConverter:
    """NCM文件转换器"""
    
    def __init__(self, input_path: str, output_path: str, skip_existing: bool = True):
        """
        初始化转换器
        :param input_path: 输入路径（包含NCM文件的文件夹）
        :param output_path: 输出路径
        :param skip_existing: 是否跳过已存在的文件
        """
        self.input_path = input_path
        self.output_path = output_path
        self.skip_existing = skip_existing
        self._is_converting = False
        self._should_stop = False
    
    def get_ncm_files(self) -> list:
        """获取输入路径中的所有NCM文件"""
        if not os.path.exists(self.input_path):
            return []
        
        return [f for f in os.listdir(self.input_path) if f.lower().endswith('.ncm')]
    
    def get_ncm_count(self) -> int:
        """获取NCM文件数量"""
        return len(self.get_ncm_files())
    
    def get_total_size_mb(self) -> float:
        """获取NCM文件总大小（MB）"""
        total_size = 0
        for filename in self.get_ncm_files():
            filepath = os.path.join(self.input_path, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
        return total_size / (1024 * 1024)
    
    def ensure_output_dir(self) -> bool:
        """确保输出目录存在"""
        if not os.path.exists(self.output_path):
            try:
                os.makedirs(self.output_path)
                return True
            except Exception as e:
                print(f"无法创建输出目录: {e}")
                return False
        return True
    
    def check_file_exists(self, filename: str) -> bool:
        """检查输出文件是否已存在"""
        name_without_ext = os.path.splitext(filename)[0]
        for ext in ['.mp3', '.flac']:
            check_path = os.path.join(self.output_path, name_without_ext + ext)
            if os.path.exists(check_path):
                return True
        return False
    
    def convert_file(self, filename: str) -> ConversionResult:
        """
        转换单个NCM文件
        :param filename: NCM文件名
        :return: ConversionResult对象
        """
        ncm_file_path = os.path.join(self.input_path, filename)
        
        # 检查是否已存在
        if self.skip_existing and self.check_file_exists(filename):
            return ConversionResult(
                success=True,
                input_file=filename,
                output_file="(已跳过)",
                size_mb=0,
                elapsed_time=0
            )
        
        start_time = time.time()
        
        try:
            # 定义输出路径生成函数
            def output_path_generator(input_path, meta):
                name_without_ext = os.path.splitext(os.path.basename(input_path))[0]
                return os.path.join(self.output_path, name_without_ext + '.' + meta['format'])
            
            # 执行转换
            output_path = dump(ncm_file_path, output_path_generator, skip=self.skip_existing)
            
            elapsed_time = time.time() - start_time
            
            if output_path and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                size_mb = file_size / (1024 * 1024)
                
                return ConversionResult(
                    success=True,
                    input_file=filename,
                    output_file=os.path.basename(output_path),
                    size_mb=size_mb,
                    elapsed_time=elapsed_time
                )
            else:
                return ConversionResult(
                    success=False,
                    input_file=filename,
                    error="转换失败，无法生成输出文件"
                )
                
        except Exception as e:
            return ConversionResult(
                success=False,
                input_file=filename,
                error=str(e)
            )
    
    def convert_all(self, progress_callback=None, log_callback=None):
        """
        转换所有NCM文件
        :param progress_callback: 进度回调函数 callback(current, total, filename)
        :param log_callback: 日志回调函数 callback(message)
        """
        if self._is_converting:
            return
        
        self._is_converting = True
        self._should_stop = False
        
        # 确保输出目录存在
        if not self.ensure_output_dir():
            if log_callback:
                log_callback("错误: 无法创建输出目录")
            self._is_converting = False
            return
        
        ncm_files = self.get_ncm_files()
        total = len(ncm_files)
        
        if total == 0:
            if log_callback:
                log_callback("未找到NCM文件")
            self._is_converting = False
            return
        
        if log_callback:
            log_callback(f"开始转换 {total} 个文件...")
        
        success_count = 0
        failure_count = 0
        
        for i, filename in enumerate(ncm_files, 1):
            if self._should_stop:
                if log_callback:
                    log_callback("转换已取消")
                break
            
            # 更新进度
            if progress_callback:
                progress_callback(i, total, filename)
            
            # 转换文件
            result = self.convert_file(filename)
            
            if result.success:
                success_count += 1
                if log_callback:
                    if result.output_file == "(已跳过)":
                        log_callback(f"✓ 跳过: {filename}")
                    else:
                        log_callback(f"✓ {filename} -> {result.output_file} ({result.size_mb:.2f}MB, {result.elapsed_time:.2f}s)")
            else:
                failure_count += 1
                if log_callback:
                    log_callback(f"✗ 失败: {filename} - {result.error}")
        
        self._is_converting = False
        
        if log_callback:
            log_callback(f"\n转换完成! 成功: {success_count}, 失败: {failure_count}")
    
    def stop(self):
        """停止转换"""
        self._should_stop = True
    
    @property
    def is_converting(self):
        return self._is_converting
