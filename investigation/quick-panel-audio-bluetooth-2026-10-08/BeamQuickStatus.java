package com.xgimi.misckey.cell;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.Context;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import java.lang.reflect.*;
import java.lang.ref.WeakReference;
import java.util.*;

/** Display-only additions. No pairing, audio switching or persistent DB writes. */
public final class BeamQuickStatus {
    private static final String TAG = "BeamQuickStatus";
    private static final String ENTITY = "com.xgimi.support.database.data.entity.";
    private static final String CELL = "com.xgimi.view.cell.";
    private static final Map<Object, Status> items = new WeakHashMap<>();
    private static final Handler handler = new Handler(Looper.getMainLooper());
    private static boolean scheduled;
    private static boolean reported;
    private static final class Status {
        WeakReference<Object> cell, text;
        String value = "";
        boolean attached;
    }
    private static final Runnable tick = new Runnable() {
        public void run() {
            scheduled = false;
            boolean active = false;
            for (Object item : new ArrayList<>(items.keySet())) {
                Status status = items.get(item);
                if (status != null && status.attached) {
                    active = true;
                    refresh(item);
                }
            }
            if (active) schedule();
        }
    };
    private static void schedule() {
        if (!scheduled) { scheduled = true; handler.postDelayed(tick, 1000); }
    }
    private static void error(Throwable e) {
        if (!reported) { reported = true; Log.e(TAG, "Quick status unavailable", e); }
    }
    private static Object call(Object object, String method, Class<?>[] types, Object... args) throws Exception {
        return object.getClass().getMethod(method, types).invoke(object, args);
    }
    private static Object call(Object object, String method) throws Exception {
        return call(object, method, new Class<?>[0]);
    }
    private static Object field(Object object, String name) throws Exception {
        Field f = object.getClass().getDeclaredField(name);
        f.setAccessible(true);
        return f.get(object);
    }
    private static Context context() throws Exception {
        Object companion = Class.forName("com.xgimi.common.BaseApp").getField("Companion").get(null);
        return (Context) call(companion, "getInstance");
    }

    /** Insert a synthetic native function after Atmosphere, retaining all original rows. */
    public static List<?> augment(List<?> original) {
        if (original == null) return null;
        try {
            int wall = -1;
            for (int index = 0; index < original.size(); index++) {
                Object func = original.get(index);
                String icon = (String) call(func, "getIcon");
                if ("sound_output".equals(icon)) return original;
                if ("xgimi_wall".equals(icon)) wall = index;
            }
            if (wall < 0 || original.size() >= 4) return original;
            Class<?> intentClass = Class.forName(ENTITY + "IntentX");
            Object intent = intentClass.getConstructor(int.class, String.class, String.class).newInstance(
                4, "#Intent;action=Settings://com.xgimi.settings.sound/soundOutput;S.funType=sound_output;end", "sound_output");
            Object sound = Class.forName(ENTITY + "MisckeyConfigFunc").getConstructor(
                int.class, String.class, intentClass, int.class, int.class, int.class, String.class, int.class
            ).newInstance(900001, "Звук", intent, 0, 1, 1, "sound_output", 1);
            List<Object> result = new ArrayList<Object>(original);
            result.add(wall + 1, sound);
            return result;
        } catch (Throwable e) { error(e); return original; }
    }

    public static void attach(Object item) {
        refresh(item);
        Status status = items.get(item);
        if (status != null) { status.attached = true; schedule(); }
    }
    public static void detach(Object item) {
        Status status = items.get(item);
        if (status != null) status.attached = false;
        boolean active = false;
        for (Status value : items.values()) active |= value.attached;
        if (!active) { handler.removeCallbacks(tick); scheduled = false; }
    }

