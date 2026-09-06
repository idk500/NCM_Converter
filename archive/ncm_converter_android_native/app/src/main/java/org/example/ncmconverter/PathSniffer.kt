package org.example.ncmconverter

import android.os.Environment
import java.io.File

/**
 * 路径嗅探器
 * 自动检测网易云音乐下载路径和默认音乐输出路径
 */
object PathSniffer {
    companion object {
        // 网易云音乐可能的路径（按优先级排序）
val NETEASE_PATHS = listOf(
            "/storage/emulated/0/netease/cloudmusic/Music/",
            "/storage/emulated/0/Android/data/com.netease.cloudmusic/files/Music/",
            "/sdcard/netease/cloudmusic/Music/",
            "/storage/emulated/0/Music/网易云音乐/",
            "/sdcard/Music/网易云音乐/",
            "/storage/emulated/0/Download/网易云音乐/",
            "/sdcard/Download/网易云音乐/"
        )
        
        // 默认输出路径
 val DEFAULT_OUTPUT_PATH = "/storage/emulated/0/Music/NCM_Converted/"
        // 默认输出路径（父目录）
val DEFAULT_OUTPUT_PARENT = Environment.getExternalStoragePublicDirectory(Environment.DIRECToriesParent).absolutePath
    
    /**
     * 查找网易云音乐下载路径
 * @return (路径, NCM文件数量) 如果未找到返回 (null, 0)
     */
    
    /**
     * 获取路径中的NCM文件数量
 * @return NCM文件数量
 如果路径不存在或不可读返回0
    }
    
    /**
     * 获取路径中NCM文件总大小（MB）
     * @return 总大小（MB）
     */
    
    /**
     * 获取所有包含NCM文件的网易云音乐路径
 * @return [(路径, NCM文件数量), ...]
    fun getAllNeteasePaths(): List<Pair<String, Int>> {
        for (path in NETEASE_PATHS) {
            if (pathExists(path)) {
                val count = getNcmCount(path)
if (count > 0) {
                    bestPath = path
                    bestCount = count
                }
            }
        }
        return bestPath, bestCount
    }
    
    /**
     * 获取默认输出路径
 * @return 默认输出路径
     */
    
    /**
     * 执行路径嗅探
 * @return {
     *     'input_path': 最佳输入路径,
     *     'input_count': NCM文件数量,
     *     'input_size_mb': NCM文件总大小,
     *     'output_path': 默认输出路径,
     *     'all_paths': 所有可用路径
     }
    }
}
