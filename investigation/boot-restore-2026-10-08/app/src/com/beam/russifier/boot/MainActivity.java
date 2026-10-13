package com.beam.russifier.boot;
import android.app.Activity;
import android.os.Bundle;
import android.widget.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private TextView result;
    private final android.os.Handler handler = new android.os.Handler(android.os.Looper.getMainLooper());
    private final Runnable update = new Runnable() {
        public void run() {
            String text=RestorePrefs.get(MainActivity.this).getString("last","Ещё не запускалось");
            result.setText("Последний результат: " + text);
            handler.postDelayed(this,1000);
        }
    };
    public void onCreate(Bundle state) {
        super.onCreate(state);
        RestorePrefs.migrate(this);
        LinearLayout layout=new LinearLayout(this);layout.setOrientation(1);layout.setPadding(64,48,64,48);
        TextView title=new TextView(this);title.setText("Русификатор XGIMI");title.setTextSize(32);layout.addView(title);
        TextView description=new TextView(this);description.setTextSize(22);
        description.setText("Восстановление перевода и изменений панелей после полного включения.\nXGIMI Play 6 · прошивка v1.7.116");layout.addView(description);
        CheckBox enabled=new CheckBox(this);enabled.setTextSize(24);enabled.setText("Восстанавливать автоматически после включения");
        enabled.setChecked(RestorePrefs.get(MainActivity.this).getBoolean("enabled",true));layout.addView(enabled);
        enabled.setOnCheckedChangeListener((button,value)->{ RestorePrefs.get(MainActivity.this).edit().putBoolean("enabled",value).apply(); BootJob.configure(this); });
        BootJob.configure(this);
        Button button=new Button(this);button.setText("Восстановить сейчас");layout.addView(button);
        button.setOnClickListener(v -> { result.setText("Восстановление…");startForegroundService(new android.content.Intent(this,RestoreService.class).putExtra("manual",true)); });
        result=new TextView(this);result.setTextSize(22);layout.addView(result);
        TextView note=new TextView(this);note.setTextSize(20);
        note.setText("Если отключить автоматическое восстановление, после следующей полной перезагрузки изменения APK нужно будет применить вручную. Для отключения автозапуска снимите флажок выше.");layout.addView(note);
        setContentView(layout);button.requestFocus();
    }
    public void onResume() { super.onResume();handler.post(update); }
    public void onPause() { handler.removeCallbacks(update);super.onPause(); }
    static String exec(String... args) throws Exception {
        Process process = new ProcessBuilder(args).redirectErrorStream(true).start();
        if (!process.waitFor(10,java.util.concurrent.TimeUnit.SECONDS)) { process.destroyForcibly();throw new IOException("Команда не завершилась за 10 секунд"); }
        ByteArrayOutputStream bytes = new ByteArrayOutputStream(); byte[] buffer = new byte[1024]; int read;
        while ((read = process.getInputStream().read(buffer)) >= 0) bytes.write(buffer,0,read);
        int exit = process.waitFor(); String text = new String(bytes.toByteArray(), StandardCharsets.UTF_8).trim();
        if (exit != 0) throw new IOException("exit="+exit+" "+text);
        return text;
    }
    static String read(String path) throws Exception {
        File file = new File(path); if (!file.exists()) return "";
        try (FileInputStream stream = new FileInputStream(file)) {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream(); byte[] buffer = new byte[1024]; int count;
            while ((count=stream.read(buffer))>=0) bytes.write(buffer,0,count);
            return new String(bytes.toByteArray(), StandardCharsets.UTF_8).trim();
        }
    }
}
