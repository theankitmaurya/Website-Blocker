package com.websiteblocker.app.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.websiteblocker.app.data.dao.SessionDao
import com.websiteblocker.app.data.dao.WebsiteDao
import com.websiteblocker.app.data.models.SessionEntity
import com.websiteblocker.app.data.models.WebsiteEntity

@Database(
    entities = [WebsiteEntity::class, SessionEntity::class],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {

    abstract fun websiteDao(): WebsiteDao
    abstract fun sessionDao(): SessionDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "website_blocker_db"
                ).fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