    /** Called after native data binding and while attached; leaves other tiles untouched. */
    public static void refresh(Object item) {
        try {
            Object func = call(item, "getCurrentFunc");
            if (func == null) return;
            String icon = (String) call(func, "getIcon");
            boolean bluetooth = "bluetooth".equals(icon) || "bluetooth.json".equals(icon);
            if (!bluetooth && !"sound_output".equals(icon) && !"sound_output.json".equals(icon)) return;
            Status status = items.get(item);
            Object cell = status == null ? null : status.cell.get();
            Object text = status == null ? null : status.text.get();
            if (cell == null || text == null) {
                status = new Status();
                Class<?> cellClass = Class.forName(CELL + "Cell");
                Class<?> textClass = Class.forName(CELL + "component.TextComponent");
                cell = cellClass.getConstructor().newInstance();
                text = textClass.getConstructor().newInstance();
                status.cell = new WeakReference<>(cell);
                status.text = new WeakReference<>(text);
                call(text, "setTextSize", new Class<?>[]{float.class}, 20f);
                call(text, "setGravity", new Class<?>[]{int.class}, 3 | 16);
                call(text, "setEllipsis", new Class<?>[]{boolean.class}, true);
                call(cell, "setMask", new Class<?>[]{boolean.class}, true);
                call(cell, "addComponent", new Class<?>[]{Class.forName(CELL + "Component")}, text);
                Object params = Class.forName(CELL + "layout.FrameLayout$Params").getConstructor(
                    int.class, int.class, int.class).newInstance(208, 28, 3);
                call(params, "setMargin", new Class<?>[]{int.class,int.class,int.class,int.class}, 24, 78, 0, 0);
                call(item, "addCell", new Class<?>[]{cellClass, Class.forName(CELL + "Layout$Params")}, cell, params);
                items.put(item, status);
            }
            int state = (Integer) field(item, "currentState");
            boolean expanded = state == 1;
            call(cell, "setVisibility", new Class<?>[]{byte.class}, (byte)(expanded ? 0 : 8));
            if (!expanded) return;
            // Keep native icon/title arrangement, raising it to make room for one status line.
            Object heading = field(item, "iconAndTitleCell");
            Object params = call(heading, "getLayoutParams");
            call(params, "setMarginTop", new Class<?>[]{int.class}, 20);
            call(heading, "setLayoutParams", new Class<?>[]{Class.forName(CELL + "Layout$Params")}, params);
            boolean focused = (Boolean) call(item, "isFocused");
            call(text, "setColor", new Class<?>[]{int.class}, focused ? 0xff444444 : 0xffd2d2d2);
            call(text, "setMarquee", new Class<?>[]{boolean.class}, focused);
            String value = bluetooth ? bluetoothNames() : audioOutput();
            if (!value.equals(status.value)) {
                status.value = value;
                call(text, "setText", new Class<?>[]{String.class}, value);
                Log.i(TAG, (bluetooth ? "Bluetooth: " : "Sound output: ") + value);
            }
        } catch (Throwable e) { error(e); }
    }

    private static String bluetoothNames() {
        try {
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null || !adapter.isEnabled()) return "Выключен";
            Set<String> names = new TreeSet<String>();
            for (BluetoothDevice device : adapter.getBondedDevices()) {
                if (Boolean.TRUE.equals(call(device, "isConnected"))) {
                    String name = device.getName();
                    names.add(name == null || name.trim().isEmpty() ? "Устройство Bluetooth" : name);
                }
            }
            return names.isEmpty() ? "Нет подключений" : join(names);
        } catch (Throwable e) { error(e); return "Статус недоступен"; }
    }
    private static String join(Collection<String> names) {
        StringBuilder result = new StringBuilder();
        for (String name : names) { if (result.length() > 0) result.append(" · "); result.append(name); }
        return result.toString();
    }
    private static String bluetoothAudioName() {
        try {
            AudioManager audio = (AudioManager) context().getSystemService(Context.AUDIO_SERVICE);
            Set<String> names = new TreeSet<String>();
            for (AudioDeviceInfo device : audio.getDevices(AudioManager.GET_DEVICES_OUTPUTS)) {
                if (device.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP || device.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_SCO)
                    names.add(device.getProductName().toString());
            }
            return names.isEmpty() ? "Bluetooth" : join(names);
        } catch (Throwable e) { error(e); return "Bluetooth"; }
    }
    private static String audioOutput() {
        try {
            // Android's effective media route takes precedence over amplifier-only vendor state.
            int route = (Integer) Class.forName("android.media.AudioSystem").getMethod(
                "getDevicesForStream", int.class).invoke(null, AudioManager.STREAM_MUSIC);
            if ((route & 0x380) != 0) return bluetoothAudioName();
            if ((route & 0x8) != 0 || (route & 0x4) != 0) return "Наушники";
            if ((route & 0x40000) != 0) return "HDMI ARC";
            if ((route & 0x80000) != 0) return "S/PDIF";
            Number output = (Number) Class.forName("com.xgimi.device.GmAudioManager").getMethod("getAudioOutput").invoke(null);
            if (output == null) return "Статус недоступен";
            switch (output.intValue()) {
                case 0: return "Динамики проектора";
                case 1: return "S/PDIF";
                case 2: return "HDMI ARC";
                case 3: return bluetoothAudioName();
                default: return "Аудиовыход " + output.intValue();
            }
        } catch (Throwable e) { error(e); return "Статус недоступен"; }
    }
}
