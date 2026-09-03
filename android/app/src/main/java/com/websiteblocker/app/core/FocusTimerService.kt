package com.websiteblocker.app.core

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.NotificationCompat
import com.websiteblocker.app.MainActivity
import com.websiteblocker.app.R
import com.websiteblocker.app.WebsiteBlockerApp
import com.websiteblocker.app.data.models.SessionEntity
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.Locale

class FocusTimerService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.Main + Job())
    private var timerJob: Job? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private var currentSessionId: Long = 0

    companion object {
        const val ACTION_START_TIMER = "com.websiteblocker.app.START_TIMER"
        const val ACTION_STOP_TIMER = "com.websiteblocker.app.STOP_TIMER"
        const val EXTRA_DURATION_SECONDS = "extra_duration_seconds"

        const val CHANNEL_ID = "focus_session_channel"
        const val NOTIFICATION_ID = 1001

        private val _remainingSeconds = MutableStateFlow(0)
        val remainingSeconds = _remainingSeconds.asStateFlow()

        private val _totalDurationSeconds = MutableStateFlow(0)
        val totalDurationSeconds = _totalDurationSeconds.asStateFlow()

        private val _isSessionActive = MutableStateFlow(false)
        val isSessionActive = _isSessionActive.asStateFlow()
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "WebsiteBlocker::FocusTimerWakeLock")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP_TIMER -> {
                // Strict mode: Timer cannot be stopped early until it reaches zero
                if (!_isSessionActive.value) {
                    stopTimer("stopped")
                }
            }
            ACTION_START_TIMER -> {
                val duration = intent.getIntExtra(EXTRA_DURATION_SECONDS, 3600)
                startTimer(duration)
            }
        }
        return START_STICKY
    }

    private fun startTimer(durationSeconds: Int) {
        if (_isSessionActive.value) return

        wakeLock?.acquire(durationSeconds * 1000L + 5000L)
        _totalDurationSeconds.value = durationSeconds
        _remainingSeconds.value = durationSeconds
        _isSessionActive.value = true

        startForeground(NOTIFICATION_ID, buildNotification(durationSeconds))

        // 1. Start Local VPN DNS Blocking Service
        val vpnIntent = Intent(this, BlockerVpnService::class.java).apply {
            action = BlockerVpnService.ACTION_START
        }
        startService(vpnIntent)

        // 2. Insert Session in Database
        serviceScope.launch(Dispatchers.IO) {
            val db = (application as WebsiteBlockerApp).database
            val session = SessionEntity(
                durationSeconds = durationSeconds,
                status = "active"
            )
            currentSessionId = db.sessionDao().insert(session)
        }

        // 3. Wall-clock countdown loop
        val targetTimestamp = System.currentTimeMillis() + (durationSeconds * 1000L)

        timerJob = serviceScope.launch {
            while (isActive) {
                val now = System.currentTimeMillis()
                val remaining = ((targetTimestamp - now) / 1000).toInt()

                if (remaining <= 0) {
                    _remainingSeconds.value = 0
                    updateNotification(0)
                    stopTimer("completed")
                    break
                }

                _remainingSeconds.value = remaining
                updateNotification(remaining)
                delay(1000)
            }
        }
    }

    private fun stopTimer(status: String) {
        timerJob?.cancel()
        timerJob = null
        _isSessionActive.value = false
        _remainingSeconds.value = 0

        // Stop VPN Service
        val vpnIntent = Intent(this, BlockerVpnService::class.java).apply {
            action = BlockerVpnService.ACTION_STOP
        }
        startService(vpnIntent)

        // Update database session
        if (currentSessionId > 0) {
            serviceScope.launch(Dispatchers.IO) {
                val db = (application as WebsiteBlockerApp).database
                db.sessionDao().endSession(currentSessionId, status)
                currentSessionId = 0
            }
        }

        if (wakeLock?.isHeld == true) {
            wakeLock?.release()
        }

        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun buildNotification(remainingSec: Int): Notification {
        val h = remainingSec / 3600
        val m = (remainingSec % 3600) / 60
        val s = remainingSec % 60
        val timeStr = String.format(Locale.getDefault(), "%02d:%02d:%02d", h, m, s)

        val openAppIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("🔒 Strict Focus Session Active")
            .setContentText("Websites blocked • Remaining: $timeStr (Locked)")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun updateNotification(remainingSec: Int) {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(NOTIFICATION_ID, buildNotification(remainingSec))
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Focus Session Channel",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows website blocker active countdown"
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        stopTimer("stopped")
        super.onDestroy()
    }
}
