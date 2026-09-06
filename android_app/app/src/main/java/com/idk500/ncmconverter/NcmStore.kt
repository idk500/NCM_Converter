package com.idk500.ncmconverter

import android.content.ContentUris
import android.content.ContentValues
import android.content.Context
import android.net.Uri
import android.provider.DocumentsContract
import android.provider.MediaStore
import java.io.File

/** Output sinks: the system MediaStore (default) or a user-picked SAF folder. */
object NcmStore {

    const val OUTPUT_RELATIVE_PATH = "Music/NCM_Converted"
    private const val TREE_OUTPUT_PREFIX = "NCM_Converted"

    fun mimeOf(format: String): String = when (format) {
        "flac" -> "audio/flac"
        else -> "audio/mpeg"
    }

    fun displayNameOf(context: Context, uri: Uri): String? =
        context.contentResolver.query(
            uri,
            arrayOf(android.provider.OpenableColumns.DISPLAY_NAME),
            null, null, null,
        )?.use { c -> if (c.moveToFirst()) c.getString(0) else null }

    /** All .ncm documents directly inside a SAF tree (non-recursive, like the desktop version). */
    fun listNcmInTree(context: Context, treeUri: Uri): List<Pair<Uri, String>> {
        val resolver = context.contentResolver
        val rootId = DocumentsContract.getTreeDocumentId(treeUri)
        val childrenUri = DocumentsContract.buildChildDocumentsUriUsingTree(treeUri, rootId)
        val result = mutableListOf<Pair<Uri, String>>()
        resolver.query(
            childrenUri,
            arrayOf(
                DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                DocumentsContract.Document.COLUMN_DISPLAY_NAME,
            ),
            null, null, null,
        )?.use { c ->
            while (c.moveToNext()) {
                val name = c.getString(1) ?: continue
                if (name.endsWith(".ncm", ignoreCase = true)) {
                    result += DocumentsContract.buildDocumentUriUsingTree(treeUri, c.getString(0)) to name
                }
            }
        }
        return result
    }

    fun treeContains(context: Context, treeUri: Uri, displayName: String): Boolean =
        listNcmInTree(context, treeUri).any { it.second.equals(displayName, ignoreCase = true) }

    /** True when [displayName] already exists under Music/NCM_Converted. */
    fun mediaStoreContains(context: Context, displayName: String): Boolean {
        val collection = MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
        context.contentResolver.query(
            collection,
            arrayOf(MediaStore.Audio.Media._ID),
            "${MediaStore.Audio.Media.DISPLAY_NAME} = ? AND ${MediaStore.Audio.Media.RELATIVE_PATH} = ?",
            arrayOf(displayName, "$OUTPUT_RELATIVE_PATH/"),
            null,
        )?.use { return it.count > 0 }
        return false
    }

    /** Copies [tempFile] into Music/NCM_Converted via MediaStore (no storage permission needed). */
    fun saveToMediaStore(context: Context, tempFile: File, displayName: String, mime: String): Uri {
        val resolver = context.contentResolver
        val collection = MediaStore.Audio.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
        val values = ContentValues().apply {
            put(MediaStore.Audio.Media.DISPLAY_NAME, displayName)
            put(MediaStore.Audio.Media.MIME_TYPE, mime)
            put(MediaStore.Audio.Media.RELATIVE_PATH, OUTPUT_RELATIVE_PATH)
            put(MediaStore.Audio.Media.IS_PENDING, 1)
        }
        val item = resolver.insert(collection, values) ?: error("MediaStore 写入失败")
        try {
            resolver.openOutputStream(item)?.use { out -> tempFile.inputStream().use { it.copyTo(out) } }
                ?: error("无法打开输出流")
        } catch (e: Exception) {
            resolver.delete(item, null, null)
            throw e
        }
        resolver.update(item, ContentValues().apply { put(MediaStore.Audio.Media.IS_PENDING, 0) }, null, null)
        return item
    }

    /** Copies [tempFile] into a user-picked SAF tree, skipping existing names. */
    fun saveToTree(context: Context, treeUri: Uri, tempFile: File, displayName: String, mime: String): Uri {
        val resolver = context.contentResolver
        val treeDoc = DocumentsContract.buildDocumentUriUsingTree(
            treeUri, DocumentsContract.getTreeDocumentId(treeUri),
        )
        if (treeContains(context, treeUri, displayName)) error("目标文件夹已存在同名文件")
        val created = DocumentsContract.createDocument(resolver, treeDoc, mime, displayName)
            ?: error("无法在所选文件夹创建文件")
        resolver.openOutputStream(created)?.use { out -> tempFile.inputStream().use { it.copyTo(out) } }
            ?: error("无法打开输出流")
        return created
    }

    fun friendlyTreeName(context: Context, treeUri: Uri): String =
        runCatching { ContentUris.parseId(treeUri).toString() }.getOrNull()
            ?: treeUri.lastPathSegment ?: treeUri.toString()
}
