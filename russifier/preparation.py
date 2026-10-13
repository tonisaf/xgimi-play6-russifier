"""Reversible preparation from the BEAM guide; never installs or replaces BEAM."""
import argparse, json, re, time
from pathlib import Path
from installer import Installer, MANIFEST, BASE, FILES, q, save

ZONES = ['Europe/Moscow','Europe/Kaliningrad','Europe/Samara','Asia/Yekaterinburg',
         'Asia/Omsk','Asia/Novosibirsk','Asia/Krasnoyarsk','Asia/Irkutsk','Asia/Yakutsk',
         'Asia/Vladivostok','Asia/Magadan','Asia/Kamchatka','Europe/Minsk','Europe/Kyiv',
         'Asia/Almaty','Europe/Berlin','Europe/London','UTC']
SERVICES = {
 'com.xgimi.adservice':'Реклама', 'com.xgimi.datareporter':'Телеметрия',
 'com.xgimi.bugreportsender':'Отчёты об ошибках', 'com.xgimi.newappmarket':'Китайский магазин',
 'com.xgimi.doubanfm':'Douban FM', 'com.xgimi.duertts':'Голосовой движок Baidu',
 'com.xgimi.msgcenter':'Центр уведомлений', 'com.xgimi.payview':'Оплата',
 'com.xgimi.vcontrol':'Голосовое/телефонное управление XGIMI',
 'com.xgimi.xgimihilink':'Huawei HiLink', 'com.xgimi.xgimiiotserver':'Умный дом XGIMI',
}
IME = 'org.liskovsoft.androidtv.rukeyboard/com.liskovsoft.leankeyboard.ime.LeanbackImeService'
GUARDED = {'com.sohu.inputmethod.sogou.tv':'Sogou', 'com.xgimi.home':'Штатный лаунчер',
           'com.spocky.projengmenu':'Projectivy'}
SETTINGS = {'locale':('prop','persist.sys.locale'), 'timezone':('prop','persist.sys.timezone'),
            'autoZone':('global','auto_time_zone'), 'ime':('secure','default_input_method'),
            'enabledImes':('secure','enabled_input_methods')}

def read(r, key):
    kind, name = SETTINGS[key]
    return r.shell('getprop '+name if kind=='prop' else 'settings get '+kind+' '+name)

def package_state(r, package):
    text = r.shell('dumpsys package '+package)
    m = re.search(r'User 0:.*?enabled=(\d+)',text)
    return int(m[1]) if m else None

def identity(r):
    if ':' in r.serial: r.command('connect',r.serial)
    if r.command('get-state').stdout.strip()!='device': raise RuntimeError('ADB недоступен или не авторизован')
    props={key:r.shell('getprop '+key) for key in ('ro.build.fingerprint','ro.serialno')}
    if props['ro.build.fingerprint']!=MANIFEST['fingerprint'] or not props['ro.serialno']:
        raise RuntimeError('Неподдерживаемая прошивка или отсутствует идентификатор устройства')
    for item in MANIFEST['originals'].values():
        if r.shell('sha256sum '+q(item['path'])).split()[0]!=item['sha256']:
            raise RuntimeError('Исходный APK отличается: '+item['path'])
    return props

def zone(r, value):
    r.shell('service call alarm 3 s16 '+q(value),check=False)
    if read(r,'timezone')!=value: r.shell('cmd alarm set-timezone '+q(value),check=False)
    if read(r,'timezone')!=value: raise RuntimeError('Часовой пояс не применился: '+value)

def current_plan(r, timezone, debloat):
    props=identity(r)
    states={package:package_state(r,package) for package in {**SERVICES,**GUARDED}}
    home=r.shell('cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME')
    lean=r.shell('pm path org.liskovsoft.androidtv.rukeyboard',check=False).startswith('package:')
    enabled_imes=r.shell('ime list -s')
    return {'device':props,'before':{key:read(r,key) for key in SETTINGS},'packages':states,
            'home':home,'leanKey':lean and IME in enabled_imes.splitlines(),
            'timezone':timezone,'disableServices':debloat}

