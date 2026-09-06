package com.idk500.ncmconverter

import com.chaquo.python.Python
import org.json.JSONObject

data class ConvertedFile(
    val path: String,
    val name: String,
    val format: String,
    val title: String,
)

/** Thin Kotlin -> Python bridge; all conversion logic lives in the shared ncmdump core. */
object PythonConverter {

    fun convert(ncmPath: String, outputDir: String, baseName: String): ConvertedFile {
        val py = Python.getInstance()
        val json = py.getModule("converter_wrapper")
            .callAttr("convert", ncmPath, outputDir, baseName)
            .toString()
        val o = JSONObject(json)
        require(!o.has("error")) { o.optString("error") }
        return ConvertedFile(
            path = o.getString("path"),
            name = o.getString("name"),
            format = o.getString("format"),
            title = o.optString("title"),
        )
    }
}
