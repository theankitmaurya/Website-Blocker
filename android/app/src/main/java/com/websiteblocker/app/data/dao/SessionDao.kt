package com.websiteblocker.app.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.websiteblocker.app.data.models.SessionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SessionDao {
    @Query("SELECT * FROM sessions ORDER BY startTime DESC")
    fun getAllSessions(): Flow<List<SessionEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(session: SessionEntity): Long

    @Query("UPDATE sessions SET status = :status, endTime = :endTime WHERE id = :sessionId")
    suspend fun endSessionInternal(sessionId: Long, status: String, endTime: Long)

    suspend fun endSession(sessionId: Long, status: String) {
        endSessionInternal(sessionId, status, System.currentTimeMillis())
    }

    @Query("DELETE FROM sessions")
    suspend fun clearAll()
}
