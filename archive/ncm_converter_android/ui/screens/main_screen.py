"""
主界面 - Material Design风格
"""
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFloatingActionButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout

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
        
        # 构建UI
        self._build_ui()
        
        # 嗅探路径
        Clock.schedule_once(self.sniff_paths)
    
    def _build_ui(self):
        """构建用户界面"""
        # 主布局
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding='16dp',
            spacing='16dp'
        )
        
        # 标题
        title_label = MDLabel(
            text='NCM转换器',
            font_style='H4',
            halign='center',
            size_hint_y=None,
            height='48dp'
        )
        main_layout.add_widget(title_label)
        
        # 输入路径卡片
        input_card = MDCard(
            orientation='vertical',
            padding='16dp',
            spacing='8dp',
            size_hint_y=None,
            height='120dp',
            elevation=2
        )
        
        input_title = MDLabel(
            text='输入路径',
            font_style='Subtitle1',
            size_hint_y=None,
            height='24dp'
        )
        input_card.add_widget(input_title)
        
        self.ids.input_path_label = MDLabel(
            text='正在检测...',
            font_style='Body2',
            theme_text_color='Secondary',
            size_hint_y=None,
            height='24dp'
        )
        input_card.add_widget(self.ids.input_path_label)
        
        self.ids.input_info_label = MDLabel(
            text='',
            font_style='Caption',
            theme_text_color='Hint',
            size_hint_y=None,
            height='24dp'
        )
        input_card.add_widget(self.ids.input_info_label)
        
        main_layout.add_widget(input_card)
        
        # 输出路径卡片
        output_card = MDCard(
            orientation='vertical',
            padding='16dp',
            spacing='8dp',
            size_hint_y=None,
            height='100dp',
            elevation=2
        )
        
        output_title = MDLabel(
            text='输出路径',
            font_style='Subtitle1',
            size_hint_y=None,
            height='24dp'
        )
        output_card.add_widget(output_title)
        
        self.ids.output_path_label = MDLabel(
            text='正在检测...',
            font_style='Body2',
            theme_text_color='Secondary',
            size_hint_y=None,
            height='24dp'
        )
        output_card.add_widget(self.ids.output_path_label)
        
        main_layout.add_widget(output_card)
        
        # 进度卡片
        progress_card = MDCard(
            orientation='vertical',
            padding='16dp',
            spacing='8dp',
            size_hint_y=None,
            height='100dp',
            elevation=2
        )
        
        self.ids.progress_label = MDLabel(
            text='准备就绪',
            font_style='Body1',
            size_hint_y=None,
            height='24dp'
        )
        progress_card.add_widget(self.ids.progress_label)
        
        self.ids.progress_bar = MDProgressBar(
            value=0,
            size_hint_y=None,
            height='8dp'
        )
        progress_card.add_widget(self.ids.progress_bar)
        
        main_layout.add_widget(progress_card)
        
        # 日志区域
        log_card = MDCard(
            orientation='vertical',
            padding='16dp',
            spacing='8dp',
            size_hint_y=None,
            elevation=2
        )
        
        log_title = MDLabel(
            text='转换日志',
            font_style='Subtitle1',
            size_hint_y=None,
            height='24dp'
        )
        log_card.add_widget(log_title)
        
        scroll_view = ScrollView(
            size_hint_y=None,
            height='150dp'
        )
        
        self.ids.log_label = MDLabel(
            text='等待开始...',
            font_style='Caption',
            size_hint_y=None,
            valign='top',
            text_size=(None, None)
        )
        self.ids.log_label.bind(texture_size=self.ids.log_label.setter('size'))
        scroll_view.add_widget(self.ids.log_label)
        log_card.add_widget(scroll_view)
        
        main_layout.add_widget(log_card)
        
        # 转换按钮
        self.ids.convert_button = MDRaisedButton(
            text='开始转换',
            pos_hint={'center_x': 0.5},
            size_hint_x=None,
            width='200dp',
            on_release=self._on_convert_button_pressed
        )
        main_layout.add_widget(self.ids.convert_button)
        
        # 添加到屏幕
        self.add_widget(main_layout)
    
    def _on_convert_button_pressed(self, instance):
        """转换按钮点击事件"""
        if self.is_converting:
            self.stop_conversion()
        else:
            self.start_conversion()
    
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
        self.ids.convert_button.text = '停止转换'
        
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
        self.ids.convert_button.text = '开始转换'
    
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
        if current >= total:
            self.is_converting = False
            self.ids.convert_button.text = '开始转换'
    
    def _add_log(self, message: str):
        """添加日志"""
        self.logs.append(message)
        self.ids.log_label.text = '\n'.join(self.logs)
