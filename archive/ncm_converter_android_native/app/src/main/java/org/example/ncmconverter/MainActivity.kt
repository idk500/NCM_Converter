package org.example.ncmconverter

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.util.Locale

class MainActivity : AppCompatActivity() {
    
    // UI组件
    private lateinit var tvInputPath: TextView
    private lateinit var tvInputInfo: TextView
    private lateinit var tvOutputPath: TextView
    private lateinit var tvProgress: TextView
    private lateinit var tvCurrentFile: TextView
    private lateinit var tvLog: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var btnConvert: Button
    private lateinit var scrollView: ScrollView
    
    // 状态
    private var inputPath: String? = null
    private var outputPath: String? = null
    private var ncmFiles: List<File> = emptyList()
    private var isConverting: Boolean = false
    private var shouldStop: Boolean = false
    
    // 权限请求码
    private val PERMISSION_REQUEST_CODE = 100
    
    companion object {
        // 网易云音乐可能的路径
        val NETEASE_PATHS = listOf(
            "/storage/emulated/0/netease/cloudmusic/Music/",
            "/storage/emulated/0/Android/data/com.netease.cloudmusic/files/Music/",
            "/sdcard/netease/cloudmusic/Music/",
            "/storage/emulated/0/Music/网易云音乐/",
            "/sdcard/Music/网易云音乐/"
        )
        
        // 默认输出路径
        val DEFAULT_OUTPUT_PATH = "/storage/emulated/0/Music/NCM_Converted/"
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        initViews()
        checkPermissions()
    }
    
    private fun initViews() {
        tvInputPath = findViewById(R.id.tv_input_path)
        tvInputInfo = findViewById(R.id.tv_input_info)
        tvOutputPath = findViewById(R.id.tv_output_path)
        tvProgress = findViewById(R.id.tv_progress)
        tvCurrentFile = findViewById(R.id.tv_current_file)
        tvLog = findViewById(R.id.tv_log)
        progressBar = findViewById(R.id.progress_bar)
        btnConvert = findViewById(R.id.btn_convert)
        scrollView = findViewById(R.id.scroll_view)
        
        btnConvert.setOnClickListener {
            if (isConverting) {
                stopConversion()
            } else {
                startConversion()
            }
        }
    }
    
    private fun checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            // Android 10及以上需要MANAGE_EXTERNAL_STORAGE权限
            if (checkSelfPermission(Manifest.permission.MANAGE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                // 请求MANAGE_EXTERNAL_STORAGE权限
                requestPermissions(arrayOfManifest.permission.MANAGE_EXTERNAL_STORAGE), PERMISSION_REQUEST_CODE)
            } else {
                // Android 10以下需要READ_EXTERNAL_STORAGE和 WRITE_EXTERNAL_STORAGE权限
                if (checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED ||
                    ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE), PERMISSION_REQUEST_CODE)
                }
                if (checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                    ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE), PERMISSION_REQUEST_CODE)
                }
            }
        }
    }
    
    private fun sniffPaths() {
        lifecycleScope.launch(Dispatchers.IO) {
            // 查找网易云音乐路径
            var foundPath: String? = null
            var foundCount = 0
            var foundSize = 0L
            
            for (path in NETEASE_PATHS) {
                val dir = File(path)
                if (dir.exists() && dir.isDirectory) {
                    val files = dir.listFiles { _, it -> it.endsWith(".ncm", ignoreCase = true) }
                    val count = files.size
                    val size = files.sum { it.length() }
                    if (count > foundCount) {
                        foundPath = path
                        foundCount = count
                        foundSize = size
                    }
                }
            }
            
            // 设置路径
            inputPath = foundPath
            ncmFiles.clear()
            if (foundPath != null) {
                for (f in File(foundPath).listFiles()) {
                    if (f.endsWith(".ncm", ignoreCase = true)) {
                        ncmFiles.add(f)
                    }
                }
            }
            
            // 设置输出路径
            outputPath = DEFAULT_OUTPUT_PATH
            val outputDir = File(outputPath)
            if (!outputDir.exists()) {
                outputDir.mkdirs()
            }
            
            // 更新UI
            withContext(Dispatchers.Main) {
                if (foundPath != null) {
                    tvInputPath.text = "未检测到NCM文件"
                    tvInputInfo.text = "请手动选择输入路径"
                    btnConvert.isEnabled = false
                } else {
                    tvInputPath.text = foundPath
                    tvInputInfo.text = "发现 ${foundCount} 个NCM文件 (${formatSize(foundSize / (1024.0 / 1024)} MB)"
                    btnConvert.isEnabled = true
                }
                tvOutputPath.text = outputPath
            }
        }
    }
    
    private fun startConversion() {
        if (inputPath == null || ncmFiles.isEmpty()) {
            Toast.makeText(this, "请先选择输入路径", Toast.LENGTH_SHORT).show()
            return
        }
        
        if (outputPath == null) {
            Toast.makeText(this, "请先选择输出路径", Toast.LENGTH_SHORT).show()
            return
        }
        
        isConverting = true
        shouldStop = false
        btnConvert.text = "停止转换"
        progressBar.progress = 0
        tvProgress.text = "准备开始转换..."
        tvLog.text = ""
        
        lifecycleScope.launch(Dispatchers.IO) {
            var successCount = 0
            var failureCount = 0
            
            for ((index, file) in ncmFiles.withIndex()) {
                if (shouldStop) {
                    withContext(Dispatchers.Main) {
                        tvProgress.text = "转换已取消"
                        btnConvert.text = "开始转换"
                        isConverting = false
                    }
                    return@withContext(Dispatchers.IO) {
                        break
                    }
                }
                
                try {
                    val result = NCMConverter.convert(file.absolutePath, outputPath!!)
                    
                    if (result.success) {
                        successCount++
                        val sizeMB = result.sizeBytes / (1024.0 * 1024)
                        withContext(Dispatchers.Main) {
                            tvLog.append("✓ ${file.name} -> ${result.outputName} (${String.format("%.2f MB", sizeMB)}")
                        }
                    } else {
                        failureCount++
                        withContext(Dispatchers.Main) {
                            tvLog.append("✗ ${file.name} - ${result.error}")
                        }
                    }
                    
                    withContext(Dispatchers.Main) {
                        val progress = ((index + 1) * 100 / ncmFiles.size)
                        progressBar.progress = progress
                        tvCurrentFile.text = "正在转换: ${file.name} (${index + 1}/${ncmFiles.size})"
                    }
                } catch (e: Exception) {
                    failureCount++
                    withContext(Dispatchers.Main) {
                        tvLog.append("✗ ${file.name} - ${e.message}")
                    }
                }
            }
            
            withContext(Dispatchers.Main) {
                isConverting = false
                btnConvert.text = "开始转换"
                tvProgress.text = "转换完成! 成功: $successCount, 夲失败: $failureCount"
                tvLog.append("\n转换完成! 成功: $successCount, 夲失败: $failureCount")
                
                Toast.makeText(this, "转换完成! 成功: $successCount, 夲失败: $failureCount", Toast.LENGTH_LONG).show()
            }
        }
    }
    
    private fun stopConversion() {
        shouldStop = true
        isConverting = false
        btnConvert.text = "开始转换"
        tvProgress.text = "转换已停止"
    }
}
