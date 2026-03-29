package org.example.ncmconverter

import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.io.RandomAccessFile
import org.json.JSONObject

/**
 * NCM文件转换器
 * 基于ncmdump算法移植到Kotlin
 */
class NCMConverter {
    companion object {
        // AES密钥和IV
        private val AES_KEY = byteArrayOf(
            0x43, 0x32, 0x38, 0x34, 0x44, 0x37, 0x30, 0x42,
            0x33, 0x33, 0x42, 0x46, 0x34, 0x44, 0x31, 0x44,
            0x39, 0x36, 0x41, 0x31, 0x42, 0x37, 0x43, 0x37,
            0x41, 0x37, 0x45, 0x32, 0x37, 0x42, 0x32, 0x44
        )
        
        private val AES_IV = byteArrayOf(
            0x37, 0x37, 0x36, 0x42, 0x35, 0x46, 0x35, 0x44,
            0x34, 0x31, 0x35, 0x30, 0x37, 0x36, 0x37, 0x31,
            0x35, 0x41, 0x35, 0x46, 0x37, 0x41, 0x36, 0x42,
            0x35, 0x39, 0x35, 0x33, 0x34, 0x45, 0x34, 0x44
        )
        
        /**
         * XOR加密/解密
         */
        private fun xorBytes(data: ByteArray, key: ByteArray): ByteArray {
            val result = ByteArray(data.size)
            val keyLen = key.size
            for (i in data.indices) {
                result[i] = (data[i].toInt() xor key[i % keyLen].toInt()).toByte()
            }
            return result
        }
        
        /**
         * 构建密钥盒
         */
        private fun buildKeyBox(key: ByteArray): IntArray {
            val box = IntArray(256)
            for (i in 0..255) {
                box[i] = i
            }
            val keyLen = key.size
            var j = 0
            for (i in 0..255) {
                j = (j + box[i] + (key[i % keyLen].toInt() and 0xFF)) and 0xFF
                val temp = box[i]
                box[i] = box[j]
                box[j] = temp
            }
            return box
        }
        
        /**
         * 核心解密算法
         */
        private fun decryptCore(data: ByteArray, keyBox: IntArray): ByteArray {
            val result = ByteArray(data.size)
            val box = keyBox.copyOf()
            var j = 0
            var k = 0
            for (i in data.indices) {
                j = (j + 1) and 0xFF
                k = (k + box[j]) and 0xFF
                val temp = box[j]
                box[j] = box[k]
                box[k] = temp
                result[i] = (data[i].toInt() xor box[(box[j] + box[k]) and 0xFF].toInt()).toByte()
            }
            return result
        }
    }
    
    /**
     * 转换结果
     */
    data class ConversionResult(
        val success: Boolean,
        val inputFile: String,
        val outputFile: String? = null,
        val error: String? = null,
        val sizeMB: Double = 0.0,
        val elapsedTime: Double = 0.0
    )
    
    /**
     * 解码单个NCM文件
     */
    fun decode(inputPath: String, outputPath: String): ConversionResult {
        val startTime = System.currentTimeMillis()
        
        return try {
            val inputFile = File(inputPath)
            if (!inputFile.exists()) {
                return ConversionResult(false, inputPath, error = "文件不存在")
            }
            
            val raf = RandomAccessFile(inputFile, "r")
            
            // 读取魔数
            val magic = ByteArray(8)
            raf.readFully(magic)
            if (!magic.contentEquals("CTENFDAM".toByteArray())) {
                raf.close()
                return ConversionResult(false, inputPath, error = "无效的NCM文件")
            }
            
            // 跳过2字节
            raf.skipBytes(2)
            
            // 读取密钥数据长度
            val keyLenBytes = ByteArray(4)
            raf.readFully(keyLenBytes)
            val keyLen = bytesToIntLittleEndian(keyLenBytes)
            
            // 读取加密的密钥数据
            val encryptedKey = ByteArray(keyLen)
            raf.readFully(encryptedKey)
            
            // 解密密钥
            val decryptedKey = xorBytes(encryptedKey, AES_KEY)
            
            // 构建密钥盒
            val keyBox = buildKeyBox(decryptedKey)
            
            // 读取元数据长度
            val metaLenBytes = ByteArray(4)
            raf.readFully(metaLenBytes)
            val metaLen = bytesToIntLittleEndian(metaLenBytes)
            
            // 解析元数据
            var format = "mp3"
            if (metaLen > 0) {
                val encryptedMeta = ByteArray(metaLen)
                raf.readFully(encryptedMeta)
                val decryptedMeta = xorBytes(encryptedMeta, AES_IV)
                
                // 跳过第一个字节
                var metaStr = if (decryptedMeta.isNotEmpty() && 
                                  (decryptedMeta[0].toInt() == 0x7F || decryptedMeta[0].toInt() < 0x20)) {
                    String(decryptedMeta, 1, decryptedMeta.size - 1, Charsets.UTF_8)
                } else {
                    String(decryptedMeta, Charsets.UTF_8)
                }
                
                // 清理JSON字符串
                metaStr = metaStr.trim('\u0000').trim()
                
                if (metaStr.startsWith("{")) {
                    try {
                        val json = JSONObject(metaStr)
                        format = json.optString("format", "mp3").lowercase()
                    } catch (e: Exception) {
                        format = "mp3"
                    }
                }
            }
            
            // 跳过CRC和图片等数据
            raf.skipBytes(5)
            
            // 跳过图片数据
            val imgLenBytes = ByteArray(4)
            raf.readFully(imgLenBytes)
            val imgLen = bytesToIntLittleEndian(imgLenBytes)
            if (imgLen > 0) {
                raf.skipBytes(imgLen)
            }
            
            // 记录音频数据起始位置
            val audioOffset = raf.filePointer
            val audioSize = raf.length() - audioOffset
            
            // 确保输出目录存在
            val outputFile = File(outputPath)
            outputFile.parentFile?.mkdirs()
            
            // 读取并解密音频数据
            val fos = FileOutputStream(outputFile)
            val buffer = ByteArray(8192)
            raf.seek(audioOffset)
            
            var totalRead = 0L
            while (totalRead < audioSize) {
                val toRead = minOf(buffer.size.toLong(), audioSize - totalRead).toInt()
                val bytesRead = raf.read(buffer, 0, toRead)
                if (bytesRead <= 0) break
                
                val decryptedChunk = decryptCore(buffer.copyOf(bytesRead), keyBox)
                fos.write(decryptedChunk)
                totalRead += bytesRead
            }
            
            fos.close()
            raf.close()
            
            val elapsedTime = (System.currentTimeMillis() - startTime) / 1000.0
            val sizeMB = outputFile.length() / (1024.0 * 1024.0)
            
            ConversionResult(
                success = true,
                inputFile = inputFile.name,
                outputFile = outputFile.name,
                sizeMB = sizeMB,
                elapsedTime = elapsedTime
            )
        } catch (e: Exception) {
            ConversionResult(false, inputPath, error = e.message)
        }
    }
    
    private fun bytesToIntLittleEndian(bytes: ByteArray): Int {
        return (bytes[0].toInt() and 0xFF) or
               ((bytes[1].toInt() and 0xFF) shl 8) or
               ((bytes[2].toInt() and 0xFF) shl 16) or
               ((bytes[3].toInt() and 0xFF) shl 24)
    }
}
