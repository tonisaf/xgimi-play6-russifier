package com.beam.remote;

import java.util.*;

public class RegistryTest {
    static class Port implements KeyRegistry.Port {
        List<String> events = new ArrayList<>();
        boolean failSecond, failRelease, deny;
        public boolean add(long key) throws Exception {
            events.add("add"+key);
            if (key==2119 && failSecond) { failSecond=false; throw new Exception("lost reply"); }
            return !deny;
        }
        public void remove(long key) throws Exception {
            events.add("remove"+key);
            if (key==2118 && failRelease) { failRelease=false; throw new Exception("release failed"); }
        }
    }
    static Set<Long> keys(long... keys) { Set<Long> result=new TreeSet<>(); for(long k:keys)result.add(k); return result; }
    static void require(boolean value) { if(!value)throw new AssertionError(); }
    public static void main(String[] args) throws Exception {
        Port p=new Port(); KeyRegistry r=new KeyRegistry(p);
        r.sync(keys(2118,2119)); int count=p.events.size(); r.sync(keys(2118,2119));require(p.events.size()==count);
        r.sync(keys(2119));require(p.events.contains("remove2118"));r.release();

        p=new Port();r=new KeyRegistry(p);p.failSecond=true;
        try {r.sync(keys(2118,2119));throw new AssertionError();}catch(Exception expected){}
        r.sync(keys(2118,2119));
        require(Collections.frequency(p.events,"add2118")==1);
        require(p.events.indexOf("remove2119") < p.events.lastIndexOf("add2119"));
        r.release();require(p.events.contains("remove2118"));

        p=new Port();r=new KeyRegistry(p);r.sync(keys(2118));p.failRelease=true;
        try {r.release();throw new AssertionError();}catch(Exception expected){}
        r.release();require(Collections.frequency(p.events,"remove2118")==2);

        p=new Port();r=new KeyRegistry(p);p.deny=true;require(!r.sync(keys(2118)));r.release();
        require(!p.events.contains("remove2118")); // Never unregister somebody else's denied key.

        p=new Port();r=new KeyRegistry(p);r.sync(keys(2118));r.serverDied();r.release();
        require(!p.events.contains("remove2118"));
        System.out.println("Registry: repeat sync, partial failure, uncertain reply, failed cleanup, denial and death passed");
    }
}
