package com.beam.russifier.boot;
import android.content.*;
public final class BootReceiver extends BroadcastReceiver {
    public void onReceive(Context context,Intent intent) {
        if(RestorePrefs.get(context).getBoolean("enabled",true))
            context.startForegroundService(new Intent(context,RestoreService.class));
    }
}
