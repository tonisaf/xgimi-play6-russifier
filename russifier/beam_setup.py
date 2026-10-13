"""Optional BEAM install profile, copied from the guide's behavior, not its source tree."""
from pathlib import Path
import hashlib,json,os,re,struct,urllib.request,zipfile
from installer import BASE,MANIFEST,Installer,q,save
from preparation import IME,package_state

# Only the launcher itself is installed. The four "stub-button" apps of older BEAM releases are no longer used:
# the independent module com.beam.remote handles the remote's four app keys (see remote_setup.py).
NAMES=['app-release.apk']
PACKAGES=['com.home.tiles']
KEYBOARD='org.liskovsoft.androidtv.rukeyboard'
KEYBOARD_URL='https://github.com/yuliskov/LeanKeyboard/releases/download/6.1.31/LeanKeyboard_v6.1.31_playstore_r.apk'
KEYBOARD_SHA256='5a90529fcae55c664128fb36e752f90e84d158266eced85084594c1d336a1468'
HOME_QUERY='cmd package query-activities --brief -a android.intent.action.MAIN -c android.intent.category.HOME'
PROTECTED=set(MANIFEST['originals'])|{'com.home.tiles','com.xgimi.home','com.android.settings','com.android.systemui'}

def competing_launchers(r):
    text=r.shell(HOME_QUERY)
    packages=set()
    for line in text.splitlines():
        m=re.fullmatch(r'([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)/([A-Za-z0-9_.$]+)',line.strip())
        if m and 'FallbackHome' not in m[2] and m[1] not in PROTECTED:packages.add(m[1])
    return sorted(packages)

def restore_launcher_changes(r,record,journal):
    operations={0:'default-state',1:'enable',2:'disable',3:'disable-user',4:'disable-until-used'}
    for change in reversed(record.get('launcherChanges',[])):
        if change.get('restored'):continue
        package=change['package']
        if (package in PROTECTED and package!='com.xgimi.home') or change['before'] not in operations:raise RuntimeError('Небезопасная запись возврата лаунчера')
        current=package_state(r,package)
        if current==change['before']:change['restored']=True;save(journal,record);continue
        if current!=3:raise RuntimeError('Лаунчер изменён независимо: '+package)
        r.shell('pm '+operations[change['before']]+' --user 0 '+package)
        if package_state(r,package)!=change['before']:raise RuntimeError('Состояние лаунчера не восстановлено: '+package)
        change['restored']=True;save(journal,record)

def launcher_cli():
    import argparse
    from preparation import identity
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['list-launchers','restore-launchers'])
    parser.add_argument('--device',required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--backup',type=Path)
    args=parser.parse_args();r=None
    try:
        r=Installer(args);device=identity(r)
        if args.mode=='list-launchers':
            result={'device':device,'launchers':competing_launchers(r)}
            if args.output:save(args.output,result)
            print(json.dumps(result,ensure_ascii=True));return 0
        if not args.backup:raise RuntimeError('Выберите каталог с beam-setup.json')
        journal=args.backup/'beam-setup.json';record=json.loads(journal.read_text(encoding='utf-8'))
        if record.get('device')!=device:raise RuntimeError('Копия относится к другому устройству')
        restore_launcher_changes(r,record,journal)
        print('Прежние состояния выбранных лаунчеров восстановлены. BEAM не удалён.');return 0
    except Exception as exc:
        print('ОШИБКА:',exc);return 1

def apk_package(path):
    # Read the package attribute of binary AndroidManifest.xml; never execute APK data.
    with zipfile.ZipFile(path) as apk: data=apk.read('AndroidManifest.xml')
    strings=[];position=8
    while position<len(data):
        kind,header,size=struct.unpack_from('<HHI',data,position)
        if size<header or position+size>len(data):raise ValueError('Malformed APK manifest')
        if kind==1:
            count,_,flags,start,_=struct.unpack_from('<IIIII',data,position+8)
            def length(offset,utf8):
                if utf8:
                    value=data[offset];return (((value&127)<<8)|data[offset+1],offset+2) if value&128 else (value,offset+1)
                value=struct.unpack_from('<H',data,offset)[0]
                return (((value&32767)<<16)|struct.unpack_from('<H',data,offset+2)[0],offset+4) if value&32768 else (value,offset+2)
            for i in range(count):
                offset=position+start+struct.unpack_from('<I',data,position+header+4*i)[0]
                utf8=bool(flags&256);n,offset=length(offset,utf8)
                if utf8:n,offset=length(offset,True)
                strings.append(data[offset:offset+n*(1 if utf8 else 2)].decode('utf-8' if utf8 else 'utf-16le'))
        elif kind==0x102:
            _,name,attribute_start,attribute_size,count=struct.unpack_from('<IIHHH',data,position+16)
            if strings[name]=='manifest':
                for i in range(count):
                    a=position+16+attribute_start+i*attribute_size
                    _,key,raw=struct.unpack_from('<III',data,a)
                    if strings[key]=='package':
                        if raw!=0xffffffff:return strings[raw]
                        if data[a+15]==3:return strings[struct.unpack_from('<I',data,a+16)[0]]
                break
        position+=size
    raise ValueError('APK package attribute not found')

def request(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'xgimi-russifier-installer'}),timeout=45)

