package com.beam.russifier.boot;
import android.app.*;
import android.content.Intent;
import android.os.IBinder;
import java.io.*;
import java.security.MessageDigest;

public final class RestoreService extends Service {
    private static boolean running;
    public IBinder onBind(Intent intent) { return null; }
    public int onStartCommand(Intent intent, int flags, int startId) {
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("restore","Восстановление настроек",NotificationManager.IMPORTANCE_LOW));
        startForeground(1,new Notification.Builder(this,"restore").setSmallIcon(android.R.drawable.ic_popup_sync)
            .setContentTitle("Русификатор XGIMI").setContentText("Восстановление изменений панели").build());
        if (!running) {
            running=true;
            new Thread(() -> {
                String result;
                try {
                    String boot=MainActivity.read("/proc/sys/kernel/random/boot_id");
                    result=!(intent!=null && intent.getBooleanExtra("manual",false)) && boot.equals(RestorePrefs.get(this).getString("boot","")) ? "Изменения восстановлены" : restore();
                } catch(Exception e) { result="Ошибка: "+e.getMessage(); }
                RestorePrefs.get(this).edit().putString("last",result).putLong("time",System.currentTimeMillis()).apply();
                running=false; stopForeground(true);stopSelf();
            },"xgimi-restore").start();
        }
        return START_NOT_STICKY;
    }
    private String restore() {
        final String key="vendor.xgimi.system.debug.cmd", start="vendor.xgimi.system.debugserver";
        String command=null,flag=null; boolean owned=false;String report;
        try {
            if (!MainActivity.exec("/system/bin/getprop","ro.build.fingerprint").equals(RestoreConfig.FINGERPRINT))
                throw new IOException("Прошивка не поддерживается");
            if (!MainActivity.exec("/system/bin/getenforce").equals("Permissive")) throw new IOException("Системный доступ недоступен");
            for(int i=0;!MainActivity.exec("/system/bin/getprop","sys.boot_completed").equals("1");i++) {
                if(i>=120)throw new IOException("Android ещё не завершил загрузку");Thread.sleep(250);
            }
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            try (FileInputStream file=new FileInputStream(RestoreConfig.SCRIPT)) {
                byte[] buffer=new byte[4096];int count;while((count=file.read(buffer))>=0)digest.update(buffer,0,count);
            }
            StringBuilder hash=new StringBuilder();for(byte b:digest.digest())hash.append(String.format("%02x",b&255));
            if (!hash.toString().equals(RestoreConfig.SHA256)) throw new IOException("Файлы восстановления изменены");
            for(int i=0;i<20;i++) {
                command=MainActivity.exec("/system/bin/getprop",key);flag=MainActivity.exec("/system/bin/getprop",start);
                String state=MainActivity.exec("/system/bin/getprop","init.svc.debugserver");
                if (command.isEmpty() && (flag.isEmpty() || flag.equals("0")) && !state.equals("running")) break;
                if(i==19)throw new IOException("Диагностическая служба занята");Thread.sleep(500);
            }
            String before=MainActivity.read(RestoreConfig.DIRECTORY+"/done");
            owned=true;
            String expected="/system/bin/sh "+RestoreConfig.SCRIPT;
            MainActivity.exec("/system/bin/setprop",key,expected);
            if (!MainActivity.exec("/system/bin/getprop",key).equals(expected)) throw new IOException("Нет доступа к системной службе");
            MainActivity.exec("/system/bin/setprop",start,"1");
            if (!MainActivity.exec("/system/bin/getprop",start).equals("1")) throw new IOException("Служба не запущена");
            report=null;
            for(int i=0;i<180;i++) {
                String done=MainActivity.read(RestoreConfig.DIRECTORY+"/done");
                if (!done.isEmpty() && !done.equals(before)) {
                    if (!done.endsWith(" 0")) throw new IOException("Проверка или восстановление не прошло. Код: "+done.substring(done.lastIndexOf(' ')+1));
                    RestorePrefs.get(this).edit().putString("boot",MainActivity.read("/proc/sys/kernel/random/boot_id")).apply();
                    report="Изменения восстановлены";break;
                }
                Thread.sleep(500);
            }
            if(report==null)throw new IOException("Восстановление не завершилось за 90 секунд");
        } catch(Exception e) { report="Ошибка: "+e.getMessage(); }
        finally {
            if(owned)try {
                MainActivity.exec("/system/bin/setprop",start,flag);MainActivity.exec("/system/bin/setprop",key,command);
                if(!MainActivity.exec("/system/bin/getprop",key).equals(command) || !MainActivity.exec("/system/bin/getprop",start).equals(flag))
                    throw new IOException("свойства не восстановлены");
            } catch(Exception e) { report="Ошибка восстановления системной службы: "+e.getMessage(); }
        }
        return report;
    }
}
