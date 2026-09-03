package com.websiteblocker.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.websiteblocker.app.core.FocusTimerService
import com.websiteblocker.app.ui.components.CircularTimer
import com.websiteblocker.app.ui.components.StatCard
import com.websiteblocker.app.ui.theme.*

@Composable
fun DashboardScreen(
    onStartSession: (Int) -> Unit,
    enabledWebsitesCount: Int,
    todayFocusSeconds: Int,
    todaySessionsCount: Int,
    modifier: Modifier = Modifier
) {
    val isSessionActive by FocusTimerService.isSessionActive.collectAsState()
    val remainingSeconds by FocusTimerService.remainingSeconds.collectAsState()
    val totalDurationSeconds by FocusTimerService.totalDurationSeconds.collectAsState()

    val presets = listOf(
        "15m" to 15 * 60,
        "30m" to 30 * 60,
        "1 hr" to 60 * 60,
        "2 hr" to 2 * 60 * 60,
        "4 hr" to 4 * 60 * 60
    )

    var selectedPresetIndex by remember { mutableIntStateOf(2) } // default: 1 hr
    val currentSelectedSeconds = presets[selectedPresetIndex].second

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp)
    ) {
        // ── Header ──
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "Dashboard",
                    fontWeight = FontWeight.Bold,
                    fontSize = 24.sp,
                    color = TextPrimary
                )
                Text(
                    text = "Focus session & timer control",
                    fontSize = 13.sp,
                    color = TextSecondary
                )
            }

            // Status Pill
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(100.dp))
                    .background(
                        if (isSessionActive) DangerRed.copy(alpha = 0.12f)
                        else SuccessGreen.copy(alpha = 0.12f)
                    )
                    .border(
                        1.dp,
                        if (isSessionActive) DangerRed.copy(alpha = 0.3f)
                        else SuccessGreen.copy(alpha = 0.3f),
                        RoundedCornerShape(100.dp)
                    )
                    .padding(horizontal = 12.dp, vertical = 6.dp)
            ) {
                Text(
                    text = if (isSessionActive) "🔴 BLOCKING ACTIVE" else "● IDLE",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (isSessionActive) DangerRed else SuccessGreen,
                    letterSpacing = 0.8.sp
                )
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // ── Circular Timer Ring ──
        CircularTimer(
            remainingSeconds = remainingSeconds,
            totalSeconds = totalDurationSeconds,
            isActive = isSessionActive
        )

        Spacer(modifier = Modifier.height(16.dp))

        // ── Duration Preset Selector (Idle Mode) ──
        if (!isSessionActive) {
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderDark, RoundedCornerShape(16.dp))
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = "SESSION DURATION",
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            letterSpacing = 1.sp,
                            color = TextSecondary,
                            modifier = Modifier.weight(1f)
                        )
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.Lock,
                                contentDescription = "Strict Mode",
                                tint = PrimaryVioletLight,
                                modifier = Modifier.size(13.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                text = "Strict Mode (Unstoppable)",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = PrimaryVioletLight
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        presets.forEachIndexed { index, (label, _) ->
                            val isSelected = selectedPresetIndex == index
                            Box(
                                contentAlignment = Alignment.Center,
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(RoundedCornerShape(10.dp))
                                    .background(
                                        if (isSelected) PrimaryViolet.copy(alpha = 0.18f)
                                        else CardSecondary
                                    )
                                    .border(
                                        1.dp,
                                        if (isSelected) PrimaryViolet.copy(alpha = 0.5f)
                                        else BorderDark,
                                        RoundedCornerShape(10.dp)
                                    )
                                    .clickable { selectedPresetIndex = index }
                                    .padding(vertical = 10.dp)
                            ) {
                                Text(
                                    text = label,
                                    fontSize = 12.sp,
                                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                                    color = if (isSelected) PrimaryVioletLight else TextSecondary
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(18.dp))

                    // Start Button (Gradient)
                    Button(
                        onClick = { onStartSession(currentSelectedSeconds) },
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent),
                        contentPadding = PaddingValues(),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(50.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(
                                Brush.horizontalGradient(
                                    listOf(PrimaryViolet, PrimaryVioletLight)
                                )
                            )
                    ) {
                        Text(
                            text = "🚀  Start Strict Focus Session",
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            color = Color.White
                        )
                    }
                }
            }
        } else {
            // Active Session Controls - Strict Unstoppable Locked Card
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, DangerRed.copy(alpha = 0.4f), RoundedCornerShape(16.dp))
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Text(
                        text = "🛡️ Blocking $enabledWebsitesCount configured websites",
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 14.sp,
                        color = TextPrimary
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(DangerRed.copy(alpha = 0.10f))
                            .border(1.dp, DangerRed.copy(alpha = 0.28f), RoundedCornerShape(12.dp))
                            .padding(14.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.Lock,
                                contentDescription = "Strict Mode",
                                tint = DangerRed,
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(modifier = Modifier.width(12.dp))
                            Column {
                                Text(
                                    text = "Strict Mode Active",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 14.sp,
                                    color = DangerRed
                                )
                                Spacer(modifier = Modifier.height(2.dp))
                                Text(
                                    text = "Timer cannot be stopped early. Websites stay blocked until the countdown completes.",
                                    fontSize = 12.sp,
                                    color = TextSecondary,
                                    lineHeight = 16.sp
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // ── Productivity Stat Cards Row ──
        val todayHours = todayFocusSeconds / 3600
        val todayMins = (todayFocusSeconds % 3600) / 60
        val todayFocusStr = if (todayHours > 0) "${todayHours}h ${todayMins}m" else "${todayMins}m"

        Row(
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            StatCard(
                title = "Today's Focus",
                value = todayFocusStr,
                accentColor = PrimaryViolet,
                modifier = Modifier.weight(1f)
            )
            StatCard(
                title = "Sessions",
                value = todaySessionsCount.toString(),
                accentColor = SuccessGreen,
                modifier = Modifier.weight(1f)
            )
            StatCard(
                title = "Blocked Sites",
                value = "$enabledWebsitesCount active",
                accentColor = WarningAmber,
                modifier = Modifier.weight(1f)
            )
        }
    }
}
