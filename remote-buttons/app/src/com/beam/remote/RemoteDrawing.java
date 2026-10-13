package com.beam.remote;
import android.content.Context;
import android.graphics.*;
import android.view.View;
/** Scalable drawing based on the supplied Play6 remote photograph. */
public final class RemoteDrawing extends View {
 int selected=0;private final Paint p=new Paint(3);
 public RemoteDrawing(Context c){super(c);setContentDescription("Пульт XGIMI: выбранная кнопка подсвечивается синим");}
 private void fill(int color){p.setShader(null);p.setStyle(Paint.Style.FILL);p.setColor(color);}
 private void stroke(int color,float w){p.setShader(null);p.setStyle(Paint.Style.STROKE);p.setColor(color);p.setStrokeWidth(w);p.setStrokeCap(Paint.Cap.ROUND);p.setStrokeJoin(Paint.Join.ROUND);}
 private void circle(Canvas c,float x,float y,float r){fill(0xffe7e5e1);c.drawCircle(x,y,r,p);stroke(0xffbab9b7,1);c.drawCircle(x,y,r,p);}
 private void line(Canvas c,float x,float y,float xx,float yy){c.drawLine(x,y,xx,yy,p);}
 protected void onDraw(Canvas c){super.onDraw(c);float scale=Math.min(getWidth()/220f,getHeight()/780f);c.save();c.translate((getWidth()-220*scale)/2,0);c.scale(scale,scale);
 fill(0xff141414);c.drawRoundRect(15,5,211,777,25,25,p);
 p.setShader(new LinearGradient(22,0,202,0,new int[]{0xffbdbbb6,0xffeceae5,0xffdedcd7,0xffaaa9a5},null,Shader.TileMode.CLAMP));c.drawRoundRect(20,0,200,770,24,24,p);p.setShader(null);
 circle(c,58,48,24);fill(0xffab3042);c.drawCircle(58,48,4.4f,p);circle(c,162,48,24);
 stroke(0xff747472,2.4f);c.drawRoundRect(158,37,166,52,4,4,p);c.drawArc(153,40,171,58,0,180,false,p);line(c,162,58,162,64);
 fill(0xff777672);c.drawCircle(110,48,1.7f,p);
 for(int i=0;i<4;i++){int col=i%2,row=i/2;float x=30+col*80,y=91+row*45;
 if(i==selected){fill(0xff344a7c);c.drawRoundRect(x-3,y-3,x+82,y+32,14,14,p);}
 fill(i==selected?0xff4776e7:0xffe4e1dc);c.drawRoundRect(x,y,x+79,y+29,11,11,p);stroke(i==selected?0xff81a6ff:0xffb1b0ac,1);c.drawRoundRect(x,y,x+79,y+29,11,11,p);
 fill(i==selected?Color.WHITE:0xff777672);p.setTextSize(9);p.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));String name=new String[]{"Youku","Tencent","iQIYI","Mango"}[i];c.drawText(name,x+25,y+18,p);
 stroke(i==selected?Color.WHITE:0xff777672,1.7f);Path mark=new Path();if(i==0){mark.moveTo(x+8,y+9);mark.lineTo(x+14,y+19);mark.lineTo(x+20,y+9);c.drawPath(mark,p);}else if(i==1){mark.moveTo(x+8,y+8);mark.lineTo(x+20,y+14);mark.lineTo(x+8,y+21);mark.close();c.drawPath(mark,p);line(c,x+11,y+11,x+17,y+14);}else if(i==2){c.drawRoundRect(x+6,y+8,x+20,y+22,3,3,p);c.drawCircle(x+13,y+15,4,p);}else{c.drawRoundRect(x+5,y+8,x+21,y+22,4,4,p);mark.moveTo(x+8,y+19);mark.lineTo(x+8,y+11);mark.lineTo(x+13,y+16);mark.lineTo(x+18,y+11);mark.lineTo(x+18,y+19);c.drawPath(mark,p);}}
 for(float x:new float[]{54,110,166})circle(c,x,204,23);
 fill(0xff858481);for(int n=0;n<6;n++){c.save();c.rotate(n*60,54,204);c.drawOval(51,190,57,200,p);c.restore();}
 stroke(0xff858481,2);for(int a=0;a<4;a++){c.save();c.rotate(a*90,110,204);line(c,99,200,99,193);line(c,99,193,106,193);c.restore();}line(c,106,204,114,204);line(c,110,200,110,208);
 fill(0xff858481);for(int n=0;n<3;n++){c.save();c.rotate(45,166,204);c.drawRect(157+(n%2)*10,195+(n/2)*10,164+(n%2)*10,202+(n/2)*10,p);c.restore();}
 fill(0xff242527);c.drawCircle(110,332,83,p);stroke(0xff393a3d,1);for(int r=38;r<83;r+=3)c.drawCircle(110,332,r,p);
 p.setStyle(Paint.Style.FILL);p.setShader(new LinearGradient(70,300,154,370,0xff414246,0xff17181a,Shader.TileMode.CLAMP));c.drawCircle(110,332,36,p);p.setShader(null);stroke(0xff101112,2);c.drawCircle(110,332,36,p);
 for(float x:new float[]{54,110,166})circle(c,x,454,23);
 stroke(0xff858481,2.4f);Path back=new Path();back.moveTo(56,447);back.lineTo(48,454);back.lineTo(60,454);back.cubicTo(70,454,70,465,56,465);c.drawPath(back,p);
 c.save();c.translate(110,454);Path gear=new Path();for(int a=0;a<16;a++){float rad=a%2==0?11:8;double angle=a*Math.PI/8;float x=(float)Math.cos(angle)*rad,y=(float)Math.sin(angle)*rad;if(a==0)gear.moveTo(x,y);else gear.lineTo(x,y);}gear.close();c.drawPath(gear,p);c.drawCircle(0,0,3,p);c.restore();
 Path home=new Path();home.moveTo(156,453);home.lineTo(166,445);home.lineTo(177,453);home.moveTo(159,452);home.lineTo(159,463);home.lineTo(174,463);home.lineTo(174,452);c.drawPath(home,p);
 c.save();c.rotate(33,110,535);fill(0xff202123);c.drawRoundRect(94,494,126,576,16,16,p);stroke(0xff444548,1);c.drawRoundRect(96,496,124,574,14,14,p);stroke(0xff707175,2);line(c,104,511,116,511);line(c,110,505,110,517);line(c,104,559,116,559);c.restore();
 fill(0xffa1a09d);p.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));p.setTextSize(14);p.setTextAlign(Paint.Align.CENTER);c.drawText("XGIMI",110,722,p);p.setTextAlign(Paint.Align.LEFT);c.restore();
 }
}
