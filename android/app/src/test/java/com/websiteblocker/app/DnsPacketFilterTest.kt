package com.websiteblocker.app

import com.websiteblocker.app.core.DnsPacketFilter
import org.junit.Assert.*
import org.junit.Test
import java.nio.ByteBuffer

class DnsPacketFilterTest {

    @Test
    fun testIsDomainBlocked() {
        val blocked = setOf("youtube.com", "reddit.com", "instagram.com")

        assertTrue(DnsPacketFilter.isDomainBlocked("youtube.com", blocked))
        assertTrue(DnsPacketFilter.isDomainBlocked("www.youtube.com", blocked))
        assertTrue(DnsPacketFilter.isDomainBlocked("m.youtube.com", blocked))
        assertTrue(DnsPacketFilter.isDomainBlocked("api.reddit.com", blocked))

        assertFalse(DnsPacketFilter.isDomainBlocked("google.com", blocked))
        assertFalse(DnsPacketFilter.isDomainBlocked("notyoutube.com", blocked))
        assertFalse(DnsPacketFilter.isDomainBlocked("", blocked))
    }

    @Test
    fun testParseDnsQueryAndBuildResponse() {
        // Construct a standard DNS Query packet for "youtube.com"
        val domain = "youtube.com"
        val labels = domain.split(".")
        val totalLen = 12 + domain.length + 2 + 4
        val buf = ByteBuffer.allocate(totalLen)

        buf.putShort(0x1234.toShort()) // Transaction ID
        buf.putShort(0x0100.toShort()) // Standard Query flags
        buf.putShort(1.toShort())      // QDCOUNT = 1
        buf.putShort(0.toShort())      // ANCOUNT = 0
        buf.putShort(0.toShort())      // NSCOUNT = 0
        buf.putShort(0.toShort())      // ARCOUNT = 0

        for (label in labels) {
            buf.put(label.length.toByte())
            buf.put(label.toByteArray(Charsets.US_ASCII))
        }
        buf.put(0.toByte()) // Root label
        buf.putShort(1.toShort()) // Type A
        buf.putShort(1.toShort()) // Class IN

        val queryPacket = buf.array()
        val query = DnsPacketFilter.parseDnsQuery(queryPacket)

        assertNotNull(query)
        assertEquals("youtube.com", query!!.domain)
        assertEquals(0x1234.toShort(), query.transactionId)
        assertEquals(DnsPacketFilter.TYPE_A, query.queryType)

        // Generate synthetic blocked DNS response
        val responseBytes = DnsPacketFilter.buildBlockedDnsResponse(query)
        assertNotNull(responseBytes)
        assertTrue(responseBytes.size > queryPacket.size)

        val resBuf = ByteBuffer.wrap(responseBytes)
        assertEquals(0x1234.toShort(), resBuf.short) // Same Transaction ID
        assertEquals(0x8180.toShort(), resBuf.short) // Response flags with RCODE 0
    }
}
