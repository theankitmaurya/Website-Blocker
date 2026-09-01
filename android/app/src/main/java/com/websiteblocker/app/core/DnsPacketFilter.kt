package com.websiteblocker.app.core

import java.nio.ByteBuffer
import java.util.Locale

/**
 * High-performance parser and generator for DNS packets (RFC 1035).
 * Used by BlockerVpnService for on-device local DNS inspection and filtering.
 */
object DnsPacketFilter {

    const val DNS_PORT = 53
    const val TYPE_A = 1
    const val TYPE_AAAA = 28

    data class DnsQuery(
        val transactionId: Short,
        val domain: String,
        val queryType: Int,
        val isQuery: Boolean,
        val rawHeaderAndQuestion: ByteArray
    )

    /**
     * Extracts the queried domain and transaction ID from a raw UDP DNS payload.
     */
    fun parseDnsQuery(dnsPayload: ByteArray): DnsQuery? {
        if (dnsPayload.size < 12) return null

        val buffer = ByteBuffer.wrap(dnsPayload)
        val transactionId = buffer.short
        val flags = buffer.short.toInt() and 0xFFFF
        val isQuery = (flags and 0x8000) == 0 // QR bit == 0 is Query
        val qdCount = buffer.short.toInt() and 0xFFFF

        if (!isQuery || qdCount < 1) return null

        buffer.position(12) // Skip ANCOUNT, NSCOUNT, ARCOUNT
        val domainBuilder = StringBuilder()

        while (buffer.hasRemaining()) {
            val length = buffer.get().toInt() and 0xFF
            if (length == 0) break // Root label reached
            if (length > 63) return null // Compressed label or invalid in question

            if (domainBuilder.isNotEmpty()) {
                domainBuilder.append('.')
            }

            val labelBytes = ByteArray(length)
            if (buffer.remaining() < length) return null
            buffer.get(labelBytes)
            domainBuilder.append(String(labelBytes, Charsets.US_ASCII))
        }

        if (buffer.remaining() < 4) return null
        val queryType = buffer.short.toInt() and 0xFFFF
        val queryClass = buffer.short.toInt() and 0xFFFF

        val questionEndPos = buffer.position()
        val headerAndQuestion = ByteArray(questionEndPos)
        System.arraycopy(dnsPayload, 0, headerAndQuestion, 0, questionEndPos)

        val domain = domainBuilder.toString().lowercase(Locale.ROOT)
        return DnsQuery(
            transactionId = transactionId,
            domain = domain,
            queryType = queryType,
            isQuery = true,
            rawHeaderAndQuestion = headerAndQuestion
        )
    }

    /**
     * Checks if [queryDomain] matches [blockedDomain] directly or as a subdomain.
     * E.g. queryDomain "m.youtube.com" matches blockedDomain "youtube.com".
     */
    fun isDomainBlocked(queryDomain: String, blockedDomains: Set<String>): Boolean {
        if (blockedDomains.isEmpty() || queryDomain.isBlank()) return false
        val cleanQuery = queryDomain.lowercase(Locale.ROOT).trimEnd('.')

        if (blockedDomains.contains(cleanQuery)) {
            return true
        }

        for (blocked in blockedDomains) {
            val cleanBlocked = blocked.lowercase(Locale.ROOT).trimEnd('.')
            if (cleanQuery.endsWith(".$cleanBlocked")) {
                return true
            }
        }
        return false
    }

    /**
     * Builds a synthetic DNS response pointing blocked A records to 0.0.0.0 or AAAA to ::
     */
    fun buildBlockedDnsResponse(query: DnsQuery): ByteArray {
        val qBytes = query.rawHeaderAndQuestion
        val isIpv6 = query.queryType == TYPE_AAAA
        val rDataSize = if (isIpv6) 16 else 4
        // Header + Question + Answer record (Name Pointer [2] + Type [2] + Class [2] + TTL [4] + RDLENGTH [2] + RDATA)
        val responseSize = qBytes.size + 12 + rDataSize
        val response = ByteBuffer.allocate(responseSize)

        // 1. Transaction ID
        response.putShort(query.transactionId)

        // 2. Flags: QR=1 (Response), AA=1, RA=1, RCODE=0 (No Error) -> 0x8180
        response.putShort(0x8180.toShort())

        // 3. QDCOUNT = 1, ANCOUNT = 1, NSCOUNT = 0, ARCOUNT = 0
        response.putShort(1.toShort())
        response.putShort(1.toShort())
        response.putShort(0.toShort())
        response.putShort(0.toShort())

        // 4. Question section (copy from query)
        response.put(qBytes, 12, qBytes.size - 12)

        // 5. Answer section:
        // Name pointer (0xc00c points to the question domain at byte 12)
        response.put(0xC0.toByte())
        response.put(0x0C.toByte())

        // Type (A = 1, AAAA = 28)
        response.putShort(query.queryType.toShort())

        // Class (IN = 1)
        response.putShort(1.toShort())

        // TTL (60 seconds)
        response.putInt(60)

        // RDLength
        response.putShort(rDataSize.toShort())

        // RData (0.0.0.0 or 0000:0000:0000:0000:0000:0000:0000:0000)
        for (i in 0 until rDataSize) {
            response.put(0.toByte())
        }

        return response.array()
    }
}
