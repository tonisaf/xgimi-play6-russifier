"""Exercise Java ownership and the actual generated namespace checks offline."""
import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from installer import Installer,MANIFEST,SETTINGS,q

ROOT=Path(__file__).resolve().parents[1]
JDK=Path(os.environ.get('JAVA_HOME',r'C:\android\jdk'))/'bin'
ANDROID=Path(os.environ.get('ANDROID_HOME',r'C:\android\sdk'))/'platforms/android-34/android.jar'
BASH=Path(r'C:\Program Files\Git\bin\bash.exe')

class RuntimeTests(unittest.TestCase):
    def java(self,directory,sources,main,classpath=None):
        javac=JDK/'javac.exe';java=JDK/'java.exe'
        if not javac.exists(): self.skipTest('Java SDK is required')
        args=[str(javac),'-encoding','UTF-8','-d',str(directory)]
        if classpath: args+=['-cp',str(classpath)]
        subprocess.run(args+[str(p) for p in sources],check=True,capture_output=True)
        cp=str(directory)+(os.pathsep+str(classpath) if classpath else '')
        subprocess.run([str(java),'-cp',cp,main],check=True,capture_output=True)
    def test_restore_policy_handles_theme_and_same_boot_upgrade(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);probe=directory/'PolicyProbe.java'
            probe.write_text('''package com.beam.russifier.boot;
class PolicyProbe {
 static void check(int mode,boolean manual,String boot,String savedBoot,String hash,String savedHash,String skin) {
  if(RestorePolicy.decide(manual,boot,savedBoot,hash,savedHash,skin,"ru.apk")!=mode) throw new AssertionError("wrong restore mode");
 }
 public static void main(String[] args) {
  check(0,false,"boot","boot","new","new","ru.apk");
  check(1,false,"boot","boot","new","new","");
  check(1,false,"boot","boot","new","new","stock.apk");
  check(2,false,"boot","boot","new","old","ru.apk");
  check(2,false,"boot2","boot1","new","new","ru.apk");
  check(2,true,"boot","boot","new","new","ru.apk");
  check(2,false,"","","new","new","ru.apk");
  zygote(0,"boot","boot","100","100");
  zygote(2,"boot","boot","200","100");
  zygote(2,"boot","boot","100","");
  zygote(0,"boot","boot","","100");
 }
 static void zygote(int mode,String boot,String savedBoot,String zygote,String savedZygote) {
  if(RestorePolicy.decide(false,boot,savedBoot,"h","h","ru.apk","ru.apk",zygote,savedZygote)!=mode) throw new AssertionError("wrong zygote mode");
 }
}''',encoding='utf-8')
            source=ROOT/'investigation/bound-startup-2026-10-08/app/src/com/beam/russifier/boot/RestorePolicy.java'
            self.java(directory,[source,probe],'com.beam.russifier.boot.PolicyProbe')
    def test_quick_status_does_not_retain_parent_graph(self):
        if not ANDROID.exists(): self.skipTest('Android SDK is required')
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory)
            handler=directory/'Handler.java';looper=directory/'Looper.java';probe=directory/'OwnershipProbe.java'
            handler.write_text('package android.os; public class Handler { public Handler(Looper l){} public boolean postDelayed(Runnable r,long t){return true;} public void removeCallbacks(Runnable r){} }')
            looper.write_text('package android.os; public class Looper { public static Looper getMainLooper(){return new Looper();} }')
            probe.write_text('''package com.xgimi.misckey.cell;
import java.util.*;import java.lang.ref.*;import java.lang.reflect.*;
class OwnershipProbe {
 static Map<Object,Object> map;
 static class Node { Object parent,child,text; }
 static WeakReference<Object> create() throws Exception {
  Node item=new Node(),cell=new Node();Object text=new Object();item.child=cell;cell.parent=item;cell.text=text;
  Class<?> status=Class.forName("com.xgimi.misckey.cell.BeamQuickStatus$Status");
  Constructor<?> c=status.getDeclaredConstructor();c.setAccessible(true);Object value=c.newInstance();
  for(String name:new String[]{"cell","text"}) { Field f=status.getDeclaredField(name);f.setAccessible(true);f.set(value,new WeakReference<>(name.equals("cell")?cell:text)); }
  map.put(item,value);return new WeakReference<>(item);
 }
 public static void main(String[] args) throws Exception {
  Field f=BeamQuickStatus.class.getDeclaredField("items");f.setAccessible(true);map=(Map<Object,Object>)f.get(null);
  WeakReference<Object> ref=create();
  for(int i=0;i<50 && ref.get()!=null;i++){System.gc();Thread.sleep(30);}
  if(ref.get()!=null || map.size()!=0) throw new AssertionError("panel graph leaked");
 }
}''',encoding='utf-8')
            source=ROOT/'investigation/quick-panel-audio-bluetooth-2026-10-08/BeamQuickStatus.java'
            self.java(directory,[source,handler,looper,probe],'com.xgimi.misckey.cell.OwnershipProbe',ANDROID)
    def test_namespace_check_rejects_stale_systemui_process(self):
        if not BASH.exists(): self.skipTest('Git Bash is required for shell execution')
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);binary=directory/'bin';binary.mkdir()
            native=[{'target':SETTINGS,'file':'panel.apk'}]+MANIFEST['runtimePatches']
            pidof='#!/bin/sh\ncase "$1" in\nzygote) echo 1;;\n'+SETTINGS+') echo 100;;\ncom.xgimi.systemui) echo 900;;\n*) exit 1;;\nesac\n'
            nsenter='#!/bin/sh\ncase "$6" in\n'
            for item in native:
                path=MANIFEST['originals'][item['target']]['path'];digest=MANIFEST['files'][item['file']]
                nsenter+=q(path)+')\n'
                if item['target']=='com.xgimi.systemui':
                    nsenter+='if [ "$2" = 900 ] && [ "$STALE" = 1 ]; then echo '+MANIFEST['originals'][item['target']]['sha256']+'; else echo '+digest+'; fi;;\n'
                else: nsenter+='echo '+digest+';;\n'
            nsenter+='*) exit 2;;\nesac\n'
            for name,text in [('pidof',pidof),('nsenter',nsenter)]:
                path=binary/name;path.write_text(text,encoding='utf-8',newline='\n');path.chmod(0o755)
            installer=Installer.__new__(Installer);installer.logs=directory
            def root(script,tag):
                path=directory/'verify.sh';path.write_text('set -e\nPATH="./bin:$PATH"\n'+script,encoding='utf-8',newline='\n')
                result=subprocess.run([str(BASH),'verify.sh'],cwd=directory,env={**os.environ,'STALE':stale},capture_output=True,text=True)
                if result.returncode: raise RuntimeError('stale process rejected')
                return result.stdout
            installer.root=root
            stale='1'
            with self.assertRaisesRegex(RuntimeError,'stale process'): installer.verify_native_processes()
            stale='0';output=installer.verify_native_processes()
            self.assertIn('com.xgimi.systemui 900',output)
    def test_skin_script_restores_only_skin_and_rejects_corruption(self):
        if not BASH.exists(): self.skipTest('Git Bash is required')
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);binary=directory/'bin';binary.mkdir();generation=directory/'generation';generation.mkdir()
            shutil.copy2(ROOT/'russifier/payload/skin.apk',generation/'skin.apk')
            state=directory/'property';state.write_text('stock.apk')
            commands=directory/'am.log'
            fake_getprop='''#!/bin/sh
case "$1" in
ro.build.fingerprint) echo '''+q(MANIFEST['fingerprint'])+''';;
ro.build.version.sdk) echo 30;;
persist.sys.locale) echo ru-RU;;
persist.sys.xgimi.themeV2.url) cat property;;
*) echo '';;
esac
'''
            scripts={'getprop':fake_getprop,'setprop':'#!/bin/sh\nif [ "$1" = persist.sys.xgimi.themeV2.url ]; then printf "%s" "$2" > property; fi\n',
                     'getenforce':'#!/bin/sh\necho Permissive\n','am':'#!/bin/sh\necho "$*" >> am.log\n'}
            for name,text in scripts.items():
                path=binary/name;path.write_text(text,encoding='utf-8',newline='\n');path.chmod(0o755)
            source=(ROOT/'investigation/bound-startup-2026-10-08/skin.sh').read_text(encoding='utf-8')
            source='\n'.join('D='+q(generation.as_posix()) if line.startswith('D=') else 'RUN=test-run' if line.startswith('RUN=') else line for line in source.splitlines())+'\n'
            script=directory/'skin-test.sh';script.write_text('PATH="./bin:$PATH"\n'+source,encoding='utf-8',newline='\n')
            def run(): return subprocess.run([str(BASH),'skin-test.sh'],cwd=directory,capture_output=True)
            self.assertEqual(run().returncode,0)
            self.assertEqual(state.read_text(),(generation/'skin.apk').as_posix())
            self.assertEqual(commands.read_text().strip(),'force-stop com.android.newsettings')
            self.assertEqual(run().returncode,0);self.assertEqual(len(commands.read_text().splitlines()),1)
            state.write_text('stock-again.apk');(generation/'skin.apk').write_bytes(b'corrupted')
            self.assertNotEqual(run().returncode,0)
            self.assertEqual(state.read_text(),'stock-again.apk');self.assertEqual(len(commands.read_text().splitlines()),1)
