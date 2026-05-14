package com.moonjar.stories

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.moonjar.stories.data.ContentRepository
import com.moonjar.stories.ui.MoonJarApp
import com.moonjar.stories.ui.MoonJarTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val repository = ContentRepository(assets)
        val demoSelfTest = intent.getStringExtra("moonjar.selfTest")
        val demoSelfTestToken = intent.getStringExtra("moonjar.selfTestToken")
        setContent {
            MoonJarTheme {
                MoonJarApp(
                    repository = repository,
                    demoSelfTest = demoSelfTest,
                    demoSelfTestToken = demoSelfTestToken,
                    selfTestOutputDir = filesDir
                )
            }
        }
    }
}
