package com.websiteblocker.app.core

import android.content.Intent
import android.net.VpnService
import android.os.ParcelFileDescriptor
import android.util.Log
import com.websiteblocker.app.WebsiteBlockerApp
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.FileInputStream
import java.io.FileOutputStream
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.util.concurrent.atomic.AtomicBoolean

class BlockerVpnService : VpnService() {

    private var vpnInterface: ParcelFileDescriptor? = null
    private var vpnJob: Job? = null
    private val isRunning = AtomicBoolean(false)
    private var blockedDomains = setOf<String>()

    companion object {
        private const val TAG = "BlockerVpnService"
        const val ACTION_START = "com.websiteblocker.app.START_VPN"
        const val ACTION_STOP = "com.websiteblocker.app.STOP_VPN"

        private const val VPN_ADDRESS = "10.0.0.2"
        private const val VPN_DNS = "10.0.0.2"
        private const val UPSTREAM_DNS_PRIMARY = "1.1.1.1"
        private const val UPSTREAM_DNS_SECONDARY = "8.8.8.8"

        private val _isVpnActive = MutableStateFlow(false)
        val isVpnActive = _isVpnActive.asStateFlow()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action
        if (action == ACTION_STOP) {
            stopVpn()
            return START_NOT_STICKY
        }

        if (action == ACTION_START || action == null) {
            startVpn()
        }

        return START_STICKY
    }

