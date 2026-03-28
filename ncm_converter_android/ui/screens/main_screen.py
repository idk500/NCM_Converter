"""
主界面 - Material Design风格
简化版本，直接使用Python代码创建界面
"""
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFloatingActionButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.boxlayout import MDBoxLayout

from app.converter import NCMConverter
from app.path_sniffer import PathSniffer as PathSnifferClass


class MainScreen(MDScreen):
    """主界面"""
    
    input_path = StringProperty(None)
    output_path = StringProperty(None)
    ncm_count = NumericProperty(0)
    total_size_mb = NumericProperty(0)
    progress = NumericProperty(0)
    total = NumericProperty(1)
    current_file = StringProperty(None)
    logs = ListProperty([])
    is_converting = BooleanProperty(False)
    converter = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_path = None
        self.output_path = None
        self.ncm_count = 0
        self.total_size_mb = 0
        self.progress = 0
        self.total = 1
        self.current_file = ''
        self.logs = []
        self.is_converting = False
        self.converter = None
        
        # 嗅探路径
        Clock.schedule_once(self.sniff_paths)
    
    def sniff_paths(self, *args):
        """执行路径嗅探"""
        result = PathSnifferClass.sniff()
        
        if result['input_path']:
            self.input_path = result['input_path']
            self.ncm_count = result['input_count']
            self.total_size_mb = result['input_size_mb']
        else:
            self.input_path = None
            self.ncm_count = 0
            self.total_size_mb = 0
        
        self.output_path = result['output_path']
        
        # 更新UI
        self._update_ui()
    
    def _update_ui(self):
        """更新UI"""
        if self.input_path:
            self.ids.input_path_label.text = self.input_path
            self.ids.input_info_label.text = f'发现 {self.ncm_count} 个NCM文件 ({self.total_size_mb:.1f}MB)'
        else:
            self.ids.input_path_label.text = '未检测到NCM文件'
            self.ids.input_info_label.text = '请手动选择输入路径'
        
        if self.output_path:
            self.ids.output_path_label.text = self.output_path
        else:
            self.ids.output_path_label.text = '请选择输出路径'
    
    def start_conversion(self):
        """开始转换"""
        if self.is_converting:
            return
        
        if not self.input_path:
            Snackbar(text='请先选择输入路径').open()
            return
        
        if not self.output_path:
            Snackbar(text='请先选择输出路径').open()
            return
        
        self.is_converting = True
        self.converter = NCMConverter(self.input_path, self.output_path)
        
        # 更新UI
        self.ids.progress_bar.value = 0
        self.ids.progress_label.text = '准备开始转换...'
        self.ids.convert_button.disabled = True
        
        # 开始转换
        self.converter.convert_all(
            progress_callback=self._update_progress,
            log_callback=self._add_log
        )
    
    def stop_conversion(self):
        """停止转换"""
        if self.converter:
            self.converter.stop()
        self.is_converting = False
        
        # 更新UI
        self.ids.convert_button.disabled = False
        self.ids.convert_button.icon = 'play'
    
    def _update_progress(self, current: int, total: int, filename: str):
        """更新进度"""
        self.progress = current
        self.total = total
        self.current_file = filename
        
        # 更新进度条
        self.ids.progress_bar.value = current / total
        
        # 更新标签
        self.ids.progress_label.text = f'正在转换: {filename} ({current}/{total})'
        
        # 更新按钮状态
        self.ids.convert_button.disabled = current < total
        self.ids.convert_button.icon = 'stop' if current < total else 'play'
    
    def _add_log(self, message: str):
        """添加日志"""
        self.logs.append(message)
        self.ids.log_label.text = '\n'.join(self.logs)
