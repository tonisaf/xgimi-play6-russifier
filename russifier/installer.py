"""Offline ADB installer for the verified XGIMI Play 6 firmware only."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from transforms import translate_db, translate_catalog, catalog_names, restore_db
from catalog_metadata import apply_db,apply_catalog,restore_db_metadata,restore_catalog_metadata

BASE = Path(__file__).resolve().parent
MANIFEST = json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
SETTINGS = 'com.android.newsettings'
ATMOSPHERE = 'com.xgimi.atmosphere'
FILES = {'quick.db': '/data/user/0/com.android.newsettings/databases/misckey_config.db',
         'atmosphere.db': '/data/user/0/com.xgimi.atmosphere/databases/resource.db',
         'catalog.ser': '/data/user/0/com.xgimi.atmosphere/cache/ScreensaverUiDataBean.ser'}
SKIN = '/data/local/tmp/beam-skin-ru.apk'
PANEL = '/data/local/tmp/beam-russifier-panel-v6.apk'
ADB_PORT = '5038'  # Isolate this installer from SDK/IDE clients using port 5037.

def sha(path):
    h = hashlib.sha256()
    with open(path,'rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def q(value):
    return shlex.quote(str(value))

def save(path,value):
    path=Path(path)
    temporary=path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    try:
        temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
        os.replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)

def find_adb():
    """adb to use: XGIMI_ADB if set; on Windows the one bundled in the kit; elsewhere (Linux, macOS) the adb from PATH."""
    chosen = os.environ.get('XGIMI_ADB')
    if chosen:
        return chosen
    bundled = BASE/'tools/adb.exe'
    if os.name == 'nt' and bundled.is_file():
        return str(bundled)
    found = shutil.which('adb')
    if found:
        return found
    raise RuntimeError('Не найден adb. Установите Android platform-tools (команда adb должна запускаться из терминала) '
                       'или укажите путь в переменной окружения XGIMI_ADB.')

class Installer:
    def __init__(self,args):
        self.args = args
        self.serial = args.device
        if not re.fullmatch(r'[A-Za-z0-9_.:\[\]-]+',self.serial):
            raise RuntimeError('Недопустимый адрес устройства')
        self.adb = find_adb()
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
        self.logs = BASE/'runs'/stamp
        self.logs.mkdir(parents=True)
        self.remote = '/data/local/tmp/beam-ru-'+uuid.uuid4().hex[:10]
        self.mutated = False
        self.state = None

    # The local adb server can be unreachable for a moment under load ("daemon not running", "could not read ok from
    # ADB Server"). The client then never reached the server, so nothing was executed and a retry is safe.
    SERVER_DOWN = ('daemon not running','could not read ok from ADB Server','cannot connect to daemon','failed to start daemon')

    def command(self,*args,check=True,timeout=120):
        for attempt in range(6):
            proc = subprocess.run([self.adb,'-P',ADB_PORT,'-s',self.serial,*map(str,args)],capture_output=True,
                                  text=True,encoding='utf-8',errors='replace',timeout=timeout)
            if not (proc.returncode and any(m in proc.stderr for m in self.SERVER_DOWN)) or attempt == 5:
                break
            time.sleep(3)
            subprocess.run([self.adb,'-P',ADB_PORT,'start-server'],capture_output=True,timeout=30)
            if ':' in self.serial and args[:1] != ('connect',):
                subprocess.run([self.adb,'-P',ADB_PORT,'connect',self.serial],capture_output=True,timeout=30)
        # Store bounded outputs, not database contents or the user catalog.
        with (self.logs/'adb.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps({'args':list(map(str,args)),'exit':proc.returncode,
                'stdout':proc.stdout[-12000:],'stderr':proc.stderr[-3000:]},ensure_ascii=False)+'\n')
        if check and proc.returncode:
            raise RuntimeError('ADB: '+proc.stderr.strip()+' '+proc.stdout.strip())
        return proc

    def shell(self,script,check=True):
        return self.command('shell',script,check=check).stdout.strip()

    def root(self,script,tag):
        keys = ['vendor.xgimi.system.debug.cmd','vendor.xgimi.system.debugserver']
        # The channel is shared with the boot helper: right after an installation it runs its first restore (~10 s).
        # Wait for it to finish instead of failing; never write while it is busy.
        deadline = time.time()+90
        while True:
            before = {k:self.shell('getprop '+k) for k in keys}
            if not (before[keys[0]] or before[keys[1]] not in ('','0')): break
            if time.time() > deadline:
                raise RuntimeError('Диагностический сервис занят дольше 90 секунд; операция остановлена')
            time.sleep(2)
        token ='/data/local/tmp/beam-ru-cmd-'+uuid.uuid4().hex[:8]
        local = self.logs/(tag+'.sh')
        # logserver runs the script as root. Readback is possible without making app data public.
        local.write_text('#!/system/bin/sh\numask 022\n(\nset -e\n'+script+
            '\n) > '+token+'.log 2>&1\ncode=$?\nchmod 644 '+token+'.log\necho "$code" > '+token+'.done\n',encoding='utf-8',newline='\n')
        self.command('push',local,token+'.sh')
        restored = []
        try:
            self.shell('setprop '+keys[0]+' '+q('/system/bin/sh '+token+'.sh'))
            self.shell('setprop '+keys[1]+' 1')
            deadline = time.monotonic()+100
            while time.monotonic()<deadline:
                if self.command('shell','test -f '+token+'.done',check=False).returncode==0:
                    break
                time.sleep(.5)
            else:
                raise RuntimeError('Диагностическая команда не завершилась за 100 секунд')
            code = self.shell('cat '+token+'.done')
            output = self.shell('cat '+token+'.log')
            (self.logs/(tag+'.log')).write_text(output,encoding='utf-8')
            if code!='0':
                raise RuntimeError(tag+': '+output[-2500:])
            return output
        finally:
            for key in reversed(keys):
                ok=False
                for attempt in range(3):
                    try:
                        p = self.command('shell','setprop '+key+' '+q(before[key]),check=False)
                        value = self.command('shell','getprop '+key,check=False)
                        ok=p.returncode==0 and value.returncode==0 and value.stdout.strip()==before[key]
                    except Exception:
                        ok=False
                    if ok:break
                restored.append(ok)
            self.command('shell','rm -f '+token+'.sh '+token+'.log '+token+'.done',check=False)
            if not all(restored):
                raise RuntimeError('Не удалось восстановить диагностические свойства; см. журнал')

    def preflight(self,strict=True):
        # strict=False is the compatibility check on a fresh projector: Russian language and the quick-panel/Atmosphere
        # databases do not exist yet and are created by the installation itself.
        print('Проверка файлов, подключения и совместимости…',flush=True)
        for name,value in MANIFEST['files'].items():
            if sha(BASE/'payload'/name)!=value:
                raise RuntimeError('Файл установщика повреждён: '+name)
        if ':' in self.serial:
            self.command('connect',self.serial)
        if self.command('get-state').stdout.strip()!='device':
            raise RuntimeError('ADB не авторизован или устройство недоступно')
        props = {key:self.shell('getprop '+key) for key in ['ro.build.fingerprint','ro.product.name',
            'ro.product.device','ro.build.version.sdk','persist.sys.locale','ro.serialno']}
        expected = {'ro.build.fingerprint':MANIFEST['fingerprint'],'ro.product.name':MANIFEST['product'],
                    'ro.product.device':MANIFEST['device'],'ro.build.version.sdk':MANIFEST['sdk']}
        for key,value in expected.items():
            if props[key]!=value:
                raise RuntimeError('Неподдерживаемая модель/прошивка: '+key+'='+props[key])
        if not props['ro.serialno']:
            raise RuntimeError('Не удалось определить серийный номер для резервной копии')
        if strict and not props['persist.sys.locale'].lower().startswith('ru'):
            raise RuntimeError('Сначала выберите русский язык Android и перезапустите проектор')
        for info in MANIFEST['originals'].values():
            if self.shell('sha256sum '+q(info['path'])).split()[0]!=info['sha256']:
                raise RuntimeError('Системный APK отличается от проверенного: '+info['path'])
        script = 'test "$(id -u)" = 0\ncommand -v idmap2\ncommand -v nsenter\n'
        script += 'zyg=$(pidof zygote)\ntest -n "$zyg"\n'
        script += 'nsenter -t "$zyg" -m -- sha256sum '+q(MANIFEST['originals'][SETTINGS]['path'])+'\n'
        for item in MANIFEST.get('runtimePatches',[]):
            script += 'nsenter -t "$zyg" -m -- sha256sum '+q(MANIFEST['originals'][item['target']]['path'])+'\n'
        for name,path in FILES.items():
            if strict and name!='catalog.ser':
                script += 'test -f '+q(path)+' || { echo "Сначала откройте быструю панель и Atmosphere"; exit 10; }\n'
        output = self.root(script,'preflight')
        runtime_hash = output.splitlines()[2].split()[0]
        allowed = {MANIFEST['originals'][SETTINGS]['sha256'],MANIFEST['files']['panel.apk'],
                   *MANIFEST.get('previousPanelHashes', [])}
        if runtime_hash not in allowed:
            raise RuntimeError('Обнаружена другая подмена APK настроек; автоматически заменять её нельзя')
        self.native_runtime={}
        for item in MANIFEST.get('runtimePatches',[]):
            path=MANIFEST['originals'][item['target']]['path']
            hashes=[line.split()[0] for line in output.splitlines() if line.endswith('  '+path)]
            allowed_native={MANIFEST['originals'][item['target']]['sha256'],MANIFEST['files'][item['file']],
                            *item.get('previousHashes',[])}
            if len(hashes)!=1 or hashes[0] not in allowed_native:
                raise RuntimeError('Обнаружена другая подмена APK: '+item['target'])
            self.native_runtime[item['target']]=hashes[0]
        save(self.logs/'preflight.json',{'properties':props,'runtimeSettingsSha256':runtime_hash})
        self.runtime_hash = runtime_hash
        self.props = props
        print('Совместимо: XGIMI Play 6, v1.7.116, Android 11.',flush=True)

    def overlay_states(self):
        output = {}
        for item in MANIFEST['overlays']:
            pkg = item['package']
            p = self.command('shell','pm path '+pkg,check=False)
            paths = [line[8:] for line in p.stdout.splitlines() if line.startswith('package:')]
            dump = self.command('shell','cmd overlay dump '+pkg,check=False).stdout
            if len(paths)>1:
                raise RuntimeError('Неожиданный split APK: '+pkg)
            output[pkg] = {'path':paths[0] if paths else None,'enabled':bool(re.search(r'mIsEnabled\.+:\s*true',dump)),
                           'state':dump[-1800:]}
        return output

    def snapshot(self):
        print('Сохранение резервных копий и текущего состояния…',flush=True)
        backup = self.logs/'before';backup.mkdir()
        overlays = self.overlay_states()
        skin_prop = self.shell('getprop persist.sys.xgimi.themeV2.url')
        if skin_prop and not skin_prop.startswith('/'):
            raise RuntimeError('Неожиданный путь текущего скина')
        self.state = {'device':self.serial,'identity':self.props,'skinProperty':skin_prop,
                      'overlays':overlays,'runtimeHash':self.runtime_hash,'version':MANIFEST['version'],
                      'files':{},'status':'backing-up','mountChanged':False,
                      'nativeRuntimeHashes':self.native_runtime,'nativeMountsChanged':[]}
        for pkg,info in overlays.items():
            if info['path']:
                name = pkg+'.apk'
                self.command('pull',info['path'],backup/name)
                info['sha256'] = sha(backup/name)
        script = 'mkdir -p '+q(self.remote)+'\nchown root:shell '+q(self.remote)+'\nchmod 770 '+q(self.remote)+'\n'
        script += 'am force-stop '+SETTINGS+'\nam force-stop '+ATMOSPHERE+'\n'
        for name,path in FILES.items():
            if name.endswith('.db'):
                # Never replace a database while an uncheckpointed sidecar could replay stale data.
                for suffix in ['-wal','-journal']:
                    script += 'if [ -s '+q(path+suffix)+' ]; then echo "База имеет незавершённый журнал. Закройте настройки и Atmosphere обычным выходом и повторите установку."; exit 11; fi\n'
            script += 'if [ -f '+q(path)+' ]; then cp -p '+q(path)+' '+q(self.remote+'/'+name)+\
                '; chmod 644 '+q(self.remote+'/'+name)+'; fi\n'
        script += 'if [ -f '+q(SKIN)+' ]; then cp '+q(SKIN)+' '+q(self.remote+'/skin-path.apk')+'; chmod 644 '+q(self.remote+'/skin-path.apk')+'; fi\n'
        self.root(script,'snapshot')
        for name in [*FILES,'skin-path.apk']:
            exists = self.command('shell','test -f '+q(self.remote+'/'+name),check=False).returncode==0
            self.state['files'][name]=exists
            if exists:
                self.command('pull',self.remote+'/'+name,backup/name)
        self.state['status']='backed-up'
        save(self.logs/'state.json',self.state)

    def prepare_data(self):
        print('Подготовка перевода баз и кэша, проверка целостности…',flush=True)
        after = self.logs/'after';after.mkdir()
        before = self.logs/'before'
        rules = (BASE/'payload/quick-rules.sql').read_text(encoding='utf-8')
        translate_db(before/'quick.db',after/'quick.db','quick',rules,not self.args.keep_child)
        translate_db(before/'atmosphere.db',after/'atmosphere.db','atmosphere')
        metadata_count=apply_db(after/'atmosphere.db')
        print('Полей каталога заставок переведено: '+str(metadata_count),flush=True)
        if self.state['files']['catalog.ser']:
            count = translate_catalog(before/'catalog.ser',after/'catalog.ser')
            print('Названий категорий в кэше изменено: '+str(count),flush=True)
            print('Строк каталога в кэше переведено: '+str(apply_catalog(after/'catalog.ser')),flush=True)
        self.state['dataHashes']={p.name:sha(p) for p in after.iterdir()}
        save(self.logs/'state.json',self.state)

    def install_overlays(self):
        print('Установка ресурсных пакетов перевода…',flush=True)
        for item in MANIFEST['overlays']:
            before = self.state['overlays'][item['package']]
            if before.get('sha256')!=MANIFEST['files'][item['file']]:
                self.mutated=True
                self.command('install','-r',BASE/'payload'/item['file'])
            # Recreate the idmap even when PackageManager preserved the installed package.
            self.mutated=True
            self.enable_overlay(item,True)

    def enable_overlay(self,item,enabled):
        pkg = item['package'];target = MANIFEST['originals'][item['target']]['path']
        script = f'OVERLAY=$(pm path {pkg})\nOVERLAY=${{OVERLAY#package:}}\ntest -f "$OVERLAY"\n'
        script += 'CACHE=/data/resource-cache/$(echo "${OVERLAY#/}" | tr / @)@idmap\n'
        script += 'idmap2 create --target-apk-path '+q(target)+' --overlay-apk-path "$OVERLAY" --idmap-path "$CACHE" --policy public --ignore-overlayable\n'
        script += 'chown system:system "$CACHE"\nchmod 644 "$CACHE"\n'
        # The overlay service learns about a freshly installed package asynchronously ("Unable to retrieve overlay
        # information"): retry for up to 20 seconds instead of failing the whole installation on that race.
        action = 'enable' if enabled else 'disable'
        script += f'n=0\nuntil cmd overlay {action} --user 0 {pkg}; do\n  n=$((n+1))\n  test "$n" -lt 20\n  sleep 1\ndone\ncmd overlay dump {pkg}\n'
        self.root(script,'overlay-'+pkg.rsplit('.',1)[1])

    def apply_data(self):
        print('Применение скина, базы и временной панели…',flush=True)
        for name in self.state['dataHashes']:
            self.command('push',self.logs/'after'/name,self.remote+'/new-'+name)
        self.command('push',BASE/'payload/skin.apk',self.remote+'/new-skin.apk')
        self.command('push',BASE/'payload/panel.apk',self.remote+'/new-panel.apk')
        script = 'am force-stop '+SETTINGS+'\nam force-stop '+ATMOSPHERE+'\n'
        for name,path in FILES.items():
            if name in self.state['dataHashes']:
                script += 'cat '+q(self.remote+'/new-'+name)+' > '+q(path)+'\n'
                script += 'test "$(sha256sum '+q(path)+' | cut -d " " -f 1)" = '+q(self.state['dataHashes'][name])+'\n'
        script += 'cat '+q(self.remote+'/new-skin.apk')+' > '+q(SKIN)+'\nchmod 644 '+q(SKIN)+'\n'
        script += 'setprop persist.sys.xgimi.themeV2.url '+q(SKIN)+'\n'
        if self.runtime_hash!=MANIFEST['files']['panel.apk']:
            # Stack the new mount over the previous one; unmounting restores it.
            # A distinct backing path prevents overwriting a mounted older APK.
            self.state['mountChanged']=True
            save(self.logs/'state.json',self.state)
            backing='/data/local/tmp/beam-russifier-panel-'+MANIFEST['files']['panel.apk'][:16]+'.apk'
            script += 'if [ -e '+q(backing)+' ]; then test "$(sha256sum '+q(backing)+' | cut -d " " -f 1)" = '+q(MANIFEST['files']['panel.apk'])+'; else\n'
            script += 'cat '+q(self.remote+'/new-panel.apk')+' > '+q(backing)+'\nfi\nchmod 644 '+q(backing)+'\nchown root:root '+q(backing)+'\n'
            script += 'chcon u:object_r:system_file:s0 '+q(backing)+'\n'
            script += 'zyg=$(pidof zygote)\ntest -n "$zyg"\nnsenter -t "$zyg" -m -- mount -o bind '+q(backing)+' '+q(MANIFEST['originals'][SETTINGS]['path'])+'\n'
        script += 'zyg=$(pidof zygote)\nnsenter -t "$zyg" -m -- sha256sum '+q(MANIFEST['originals'][SETTINGS]['path'])+'\n'
        for item in MANIFEST.get('runtimePatches',[]):
            target=item['target'];digest=MANIFEST['files'][item['file']]
            if self.native_runtime[target]==digest:continue
            if not re.fullmatch(r'/data/local/tmp/beam-russifier-[a-z0-9-]+\.apk',item['backing']):
                raise RuntimeError('Unexpected native APK backing path')
            self.command('push',BASE/'payload'/item['file'],self.remote+'/native-'+item['file'])
            self.state['nativeMountsChanged'].append(target)
            save(self.logs/'state.json',self.state)
            backing=item['backing'][:-4]+'-'+digest[:16]+'.apk'
            script += 'if [ -e '+q(backing)+' ]; then test "$(sha256sum '+q(backing)+' | cut -d " " -f 1)" = '+q(digest)+'; else\n'
            script += 'cat '+q(self.remote+'/native-'+item['file'])+' > '+q(backing)+'\nfi\n'
            script += 'chmod 644 '+q(backing)+'\nchown root:root '+q(backing)+'\nchcon u:object_r:system_file:s0 '+q(backing)+'\n'
            script += 'test "$(sha256sum '+q(backing)+' | cut -d " " -f 1)" = '+q(digest)+'\n'
            script += 'nsenter -t "$zyg" -m -- mount -o bind '+q(backing)+' '+q(MANIFEST['originals'][target]['path'])+'\n'
        self.mutated=True
        self.root(script,'apply-data')

    def restart(self):
        native_stops=''.join('am force-stop '+v['target']+'\n' for v in MANIFEST.get('runtimePatches',[]))
        if any(v['target']=='com.xgimi.systemui' for v in MANIFEST.get('runtimePatches',[])):
            # Persistent OEM SystemUI ignores force-stop; AMS restarts this exact process.
            native_stops+='p=$(pidof com.xgimi.systemui)\nif [ -n "$p" ]; then test "${p#* }" = "$p"; kill -9 "$p"; fi\n'
        self.root(native_stops+'am force-stop '+SETTINGS+'\nam force-stop '+ATMOSPHERE+
            '\nam force-stop com.xgimi.shutdown\nam startservice -n com.xgimi.shutdown/com.xgimi.systemui.service.SystemUIService'+
            '\n','restart-apps')
        self.shell('am startservice -a com.android.newsettings.MISCKEY -n '
            'com.android.newsettings/com.xgimi.misckey.MisckeyService --es data '
            'Misckey://com.xgimi.misckey.main/mainPage --ez needUnlock false')

    def verify_native_processes(self):
        """Check both future children of zygote and every currently running target."""
        native=[{'target':SETTINGS,'file':'panel.apk'}]+MANIFEST.get('runtimePatches',[])
        script='zyg=$(pidof zygote)\ntest -n "$zyg"\ntest "${zyg#* }" = "$zyg"\n'
        for item in native:
            target=item['target'];path=MANIFEST['originals'][target]['path']
            digest=MANIFEST['files'][item['file']]
            script+='test "$(nsenter -t "$zyg" -m -- sha256sum '+q(path)+' | cut -d " " -f 1)" = '+q(digest)+'\n'
            if target=='com.xgimi.systemui':
                script+='n=0\nwhile [ -z "$(pidof '+target+')" ] && [ "$n" -lt 20 ]; do sleep 1; n=$((n+1)); done\n'
            script+='pids=$(pidof '+q(target)+' || true)\n'
            if target in (SETTINGS,'com.xgimi.systemui'):
                script+='test -n "$pids"\n'
            script+='for p in $pids; do\n  actual=$(nsenter -t "$p" -m -- sha256sum '+q(path)+' | cut -d " " -f 1)\n'
            script+='  test "$actual" = '+q(digest)+'\n  echo '+q(target)+' "$p" "$actual"\ndone\n'
        output=self.root(script,'verify-native-processes')
        (self.logs/'native-processes.txt').write_text(output,encoding='utf-8')
        return output

    def lookups(self,checks):
        """Read many overlay values with ONE adb call; a call per value takes minutes over Wi-Fi."""
        lines = ['#!/system/bin/sh']
        for index,(target,kind,key,_,_) in enumerate(checks):
            lines.append('echo "@@@'+str(index)+'"; cmd overlay lookup '+q(target)+' '+q(target+':'+kind+'/'+key)+' 2>&1')
        lines.append('echo "@@@end"')
        local = self.logs/'lookups.sh'
        local.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
        remote = '/data/local/tmp/beam-ru-lookups-'+uuid.uuid4().hex[:8]+'.sh'
        self.command('push',local,remote)
        try:
            output = self.command('shell','sh '+remote).stdout.replace('\r','')
        finally:
            self.command('shell','rm -f '+remote,check=False)
        parts = re.split(r'^@@@(\d+|end)\n',output,flags=re.M)
        found = {parts[i]:parts[i+1].strip() for i in range(1,len(parts)-1,2)}
        if 'end' not in found or any(str(i) not in found for i in range(len(checks))):
            raise RuntimeError('Проверка переводов прервалась: ответ проектора неполный')
        return [found[str(i)] for i in range(len(checks))]

    def verify(self):
        print('Проверка включённых переводов и запуска панели…',flush=True)
        states = self.overlay_states()
        if not all(v['enabled'] and 'STATE_ENABLED' in v['state'] for v in states.values()):
            raise RuntimeError('Один из ресурсных пакетов не включился')
        self.shell('cmd overlay lookup '+SETTINGS+' '+SETTINGS+':string/head_network_setting_text')
        time.sleep(2)
        pid = self.shell('pidof '+SETTINGS)
        if not pid:
            raise RuntimeError('Процесс настроек не запустился')
        crash = self.command('logcat','-d','-b','crash','--pid='+pid).stdout
        (self.logs/'settings-crash.txt').write_text(crash,encoding='utf-8')
        if 'FATAL EXCEPTION' in crash:
            raise RuntimeError('Сбой приложения настроек; начат откат')
        power_text=self.shell('cmd overlay lookup com.xgimi.shutdown com.xgimi.shutdown:string/restart')
        if power_text!='Перезагрузить':
            raise RuntimeError('Перевод меню выключения не применился')
        focus_text=self.shell('cmd overlay lookup com.xgimi.systemui com.xgimi.systemui:string/hall_focus_success')
        if focus_text!='Фокусировка завершена. Удерживайте кнопку фокусировки для точной настройки':
            raise RuntimeError('Перевод завершения фокусировки не применился')
        checks = [(t,'string',k,v.strip(),'Перевод не применился: ') for t,d in MANIFEST.get('resourceChecks',{}).items() for k,v in d.items()]
        checks += [(t,'array',k,'\n'.join(v).strip(),'Перевод массива не применился: ') for t,d in MANIFEST.get('arrayChecks',{}).items() for k,v in d.items()]
        for (target,kind,key,expected,message),actual in zip(checks,self.lookups(checks)):
            if actual!=expected:
                raise RuntimeError(message+target+':'+key)
        self.verify_native_processes()
        shutdown_pid=self.shell('pidof com.xgimi.shutdown')
        if not shutdown_pid:
            raise RuntimeError('Сервис меню выключения не запустился')
        power_crash=self.command('logcat','-d','-b','crash','--pid='+shutdown_pid).stdout
        (self.logs/'shutdown-crash.txt').write_text(power_crash,encoding='utf-8')
        if 'FATAL EXCEPTION' in power_crash:
            raise RuntimeError('Сбой меню выключения; начат откат')
        save(self.logs/'verification.json',{'overlayStates':states,'settingsPid':pid,
             'settingsCrash':False,'shutdownPid':shutdown_pid,'shutdownCrash':False,
             'temporaryPanelUntilReboot':True})

    def cleanup(self):
        # The remote directory is a generated exact path, never supplied by the user.
        if not re.fullmatch(r'/data/local/tmp/beam-ru-[0-9a-f]{10}',self.remote):
            raise RuntimeError('Unexpected staging path')
        self.root('rm -rf '+q(self.remote),'cleanup-staging')

    def install(self):
        try:
            self.snapshot()
            self.prepare_data()
            self.install_overlays()
            self.apply_data()
            self.restart()
            self.verify()
            self.state['status']='installed'
            save(self.logs/'state.json',self.state)
            (BASE/'runs/latest-install.txt').write_text(self.logs.name,encoding='utf-8')
            print('Готово. Перевод установлен.',flush=True)
        except BaseException:
            if self.mutated:
                print('Операция не завершилась. Восстанавливаю состояние перед запуском…',flush=True)
                self.restore(immediate=True)
            else:
                self.restart()
            raise
        finally:
            self.cleanup()

    def restore(self,immediate=False):
        """Immediate recovery uses frozen backups; later rollback preserves new app data."""
        before = self.logs/'before'
        script = 'am force-stop '+SETTINGS+'\nam force-stop '+ATMOSPHERE+'\n'
        self.root(script+'mkdir -p '+q(self.remote)+'\nchown root:shell '+q(self.remote)+'\nchmod 770 '+q(self.remote),'restore-stop')
        if immediate:
            restored = before
        else:
            current = self.logs/'rollback-current';current.mkdir(exist_ok=True)
            restored = self.logs/'rollback-data';restored.mkdir(exist_ok=True)
            script = ''
            for name,path in FILES.items():
                if name.endswith('.db'):
                    for suffix in ['-wal','-journal']:
                        script += 'if [ -s '+q(path+suffix)+' ]; then echo "Незавершённый журнал базы: безопасный откат остановлен"; exit 11; fi\n'
                script += 'if [ -f '+q(path)+' ]; then cp '+q(path)+' '+q(self.remote+'/'+name)+'; chmod 644 '+q(self.remote+'/'+name)+'; fi\n'
            self.root(script,'restore-snapshot')
            for name in FILES:
                if self.command('shell','test -f '+q(self.remote+'/'+name),check=False).returncode==0:
                    self.command('pull',self.remote+'/'+name,current/name)
            for kind,name in [('quick','quick.db'),('atmosphere','atmosphere.db')]:
                restore_db(current/name,before/name,self.logs/'after'/name,restored/name,kind)
            restore_db_metadata(restored/'atmosphere.db',before/'atmosphere.db',self.logs/'after/atmosphere.db')
            if (before/'catalog.ser').exists() and (current/'catalog.ser').exists():
                old_names = catalog_names(before/'catalog.ser')
                present = catalog_names(current/'catalog.ser')
                installed = catalog_names(self.logs/'after/catalog.ser')
                inverse = {k:v for k,v in old_names.items() if present.get(k)==installed.get(k)}
                translate_catalog(current/'catalog.ser',restored/'catalog.ser',inverse)
                restore_catalog_metadata(restored/'catalog.ser',before/'catalog.ser',self.logs/'after/catalog.ser')
        script = ''
        for name,path in FILES.items():
            if (restored/name).exists():
                self.command('push',restored/name,self.remote+'/restore-'+name)
                script += 'cat '+q(self.remote+'/restore-'+name)+' > '+q(path)+'\n'
        if (before/'skin-path.apk').exists():
            self.command('push',before/'skin-path.apk',self.remote+'/restore-skin.apk')
            script += 'cat '+q(self.remote+'/restore-skin.apk')+' > '+q(SKIN)+'\nchmod 644 '+q(SKIN)+'\n'
        else:
            script += 'rm -f '+q(SKIN)+'\n'
        script += 'setprop persist.sys.xgimi.themeV2.url '+q(self.state['skinProperty'])+'\n'
        if self.state['mountChanged']:
            script += 'zyg=$(pidof zygote)\n'
            script += 'if nsenter -t "$zyg" -m -- sha256sum '+q(MANIFEST['originals'][SETTINGS]['path'])+\
                ' | grep -q '+q(MANIFEST['files']['panel.apk'])+'; then nsenter -t "$zyg" -m -- umount '+q(MANIFEST['originals'][SETTINGS]['path'])+'; fi\n'
        for item in MANIFEST.get('runtimePatches',[]):
            target=item['target']
            if target not in self.state.get('nativeMountsChanged',[]):continue
            path=MANIFEST['originals'][target]['path'];before_hash=self.state['nativeRuntimeHashes'][target]
            script += 'zyg=$(pidof zygote)\ncurrent=$(nsenter -t "$zyg" -m -- sha256sum '+q(path)+' | cut -d " " -f 1)\n'
            script += 'case "$current" in\n'+MANIFEST['files'][item['file']]+') nsenter -t "$zyg" -m -- umount '+q(path)+' ;;\n'+before_hash+') : ;;\n*) echo "Native APK changed independently"; exit 12 ;;\nesac\n'
            script += 'test "$(nsenter -t "$zyg" -m -- sha256sum '+q(path)+' | cut -d " " -f 1)" = '+q(before_hash)+'\n'
        self.root(script,'restore-data')
        for item in MANIFEST['overlays']:
            previous = self.state['overlays'][item['package']]
            if previous['path']:
                self.command('install','-r','-d',before/(item['package']+'.apk'))
                self.enable_overlay(item,previous['enabled'])
            else:
                self.command('uninstall',item['package'],check=False)
                if self.shell('pm path '+item['package'],check=False).startswith('package:'):
                    raise RuntimeError('Не удалось удалить ресурсный пакет: '+item['package'])
        self.restart()
        self.state['status']='restored'
        save(self.logs/'state.json',self.state)
        print('Предыдущее состояние восстановлено.',flush=True)

    def rollback(self):
        latest = self.args.backup or (BASE/'runs/latest-install.txt').read_text(encoding='utf-8').strip()
        if not re.fullmatch(r'[0-9]{8}-[0-9]{6}-[0-9a-f]{6}',latest):
            raise RuntimeError('Некорректное имя резервной копии')
        source = BASE/'runs'/latest
        self.state = json.loads((source/'state.json').read_text(encoding='utf-8'))
        if self.state['status']!='installed':
            raise RuntimeError('Эта установка не завершена или уже отменена')
        if self.state.get('version')!=MANIFEST['version']:
            raise RuntimeError('Для этой резервной копии используйте ту же версию установщика: '+str(self.state.get('version')))
        if set(self.state['overlays'])!={v['package'] for v in MANIFEST['overlays']}:
            raise RuntimeError('Набор пакетов в резервной копии отличается от этого установщика')
        if self.state['identity']['ro.serialno']!=self.props['ro.serialno']:
            raise RuntimeError('Резервная копия относится к другому проектору')
        if self.shell('getprop persist.sys.xgimi.themeV2.url')!=SKIN or self.shell('sha256sum '+q(SKIN)).split()[0]!=MANIFEST['files']['skin.apk']:
            raise RuntimeError('Скин изменён после установки; автоматический откат остановлен')
        # Refuse to overwrite a newer independently installed translation package.
        for item in MANIFEST['overlays']:
            path = self.overlay_states()[item['package']]['path']
            if not path or self.shell('sha256sum '+q(path)).split()[0]!=MANIFEST['files'][item['file']]:
                raise RuntimeError('Пакеты изменены после установки; автоматический откат остановлен')
        self.logs = source
        try:
            self.restore()
        finally:
            self.cleanup()

def main():
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Русификация XGIMI Play 6 v1.7.116 через ADB')
    parser.add_argument('mode',choices=['check','install','rollback'],nargs='?',default='check')
    parser.add_argument('--device',default=os.environ.get('beamDevice','192.168.1.100:5555'))
    parser.add_argument('--keep-child',action='store_true',help='Не добавлять скрытие кнопки Детский')
    parser.add_argument('--backup',help='Имя каталога конкретной установки для отката')
    args = parser.parse_args()
    install = None
    try:
        install = Installer(args)
        install.preflight(strict=args.mode!='check')
        if args.mode=='install':
            if install.shell('pm path com.beam.russifier.boot',check=False).startswith('package:'):
                raise RuntimeError('Обнаружен helper автозапуска: используйте UPDATE_BOOT или сначала отключите его')
            install.install()
        elif args.mode=='rollback':
            if install.shell('pm path com.beam.russifier.boot',check=False).startswith('package:'):
                raise RuntimeError('Обнаружен helper автозапуска: используйте REMOVE_AUTOSTART для первой установки или сначала отключите прототип')
            install.rollback()
        else:
            if not install.props['persist.sys.locale'].lower().startswith('ru'):
                print('Язык проектора пока не русский: это нормально, русский язык включится при установке русификации.')
            print('Проверка пройдена. Для установки: окно установщика (Windows) или команда prepare-install (см. MANUAL-OTHER-OS.md).')
        return 0
    except (Exception,KeyboardInterrupt) as exc:
        print('ОШИБКА: '+str(exc),file=sys.stderr,flush=True)
        if install is not None: print('Журнал: '+str(install.logs),file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
