plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.moonjar.stories"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.moonjar.stories"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    buildFeatures {
        compose = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("generated/assets"))
}

tasks.register<Copy>("copySharedContent") {
    from(rootProject.layout.projectDirectory.dir("../shared-content"))
    into(layout.buildDirectory.dir("generated/assets/shared-content"))
}

tasks.named("preBuild") {
    dependsOn("copySharedContent")
}

dependencies {
    implementation(libs.activity.compose)
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.compose.icons)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.media3.exoplayer)
    implementation(libs.play.billing)

    testImplementation(kotlin("test"))

    debugImplementation(libs.compose.ui.tooling)
}
