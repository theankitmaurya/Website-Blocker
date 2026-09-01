package com.websiteblocker.app

import android.app.Application
import com.websiteblocker.app.data.AppDatabase
import com.websiteblocker.app.data.models.WebsiteEntity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class WebsiteBlockerApp : Application() {

    val database by lazy { AppDatabase.getDatabase(this) }

    override fun onCreate() {
        super.onCreate()
        // Pre-populate popular sample websites if database is empty on first run
        CoroutineScope(Dispatchers.IO).launch {
            val dao = database.websiteDao()
            val existing = dao.getEnabledWebsitesSync()
            if (existing.isEmpty()) {
                val defaults = listOf(
                    "youtube.com",
                    "instagram.com",
                    "reddit.com",
                    "netflix.com",
                    "tiktok.com"
                )
                defaults.forEach { domain ->
                    dao.insert(WebsiteEntity(domain = domain, enabled = true))
                }
            }
        }
    }
}
