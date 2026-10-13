import subprocess, pathlib, json, shlex, time, sys
OUT=pathlib.Path(__file__).resolve().parent
ADB=r'C:\android\sdk\platform-tools\adb.exe'
DEVICE='192.168.1.100:5555'
def adb(*args, timeout=60):
    p=subprocess.run([ADB,'-s',DEVICE,*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    return {'code':p.returncode,'out':p.stdout.strip(),'err':p.stderr.strip()}
def shell(c): return adb('shell',c)
def run(script,tag):
    keys=['vendor.xgimi.system.debug.cmd','vendor.xgimi.system.debugserver']
    before={k:shell('getprop '+k)['out'] for k in keys}
    if before[keys[0]] or before[keys[1]] not in ('','0'): raise RuntimeError('Diagnostic service already configured')
    local=OUT/(tag+'.sh')
    remote='/data/local/tmp/beam-'+tag
    local.write_text('#!/system/bin/sh\numask 022\n(\n'+script+'\n) > '+remote+'.log 2>&1\necho $? > '+remote+'.done\n',encoding='utf-8',newline='\n')
    result={'before':before,'push':adb('push',str(local),remote+'.sh')}
    if result['push']['code']: raise RuntimeError(result)
    try:
        for k,v in zip(keys,['/system/bin/sh '+remote+'.sh','1']):
            r=shell('setprop '+k+' '+shlex.quote(v));result[k]=r
            if r['code']: raise RuntimeError(r)
        for _ in range(90):
            if shell('test -f '+remote+'.done')['code']==0: break
            time.sleep(1)
        else: raise RuntimeError('Root command did not finish')
        result['exit']=shell('cat '+remote+'.done')['out']
        result['log']=shell('cat '+remote+'.log')
    finally:
        result['restore']={k:shell('setprop '+k+' '+shlex.quote(before[k])) for k in reversed(keys)}
        result['cleanup']=shell('rm -f '+remote+'.sh '+remote+'.log '+remote+'.done')
        (OUT/(tag+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    text=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
    print(json.dumps(run(text,sys.argv[2]),ensure_ascii=False,indent=2))
