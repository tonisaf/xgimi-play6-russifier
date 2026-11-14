package com.beam.remote;

enum RemoteButton {
    YOUKU(2118, "Youku / CIBN", "button0"),
    TENCENT(2119, "Tencent TV", "button1"),
    IQIYI(2120, "iQIYI", "button2"),
    MANGO(2121, "Mango TV", "button3"),
    AMBIENT(2116, "Ambient", "ambient"),
    SOURCE(2115, "Source", "source");

    static final RemoteButton[] ALL = values();
    final long code;
    final String label;
    final String preference;

    RemoteButton(long code, String label, String preference) {
        this.code = code;
        this.label = label;
        this.preference = preference;
    }

    static RemoteButton fromCode(long code) {
        for (RemoteButton button : ALL) {
            if (button.code == code) return button;
        }
        return null;
    }
}
