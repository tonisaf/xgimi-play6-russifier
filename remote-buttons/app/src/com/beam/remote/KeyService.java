package com.beam.remote;

import android.app.*;
import android.content.*;
import android.os.*;
import android.util.Log;
import java.util.*;

/** OEM calls are serialized on a worker; main-thread callbacks never transact. */
public final class KeyService extends Service {
    static final String TAG = "BeamRemoteKeys", COMMON = "com.xgimi.aidl.IGimiCommon";
    static final long RETRY_MS = 5000, TIMEOUT_MS = 8000;
    final Handler main = new Handler(Looper.getMainLooper());
    HandlerThread thread;
    Handler worker;
    SharedPreferences prefs;
    Connection active; // Main thread only.
    volatile boolean closing;
    long lastKey = -1, lastTime;
    final Runnable retry = () -> connect();

    final class Connection implements ServiceConnection {
        volatile boolean live = true;
        boolean bound;
        IBinder common; // Worker thread only.
        KeyRegistry registry;
        final Runnable resync = () -> synchronize(this);
        final IBinder.DeathRecipient death = () -> main.post(() -> disconnect(this));
        final Runnable timeout = () -> {
            Log.w(TAG, "OEM connection/call timeout; waiting for worker cleanup");
            disconnect(this);
        };
        final Binder listener = new Binder() {
            protected boolean onTransact(int code, Parcel data, Parcel reply, int flags) throws RemoteException {
                if (code == INTERFACE_TRANSACTION) {
                    if (reply != null) reply.writeString("com.xgimi.aidl.IGimiInterceptKeyListener");
                    return true;
                }
                if (code == 1) {
                    data.enforceInterface("com.xgimi.aidl.IGimiInterceptKeyListener");
                    long key = data.readLong();
                    main.post(() -> { if (live && active == Connection.this && !closing) dispatch(key); });
                    if (reply != null) reply.writeNoException();
                    return true;
                }
                return super.onTransact(code, data, reply, flags);
            }
        };
        public void onServiceConnected(ComponentName name, IBinder binder) {
            if (!live || active != this) return;
            // The watchdog includes descriptor and initial registration calls.
            worker.post(() -> {
                if (!live) return;
                try {
                    Parcel data = Parcel.obtain(), reply = Parcel.obtain();
                    try {
                        if (!"com.xgimi.aidl.IXgimiService".equals(binder.getInterfaceDescriptor()))
                            throw new IllegalStateException("Unknown service");
                        data.writeInterfaceToken("com.xgimi.aidl.IXgimiService");
                        if (!binder.transact(1, data, reply, 0)) throw new RemoteException("getGimiCommon");
                        reply.readException();
                        common = reply.readStrongBinder();
                    } finally { data.recycle(); reply.recycle(); }
                    if (common == null || !COMMON.equals(common.getInterfaceDescriptor()))
                        throw new IllegalStateException("Unknown common");
                    common.linkToDeath(death, 0);
                    registry = new KeyRegistry(new KeyRegistry.Port() {
                        public boolean add(long key) throws Exception { return transact(key, true); }
                        public void remove(long key) throws Exception { transact(key, false); }
                    });
                    if (live) synchronize(this);
                } catch (Exception error) {
                    Log.e(TAG, "connect", error);
                    main.post(() -> disconnect(this));
                } finally { main.post(() -> main.removeCallbacks(timeout)); }
            });
        }
        boolean transact(long key, boolean add) throws RemoteException {
            Parcel data = Parcel.obtain(), reply = Parcel.obtain();
            try {
                data.writeInterfaceToken(COMMON);
                data.writeLong(key);
                if (add) data.writeStrongBinder(listener);
                if (!common.transact(add ? 3 : 4, data, reply, 0)) throw new RemoteException("Unsupported transaction");
                reply.readException();
                boolean accepted = !add || reply.readInt() != 0;
                Log.i(TAG, (add ? "register " : "release ") + key + " accepted=" + accepted);
                return accepted;
            } finally { data.recycle(); reply.recycle(); }
        }
        public void onServiceDisconnected(ComponentName name) { disconnect(this); }
        public void onBindingDied(ComponentName name) { disconnect(this); }
        public void onNullBinding(ComponentName name) { disconnect(this); }
    }

