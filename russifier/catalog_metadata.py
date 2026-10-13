"""Translate catalog presentation fields; retain media URLs and user selections."""
from pathlib import Path
import json,sqlite3
from transforms import parse_catalog,fields,check_db

TEXTS=json.loads((Path(__file__).resolve().parent/'payload/catalog-texts.json').read_text(encoding='utf-8'))
DB_FIELDS={'groups':['tips','second_groups'], 'screen_saver':['name','second_group']}
JAVA_FIELDS={'GroupBean':{'tips','secondGroups'},
             'Screensaver':{'name','secondGroup','groupTips','groupName','description','bubbleContent','buttonName'}}

def translated(value):
    if value in TEXTS:return TEXTS[value]
    if value and value.startswith('['):
        try:items=json.loads(value)
        except ValueError:return value
        if isinstance(items,list) and all(isinstance(v,str) for v in items):
            result=[TEXTS.get(v,v) for v in items]
            if result!=items:return json.dumps(result,ensure_ascii=False,separators=(',',':'))
    return value

def db_snapshot(db):
    result={}
    for table,cols in DB_FIELDS.items():
        for row in db.execute('select _id,'+','.join(cols)+' from '+table):
            for col,val in zip(cols,row[1:]):result[(table,row[0],col)]=val
    return result

def apply_db(path):
    db=sqlite3.connect(path)
    before=db_snapshot(db)
    # Freeze every table so changes to IDs, URLs, chosen files or settings fail.
    snapshots={}
    for (table,) in db.execute("select name from sqlite_master where type='table'"):
        cols=[x[1] for x in db.execute('pragma table_info("'+table+'")')]
        snapshots[table]=(cols,db.execute('select * from "'+table+'"').fetchall())
    changes={}
    for (table,ident,col),value in before.items():
        target=translated(value) if isinstance(value,str) else value
        if target!=value:
            db.execute('update '+table+' set '+col+'=? where _id=?',(target,ident))
            changes[(table,ident,col)]=target
    check_db(db)
    for table,(cols,rows) in snapshots.items():
        current=db.execute('select * from "'+table+'"').fetchall()
        expected=[]
        for row in rows:
            ident=row[cols.index('_id')] if '_id' in cols else None
            expected.append(tuple(changes.get((table,ident,col),val) for col,val in zip(cols,row)))
        if current!=expected:raise RuntimeError('Unrelated catalog database data changed: '+table)
    db.commit();db.close()
    return len(changes)

def restore_db_metadata(path,baseline,installed):
    now=sqlite3.connect(path);old=sqlite3.connect(baseline);ours=sqlite3.connect(installed)
    original=db_snapshot(old);applied=db_snapshot(ours);present=db_snapshot(now)
    count=0
    for key,value in original.items():
        if key in applied and applied[key]!=value and present.get(key)==applied[key]:
            table,ident,col=key
            now.execute('update '+table+' set '+col+'=? where _id=?',(value,ident));count+=1
    check_db(now);now.commit()
    for db in (now,old,ours):db.close()
    return count

def entries(parser,root):
    """Stable field identities, including repeated references to the same saver."""
    result={};uses={};seen=set();occurrences={}
    def visit(obj,selector=None):
        handle=getattr(obj,'handle',None)
        if handle in parser.strings:
            if selector is not None:
                index=occurrences.get(selector,0)
                occurrences[selector]=index+1
                selector=(*selector,index)
            uses.setdefault(handle,set()).add(selector)
            if selector is not None:result.setdefault(selector,[]).append(obj)
            return
        if id(obj) in seen:return
        seen.add(id(obj))
        if isinstance(obj,(list,tuple)):
            for i,v in enumerate(obj):visit(v,(*selector,i) if selector else None)
        elif hasattr(obj,'field_data'):
            vals=fields(obj);class_name=obj.classdesc.name
            short=class_name.rsplit('$',1)[-1]
            allowed=JAVA_FIELDS.get(short,set()) if class_name.startswith('com.xgimi.atmosphere.base.data.bean.ScreensaverUiDataBean$') else set()
            ident=str(vals['id']) if vals.get('id') is not None else ''
            if not ident and short=='Screensaver' and vals.get('groupId') is not None:
                ident='category:'+str(vals['groupId'])+':'+str(vals.get('uiType'))
            for name,value in vals.items():
                visit(value,(short,ident,name) if name in allowed and ident else None)
    visit(root)
    return result,uses

def values_of(entries):
    result={}
    for key,objects in entries.items():
        vals={str(x) for x in objects}
        if len(vals)!=1:raise RuntimeError('Conflicting catalog fields: '+str(key))
        result[key]=next(iter(vals))
    return result

def write_catalog(path,targets):
    path=Path(path);raw=path.read_bytes();parser,root=parse_catalog(raw)
    data,uses=entries(parser,root);current=values_of(data);changes={}
    for key,target in targets.items():
        if key not in data or current[key]==target:continue
        for obj in data[key]:
            handle=obj.handle
            if None in uses[handle] or any(targets.get(k,current.get(k))!=target for k in uses[handle]):
                raise RuntimeError('Shared string also used outside translated fields')
            start,end,old,code=parser.strings[handle]
            encoded=target.encode('utf-8')
            if code!=0x74 or len(encoded)>65535:raise RuntimeError('Unsupported metadata encoding')
            changes[handle]=(start,end,len(encoded).to_bytes(2,'big')+encoded,target)
    result=raw
    for start,end,value,target in sorted(changes.values(),reverse=True):result=result[:start]+value+result[end:]
    check,after=parse_catalog(result)
    if parser.strings.keys()!=check.strings.keys():raise RuntimeError('Catalog handles changed')
    for handle,record in parser.strings.items():
        expected=changes[handle][3] if handle in changes else record[2]
        if check.strings[handle][2]!=expected:raise RuntimeError('Unrelated catalog string changed')
    actual=values_of(entries(check,after)[0])
    for key,value in current.items():
        if actual[key]!=targets.get(key,value):raise RuntimeError('Catalog field did not match translation')
    path.write_bytes(result)
    return len(changes)

def apply_catalog(path):
    parser,root=parse_catalog(Path(path).read_bytes())
    original=values_of(entries(parser,root)[0])
    targets={key:translated(val) for key,val in original.items()}
    return write_catalog(path,targets)

def restore_catalog_metadata(path,baseline,installed):
    def read(p):
        parser,root=parse_catalog(Path(p).read_bytes());return values_of(entries(parser,root)[0])
    old,ours,now=read(baseline),read(installed),read(path)
    targets={k:v for k,v in old.items() if k in ours and v!=ours[k] and now.get(k)==ours[k]}
    return write_catalog(path,targets)
