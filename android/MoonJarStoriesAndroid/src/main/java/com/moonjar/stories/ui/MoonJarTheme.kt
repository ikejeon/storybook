package com.moonjar.stories.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val IndigoInk = Color(0xFF1F294F)
val DeepIndigo = Color(0xFF050B16)
val MoonIvory = Color(0xFFFAF3DE)
val IvoryWarm = Color(0xFFF6E9C7)
val Persimmon = Color(0xFFD04F2E)
val JadeLeaf = Color(0xFF307F6B)
val LotusPink = Color(0xFFDB7A94)
val LanternGold = Color(0xFFEDA83D)

private val MoonJarColors = lightColorScheme(
    primary = Persimmon,
    onPrimary = MoonIvory,
    secondary = JadeLeaf,
    onSecondary = MoonIvory,
    background = MoonIvory,
    onBackground = IndigoInk,
    surface = Color.White,
    onSurface = IndigoInk
)

@Composable
fun MoonJarTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = MoonJarColors,
        typography = MaterialTheme.typography,
        content = content
    )
}