    private fun startVpn() {
        if (isRunning.get()) return

        CoroutineScope(Dispatchers.IO).launch {
            // Load enabled domains from Room Database
            val db = (application as WebsiteBlockerApp).database
            val enabledList = db.websiteDao().getEnabledWebsitesSync()
            blockedDomains = enabledList.map { it.domain.lowercase() }.toSet()
            Log.d(TAG, "Loaded ${blockedDomains.size} blocked domains for VPN filtering.")

            try {
                val builder = Builder()
                    .setSession("Website Blocker")
                    .setMtu(1500)
                    .addAddress(VPN_ADDRESS, 32)
                    .addDnsServer(VPN_DNS)
                    // Intercept DNS traffic
                    .addRoute(VPN_DNS, 32)

                // Optional: allow bypass of the blocker app itself
                try {
                    builder.addDisallowedApplication(packageName)
                } catch (e: Exception) {
                    Log.w(TAG, "Could not add disallowed app: ${e.message}")
                }

                vpnInterface = builder.establish()
                if (vpnInterface == null) {
                    Log.e(TAG, "Failed to establish VPN interface (null).")
                    return@launch
                }

                isRunning.set(true)
                _isVpnActive.value = true
                Log.i(TAG, "Website Blocker VPN started successfully.")

                vpnJob = launch {
                    runPacketLoop()
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error starting VPN interface", e)
                stopVpn()
            }
        }
    }

    private fun runPacketLoop() {
        val pfd = vpnInterface ?: return
        val inputStream = FileInputStream(pfd.fileDescriptor)
        val outputStream = FileOutputStream(pfd.fileDescriptor)
        val packet = ByteBuffer.allocate(32767)

        var upstreamSocket: DatagramSocket? = null
        try {
            upstreamSocket = DatagramSocket()
            protect(upstreamSocket)
            upstreamSocket.soTimeout = 2000
        } catch (e: Exception) {
            Log.e(TAG, "Error creating upstream DNS socket", e)
        }

        val upstreamIp = InetAddress.getByName(UPSTREAM_DNS_PRIMARY)

        while (isRunning.get()) {
            try {
                val length = inputStream.read(packet.array())
                if (length > 0) {
                    packet.limit(length)
                    packet.position(0)

                    handleIpPacket(packet, outputStream, upstreamSocket, upstreamIp)
                    packet.clear()
                }
            } catch (e: Exception) {
                if (isRunning.get()) {
                    Log.e(TAG, "Error in packet loop", e)
                }
                break
            }
        }

        upstreamSocket?.close()
    }

    private fun handleIpPacket(
        packet: ByteBuffer,
        outputStream: FileOutputStream,
        upstreamSocket: DatagramSocket?,
        upstreamIp: InetAddress
    ) {
        val ipVersion = (packet.get(0).toInt() shr 4) and 0x0F
        if (ipVersion != 4) return // Focus on IPv4 DNS packets

        val ipHeaderLen = (packet.get(0).toInt() and 0x0F) * 4
        val protocol = packet.get(9).toInt() and 0xFF
        if (protocol != 17) return // Protocol 17 == UDP

        val srcIp = ByteArray(4).also { packet.position(12); packet.get(it) }
        val destIp = ByteArray(4).also { packet.position(16); packet.get(it) }

        // UDP Header (8 bytes)
        packet.position(ipHeaderLen)
        val srcPort = packet.short.toInt() and 0xFFFF
        val destPort = packet.short.toInt() and 0xFFFF
        val udpLength = packet.short.toInt() and 0xFFFF
        val udpChecksum = packet.short

        if (destPort != DnsPacketFilter.DNS_PORT || udpLength <= 8) return

        val dnsPayloadLength = udpLength - 8
        val dnsPayload = ByteArray(dnsPayloadLength)
        packet.position(ipHeaderLen + 8)
        packet.get(dnsPayload)

        val query = DnsPacketFilter.parseDnsQuery(dnsPayload)
        if (query != null) {
            val isBlocked = DnsPacketFilter.isDomainBlocked(query.domain, blockedDomains)
            if (isBlocked) {
                Log.i(TAG, "🛡️ BLOCKED domain query: '${query.domain}' -> 0.0.0.0")
                val responseDnsPayload = DnsPacketFilter.buildBlockedDnsResponse(query)
                val responseIpPacket = buildUdpIpPacket(
                    srcIp = destIp,
                    destIp = srcIp,
                    srcPort = destPort,
                    destPort = srcPort,
                    payload = responseDnsPayload
                )
                outputStream.write(responseIpPacket)
                return
            }
        }

        // Allowed domain: forward query to upstream DNS
        if (upstreamSocket != null) {
            try {
                val outPacket = DatagramPacket(dnsPayload, dnsPayload.size, upstreamIp, 53)
                upstreamSocket.send(outPacket)

                val inBuffer = ByteArray(1500)
                val inPacket = DatagramPacket(inBuffer, inBuffer.size)
                upstreamSocket.receive(inPacket)

                val validDnsResponse = ByteArray(inPacket.length)
                System.arraycopy(inBuffer, 0, validDnsResponse, 0, inPacket.length)

                val responseIpPacket = buildUdpIpPacket(
                    srcIp = destIp,
                    destIp = srcIp,
                    srcPort = destPort,
                    destPort = srcPort,
                    payload = validDnsResponse
                )
                outputStream.write(responseIpPacket)
            } catch (_: Exception) {
                // Timeout / network fluctuation
            }
        }
    }

    private fun buildUdpIpPacket(
        srcIp: ByteArray,
        destIp: ByteArray,
        srcPort: Int,
        destPort: Int,
        payload: ByteArray
    ): ByteArray {
        val totalLength = 20 + 8 + payload.size
        val packet = ByteBuffer.allocate(totalLength)

        // ── IPv4 Header (20 bytes) ──
        packet.put(0x45.toByte()) // Version 4, IHL 5
        packet.put(0x00.toByte()) // DSCP / ECN
        packet.putShort(totalLength.toShort()) // Total length
        packet.putShort(0.toShort()) // ID
        packet.putShort(0x4000.toShort()) // Flags (Don't Fragment)
        packet.put(64.toByte()) // TTL
        packet.put(17.toByte()) // Protocol (UDP)
        packet.putShort(0.toShort()) // Checksum placeholder
        packet.put(srcIp)
        packet.put(destIp)

        // Calculate IP Header Checksum
        val ipChecksum = computeIpChecksum(packet.array(), 0, 20)
        packet.putShort(10, ipChecksum.toShort())

        // ── UDP Header (8 bytes) ──
        packet.position(20)
        packet.putShort(srcPort.toShort())
        packet.putShort(destPort.toShort())
        packet.putShort((8 + payload.size).toShort())
        packet.putShort(0.toShort()) // UDP Checksum optional in IPv4

        // ── Payload ──
        packet.put(payload)
        return packet.array()
    }

    private fun computeIpChecksum(data: ByteArray, offset: Int, length: Int): Int {
        var sum = 0
        for (i in offset until offset + length step 2) {
            val word = ((data[i].toInt() and 0xFF) shl 8) or (data[i + 1].toInt() and 0xFF)
            sum += word
        }
        while ((sum shr 16) > 0) {
            sum = (sum and 0xFFFF) + (sum shr 16)
        }
        return sum.inv() and 0xFFFF
    }

    private fun stopVpn() {
        isRunning.set(false)
        _isVpnActive.value = false
        vpnJob?.cancel()
        vpnJob = null

        try {
            vpnInterface?.close()
        } catch (_: Exception) {}
        vpnInterface = null

        stopSelf()
        Log.i(TAG, "Website Blocker VPN stopped.")
    }

    override fun onDestroy() {
        stopVpn()
        super.onDestroy()
    }
}
