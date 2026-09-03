package com.websiteblocker.app.ui.screens

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.websiteblocker.app.ui.theme.*

@Composable
fun SettingsScreen(
    onClearHistory: () -> Unit,
    isSessionActive: Boolean = false,
    modifier: Modifier = Modifier
) {
    var showConfirmDialog by remember { mutableStateOf(false) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 16.dp)
    ) {
        // ── Header ──
        Text(
            text = "Settings",
            fontWeight = FontWeight.Bold,
            fontSize = 24.sp,
            color = TextPrimary
        )
        Text(
            text = "Network configuration and app preferences",
            fontSize = 13.sp,
            color = TextSecondary
        )

        Spacer(modifier = Modifier.height(18.dp))

        // ── Privacy & DNS Engine Info ──
        Card(
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = CardDark),
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderDark, RoundedCornerShape(14.dp))
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "LOCAL DNS FILTERING",
                    fontWeight = FontWeight.Bold,
                    fontSize = 10.sp,
                    letterSpacing = 1.sp,
                    color = PrimaryVioletLight
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "100% On-Device Protection",
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 15.sp,
                    color = TextPrimary
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Website Blocker uses Android's local VpnService loopback to intercept DNS queries. No remote servers are used, and zero internet traffic leaves your phone.",
                    fontSize = 13.sp,
                    color = TextSecondary,
                    lineHeight = 18.sp
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // ── App Information ──
        Card(
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = CardDark),
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderDark, RoundedCornerShape(14.dp))
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "APPLICATION INFO",
                    fontWeight = FontWeight.Bold,
                    fontSize = 10.sp,
                    letterSpacing = 1.sp,
                    color = TextSecondary
                )

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    horizontalArrangement = Arrangement.SpaceBetween,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("App Name", fontSize = 13.sp, color = TextSecondary)
                    Text("Website Blocker Android", fontSize = 13.sp, fontWeight = FontWeight.Medium, color = TextPrimary)
                }

                HorizontalDivider(color = BorderDark, modifier = Modifier.padding(vertical = 10.dp))

                Row(
                    horizontalArrangement = Arrangement.SpaceBetween,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Version", fontSize = 13.sp, color = TextSecondary)
                    Text("1.0.0 (Release)", fontSize = 13.sp, fontWeight = FontWeight.Medium, color = TextPrimary)
                }

                HorizontalDivider(color = BorderDark, modifier = Modifier.padding(vertical = 10.dp))

                Row(
                    horizontalArrangement = Arrangement.SpaceBetween,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Primary DNS", fontSize = 13.sp, color = TextSecondary)
                    Text("1.1.1.1 (Cloudflare)", fontSize = 13.sp, fontWeight = FontWeight.Medium, color = TextPrimary)
                }
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // ── Danger Zone / Clear History ──
        Card(
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = CardDark),
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, DangerRed.copy(alpha = 0.2f), RoundedCornerShape(14.dp))
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "DATA MANAGEMENT",
                    fontWeight = FontWeight.Bold,
                    fontSize = 10.sp,
                    letterSpacing = 1.sp,
                    color = DangerRed
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "Clear Focus History",
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 15.sp,
                    color = TextPrimary
                )
                Text(
                    text = "Wipes all recorded past focus session statistics from local database.",
                    fontSize = 12.sp,
                    color = TextSecondary
                )

                Spacer(modifier = Modifier.height(12.dp))

                OutlinedButton(
                    onClick = { showConfirmDialog = true },
                    enabled = !isSessionActive,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = DangerRed,
                        disabledContentColor = TextMuted
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = if (isSessionActive) "Session in Progress (Locked)" else "Clear All Session History",
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }

    if (showConfirmDialog) {
        AlertDialog(
            onDismissRequest = { showConfirmDialog = false },
            title = { Text("Clear Session History?", color = TextPrimary) },
            text = { Text("Are you sure you want to delete all past focus session records? This action cannot be undone.", color = TextSecondary) },
            confirmButton = {
                Button(
                    onClick = {
                        onClearHistory()
                        showConfirmDialog = false
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = DangerRed)
                ) {
                    Text("Delete History", color = Color.White)
                }
            },
            dismissButton = {
                TextButton(onClick = { showConfirmDialog = false }) {
                    Text("Cancel", color = TextSecondary)
                }
            },
            containerColor = CardDark
        )
    }
}
