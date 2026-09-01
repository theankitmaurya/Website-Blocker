package com.websiteblocker.app.utils

import java.net.URI
import java.util.Locale
import java.util.regex.Pattern

object DomainUtils {

    private val DOMAIN_REGEX = Pattern.compile(
        "^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\\.)+[a-zA-Z]{2,63}$"
    )

    private val IPV4_REGEX = Pattern.compile(
        "^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    val POPULAR_WEBSITE_NAMES = mapOf(
        "youtube.com" to "YouTube",
        "youtu.be" to "YouTube",
        "reddit.com" to "Reddit",
        "instagram.com" to "Instagram",
        "facebook.com" to "Facebook",
        "fb.com" to "Facebook",
        "twitter.com" to "Twitter",
        "x.com" to "X (Twitter)",
        "netflix.com" to "Netflix",
        "tiktok.com" to "TikTok",
        "twitch.tv" to "Twitch",
        "twitch.com" to "Twitch",
        "github.com" to "GitHub",
        "gitlab.com" to "GitLab",
        "discord.com" to "Discord",
        "discord.gg" to "Discord",
        "linkedin.com" to "LinkedIn",
        "amazon.com" to "Amazon",
        "pinterest.com" to "Pinterest",
        "quora.com" to "Quora",
        "wikipedia.org" to "Wikipedia",
        "spotify.com" to "Spotify",
        "whatsapp.com" to "WhatsApp",
        "telegram.org" to "Telegram",
        "t.me" to "Telegram",
        "hulu.com" to "Hulu",
        "disneyplus.com" to "Disney+",
        "primevideo.com" to "Prime Video",
        "chatgpt.com" to "ChatGPT",
        "openai.com" to "OpenAI",
        "claude.ai" to "Claude",
        "medium.com" to "Medium",
        "stackoverflow.com" to "Stack Overflow",
        "stackexchange.com" to "Stack Exchange",
        "steamcommunity.com" to "Steam",
        "steampowered.com" to "Steam",
        "roblox.com" to "Roblox",
        "epicgames.com" to "Epic Games",
        "cnn.com" to "CNN",
        "bbc.com" to "BBC",
        "bbc.co.uk" to "BBC",
        "nytimes.com" to "The New York Times",
        "wsj.com" to "The Wall Street Journal",
        "theverge.com" to "The Verge",
        "techcrunch.com" to "TechCrunch",
        "news.ycombinator.com" to "Hacker News",
        "ycombinator.com" to "Y Combinator",
        "ebay.com" to "eBay",
        "apple.com" to "Apple",
        "google.com" to "Google",
        "microsoft.com" to "Microsoft",
        "yahoo.com" to "Yahoo",
        "bing.com" to "Bing",
        "duckduckgo.com" to "DuckDuckGo",
        "zoom.us" to "Zoom",
        "slack.com" to "Slack",
        "notion.so" to "Notion",
        "trello.com" to "Trello",
        "figma.com" to "Figma",
        "canva.com" to "Canva",
        "threads.net" to "Threads",
        "snapchat.com" to "Snapchat",
        "tumblr.com" to "Tumblr",
        "vimeo.com" to "Vimeo",
        "soundcloud.com" to "SoundCloud",
        "coursera.org" to "Coursera",
        "udemy.com" to "Udemy",
        "imdb.com" to "IMDb",
        "duolingo.com" to "Duolingo"
    )

    private val MULTI_PART_TLDS = setOf(
        "co.uk", "gov.uk", "ac.uk", "org.uk", "net.uk",
        "co.in", "net.in", "org.in", "gov.in",
        "co.jp", "ne.jp", "ac.jp", "go.jp",
        "com.au", "net.au", "org.au", "edu.au",
        "com.br", "org.br", "net.br",
        "co.nz", "org.nz", "net.nz",
        "co.za", "org.za", "net.za",
        "com.sg", "edu.sg"
    )

    fun normalizeDomain(rawInput: String?): String? {
        if (rawInput.isNullOrBlank()) return null
        val cleaned = rawInput.trim()
        if (cleaned.any { it.isWhitespace() }) return null

        var hostname: String?
        try {
            val uri = if (!cleaned.contains("://")) {
                if (cleaned.startsWith("//")) URI("http:$cleaned") else URI("http://$cleaned")
            } else {
                URI(cleaned)
            }
            hostname = uri.host
            if (hostname.isNullOrBlank()) {
                val path = uri.path ?: ""
                hostname = path.split("/").firstOrNull()?.split(":")?.firstOrNull()
            }
        } catch (_: Exception) {
            hostname = cleaned.split("/").firstOrNull()?.split(":")?.firstOrNull()
        }

        if (hostname.isNullOrBlank()) return null
        var h = hostname.lowercase(Locale.ROOT).trim()

        if (h.contains(":")) {
            h = h.split(":").first()
        }
        if (h.startsWith("www.")) {
            h = h.substring(4)
        }
        h = h.trimEnd('.')

        if (h.isBlank() || !isValidDomain(h)) return null
        return h
    }

    fun isValidDomain(domain: String?): Boolean {
        if (domain.isNullOrBlank()) return false
        val d = domain.trim().lowercase(Locale.ROOT)
        if (d.length > 253) return false

        if (DOMAIN_REGEX.matcher(d).matches()) {
            val labels = d.split(".")
            for (label in labels) {
                if (label.isEmpty() || label.length > 63 || label.startsWith("-") || label.endsWith("-")) {
                    return false
                }
            }
            return true
        }

        return IPV4_REGEX.matcher(d).matches()
    }

    fun getWebsiteName(rawInputOrDomain: String?): String {
        if (rawInputOrDomain.isNullOrBlank()) return ""
        val domain = normalizeDomain(rawInputOrDomain) ?: rawInputOrDomain.trim().lowercase(Locale.ROOT)
        if (domain.isBlank()) return ""

        POPULAR_WEBSITE_NAMES[domain]?.let { return it }

        if (IPV4_REGEX.matcher(domain).matches()) return domain

        val parts = domain.split(".")
        val labels = if (parts.size >= 2) {
            val twoPart = "${parts[parts.size - 2]}.${parts.last()}"
            if (MULTI_PART_TLDS.contains(twoPart)) {
                parts.dropLast(2)
            } else {
                parts.dropLast(1)
            }
        } else {
            parts
        }

        val mainName = labels.lastOrNull() ?: domain
        val words = mainName.split(Regex("[-_]+")).filter { it.isNotEmpty() }
        val titleCased = words.joinToString(" ") { word ->
            word.replaceFirstChar { if (it.isLowerCase()) it.titlecase(Locale.ROOT) else it.toString() }
        }

        return titleCased.ifBlank { domain.replaceFirstChar { it.uppercase() } }
    }

    fun getFaviconUrl(domain: String): String {
        return "https://www.google.com/s2/favicons?domain=$domain&sz=128"
    }
}