def download_release():
    cache=BASE/'beam-downloads';cache.mkdir(exist_ok=True)
    print('Загрузка последнего официального релиза BEAM…',flush=True)
    with request('https://api.github.com/repos/tonisaf/beam-launcher/releases/latest') as response:
        release=json.loads(response.read(4*1024*1024))
    assets={a['name']:a['browser_download_url'] for a in release['assets']}
    def url(name):
        value=assets[name]
        if not value.startswith('https://github.com/tonisaf/beam-launcher/releases/download/'):
            raise RuntimeError('Неожиданный адрес файла BEAM')
        return value
    with request(url('SHA256SUMS.txt')) as response: content=response.read(1024*1024).decode('utf-8')
    hashes={m[2]:m[1].lower() for m in re.finditer(r'^([0-9a-fA-F]{64})\s+\*?(\S+)\s*$',content,re.M)}
    for name in NAMES:
        if name not in hashes:raise RuntimeError('Нет SHA256 для '+name)
        path=cache/name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==hashes[name]:continue
        temp=cache/(name+'.partial')
        try:
            with request(url(name)) as response,temp.open('wb') as stream:
                total=0
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    total+=len(chunk)
                    if total>160*1024*1024:raise RuntimeError('APK слишком большой')
                    stream.write(chunk)
            if hashlib.sha256(temp.read_bytes()).hexdigest()!=hashes[name]:raise RuntimeError('SHA256 не совпадает: '+name)
            os.replace(temp,path)
        finally:temp.unlink(missing_ok=True)
    for name,package in zip(NAMES,PACKAGES):
        if apk_package(cache/name)!=package:raise RuntimeError('Неожиданный пакет в '+name)
    save(cache/'release.json',{'tag':release['tag_name'],'sha256':{n:hashes[n] for n in NAMES}})
    return cache,release['tag_name']

def download_keyboard():
    cache=BASE/'keyboard-downloads';cache.mkdir(exist_ok=True)
    path=cache/'LeanKeyboard-6.1.31.apk'
    def valid(file):
        return file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest()==KEYBOARD_SHA256
    if not valid(path):
        print('Загрузка официального LeanKey 6.1.31…',flush=True)
        temp=path.with_suffix('.partial')
        try:
            with request(KEYBOARD_URL) as response,temp.open('wb') as stream:
                total=0
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    total+=len(chunk)
                    if total>40*1024*1024:raise RuntimeError('APK LeanKey слишком большой')
                    stream.write(chunk)
            if not valid(temp):raise RuntimeError('SHA256 LeanKey не совпадает')
            if apk_package(temp)!=KEYBOARD:raise RuntimeError('Неожиданный пакет LeanKey')
            os.replace(temp,path)
        finally:temp.unlink(missing_ok=True)
    if apk_package(path)!=KEYBOARD:raise RuntimeError('Неожиданный пакет LeanKey')
    return path

