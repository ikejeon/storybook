package com.moonjar.stories.billing

import android.content.Context
import android.net.Uri
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer

class AudioEngine(context: Context) {
    private val player = ExoPlayer.Builder(context).build()
    private val soundPlayer = ExoPlayer.Builder(context).build()
    private var currentUri: String? = null
    private var finishedCallback: (() -> Unit)? = null
    private val completionListener = object : Player.Listener {
        override fun onPlaybackStateChanged(playbackState: Int) {
            if (playbackState == Player.STATE_ENDED) {
                val callback = finishedCallback
                finishedCallback = null
                callback?.invoke()
            }
        }
    }

    init {
        player.addListener(completionListener)
    }

    fun playOrPause(assetUri: String, bedtimeMode: Boolean, onFinished: () -> Unit = {}) {
        if (player.isPlaying && currentUri == assetUri) {
            player.pause()
            return
        }
        if (currentUri == assetUri && player.playbackState != Player.STATE_ENDED) {
            player.play()
            return
        }
        replay(assetUri, bedtimeMode, onFinished)
    }

    fun replay(assetUri: String, bedtimeMode: Boolean, onFinished: () -> Unit = {}) {
        currentUri = assetUri
        finishedCallback = onFinished
        player.stop()
        player.clearMediaItems()
        player.volume = if (bedtimeMode) 0.52f else 0.76f
        player.setMediaItem(MediaItem.fromUri(Uri.parse(assetUri)))
        player.prepare()
        player.play()
    }

    fun pause() {
        player.pause()
    }

    fun playSound(assetUri: String, bedtimeMode: Boolean) {
        soundPlayer.stop()
        soundPlayer.clearMediaItems()
        soundPlayer.volume = if (bedtimeMode) 0.18f else 0.36f
        soundPlayer.setMediaItem(MediaItem.fromUri(Uri.parse(assetUri)))
        soundPlayer.prepare()
        soundPlayer.play()
    }

    fun stop() {
        finishedCallback = null
        player.stop()
        currentUri = null
    }

    fun release() {
        finishedCallback = null
        player.removeListener(completionListener)
        player.release()
        soundPlayer.release()
    }
}
