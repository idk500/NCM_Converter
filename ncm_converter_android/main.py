"""
NCM Converter Android - 主入口
网易云音乐NCM格式转换器安卓版
"""
import os
import sys

# 确保能找到app模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

# 导入界面
from ui.screens.main_screen import MainScreen


class NCMConverterApp(MDApp):
    """NCM转换器应用"""
    
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.title = "NCM转换器"
        
        # 创建界面管理器
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        
        return sm
    
    def on_start(self):
        """应用启动时调用"""
        pass


def main():
    """主函数"""
    NCMConverterApp().run()


if __name__ == '__main__':
    main()
