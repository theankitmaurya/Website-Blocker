package com.websiteblocker.app

import com.websiteblocker.app.data.models.WebsiteEntity
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class WebsiteEntityTest {

    @Test
    fun computesDisplayNameFromDomain() {
        val website = WebsiteEntity(domain = "youtube.com")
        assertEquals("YouTube", website.displayName)
    }

    @Test
    fun buildsGoogleFaviconUrlFromDomain() {
        val website = WebsiteEntity(domain = "reddit.com")
        assertTrue(website.faviconUrl.contains("domain=reddit.com"))
        assertTrue(website.faviconUrl.endsWith("&sz=64"))
    }
}
