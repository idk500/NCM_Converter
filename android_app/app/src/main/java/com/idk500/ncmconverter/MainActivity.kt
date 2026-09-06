package com.idk500.ncmconverter

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel

class MainActivity : ComponentActivity() {

    private val vm: ConverterViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }
        setContent {
            MaterialTheme(colorScheme = MaterialTheme.colorScheme) {
                ConverterScreen(vm)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConverterScreen(vm: ConverterViewModel) {
    val state by vm.state.collectAsState()
    val context = LocalContext.current

    // Keep the screen on while converting; a v1 guard against mid-conversion doze.
    DisposableEffect(state.running) {
        val window = (context as? ComponentActivity)?.window
        if (state.running) window?.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        else window?.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        onDispose { window?.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) }
    }

    val pickFiles = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
        if (uris.isNotEmpty()) vm.onFilesPicked(uris)
    }
    val pickInputFolder = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        uri?.let(vm::onInputFolderPicked)
    }
    val pickOutputFolder = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        uri?.let(vm::onOutputFolderPicked)
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("NCM 转换器") },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                ),
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .padding(horizontal = 16.dp)
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            SourceCard(
                state = state,
                onPickFiles = { pickFiles.launch(arrayOf("*/*")) },
                onPickFolder = { pickInputFolder.launch(null) },
                onClear = vm::clearInputs,
            )
            OutputCard(
                state = state,
                onPick = { pickOutputFolder.launch(null) },
                onReset = vm::onOutputFolderReset,
            )
            Button(
                onClick = vm::startConversion,
                enabled = state.inputs.isNotEmpty() && !state.running,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(if (state.running) "转换中…" else "开始转换")
            }
            if (state.total > 0) {
                LinearProgressIndicator(
                    progress = { if (state.total == 0) 0f else state.done.toFloat() / state.total },
                    modifier = Modifier.fillMaxWidth(),
                )
                Text(
                    "${state.done} / ${state.total}",
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.align(Alignment.CenterHorizontally),
                )
            }
            LogCard(state.logs)
            Spacer(modifier = Modifier.height(12.dp))
        }
    }
}

@Composable
private fun SourceCard(
    state: UiState,
    onPickFiles: () -> Unit,
    onPickFolder: () -> Unit,
    onClear: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("① 选择要转换的 NCM 文件", style = MaterialTheme.typography.titleMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onPickFiles, modifier = Modifier.weight(1f)) { Text("选择文件") }
                OutlinedButton(onClick = onPickFolder, modifier = Modifier.weight(1f)) { Text("选择文件夹") }
            }
            val source = when {
                state.inputs.isEmpty() -> "未选择。可直接从网易云音乐下载目录挑选。"
                state.inputFolderName != null ->
                    "已选择文件夹，共 ${state.inputs.size} 个 NCM 文件"
                else -> "已选择 ${state.inputs.size} 个文件"
            }
            Text(source, style = MaterialTheme.typography.bodySmall)
            if (state.inputs.isNotEmpty()) {
                TextButton(onClick = onClear) { Text("清空已选") }
            }
        }
    }
}

@Composable
private fun OutputCard(state: UiState, onPick: () -> Unit, onReset: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("② 输出位置", style = MaterialTheme.typography.titleMedium)
            if (state.outputTreeUri == null) {
                Text(
                    "默认保存到系统的 Music/NCM_Converted（音乐类应用可直接看到）",
                    style = MaterialTheme.typography.bodySmall,
                )
            } else {
                Text("保存到所选文件夹", style = MaterialTheme.typography.bodySmall)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = onPick, modifier = Modifier.weight(1f)) {
                    Text(if (state.outputTreeUri == null) "自定义文件夹" else "更换文件夹")
                }
                if (state.outputTreeUri != null) {
                    OutlinedButton(onClick = onReset) { Text("恢复默认") }
                }
            }
        }
    }
}

@Composable
private fun LogCard(logs: List<String>) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("日志", style = MaterialTheme.typography.titleMedium)
            if (logs.isEmpty()) {
                Text("转换日志会显示在这里", style = MaterialTheme.typography.bodySmall)
            } else {
                HorizontalDivider()
                LazyColumn(modifier = Modifier.height(220.dp)) {
                    items(logs) { line ->
                        Text(line, fontSize = 13.sp, lineHeight = 18.sp)
                        Spacer(modifier = Modifier.width(4.dp))
                    }
                }
            }
        }
    }
}
