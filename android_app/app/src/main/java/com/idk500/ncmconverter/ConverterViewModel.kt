package com.idk500.ncmconverter

import android.Manifest
import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.pm.PackageManager
import android.net.Uri
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class InputFile(val uri: Uri, val name: String)

data class UiState(
    val inputs: List<InputFile> = emptyList(),
    val inputFolderName: String? = null,
    val outputTreeUri: Uri? = null,
    val running: Boolean = false,
    val done: Int = 0,
    val total: Int = 0,
    val logs: List<String> = emptyList(),
)

class ConverterViewModel(app: Application) : AndroidViewModel(app) {

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    private val logLock = Any()

    fun onFilesPicked(uris: List<Uri>) {
        viewModelScope.launch {
            val files = withContext(Dispatchers.IO) {
                uris.mapNotNull { uri ->
                    NcmStore.displayNameOf(getApplication(), uri)?.let { InputFile(uri, it) }
                }
            }
            _state.update {
                it.copy(inputs = (it.inputs + files).distinctBy(InputFile::uri), inputFolderName = null)
            }
        }
    }

    fun onInputFolderPicked(treeUri: Uri) {
        val app = getApplication<Application>()
        runCatching {
            app.contentResolver.takePersistableUriPermission(
                treeUri,
                android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION,
            )
        }
        viewModelScope.launch {
            val files = withContext(Dispatchers.IO) { NcmStore.listNcmInTree(app, treeUri) }
                .map { (uri, name) -> InputFile(uri, name) }
            _state.update {
                it.copy(
                    inputs = (it.inputs + files).distinctBy(InputFile::uri),
                    inputFolderName = NcmStore.friendlyTreeName(app, treeUri),
                )
            }
        }
    }

    fun onOutputFolderPicked(treeUri: Uri) {
        runCatching {
            getApplication<Application>().contentResolver.takePersistableUriPermission(
                treeUri,
                android.content.Intent.FLAG_GRANT_WRITE_URI_PERMISSION,
            )
        }
        _state.update { it.copy(outputTreeUri = treeUri) }
    }

    fun onOutputFolderReset() = _state.update { it.copy(outputTreeUri = null) }

    fun clearInputs() = _state.update { it.copy(inputs = emptyList(), inputFolderName = null) }

    fun appendLog(line: String) {
        synchronized(logLock) {
            _state.update { it.copy(logs = (it.logs + line).takeLast(300)) }
        }
    }

    fun startConversion() {
        val app = getApplication<Application>()
        val current = _state.value
        if (current.running || current.inputs.isEmpty()) return

        _state.update { it.copy(running = true, done = 0, total = current.inputs.size) }
        ensureNotificationChannel()

        viewModelScope.launch {
            val workDir = File(app.cacheDir, "conv").apply { deleteRecursively(); mkdirs() }
            val inputs = current.inputs
            withContext(Dispatchers.IO) {
                inputs.forEachIndexed { index, input ->
                    appendLog("(${index + 1}/${inputs.size}) 开始：${input.name}")
                    try {
                        val tempIn = File(workDir, "in_$index.ncm")
                        app.contentResolver.openInputStream(input.uri)?.use { stream ->
                            tempIn.outputStream().use { stream.copyTo(it) }
                        } ?: error("无法读取所选文件")

                        val out = PythonConverter.convert(
                            tempIn.absolutePath,
                            workDir.absolutePath,
                            input.name.removeSuffix(".ncm"),
                        )
                        val converted = File(out.path)
                        if (!converted.exists()) error("转换未产出文件")

                        val alreadyExists = _state.value.outputTreeUri?.let { tree ->
                            NcmStore.treeContains(app, tree, out.name)
                        } ?: NcmStore.mediaStoreContains(app, out.name)

                        if (alreadyExists) {
                            appendLog("跳过（已存在）：${out.name}")
                        } else {
                            val tree = _state.value.outputTreeUri
                            if (tree != null) {
                                NcmStore.saveToTree(app, tree, converted, out.name, NcmStore.mimeOf(out.format))
                            } else {
                                NcmStore.saveToMediaStore(app, converted, out.name, NcmStore.mimeOf(out.format))
                            }
                            appendLog("完成：${out.name}")
                        }
                        converted.delete()
                    } catch (e: Exception) {
                        appendLog("失败：${input.name} — ${e.message ?: e.javaClass.simpleName}")
                    } finally {
                        File(workDir, "in_$index.ncm").delete()
                    }
                    _state.update { it.copy(done = index + 1) }
                }
                workDir.deleteRecursively()
            }
            val finished = _state.value
            _state.update { it.copy(running = false) }
            notifyDone(finished.inputs.size)
        }
    }

    private fun ensureNotificationChannel() {
        val nm = getApplication<Application>().getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "转换完成", NotificationManager.IMPORTANCE_DEFAULT),
        )
    }

    private fun notifyDone(total: Int) {
        val app = getApplication<Application>()
        if (ContextCompat.checkSelfPermission(app, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            return
        }
        val okCount = _state.value.logs.count { it.startsWith("完成：") }
        val notification = android.app.Notification.Builder(app, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_download_done)
            .setContentTitle("NCM 转换完成")
            .setContentText("成功 $okCount / 共 $total 个文件")
            .setAutoCancel(true)
            .build()
        NotificationManagerCompat.from(app).notify(NOTIFY_ID, notification)
    }

    companion object {
        private const val CHANNEL_ID = "conversion"
        private const val NOTIFY_ID = 1
    }
}
