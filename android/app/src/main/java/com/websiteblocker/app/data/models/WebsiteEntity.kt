package com.websiteblocker.app.data.models

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.websiteblocker.app.utils.DomainUtils

@Entity(tableName = "websites")
data class WebsiteEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val domain: String,
    val enabled: Boolean = true
) {
    val displayName: String
        get() = DomainUtils.getWebsiteName(domain)

    val faviconUrl: String
        get() = "https://www.google.com/s2/favicons?domain=$domain&sz=64"
}
