package com.beam.remote;
import android.app.*;import android.content.*;import android.content.pm.*;import android.graphics.*;import android.graphics.drawable.GradientDrawable;import android.os.*;import android.view.*;import android.widget.*;import org.json.*;import java.io.*;import java.util.*;
/** Independent assignments UI; OEM interception belongs to KeyService. */
public final class RemoteActivity extends Activity {
 static final String[] NAMES={"Youku / CIBN","Tencent TV","iQIYI","Mango TV"};
 static final String[] STOCK={"com.cibn.tv","com.ktcp.tvvideo","com.gitvjimi.video","com.hunantv.license"};
 TextView status;AssignmentRow[] buttons=new AssignmentRow[4];RemoteDrawing remote;SharedPreferences prefs;boolean bound;Handler h=new Handler(Looper.getMainLooper());
 Runnable timeout=()->{report("timeout","Нет ответа от сервиса за 8 секунд");unbind();};
 ServiceConnection connection=new ServiceConnection(){
 public void onServiceConnected(ComponentName n,IBinder b){h.removeCallbacks(timeout);new Thread(()->{
 String code,text;Parcel d=Parcel.obtain(),r=Parcel.obtain();try{
 if(!"com.xgimi.aidl.IXgimiService".equals(b.getInterfaceDescriptor()))throw new IOException("Неизвестный интерфейс");
 d.writeInterfaceToken("com.xgimi.aidl.IXgimiService");if(!b.transact(1,d,r,0))throw new IOException("getGimiCommon недоступен");r.readException();IBinder common=r.readStrongBinder();
 if(common==null||!"com.xgimi.aidl.IGimiCommon".equals(common.getInterfaceDescriptor()))throw new IOException("Неизвестный GimiCommon");
 code="connected";text="API XGIMI доступен. Перехват ещё не проверен.";
 if(getIntent().getBooleanExtra("registerProbe",false)){
 boolean accepted=false;Parcel kd=Parcel.obtain(),kr=Parcel.obtain();
 try{kd.writeInterfaceToken("com.xgimi.aidl.IGimiCommon");kd.writeLong(2119L);
 kd.writeStrongBinder(new Binder(){protected boolean onTransact(int c,Parcel data,Parcel reply,int flags)throws RemoteException{
 if(c==INTERFACE_TRANSACTION){if(reply!=null)reply.writeString("com.xgimi.aidl.IGimiInterceptKeyListener");return true;}
 if(c==1){data.enforceInterface("com.xgimi.aidl.IGimiInterceptKeyListener");long key=data.readLong();android.util.Log.i("BeamRemoteProbe","temporary key="+key);if(reply!=null)reply.writeNoException();return true;}
 return super.onTransact(c,data,reply,flags);}});
 if(!common.transact(3,kd,kr,0))throw new IOException("registerInterceptKey недоступен");kr.readException();accepted=kr.readInt()!=0;
 }finally{kd.recycle();kr.recycle();if(accepted){Parcel ud=Parcel.obtain(),ur=Parcel.obtain();try{ud.writeInterfaceToken("com.xgimi.aidl.IGimiCommon");ud.writeLong(2119L);if(!common.transact(4,ud,ur,0))throw new IOException("Не удалось снять перехват");ur.readException();}finally{ud.recycle();ur.recycle();}}}
 code=accepted?"registration-ok":"registration-denied";text=accepted?"Перехват кнопки разрешён. Тестовая регистрация снята.":"API не разрешил перехват кнопки.";
 }
 }catch(Exception e){code="error";text=e.getClass().getSimpleName()+": "+e.getMessage();}finally{r.recycle();d.recycle();}
 final String c=code,t=text;h.post(()->{if(!isFinishing()){report(c,t);unbind();}});
 },"RemoteProbe").start();}
 public void onServiceDisconnected(ComponentName n){report("disconnected","Сервис отключился");}
 public void onNullBinding(ComponentName n){h.removeCallbacks(timeout);report("null","Пустое подключение");unbind();}
 };
 public void onCreate(Bundle saved){super.onCreate(saved);for(String k:new String[]{"VIDEO0","VIDEO1","VIDEO2","VIDEO3"})android.util.Log.i("BeamRemoteProbe",k+"="+KeyEvent.keyCodeFromString("KEYCODE_"+k));prefs=getSharedPreferences("buttons",MODE_PRIVATE);
 LinearLayout root=new LinearLayout(this);root.setOrientation(0);root.setPadding(dp(98),dp(42),dp(94),dp(34));root.setBackgroundColor(Color.BLACK);
 LinearLayout left=new LinearLayout(this);left.setOrientation(1);left.setPadding(0,dp(64),dp(40),0);root.addView(left,new LinearLayout.LayoutParams(0,-1,1));
 text(left,"Кнопки пульта",32,0xffeeeeee);TextView sub=text(left,"Выберите кнопку и назначьте приложение",19,0xff929292);sub.setPadding(0,dp(16),0,dp(22));
 remote=new RemoteDrawing(this);left.addView(remote,new LinearLayout.LayoutParams(dp(150),0,1));
 LinearLayout right=new LinearLayout(this);right.setOrientation(1);root.addView(right,new LinearLayout.LayoutParams(dp(410),-1));
 TextView header=text(right,"Назначение кнопок",17,0xff929292);header.setPadding(dp(18),0,0,dp(14));
 for(int i=0;i<4;i++){final int index=i;AssignmentRow row=new AssignmentRow(this,i);buttons[i]=row;
 row.setId(500+i);row.setNextFocusUpId(500+Math.max(0,i-1));row.setNextFocusDownId(500+Math.min(3,i+1));
 row.setOnFocusChangeListener((v,f)->{row.focus(f);if(f){remote.selected=index;remote.invalidate();}});row.setOnClickListener(v->choose(index));
 LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,dp(78));rp.setMargins(0,0,0,dp(14));right.addView(row,rp);}
 refresh();TextView note=text(right,"Выбранное действие сохраняется автоматически",15,0xff929292);note.setPadding(dp(18),dp(12),dp(18),0);
 status=new TextView(this);status.setTextSize(14);status.setTextColor(0xff929292);status.setPadding(dp(18),dp(12),0,0);status.setVisibility(getIntent().getBooleanExtra("probe",false)?View.VISIBLE:View.GONE);right.addView(status);
 setContentView(root);buttons[0].requestFocus();if(getIntent().getBooleanExtra("probe",false))h.post(this::probe);
 }
 final class AssignmentRow extends LinearLayout{
 TextView name,value,arrow;Icon icon;
 AssignmentRow(Context c,int i){super(c);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(16),0,dp(18),0);setFocusable(true);setClickable(true);setBackground(bg(false));
 icon=new Icon(c,i);addView(icon,new LinearLayout.LayoutParams(dp(30),dp(30)));
 name=new TextView(c);name.setTextSize(18);name.setSingleLine(true);name.setEllipsize(android.text.TextUtils.TruncateAt.END);name.setPadding(dp(12),0,dp(8),0);addView(name,new LinearLayout.LayoutParams(0,-2,1));
 value=new TextView(c);value.setTextSize(16);value.setSingleLine(true);value.setEllipsize(android.text.TextUtils.TruncateAt.END);value.setMaxWidth(dp(150));value.setGravity(Gravity.RIGHT);addView(value,new LinearLayout.LayoutParams(dp(150),-2));
 arrow=new TextView(c);arrow.setText("›");arrow.setTextSize(28);arrow.setPadding(dp(12),0,0,0);addView(arrow);focus(false);}
 void setText(String s){String[] parts=s.split("\\n",2);name.setText(parts[0]);value.setText(parts.length>1?parts[1]:"");}
 void focus(boolean f){setBackground(bg(f));name.setTextColor(f?0xff191919:0xffdddddd);value.setTextColor(f?0xff656565:0xff999999);arrow.setTextColor(0xff858585);icon.color=f?0xff555555:0xffbfc2c8;icon.invalidate();}
 }

 TextView text(LinearLayout root,String s,int size,int color){TextView v=new TextView(this);v.setText(s);v.setTextSize(size);v.setTextColor(color);root.addView(v);return v;}
 int dp(float v){return Math.round(v*getResources().getDisplayMetrics().density);}
 GradientDrawable bg(boolean f){GradientDrawable d=new GradientDrawable();d.setColor(f?Color.WHITE:0xff242424);d.setCornerRadius(dp(18));return d;}
 void refresh(){for(int i=0;i<4;i++){String value=prefs.getString("button"+i,"");String label="Как в прошивке";if(value.equals("none"))label="Не выполнять действие";else if(value.equals("media:play_pause"))label="Плей / пауза";else if(value.equals("media:next"))label="Следующий трек";else if(value.equals("media:previous"))label="Предыдущий трек";else if(value.startsWith("app:")){try{label=getPackageManager().getApplicationLabel(getPackageManager().getApplicationInfo(value.substring(4),0)).toString();}catch(Exception e){label="Приложение удалено";}}buttons[i].setText(NAMES[i]+"\n"+label);}}
 void choose(int i){showChoices(i,NAMES[i],new String[]{"Запустить приложение", "Воспроизведение / пауза", "Следующий трек", "Предыдущий трек", "Как в прошивке", "Не выполнять действие"},new String[]{"picker","media:play_pause","media:next","media:previous","","none"});}
 void applications(int i){List<ResolveInfo> all=getPackageManager().queryIntentActivities(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LEANBACK_LAUNCHER),0);all.addAll(getPackageManager().queryIntentActivities(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER),0));Map<String,String> unique=new HashMap<>();for(ResolveInfo a:all){String p=a.activityInfo.packageName;if(!p.equals(getPackageName())&&!Arrays.asList(STOCK).contains(p))unique.put(p,a.loadLabel(getPackageManager()).toString());}List<Map.Entry<String,String>> sorted=new ArrayList<>(unique.entrySet());Collections.sort(sorted,(a,b)->a.getValue().compareToIgnoreCase(b.getValue()));List<String> names=new ArrayList<>(),values=new ArrayList<>();for(Map.Entry<String,String> e:sorted){names.add(e.getValue());values.add("app:"+e.getKey());}showChoices(i,"Выберите приложение",names.toArray(new String[0]),values.toArray(new String[0]));}
 void showChoices(int index,String title,String[] names,String[] values){
 Dialog dialog=new Dialog(this);LinearLayout panel=new LinearLayout(this);panel.setOrientation(1);panel.setPadding(dp(24),dp(24),dp(24),dp(24));GradientDrawable background=new GradientDrawable();background.setColor(0xff111111);background.setCornerRadius(dp(24));panel.setBackground(background);
 TextView heading=text(panel,title,24,0xffeeeeee);heading.setPadding(dp(12),0,0,dp(20));ScrollView scroll=new ScrollView(this);scroll.setFillViewport(false);LinearLayout list=new LinearLayout(this);list.setOrientation(1);scroll.addView(list);panel.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
 String current=prefs.getString("button"+index,"");TextView selected=null;
 for(int n=0;n<names.length;n++){final String value=values[n];TextView row=new TextView(this);row.setText((value.equals(current)?"✓  ":"")+names[n]);row.setTextSize(19);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(20),0,dp(20),0);row.setSingleLine(true);row.setEllipsize(android.text.TextUtils.TruncateAt.END);row.setFocusable(true);row.setClickable(true);row.setTextColor(0xffdddddd);row.setBackground(bg(false));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(58));lp.bottomMargin=dp(8);list.addView(row,lp);row.setOnFocusChangeListener((v,f)->{row.setBackground(bg(f));row.setTextColor(f?0xff191919:0xffdddddd);});row.setOnClickListener(v->{dialog.dismiss();if(value.equals("picker")){applications(index);return;}prefs.edit().putString("button"+index,value).commit();startForegroundService(new Intent(this,KeyService.class));refresh();});if(value.equals(current)||(value.equals("picker")&&current.startsWith("app:")))selected=row;}
 TextView help=text(panel,"Назад — отмена",15,0xff929292);help.setPadding(dp(12),dp(14),0,0);dialog.setContentView(panel);Window window=dialog.getWindow();window.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT));dialog.show();window.setLayout(dp(560),dp(580));if(selected!=null)selected.requestFocus();else if(list.getChildCount()>0)list.getChildAt(0).requestFocus();
 }
 void probe(){if(bound)return;status.setText("Подключаюсь к XGIMI…");try{bound=bindService(new Intent().setComponent(new ComponentName("com.xgimi.xgimiservice","com.xgimi.xgimiservice.services.XgimiServices")),connection,BIND_AUTO_CREATE);if(!bound){report("unavailable","Подключение к сервису недоступно");return;}h.postDelayed(timeout,8000);}catch(Exception e){report("error",e.getClass().getSimpleName()+": "+e.getMessage());}}
 void report(String code,String message){status.setText(message);android.util.Log.i("BeamRemoteProbe",code+": "+message);try{JSONObject o=new JSONObject();o.put("status",code);o.put("message",message);o.put("fingerprint",Build.FINGERPRINT);o.put("keyRegistrationAttempted",getIntent().getBooleanExtra("registerProbe",false));try(FileOutputStream f=openFileOutput("probe.json",MODE_PRIVATE)){f.write(o.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));}}catch(Exception e){android.util.Log.e("BeamRemoteProbe","Cannot save result",e);}}
 void unbind(){if(bound){try{unbindService(connection);}catch(Exception ignored){}bound=false;}}
 public void onDestroy(){h.removeCallbacks(timeout);unbind();super.onDestroy();}
 /** Schematic vector marks, drawn independently from the remote photograph. */
 static final class Icon extends View{int type;int color=0xffd6dce7;Paint paint=new Paint(3);Icon(Context c,int t){super(c);type=t;}protected void onDraw(Canvas c){c.save();c.scale(getWidth()/64f,getHeight()/64f);paint.setColor(color);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(4);paint.setStrokeJoin(Paint.Join.ROUND);Path p=new Path();if(type==0){p.moveTo(13,15);p.lineTo(29,39);p.lineTo(44,15);c.drawPath(p,paint);paint.setStyle(Paint.Style.FILL);c.drawCircle(42,13,4,paint);}else if(type==1){for(int n=0;n<2;n++){p.reset();p.moveTo(17+n*5,12+n*5);p.lineTo(49+n*3,30+n*2);p.lineTo(17+n*5,50-n*2);p.close();c.drawPath(p,paint);}}else if(type==2){c.drawRoundRect(8,9,48,49,10,10,paint);c.drawCircle(28,29,11,paint);p.moveTo(26,24);p.lineTo(33,29);p.lineTo(26,34);p.close();c.drawPath(p,paint);c.drawLine(47,25,56,20,paint);c.drawLine(47,32,57,38,paint);}else{c.drawRoundRect(9,10,54,52,12,12,paint);p.moveTo(19,40);p.lineTo(19,23);p.lineTo(30,33);p.lineTo(44,20);p.lineTo(44,42);c.drawPath(p,paint);}c.restore();}}
}


