plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.chaquo.python")
}

android {
    namespace = "com.idk500.ncmconverter"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.idk500.ncmconverter"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        // Python 3.12+ ships 64-bit only (Chaquopy requirement).
        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    signingConfigs {
        create("release") {
            // CI injects release.keystore from secrets (see .github/workflows/release.yml);
            // without it, release builds fall back to the debug key so the APK stays installable.
            storeFile = file("release.keystore")
            storePassword = System.getenv("APK_KEYSTORE_PASSWORD")
            keyAlias = System.getenv("APK_KEY_ALIAS")
            keyPassword = System.getenv("APK_KEY_PASSWORD")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig =
                if (file("release.keystore").exists()) signingConfigs.getByName("release")
                else signingConfigs.getByName("debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

chaquopy {
    defaultConfig {
        version = "3.13"
        pip {
            // The proven desktop core. ncmdump 0.1.1 exists on PyPI as sdist only,
            // and Chaquopy's cross-build pip accepts wheels only, so the wheel is
            // vendored (built once from the sdist with `pip wheel --no-deps`).
            // It pulls in pycryptodome + mutagen (prebuilt wheels) automatically.
            install("../pypi-wheels/ncmdump-0.1.1-py3-none-any.whl")
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
}
