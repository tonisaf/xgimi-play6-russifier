package com.beam.russifier.boot;
import android.accessibilityservice.*;
import android.view.accessibility.AccessibilityEvent;
import android.content.Intent;
import android.os.SystemClock;
import android.util.Log;
public final class StartupBridge extends AccessibilityService {
    private java.util.concurrent.ScheduledExecutorService watcher;
    private long retryAfter;
    private long seenResult;
    protected void onServiceConnected() {
        AccessibilityServiceInfo info=getServiceInfo();
        info.eventTypes=0; info.flags=0; setServiceInfo(info);
        Log.i("BeamStartup", "connected uptime="+SystemClock.elapsedRealtime()+" capabilities="+info.getCapabilities());
        if(RestorePrefs.get(this).getBoolean("enabled",true)) {
            try { startForegroundService(new Intent(this,RestoreService.class)); }
            catch(Exception e) { Log.e("BeamStartup", "restore start failed",e); }
        }
        if(watcher!=null) watcher.shutdownNow();
        watcher=java.util.concurrent.Executors.newSingleThreadScheduledExecutor();
        watcher.scheduleWithFixedDelay(() -> {
            if(!RestorePrefs.get(this).getBoolean("enabled",true) || RestoreService.isRunning()) return;
            long resultTime=RestorePrefs.get(this).getLong("time",0);
            if(resultTime!=seenResult) {
                seenResult=resultTime;
                retryAfter=RestorePrefs.get(this).getString("last","").startsWith("Ошибка")
                    ? SystemClock.elapsedRealtime()+30000 : 0;
            }
            if(SystemClock.elapsedRealtime()<retryAfter) return;
            try {
                if(RestoreService.needed(this,false)!=RestorePolicy.NONE) {
                    retryAfter=SystemClock.elapsedRealtime()+5000;
                    startForegroundService(new Intent(this,RestoreService.class));
                }
            } catch(Exception e) { retryAfter=SystemClock.elapsedRealtime()+30000;Log.e("BeamStartup","theme check failed",e); }
        },5,5,java.util.concurrent.TimeUnit.SECONDS);
    }
    public void onDestroy() { if(watcher!=null) watcher.shutdownNow();super.onDestroy(); }
    public void onAccessibilityEvent(AccessibilityEvent event) {}
    public void onInterrupt() {}
}
