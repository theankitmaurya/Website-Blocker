package com.websiteblocker.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.websiteblocker.app.data.models.SessionEntity
import com.websiteblocker.app.ui.components.StatCard
import com.websiteblocker.app.ui.theme.*
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun StatisticsScreen(
    todayFocusSeconds: Int,
    todaySessionsCount: Int,
    weekFocusSeconds: Int,
    weekSessionsCount: Int,
    sessions: List<SessionEntity>,
    modifier: Modifier = Modifier
) {
    val todayH = todayFocusSeconds / 3600
    val todayM = (todayFocusSeconds % 3600) / 60
    val todayStr = if (todayH > 0) "${todayH}h ${todayM}m" else "${todayM}m"

    val weekH = weekFocusSeconds / 3600
    val weekM = (weekFocusSeconds % 3600) / 60
    val weekStr = if (weekH > 0) "${weekH}h ${weekM}m" else "${weekM}m"

    val dateFormat = SimpleDateFormat("MMM dd, yyyy  hh:mm a", Locale.getDefault())

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp, vertical = 16.dp)
    ) {
        // ── Header ──
        Text(
            text = "Statistics",
            fontWeight = FontWeight.Bold,
            fontSize = 24.sp,
            color = TextPrimary
        )
        Text(
            text = "Productivity insights and past sessions",
            fontSize = 13.sp,
            color = TextSecondary
        )

        Spacer(modifier = Modifier.height(16.dp))

        // ── Metric Cards Grid ──
        Row(
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            StatCard(
                title = "Today's Focus",
                value = todayStr,
                accentColor = PrimaryViolet,
                modifier = Modifier.weight(1f)
            )
            StatCard(
                title = "Today Sessions",
                value = todaySessionsCount.toString(),
                accentColor = SuccessGreen,
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        Row(
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            StatCard(
                title = "This Week",
                value = weekStr,
                accentColor = WarningAmber,
                modifier = Modifier.weight(1f)
            )
            StatCard(
                title = "Weekly Sessions",
                value = weekSessionsCount.toString(),
                accentColor = Color(0xFF3B82F6),
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        // ── Session History Header ──
        Text(
            text = "Session History (${sessions.size})",
            fontWeight = FontWeight.SemiBold,
            fontSize = 15.sp,
            color = TextPrimary
        )

        Spacer(modifier = Modifier.height(10.dp))

        // ── History List ──
        if (sessions.isEmpty()) {
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            ) {
                Text(
                    text = "No focus sessions recorded yet.",
                    fontSize = 13.sp,
                    color = TextMuted
                )
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.weight(1f)
            ) {
                items(sessions, key = { it.id }) { session ->
                    val durMin = session.durationSeconds / 60
                    val dateStr = dateFormat.format(Date(session.startTime))

                    Card(
                        shape = RoundedCornerShape(10.dp),
                        colors = CardDefaults.cardColors(containerColor = CardDark),
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.dp, BorderDark, RoundedCornerShape(10.dp))
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp)
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "$durMin Minutes Focus",
                                    fontWeight = FontWeight.SemiBold,
                                    fontSize = 14.sp,
                                    color = TextPrimary
                                )
                                Text(
                                    text = dateStr,
                                    fontSize = 11.sp,
                                    color = TextSecondary
                                )
                            }

                            // Status Pill
                            val (statusBg, statusFg, label) = when (session.status) {
                                "completed" -> Triple(SuccessGreen.copy(alpha = 0.12f), SuccessGreen, "Completed")
                                "stopped" -> Triple(WarningAmber.copy(alpha = 0.12f), WarningAmber, "Stopped")
                                else -> Triple(PrimaryViolet.copy(alpha = 0.12f), PrimaryVioletLight, "Active")
                            }

                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(100.dp))
                                    .background(statusBg)
                                    .padding(horizontal = 10.dp, vertical = 4.dp)
                            ) {
                                Text(
                                    text = label,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    color = statusFg
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
