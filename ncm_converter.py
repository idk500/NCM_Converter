import os
import sys
import time
import argparse
from ncmdump import dump
import traceback
import ctypes
import locale
import webbrowser

def convert_ncm_files(input_folder_path, output_folder_path, skip_existing=True):
    """
    转换指定文件夹中的所有.ncm文件
    :param input_folder_path: 包含.ncm文件的输入文件夹路径
    :param output_folder_path: 输出文件夹路径
    :param skip_existing: 是否跳过已存在的文件
    """
    if not os.path.exists(input_folder_path):
        print(f"错误: 输入文件夹 '{input_folder_path}' 不存在")
        return False
    
    if not os.path.isdir(input_folder_path):
        print(f"错误: '{input_folder_path}' 不是一个有效的文件夹")
        return False
    
    # 创建输出文件夹（如果不存在）
    if not os.path.exists(output_folder_path):
        try:
            os.makedirs(output_folder_path)
            print(f"创建输出文件夹: {output_folder_path}")
        except Exception as e:
            print(f"错误: 无法创建输出文件夹 '{output_folder_path}': {str(e)}")
            return False
    
    if not os.path.isdir(output_folder_path):
        print(f"错误: '{output_folder_path}' 不是一个有效的文件夹")
        return False
    
    # 获取所有.ncm文件
    ncm_files = [f for f in os.listdir(input_folder_path) if f.lower().endswith('.ncm')]
    
    if not ncm_files:
        print(f"在文件夹 '{input_folder_path}' 中未找到.ncm文件")
        return False
    
    print(f"找到 {len(ncm_files)} 个.ncm文件待转换")
    print(f"输出文件夹: {output_folder_path}")
    
    success_count = 0
    failure_count = 0
    total_start_time = time.time()
    
    for i, filename in enumerate(ncm_files, 1):
        try:
            ncm_file_path = os.path.join(input_folder_path, filename)
            print(f"[{i}/{len(ncm_files)}] 正在转换: {filename}...")
            
            # 记录单个文件转换开始时间
            start_time = time.time()
            
            # 检查是否已存在目标文件且需要跳过
            # 由于我们不知道确切的扩展名，我们需要检查常见的音频格式
            target_exists = False
            if skip_existing:
                name_without_ext = os.path.splitext(filename)[0]
                for ext in ['.mp3', '.flac']:
                    check_path = os.path.join(output_folder_path, name_without_ext + ext)
                    if os.path.exists(check_path):
                        target_exists = True
                        break
            
            if target_exists and skip_existing:
                print(f"→ 跳过已存在的文件: {filename}")
                success_count += 1
                continue
            
            # 使用ncmdump进行转换到指定输出文件夹
            # 我们需要创建一个函数来生成正确的输出路径
            def output_path_generator(input_path, meta):
                name_without_ext = os.path.splitext(os.path.basename(input_path))[0]
                output_file = os.path.join(output_folder_path, name_without_ext + '.' + meta['format'])
                return output_file
            
            output_path = dump(ncm_file_path, output_path_generator, skip=skip_existing)
            
            # 计算转换耗时
            elapsed_time = time.time() - start_time
            
            if output_path and os.path.exists(output_path):
                # 获取文件大小
                file_size = os.path.getsize(output_path)
                size_mb = file_size / (1024 * 1024)
                print(f"✓ 成功转换 {filename} 到 {os.path.basename(output_path)} ({size_mb:.2f}MB, 耗时: {elapsed_time:.2f}秒)")
                success_count += 1
            else:
                print(f"✗ 转换失败: {filename}")
                failure_count += 1
                
        except Exception as e:
            print(f"✗ 转换出错 {filename}: {str(e)}")
            traceback.print_exc()
            failure_count += 1
    
    # 总耗时
    total_elapsed_time = time.time() - total_start_time
    
    print(f"\n转换完成! 成功: {success_count}, 失败: {failure_count}")
    print(f"总耗时: {total_elapsed_time:.2f}秒")
    
    if success_count > 0:
        avg_time = total_elapsed_time / success_count
        print(f"平均每个文件转换耗时: {avg_time:.2f}秒")
    
    return failure_count == 0