def install_beam(r, keyboard, selected_launchers=()):
    selected_launchers=sorted(set(selected_launchers))
    candidates=competing_launchers(r)
    if any(package not in candidates or package in PROTECTED for package in selected_launchers):
        raise RuntimeError('Выбранный лаунчер отсутствует среди текущих кандидатов HOME; обновите список')
    if not r.shell('pm path '+KEYBOARD,check=False).startswith('package:'):
        if keyboard is None:keyboard=download_keyboard()
        if not keyboard.is_file() or apk_package(keyboard)!=KEYBOARD:
            raise RuntimeError('Для BEAM выберите APK LeanKey Keyboard. Sogou пока сохранена.')
    elif keyboard is not None and (not keyboard.is_file() or apk_package(keyboard)!=KEYBOARD):
        raise RuntimeError('Выбранный APK не является LeanKey Keyboard')
    cache,tag=download_release()  # All files verified before any device mutation.
    from preparation import identity
    record={'status':'prepared','release':tag,'packages':{},'settings':{},'permissions':{},
            'device':identity(r),'selectedLaunchers':selected_launchers,'launcherChanges':[]}
    for package in list(dict.fromkeys(PACKAGES+[KEYBOARD,'com.xgimi.home']+selected_launchers)):
        dump=r.shell('dumpsys package '+package)
        paths=[line[8:] for line in r.shell('pm path '+package,check=False).splitlines() if line.startswith('package:')]
        record['packages'][package]={'enabled':package_state(r,package),'paths':paths}
        if paths:
            for i,path in enumerate(paths):r.command('pull',path,r.logs/(package+'-'+str(i)+'.apk'))
        if package=='com.home.tiles':(r.logs/'beam-before-dump.txt').write_text(dump,encoding='utf-8')
    for key in ['default_input_method','enabled_input_methods','enabled_accessibility_services','accessibility_enabled']:
        record['settings'][key]=r.shell('settings get secure '+key)
    record['home']=r.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME')
    record['notificationListeners']=r.shell('settings get secure enabled_notification_listeners')
    record['appops']=r.shell('appops get com.home.tiles',check=False)
    journal=r.logs/'beam-setup.json';save(journal,record)
    try:
        record['status']='applying';save(journal,record)
        if keyboard:r.command('install','-r',keyboard)
        if not r.shell('pm path '+KEYBOARD).startswith('package:'):raise RuntimeError('LeanKey не установилась')
        for name in NAMES:r.command('install','-r',cache/name)
        r.shell('ime enable '+IME);r.shell('ime set '+IME)
        if r.shell('settings get secure default_input_method')!=IME:raise RuntimeError('LeanKey не стала текущей клавиатурой')
        r.shell('appops set com.home.tiles GET_USAGE_STATS allow')
        r.shell('cmd notification allow_listener com.home.tiles/com.home.tiles.MediaListener')
        # A BEAM release may drop a permission it no longer needs (v0.4.11 has no WRITE_SECURE_SETTINGS / RECORD_AUDIO);
        # a right the app does not request is skipped, any other failure still stops the installation.
        for permission in ['READ_TV_LISTINGS','WRITE_SECURE_SETTINGS','ACCESS_FINE_LOCATION','ACCESS_COARSE_LOCATION','RECORD_AUDIO']:
            try:
                r.shell('pm grant com.home.tiles android.permission.'+permission)
            except RuntimeError as error:
                if 'has not requested permission' not in str(error): raise
                print('Пропущено: эта версия BEAM не запрашивает право '+permission+'.')
        r.shell('appops set com.home.tiles WRITE_SETTINGS allow')
        # Disable other HOME candidates only when selected by the user.
        for package in selected_launchers:
            before=record['packages'][package]['enabled']
            if before is None or before not in range(5):raise RuntimeError('Неизвестное состояние лаунчера: '+package)
            if package_state(r,package)!=before:raise RuntimeError('Лаунчер изменился во время установки: '+package)
            if before==3:continue
            record['launcherChanges'].append({'package':package,'before':before,'after':3})
            save(journal,record)
            r.shell('pm disable-user --user 0 '+package)
            if package_state(r,package)!=3:raise RuntimeError('Лаунчер не отключился: '+package)
        r.shell('cmd package set-home-activity com.home.tiles/.MainActivity')
        # XGIMI keeps resolving HOME to its chooser while its stock home is enabled.
        # Journal the reversible disable before verifying the final HOME resolution.
        package='com.xgimi.home'
        before=record['packages'][package]['enabled']
        if before is not None:
            if before not in range(5):raise RuntimeError('Неизвестное состояние штатного лаунчера')
            if package_state(r,package)!=before:raise RuntimeError('Штатный лаунчер изменился во время установки')
            if before!=3:
                record['launcherChanges'].append({'package':package,'before':before,'after':3})
                save(journal,record)
                r.shell('pm disable-user --user 0 '+package)
                if package_state(r,package)!=3:raise RuntimeError('Штатный лаунчер не отключился')
        home=r.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME')
        if not re.search(r'^com\.home\.tiles/(?:\.MainActivity|com\.home\.tiles\.MainActivity)$',home,re.M):
            raise RuntimeError('BEAM не назначен домашним экраном: выполняется возврат лаунчеров')
        remaining=competing_launchers(r)
        if remaining:print('Другие лаунчеры оставлены включёнными по выбору пользователя: '+', '.join(remaining)+'. Проверьте Домой после reboot.',flush=True)
        # Older BEAM releases had an accessibility service (PanelOverlay); newer ones (0.4.x) declare none.
        # It is enabled only when the installed APK really offers it, so no dangling entry is left behind.
        offered=r.shell('cmd package query-services --brief -a android.accessibilityservice.AccessibilityService',check=False)
        if 'com.home.tiles/' in offered:
            current=r.shell('settings get secure enabled_accessibility_services')
            components=[] if current in ('','null') else current.split(':')
            if not any(c in ('com.home.tiles/.PanelOverlay','com.home.tiles/com.home.tiles.PanelOverlay') for c in components):
                components.append('com.home.tiles/com.home.tiles.PanelOverlay')
            r.shell('settings put secure enabled_accessibility_services '+q(':'.join(components)))
            r.shell('settings put secure accessibility_enabled 1')
        # The Bluetooth-name hook of the old AdbCommandReceiver (bt_name) was removed from BEAM 0.4.x; the name is no longer touched.
        record['status']='complete';save(journal,record)
        print('BEAM установлен: права, клавиатура и домашний экран настроены.',flush=True)
    except BaseException:
        record['status']='incomplete';save(journal,record)
        try:restore_launcher_changes(r,record,journal)
        except Exception as exc:print('Автовозврат выбранных лаунчеров остановлен:',exc,flush=True)
        print('Установка BEAM прервана. Протокол и прежние APK:',r.logs,flush=True)
        raise

if __name__=='__main__':raise SystemExit(launcher_cli())
