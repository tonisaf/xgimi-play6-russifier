package com.beam.russifier.boot;
import android.app.job.*;
import android.content.*;
public final class BootJob extends JobService {
    static void configure(Context context) {
        JobScheduler scheduler=context.getSystemService(JobScheduler.class);
        if (!RestorePrefs.get(context).getBoolean("enabled",true)) { scheduler.cancel(1400);return; }
        if(scheduler.getPendingJob(1400)==null) scheduler.schedule(new JobInfo.Builder(1400,new ComponentName(context,BootJob.class))
            .setPersisted(true).setPeriodic(15*60*1000L,15*60*1000L).build());
    }
    public boolean onStartJob(JobParameters params) {
        new Thread(() -> {
            try {
                if(RestorePrefs.get(this).getBoolean("enabled",true)
                  && MainActivity.exec("/system/bin/getprop","sys.boot_completed").equals("1")
                  && !MainActivity.read("/proc/sys/kernel/random/boot_id").equals(RestorePrefs.get(this).getString("boot","")))
                    startForegroundService(new Intent(this,RestoreService.class));
            } catch(Exception e) {
                RestorePrefs.get(this).edit().putString("last","Ошибка планировщика: "+e.getMessage()).apply();
            }
            jobFinished(params,false);
        },"xgimi-boot-check").start();
        return true;
    }
    public boolean onStopJob(JobParameters params) { return true; }
}
