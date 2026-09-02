package com.websiteblocker.app.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.websiteblocker.app.data.models.WebsiteEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface WebsiteDao {
    @Query("SELECT * FROM websites ORDER BY domain ASC")
    fun getAllWebsites(): Flow<List<WebsiteEntity>>

    @Query("SELECT * FROM websites WHERE enabled = 1 ORDER BY domain ASC")
    suspend fun getEnabledWebsitesSync(): List<WebsiteEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(website: WebsiteEntity): Long

    @Query("UPDATE websites SET enabled = :enabled WHERE id = :id")
    suspend fun setEnabled(id: Long, enabled: Boolean)

    @Query("DELETE FROM websites WHERE id = :id")
    suspend fun deleteById(id: Long)

    @Query("UPDATE websites SET enabled = :enabled")
    suspend fun setAllEnabled(enabled: Boolean)
}