    public void onCreate() {
        super.onCreate();
        prefs = getSharedPreferences("buttons", MODE_PRIVATE);
        thread = new HandlerThread("RemoteKeysBinder");
        thread.start(); worker = new Handler(thread.getLooper());
        NotificationManager manager = getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("keys", "Кнопки пульта", NotificationManager.IMPORTANCE_LOW));
        startForeground(1, new Notification.Builder(this, "keys").setSmallIcon(android.R.drawable.ic_menu_manage)
            .setContentTitle("Настройка кнопок пульта включена").build());
    }
    public int onStartCommand(Intent intent, int flags, int id) {
        if (active != null && active.live) {
            Connection current = active;
            worker.post(() -> { if (current.live && current.registry != null) synchronize(current); });
        } else connect();
        return START_STICKY;
    }
    void connect() {
        if (active != null || closing) return;
        main.removeCallbacks(retry);
        Connection next = new Connection(); active = next;
        try {
            next.bound = bindService(new Intent().setComponent(new ComponentName("com.xgimi.xgimiservice",
                "com.xgimi.xgimiservice.services.XgimiServices")), next, BIND_AUTO_CREATE);
            if (!next.bound) disconnect(next);
            else main.postDelayed(next.timeout, TIMEOUT_MS);
        } catch (Exception error) { Log.e(TAG, "bind", error); disconnect(next); }
    }
    void synchronize(Connection current) {
        if (!current.live || closing) return;
        Set<Long> wanted = new TreeSet<>();
        for (int i = 0; i < 4; i++) if (!prefs.getString("button" + i, "").isEmpty()) wanted.add(2118L + i);
        try {
            if (!current.registry.sync(wanted)) scheduleSync(current);
        } catch (Exception error) {
            Log.e(TAG, "sync; retaining registration ledger", error);
            if (!current.common.isBinderAlive()) main.post(() -> disconnect(current));
            else scheduleSync(current);
        }
    }
    void scheduleSync(Connection current) {
        // At most one delayed sync per generation.
        worker.removeCallbacks(current.resync);
        worker.postDelayed(current.resync, RETRY_MS);
    }
    void disconnect(Connection current) {
        if (active != current || !current.live) return;
        current.live = false;
        main.removeCallbacks(current.timeout);
        worker.removeCallbacks(current.resync);
        if (current.bound) {
            try { unbindService(current); } catch (Exception error) { Log.w(TAG, "unbind", error); }
            current.bound = false;
        }
        worker.post(() -> cleanup(current));
    }
    void cleanup(Connection current) {
        // A synchronous transact cannot be cancelled. Wait for this single worker
        // rather than creating overlapping listeners or blocking the UI.
        try {
            if (current.registry != null) {
                if (current.common.isBinderAlive()) current.registry.release();
                else current.registry.serverDied();
            }
        } catch (Exception error) {
            Log.w(TAG, "release pending; reconnect postponed", error);
            worker.postDelayed(() -> cleanup(current), RETRY_MS);
            return;
        }
        if (current.common != null) {
            try { current.common.unlinkToDeath(current.death, 0); } catch (Exception ignored) {}
        }
        main.post(() -> {
            if (active == current) active = null;
            if (!closing) main.postDelayed(retry, RETRY_MS);
        });
        if (closing) thread.quitSafely();
    }
    void dispatch(long key) {
        int index = (int)(key - 2118); if (index < 0 || index > 3) return;
        long now = SystemClock.elapsedRealtime();
        if (lastKey == key && now - lastTime < 400) return;
        lastKey = key; lastTime = now;
        String action = prefs.getString("button" + index, "");
        Log.i(TAG, "key=" + key + " action=" + action);
        try {
            if (action.startsWith("media:")) {
                int code = action.equals("media:play_pause") ? android.view.KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE
                    : action.equals("media:next") ? android.view.KeyEvent.KEYCODE_MEDIA_NEXT
                    : action.equals("media:previous") ? android.view.KeyEvent.KEYCODE_MEDIA_PREVIOUS : 0;
                if (code == 0) return;
                android.media.AudioManager audio = getSystemService(android.media.AudioManager.class);
                audio.dispatchMediaKeyEvent(new android.view.KeyEvent(now, now, android.view.KeyEvent.ACTION_DOWN, code, 0));
                audio.dispatchMediaKeyEvent(new android.view.KeyEvent(now, now, android.view.KeyEvent.ACTION_UP, code, 0));
            } else if (action.startsWith("app:")) {
                String pkg = action.substring(4);
                Intent launch = getPackageManager().getLeanbackLaunchIntentForPackage(pkg);
                if (launch == null) launch = getPackageManager().getLaunchIntentForPackage(pkg);
                if (launch != null) startActivity(launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            }
        } catch (Exception error) { Log.e(TAG, "dispatch", error); }
    }
    public void onDestroy() {
        closing = true; main.removeCallbacksAndMessages(null);
        if (active != null && active.live) disconnect(active);
        else if (active == null) thread.quitSafely();
        super.onDestroy();
    }
    public IBinder onBind(Intent intent) { return null; }
}