def mutate_setting(r, record, path, key, expected, command):
    existing=next((c for c in record['changes'] if c['kind']=='setting' and c['key']==key),None)
    current=read(r,key)
    if current==expected: return
    if existing and current not in (existing['before'],existing['after']):
        raise RuntimeError('Настройка изменена независимо: '+key)
    if existing: existing['after']=expected
    else: record['changes'].append({'kind':'setting','key':key,'before':current,'after':expected})
    save(path,record)  # Intent is saved before the write, including failure/unknown result.
    command()
    if read(r,key)!=expected: raise RuntimeError('Настройка не применилась: '+key)

def disable(r, record, path, package):
    current=package_state(r,package)
    if current is None or current==3: return
    record['changes'].append({'kind':'package','key':package,'before':current,'after':3})
    save(path,record)
    r.shell('pm disable-user --user 0 '+package)
    if package_state(r,package)!=3: raise RuntimeError('Пакет не отключился: '+package)
    print('Отключён:',package,flush=True)

def prepare(r, timezone, debloat):
    plan=current_plan(r,timezone,debloat)
    pointer=BASE/'runs/latest-prepare.txt'
    path=r.logs/'preparation.json';record={'device':plan['device'],'before':plan,'changes':[],'status':'applying'}
    if pointer.exists():
        name=pointer.read_text(encoding='utf-8').strip()
        if re.fullmatch(r'[0-9]{8}-[0-9]{6}-[0-9a-f]{6}',name):
            previous=BASE/'runs'/name/'preparation.json'
            if previous.exists():
                old=json.loads(previous.read_text(encoding='utf-8'))
                if old['device']==plan['device'] and old['status']=='reboot-required':
                    record=old;path=previous;record['status']='applying'
    save(path,record);pointer.write_text(path.parent.name,encoding='utf-8')
    try:
        mutate_setting(r,record,path,'locale','ru-RU',lambda:r.shell('setprop persist.sys.locale ru-RU'))
        if timezone:
            mutate_setting(r,record,path,'autoZone','0',lambda:r.shell('settings put global auto_time_zone 0'))
            mutate_setting(r,record,path,'timezone',timezone,lambda:zone(r,timezone))
        if debloat:
            for package in SERVICES: disable(r,record,path,package)
            # Establish a working IME before disabling the original keyboard.
            if plan['leanKey']:
                before_enabled=read(r,'enabledImes')
                if IME not in (before_enabled or '').split(':'):
                    # Capture the exact result of ime enable as part of the journal.
                    record['changes'].append({'kind':'setting','key':'enabledImes','before':before_enabled,'after':None})
                    save(path,record);r.shell('ime enable '+IME)
                    record['changes'][-1]['after']=read(r,'enabledImes');save(path,record)
                mutate_setting(r,record,path,'ime',IME,lambda:r.shell('ime set '+IME))
                disable(r,record,path,'com.sohu.inputmethod.sogou.tv')
            else: print('Sogou сохранена: сначала установите LeanKey.',flush=True)
            print('Настройки домашнего экрана применяются только при выборе установки BEAM.',flush=True)
        config=r.shell('am get-config')
        if not re.search(r'(?:^|[-\s])ru-rRU(?:[-\s]|$)',config):
            record['status']='reboot-required';save(path,record)
            print('Русская локаль записана. Выполните полную перезагрузку и повторите установку.',flush=True)
            print('Подготовка сохранена:',path.parent,flush=True)
            return 10
        record['status']='complete';save(path,record)
        print('Подготовка выполнена. Резервная копия:',path.parent,flush=True)
        return 0
    except BaseException:
        record['status']='incomplete';save(path,record)
        print('Подготовка прервана. Для возврата используйте undo-prepare --backup',path.parent,flush=True)
        raise

def initialize(r):
    activities={'quick.db':('service','com.android.newsettings/com.xgimi.misckey.MisckeyService'),
                'atmosphere.db':('activity','com.xgimi.atmosphere/.ScreensaverActivity')}
    for name,(kind,component) in activities.items():
        path=FILES[name]
        if r.root('if [ -f '+q(path)+' ]; then echo present; else echo missing; fi','db-'+name.replace('.','-'))=='present':continue
        print('Создание базы приложения:',name,flush=True)
        if kind=='service':
            output=r.shell('am startservice -a com.android.newsettings.MISCKEY -n '+component+' --es data Misckey://com.xgimi.misckey.main/mainPage')
        else: output=r.shell('am start -n '+component)
        if 'Error' in output or 'Exception' in output: raise RuntimeError(output)
        for attempt in range(8):
            if r.root('if [ -f '+q(path)+' ]; then echo present; else echo missing; fi','wait-'+name.replace('.','-')+'-'+str(attempt))=='present':break
            time.sleep(1)
        else: raise RuntimeError('База не создана: откройте быструю панель и Atmosphere вручную')

