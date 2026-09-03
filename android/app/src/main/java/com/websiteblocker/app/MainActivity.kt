package com.websiteblocker.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.VpnService
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.core.content.ContextCompat
import com.websiteblocker.app.core.FocusTimerService
import com.websiteblocker.app.data.models.WebsiteEntity
import com.websiteblocker.app.ui.screens.*
import com.websiteblocker.app.ui.theme.CardDark
import com.websiteblocker.app.ui.theme.PrimaryViolet
import com.websiteblocker.app.ui.theme.TextMuted
import com.websiteblocker.app.ui.theme.WebsiteBlockerTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.util.Calendar

sealed class Screen(val route: String, val title: String, val icon: ImageVector) {
    object Dashboard : Screen("dashboard", "Dashboard", Icons.Default.Dashboard)
    object Websites : Screen("websites", "Websites", Icons.Default.Language)
    object Statistics : Screen("statistics", "Stats", Icons.Default.BarChart)
    object Settings : Screen("settings", "Settings", Icons.Default.Settings)
}

class MainActivity : ComponentActivity() {

    private var pendingDurationSeconds: Int = 3600

    private val vpnPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            launchFocusTimerService(pendingDurationSeconds)
        } else {
            Toast.makeText(this, "VPN permission is required to block websites.", Toast.LENGTH_LONG).show()
        }
    }

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* optional handler */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestRequiredPermissions()

        val db = (application as WebsiteBlockerApp).database

        setContent {
            WebsiteBlockerTheme {
                val coroutineScope = rememberCoroutineScope()
                var currentScreen by remember { mutableStateOf<Screen>(Screen.Dashboard) }

                // Database reactive flows
                val websites by db.websiteDao().getAllWebsites().collectAsState(initial = emptyList())
                val sessions by db.sessionDao().getAllSessions().collectAsState(initial = emptyList())
                val isSessionActive by FocusTimerService.isSessionActive.collectAsState()

                // Calculate statistics
                val todayStart = remember {
                    Calendar.getInstance().apply {
                        set(Calendar.HOUR_OF_DAY, 0)
                        set(Calendar.MINUTE, 0)
                        set(Calendar.SECOND, 0)
                        set(Calendar.MILLISECOND, 0)
                    }.timeInMillis
                }

                val weekStart = remember {
                    Calendar.getInstance().apply {
                        set(Calendar.DAY_OF_WEEK, firstDayOfWeek)
                        set(Calendar.HOUR_OF_DAY, 0)
                        set(Calendar.MINUTE, 0)
                        set(Calendar.SECOND, 0)
                    }.timeInMillis
                }

                val todayCompleted = sessions.filter { it.startTime >= todayStart && it.status == "completed" }
                val weekCompleted = sessions.filter { it.startTime >= weekStart && it.status == "completed" }

                val todayFocusSeconds = todayCompleted.sumOf { it.durationSeconds }
                val weekFocusSeconds = weekCompleted.sumOf { it.durationSeconds }

                Scaffold(
                    bottomBar = {
                        NavigationBar(
                            containerColor = CardDark
                        ) {
                            val items = listOf(
                                Screen.Dashboard,
                                Screen.Websites,
                                Screen.Statistics,
                                Screen.Settings
                            )
                            items.forEach { screen ->
                                NavigationBarItem(
                                    icon = { Icon(screen.icon, contentDescription = screen.title) },
                                    label = { Text(screen.title) },
                                    selected = currentScreen == screen,
                                    onClick = { currentScreen = screen },
                                    colors = NavigationBarItemDefaults.colors(
                                        selectedIconColor = PrimaryViolet,
                                        selectedTextColor = PrimaryViolet,
                                        unselectedIconColor = TextMuted,
                                        unselectedTextColor = TextMuted,
                                        indicatorColor = PrimaryViolet.copy(alpha = 0.12f)
                                    )
                                )
                            }
                        }
                    }
                ) { innerPadding ->
                    when (currentScreen) {
                        Screen.Dashboard -> DashboardScreen(
                            onStartSession = { duration ->
                                startSessionWithVpn(duration)
                            },
                            enabledWebsitesCount = websites.count { it.enabled },
                            todayFocusSeconds = todayFocusSeconds,
                            todaySessionsCount = todayCompleted.size,
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(innerPadding)
                        )
                        Screen.Websites -> WebsitesScreen(
                            websites = websites,
                            isSessionActive = isSessionActive,
                            onAddWebsite = { domain ->
                                coroutineScope.launch(Dispatchers.IO) {
                                    db.websiteDao().insert(WebsiteEntity(domain = domain))
                                }
                            },
                            onToggleWebsite = { site, enabled ->
                                coroutineScope.launch(Dispatchers.IO) {
                                    db.websiteDao().setEnabled(site.id, enabled)
                                }
                            },
                            onDeleteWebsite = { site ->
                                coroutineScope.launch(Dispatchers.IO) {
                                    db.websiteDao().deleteById(site.id)
                                }
                            },
                            onEnableAll = {
                                coroutineScope.launch(Dispatchers.IO) {
                                    db.websiteDao().setAllEnabled(true)
                                }
                            },
                            onDisableAll = {
                                coroutineScope.launch(Dispatchers.IO) {
                                    db.websiteDao().setAllEnabled(false)
                                }
                            },
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(innerPadding)
                        )
                        Screen.Statistics -> StatisticsScreen(
                            todayFocusSeconds = todayFocusSeconds,
                            todaySessionsCount = todayCompleted.size,
                            weekFocusSeconds = weekFocusSeconds,
                            weekSessionsCount = weekCompleted.size,
                            sessions = sessions,
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(innerPadding)
                        )
                        Screen.Settings -> SettingsScreen(
                            onClearHistory = {
                                coroutineScope.launch(Dispatchers.IO) {
                                    db.sessionDao().clearAll()
                                }
                            },
                            isSessionActive = isSessionActive,
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(innerPadding)
                        )
                    }
                }
            }
        }
    }

    private fun requestRequiredPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    private fun startSessionWithVpn(durationSeconds: Int) {
        pendingDurationSeconds = durationSeconds
        val vpnIntent = VpnService.prepare(this)
        if (vpnIntent != null) {
            // Must ask user for Android VPN connection approval dialog
            vpnPermissionLauncher.launch(vpnIntent)
        } else {
            // Already approved
            launchFocusTimerService(durationSeconds)
        }
    }

    private fun launchFocusTimerService(durationSeconds: Int) {
        val serviceIntent = Intent(this, FocusTimerService::class.java).apply {
            action = FocusTimerService.ACTION_START_TIMER
            putExtra(FocusTimerService.EXTRA_DURATION_SECONDS, durationSeconds)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
    }
}
