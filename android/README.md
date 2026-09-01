# 📱 Website Blocker (Android Mobile Application)

A native Android mobile application built with **Kotlin**, **Jetpack Compose**, and **Room SQLite**. It blocks distracting websites on Android mobile devices at the system level across **all mobile web browsers** (Chrome, Edge, Firefox, Brave, Samsung Internet) using an on-device local `VpnService` with zero remote servers or telemetry.

---

## ✨ Android Features

- 🛡️ **100% On-Device Local VPN Blocking**: Uses Android's `VpnService` API to intercept DNS queries locally and resolve blocked domains to `0.0.0.0`. No external VPN server is contacted.
- 🎨 **Jetpack Compose Dark Theme**: Matches the desktop experience with custom animated circular countdown ring, responsive layout, and smooth typography.
- 🏷️ **Smart Brand Name Detection**: Paste any link or URL (e.g. `https://www.youtube.com/watch?v=123`) and it automatically displays as **YouTube**, **Reddit**, **Instagram**, etc.
- 🖼️ **Real Favicon Rendering**: Dynamically renders high-resolution website favicons with fallback colored avatars.
- ⏱️ **Foreground Focus Timer Service**: Runs in the background with an ongoing Android status bar notification and a quick "Stop" button.
- 📊 **Productivity Statistics**: Real-time SQLite tracking of daily focus hours, weekly metrics, and past session history.

---

## 🛠️ Opening & Building in Android Studio

1. Open **Android Studio** (Koala / Ladybug or newer).
2. Select **File $\rightarrow$ Open...** and navigate to the [`android/`](file:///c:/Users/ankit/OneDrive/ドキュメント/Projects/website-blocker/android) folder.
3. Allow Gradle to sync dependencies automatically.
4. Select a connected physical Android device or Android Virtual Device (AVD / Emulator) running **Android 8.0 (API 26) or higher**.
5. Click **Run $\rightarrow$ Run 'app'** (`Shift + F10`) to deploy and test.

---

## 🧪 Running Unit Tests

Run local JVM unit tests via Gradle:

```bash
cd android
./gradlew testDebugUnitTest
```

---

## 🔒 Android Permissions

- `android.permission.INTERNET`: Used for fetching high-resolution website favicons and querying upstream DNS (`1.1.1.1`).
- `android.permission.BIND_VPN_SERVICE`: Required for on-device local DNS query interception.
- `android.permission.FOREGROUND_SERVICE`: Keeps countdown timer running when device screen is off.
- `android.permission.POST_NOTIFICATIONS`: Shows ongoing notification timer on Android 13+.