def get_system_language():
    """
    Get the system UI language
    获取系统UI语言
    """
    try:
        # Get Windows system language code
        windll = ctypes.windll.kernel32
        lang_code = windll.GetUserDefaultUILanguage()
        # Convert to language name using locale.windows_locale
        lang_name = locale.windows_locale.get(lang_code, 'en_US')
        # Check if it's Chinese
        if lang_name.startswith('zh_'):
            return 'zh'
        else:
            return 'en'
    except Exception:
        # Default to English if there's an error
        return 'en'

def main():
    """
    Main function
    主函数
    """
    # Get system language
    lang = get_system_language()
    
    # Configure argument parser based on language
    if lang == 'zh':
        parser = argparse.ArgumentParser(description="NCM格式音频文件转换工具")
        parser.add_argument("input_folder", nargs="?", help="包含.ncm文件的输入文件夹路径（默认为当前目录）")
        parser.add_argument("output_folder", nargs="?", help="输出文件夹路径（默认为 ./decode）")
        parser.add_argument("--force", action="store_true", help="强制覆盖已存在的文件")
        parser.add_argument("--version", action="version", version="NCM转换工具 1.0")
        parser.add_argument("--about", action="store_true", help="显示关于信息")
    else:
        parser = argparse.ArgumentParser(description="NCM Audio File Converter")
        parser.add_argument("input_folder", nargs="?", help="Input folder path containing .ncm files (default: current directory)")
        parser.add_argument("output_folder", nargs="?", help="Output folder path (default: ./decode)")
        parser.add_argument("--force", action="store_true", help="Force overwrite existing files")
        parser.add_argument("--version", action="version", version="NCM Converter 1.0")
        parser.add_argument("--about", action="store_true", help="Show about information")
    
    args = parser.parse_args()
    
    # Handle --about parameter
    if args.about:
        if lang == 'zh':
            print("=== 关于 NCM转换工具 ===")
            print("作者: idk500")
            print("GitHub: https://github.com/idk500/")
        else:
            print("=== About NCM Converter ===")
            print("Author: idk500")
            print("GitHub: https://github.com/idk500/")
        
        try:
            webbrowser.open('https://github.com/idk500/')
            if lang == 'zh':
                print("\n已打开浏览器访问GitHub页面")
            else:
                print("\nBrowser opened to GitHub page")
        except Exception:
            if lang == 'zh':
                print("\n无法打开浏览器，请手动访问GitHub页面")
            else:
                print("\nFailed to open browser, please visit GitHub page manually")
        
        sys.exit(0)
    
    # Print welcome message based on language
    if lang == 'zh':
        print("=== NCM格式音频文件转换工具 ===")
        print("注意: 此工具仅用于个人学习和研究目的，请尊重版权")
    else:
        print("=== NCM Audio File Converter ===")
        print("Note: This tool is for personal learning and research purposes only. Please respect copyright.")
    print()
    
    # 设置默认路径
    input_folder = args.input_folder if args.input_folder else "."
    output_folder = args.output_folder if args.output_folder else "./decode"
    
    # 处理路径中的引号（用户可能复制粘贴带引号的路径）
    input_folder = input_folder.strip('"\'')
    output_folder = output_folder.strip('"\'')
    
    # 转换文件
    success = convert_ncm_files(input_folder, output_folder, skip_existing=not args.force)
    
    if success:
        print("\n🎉 所有文件转换成功!")
    else:
        print("\n⚠️ 部分文件转换失败，请查看上面的错误信息")
    
    # 等待用户按键后退出
    if lang == 'zh':
        input("\n按回车键退出...")
    else:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()