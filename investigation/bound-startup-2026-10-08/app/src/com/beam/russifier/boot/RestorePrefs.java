package com.beam.russifier.boot;
import android.content.*;
final class RestorePrefs {
    static SharedPreferences get(Context context) {
        return context.createDeviceProtectedStorageContext().getSharedPreferences("restore",Context.MODE_MULTI_PROCESS);   // the screen runs in its own process (":ui")
    }
    static void migrate(Context context) {
        if(!get(context).contains("last")) context.createDeviceProtectedStorageContext().moveSharedPreferencesFrom(context,"restore");
    }
}