def undo(r, directory):
    path=Path(directory)/'preparation.json';record=json.loads(path.read_text(encoding='utf-8'))
    if identity(r)!=record['device']: raise RuntimeError('Копия относится к другому проектору')
    operations={0:'default-state',1:'enable',2:'disable',3:'disable-user',4:'disable-until-used'}
    for c in reversed(record['changes']):
        if c.get('restored'):continue
        current=package_state(r,c['key']) if c['kind']=='package' else read(r,c['key'])
        if current==c['before']:c['restored']=True;save(path,record);continue
        if c['after'] is None or current!=c['after']:raise RuntimeError('Независимое изменение или неизвестный результат: '+c['key'])
        if c['kind']=='package':r.shell('pm '+operations[c['before']]+' --user 0 '+c['key'])
        else:
            kind,name=SETTINGS[c['key']]
            if c['key']=='timezone':zone(r,c['before'])
            elif kind=='prop':r.shell('setprop '+name+' '+q(c['before']))
            elif c['before'] in ('','null'):r.shell('settings delete '+kind+' '+name)
            else:r.shell('settings put '+kind+' '+name+' '+q(c['before']))
        actual=package_state(r,c['key']) if c['kind']=='package' else read(r,c['key'])
        if actual!=c['before']:raise RuntimeError('Возврат не подтверждён: '+c['key'])
        c['restored']=True;save(path,record)
    record['status']='restored';save(path,record);print('Подготовка отменена. Для языка может понадобиться полная перезагрузка.')

def main():
    parser=argparse.ArgumentParser(description='Подготовка по инструкции BEAM с отдельным журналом и откатом')
    parser.add_argument('mode',choices=['prepare','prepare-install','undo-prepare'])
    parser.add_argument('--device',required=True)
    parser.add_argument('--timezone',choices=ZONES)
    parser.add_argument('--disable-services',action='store_true')
    parser.add_argument('--plan',action='store_true',help='Только прочитать настройки и составить план')
    parser.add_argument('--backup',type=Path)
    parser.add_argument('--bundle',type=Path,default=BASE/'boot-helper')
    parser.add_argument('--keep-child',action='store_true',help='Не добавлять скрытие кнопки Детский')
    parser.add_argument('--install-beam',action='store_true')
    parser.add_argument('--keyboard-apk',type=Path)
    parser.add_argument('--disable-launcher',action='append',default=[])
    args=parser.parse_args();r=None
    try:
        r=Installer(args)
        if args.mode=='undo-prepare':
            if not args.backup:raise RuntimeError('Выберите каталог с preparation.json')
            undo(r,args.backup);return 0
        if args.plan:
            plan=current_plan(r,args.timezone,args.disable_services);save(r.logs/'preparation-plan.json',plan)
            print('Текущая локаль:',plan['before']['locale']);print('Текущий пояс:',plan['before']['timezone'])
            print('Новый пояс:',args.timezone or 'сохранить');print('Отключение сервисов:',args.disable_services)
            print('Установка BEAM и настройка его прав/пульта/домашнего экрана:',args.install_beam)
            for package in {**SERVICES,**GUARDED}:print(package,plan['packages'][package])
            print('План сохранён:',r.logs);return 0
        identity(r)
        if args.mode=='prepare-install' and r.shell('pm path com.beam.russifier.boot',check=False).startswith('package:'):
            raise RuntimeError('Русификатор уже установлен: выберите обновление или отдельную подготовку')
        if args.install_beam:
            from beam_setup import install_beam
            install_beam(r,args.keyboard_apk,args.disable_launcher)
        code=prepare(r,args.timezone,args.disable_services)
        if code:return code
        initialize(r)
        if args.mode=='prepare-install':
            from boot_setup import install
            install(r,args.bundle)
        return 0
    except (Exception,KeyboardInterrupt) as exc:
        print('ОШИБКА:',exc)
        if r:print('Журнал:',r.logs)
        return 1

if __name__=='__main__':raise SystemExit(main())
