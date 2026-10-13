package com.beam.russifier.boot;

/** State checks shared by startup and the theme watcher; no Android dependencies. */
final class RestorePolicy {
    static final int NONE=0, SKIN=1, FULL=2;
    static int decide(boolean manual, String boot, String savedBoot, String hash,
                      String savedHash, String skin, String expectedSkin) {
        return decide(manual, boot, savedBoot, hash, savedHash, skin, expectedSkin, "", "");
    }
    /** A restarted zygote (same kernel boot) drops the namespace mounts, so a new zygote pid also needs a full restore. */
    static int decide(boolean manual, String boot, String savedBoot, String hash,
                      String savedHash, String skin, String expectedSkin, String zygote, String savedZygote) {
        if (manual || boot.isEmpty() || !boot.equals(savedBoot) || !hash.equals(savedHash)) return FULL;
        if (!zygote.isEmpty() && !zygote.equals(savedZygote)) return FULL;
        return skin.equals(expectedSkin) ? NONE : SKIN;
    }
}
