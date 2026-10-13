package com.beam.remote;

import java.util.HashSet;
import java.util.Set;

/** Worker-thread ledger, including registrations whose reply was lost. */
final class KeyRegistry {
    interface Port {
        boolean add(long key) throws Exception;
        void remove(long key) throws Exception;
    }
    private final Port port;
    private final Set<Long> owned = new HashSet<>();
    private final Set<Long> uncertain = new HashSet<>();
    KeyRegistry(Port port) { this.port = port; }

    boolean sync(Set<Long> wanted) throws Exception {
        for (long key : new HashSet<>(uncertain)) {
            port.remove(key);
            uncertain.remove(key);
            owned.remove(key);
        }
        for (long key : new HashSet<>(owned)) {
            if (!wanted.contains(key)) {
                port.remove(key);
                owned.remove(key);
            }
        }
        boolean complete = true;
        for (long key : wanted) {
            if (owned.contains(key)) continue;
            uncertain.add(key);
            boolean accepted = port.add(key);
            uncertain.remove(key);
            if (accepted) owned.add(key);
            else complete = false; // A denied key is not ours to unregister.
        }
        return complete;
    }

    void release() throws Exception {
        Set<Long> pending = new HashSet<>(owned);
        pending.addAll(uncertain);
        Exception failure = null;
        for (long key : pending) {
            try {
                port.remove(key);
                owned.remove(key);
                uncertain.remove(key);
            } catch (Exception error) { failure = error; }
        }
        if (failure != null) throw failure;
    }
    void serverDied() { owned.clear(); uncertain.clear(); }
}

