package com.websiteblocker.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.websiteblocker.app.data.models.WebsiteEntity
import com.websiteblocker.app.ui.theme.*
import kotlin.math.abs

@Composable
fun WebsiteRow(
    website: WebsiteEntity,
    isLocked: Boolean,
    onToggle: (Boolean) -> Unit,
    onDelete: () -> Unit,
    modifier: Modifier = Modifier
) {
    val avatarColors = listOf(
        PrimaryViolet,
        SuccessGreen,
        WarningAmber,
        Color(0xFF3B82F6),
        Color(0xFFEC4899),
        Color(0xFF14B8A6),
        Color(0xFFF97316)
    )
    val accentColor = avatarColors[abs(website.domain.hashCode()) % avatarColors.size]

    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = CardDark),
        modifier = modifier
            .fillMaxWidth()
            .border(1.dp, BorderDark, RoundedCornerShape(12.dp))
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier
                .padding(horizontal = 14.dp, vertical = 10.dp)
                .fillMaxWidth()
        ) {
            // ── Favicon / Avatar ──
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(accentColor.copy(alpha = 0.15f))
                    .border(1.dp, accentColor.copy(alpha = 0.35f), CircleShape)
            ) {
                AsyncImage(
                    model = website.faviconUrl,
                    contentDescription = website.displayName,
                    modifier = Modifier.size(24.dp)
                )
            }

            Spacer(modifier = Modifier.width(12.dp))

            // ── Name & Domain ──
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = website.displayName,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 15.sp,
                    color = if (website.enabled) TextPrimary else TextMuted
                )
                Text(
                    text = website.domain,
                    fontSize = 12.sp,
                    color = TextSecondary
                )
            }

            // ── Enabled Switch ──
            Switch(
                checked = website.enabled,
                onCheckedChange = { if (!isLocked) onToggle(it) },
                enabled = !isLocked,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = Color.White,
                    checkedTrackColor = PrimaryViolet,
                    uncheckedThumbColor = TextSecondary,
                    uncheckedTrackColor = CardSecondary
                )
            )

            Spacer(modifier = Modifier.width(6.dp))

            // ── Delete Button ──
            IconButton(
                onClick = { if (!isLocked) onDelete() },
                enabled = !isLocked
            ) {
                Icon(
                    imageVector = Icons.Default.Delete,
                    contentDescription = "Delete website",
                    tint = if (!isLocked) DangerRed.copy(alpha = 0.8f) else TextMuted
                )
            }
        }
    }
}
