package com.websiteblocker.app

import com.websiteblocker.app.utils.DomainUtils
import org.junit.Assert.*
import org.junit.Test

class DomainUtilsTest {

    @Test
    fun testNormalizeDomain() {
        assertEquals("youtube.com", DomainUtils.normalizeDomain("youtube.com"))
        assertEquals("youtube.com", DomainUtils.normalizeDomain("www.youtube.com"))
        assertEquals("youtube.com", DomainUtils.normalizeDomain("https://www.youtube.com/watch?v=123"))
        assertEquals("reddit.com", DomainUtils.normalizeDomain("http://reddit.com/r/android"))
        assertEquals("instagram.com", DomainUtils.normalizeDomain("HTTPS://INSTAGRAM.COM/p/abc"))
        assertEquals("netflix.com", DomainUtils.normalizeDomain("www.netflix.com:443"))
        assertEquals("sub.domain.co.uk", DomainUtils.normalizeDomain("sub.domain.co.uk"))
        assertEquals("192.168.1.1", DomainUtils.normalizeDomain("192.168.1.1"))

        assertNull(DomainUtils.normalizeDomain(""))
        assertNull(DomainUtils.normalizeDomain("   "))
        assertNull(DomainUtils.normalizeDomain("hello world"))
        assertNull(DomainUtils.normalizeDomain("http://"))
        assertNull(DomainUtils.normalizeDomain("random text"))
    }

    @Test
    fun testIsValidDomain() {
        assertTrue(DomainUtils.isValidDomain("youtube.com"))
        assertTrue(DomainUtils.isValidDomain("reddit.com"))
        assertTrue(DomainUtils.isValidDomain("sub.example.org"))
        assertTrue(DomainUtils.isValidDomain("127.0.0.1"))

        assertFalse(DomainUtils.isValidDomain("hello"))
        assertFalse(DomainUtils.isValidDomain(""))
        assertFalse(DomainUtils.isValidDomain("-test.com"))
        assertFalse(DomainUtils.isValidDomain("256.256.256.256"))
    }

    @Test
    fun testGetWebsiteName() {
        assertEquals("YouTube", DomainUtils.getWebsiteName("youtube.com"))
        assertEquals("YouTube", DomainUtils.getWebsiteName("https://www.youtube.com/watch?v=123"))
        assertEquals("Reddit", DomainUtils.getWebsiteName("reddit.com"))
        assertEquals("Instagram", DomainUtils.getWebsiteName("https://instagram.com/p/abc"))
        assertEquals("Netflix", DomainUtils.getWebsiteName("netflix.com"))
        assertEquals("Twitter", DomainUtils.getWebsiteName("twitter.com"))
        assertEquals("X (Twitter)", DomainUtils.getWebsiteName("x.com"))
        assertEquals("Hacker News", DomainUtils.getWebsiteName("news.ycombinator.com"))
        assertEquals("ChatGPT", DomainUtils.getWebsiteName("chatgpt.com"))
        assertEquals("Example", DomainUtils.getWebsiteName("sub.example.co.uk"))
        assertEquals("My Productivity Hub", DomainUtils.getWebsiteName("my-productivity-hub.org"))
        assertEquals("192.168.1.1", DomainUtils.getWebsiteName("192.168.1.1"))
    }
}
