package com.websiteblocker.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.websiteblocker.app.data.models.WebsiteEntity
import com.websiteblocker.app.ui.components.WebsiteRow
import com.websiteblocker.app.ui.theme.*
import com.websiteblocker.app.utils.DomainUtils

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WebsitesScreen(
    websites: List<WebsiteEntity>,
    isSessionActive: Boolean,
    onAddWebsite: (String) -> Unit,
    onToggleWebsite: (WebsiteEntity, Boolean) -> Unit,
    onDeleteWebsite: (WebsiteEntity) -> Unit,
    onEnableAll: () -> Unit,
    onDisableAll: () -> Unit,
    modifier: Modifier = Modifier
) {
    var inputText by remember { mutableStateOf("") }
    var feedbackMessage by remember { mutableStateOf<Pair<String, Boolean>?>(null) } // Text to isError

    val quickAddList = listOf("youtube.com", "instagram.com", "reddit.com", "netflix.com", "tiktok.com", "twitter.com")

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp, vertical = 16.dp)
    ) {
        // ── Header ──
        Text(
            text = "Websites",
            fontWeight = FontWeight.Bold,
            fontSize = 24.sp,
            color = TextPrimary
        )
        Text(
            text = "Manage websites to block during focus mode",
            fontSize = 13.sp,
            color = TextSecondary
        )

        Spacer(modifier = Modifier.height(14.dp))

        // ── Lock Banner when active ──
        if (isSessionActive) {
            Card(
                shape = RoundedCornerShape(10.dp),
                colors = CardDefaults.cardColors(containerColor = WarningAmber.copy(alpha = 0.1f)),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, WarningAmber.copy(alpha = 0.3f), RoundedCornerShape(10.dp))
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(12.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Lock,
                        contentDescription = "Locked",
                        tint = WarningAmber,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Session active. Website list is locked.",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = WarningAmber
                    )
                }
            }
            Spacer(modifier = Modifier.height(12.dp))
        }

        // ── Add Website Card ──
        Card(
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = CardDark),
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderDark, RoundedCornerShape(14.dp))
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "ADD WEBSITE",
                    fontWeight = FontWeight.Bold,
                    fontSize = 10.sp,
                    letterSpacing = 1.sp,
                    color = TextSecondary
                )

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    OutlinedTextField(
                        value = inputText,
                        onValueChange = { inputText = it },
                        placeholder = { Text("Paste link or domain (e.g. youtube.com)", fontSize = 13.sp, color = TextMuted) },
                        singleLine = true,
                        enabled = !isSessionActive,
                        shape = RoundedCornerShape(10.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = PrimaryViolet,
                            unfocusedBorderColor = BorderDark,
                            focusedTextColor = TextPrimary,
                            unfocusedTextColor = TextPrimary,
                            focusedContainerColor = CardSecondary,
                            unfocusedContainerColor = CardSecondary
                        ),
                        modifier = Modifier.weight(1f)
                    )

                    Spacer(modifier = Modifier.width(8.dp))

                    Button(
                        onClick = {
                            val domain = DomainUtils.normalizeDomain(inputText)
                            if (domain == null) {
                                feedbackMessage = "Invalid domain or URL link." to true
                            } else {
                                onAddWebsite(domain)
                                val siteName = DomainUtils.getWebsiteName(domain)
                                feedbackMessage = "Added '$siteName' ($domain)" to false
                                inputText = ""
                            }
                        },
                        enabled = !isSessionActive && inputText.isNotBlank(),
                        shape = RoundedCornerShape(10.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryViolet),
                        modifier = Modifier.height(52.dp)
                    ) {
                        Icon(imageVector = Icons.Default.Add, contentDescription = "Add", tint = Color.White)
                    }
                }

                // Inline Feedback
                feedbackMessage?.let { (msg, isError) ->
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = msg,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = if (isError) DangerRed else SuccessGreen
                    )
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Quick Add Chips
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState())
                ) {
                    Text(
                        text = "Quick add: ",
                        fontSize = 11.sp,
                        color = TextSecondary
                    )
                    quickAddList.forEach { domain ->
                        val brand = DomainUtils.getWebsiteName(domain)
                        Box(
                            modifier = Modifier
                                .padding(end = 6.dp)
                                .clip(RoundedCornerShape(100.dp))
                                .background(PrimaryViolet.copy(alpha = 0.08f))
                                .border(1.dp, PrimaryViolet.copy(alpha = 0.25f), RoundedCornerShape(100.dp))
                                .clickable(enabled = !isSessionActive) {
                                    onAddWebsite(domain)
                                    feedbackMessage = "Added '$brand' ($domain)" to false
                                }
                                .padding(horizontal = 10.dp, vertical = 4.dp)
                        ) {
                            Text(
                                text = "+ $brand",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Medium,
                                color = PrimaryVioletLight
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // ── List Header & Toggle All ──
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth()
        ) {
            val enabledCount = websites.count { it.enabled }
            Text(
                text = "Configured Websites ($enabledCount/${websites.size})",
                fontWeight = FontWeight.SemiBold,
                fontSize = 13.sp,
                color = TextPrimary,
                modifier = Modifier.weight(1f)
            )

            TextButton(
                onClick = onEnableAll,
                enabled = !isSessionActive,
                contentPadding = PaddingValues(horizontal = 8.dp)
            ) {
                Text("Enable all", fontSize = 12.sp, color = if (!isSessionActive) PrimaryVioletLight else TextMuted)
            }

            TextButton(
                onClick = onDisableAll,
                enabled = !isSessionActive,
                contentPadding = PaddingValues(horizontal = 8.dp)
            ) {
                Text("Disable all", fontSize = 12.sp, color = if (!isSessionActive) TextSecondary else TextMuted)
            }
        }

        Spacer(modifier = Modifier.height(6.dp))

        // ── Website Cards List ──
        if (websites.isEmpty()) {
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(text = "🌐", fontSize = 36.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "No websites added yet.",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                        color = TextSecondary
                    )
                    Text(
                        text = "Add distracting websites above to begin focusing.",
                        fontSize = 12.sp,
                        color = TextMuted
                    )
                }
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.weight(1f)
            ) {
                items(websites, key = { it.id }) { site ->
                    WebsiteRow(
                        website = site,
                        isLocked = isSessionActive,
                        onToggle = { onToggleWebsite(site, it) },
                        onDelete = { onDeleteWebsite(site) }
                    )
                }
            }
        }
    }
}
