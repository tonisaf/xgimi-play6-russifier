package com.beam.remote;
import android.accessibilityservice.*;import android.content.Intent;import android.view.accessibility.AccessibilityEvent;
/** Keeps the OEM key service bound; does not read UI or filter accessibility key events. */
public final class KeyBridge extends AccessibilityService {
 protected void onServiceConnected(){AccessibilityServiceInfo info=getServiceInfo();info.eventTypes=0;info.flags=0;setServiceInfo(info);startForegroundService(new Intent(this,KeyService.class));}
 public void onAccessibilityEvent(AccessibilityEvent e){}public void onInterrupt(){}
}
