package com.websiteblocker.app.data.models

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "sessions")
data class SessionEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val durationSeconds: Int,
    val startTime: Long = System.currentTimeMillis(),
    val endTime: Long? = null,
    val status: String
)
