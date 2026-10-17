package mm;

import android.media.MediaCodec;
import android.media.MediaFormat;
import java.nio.ByteBuffer;

// Dolby Vision profile 8.4 for CameraMediaCodec (mm.i): this phone has no video/dolby-vision encoder, so the HEVC
// encoder records HLG Main 10 and the muxer track is declared Dolby Vision (the framework writes dvvC from profile and
// level) with one RPU NAL appended to every frame. Generated into smali by patch_app7.py dolby; do not edit the smali.
public final class DV implements Runnable {
    // ponytail: one fixed RPU (from libdolbyencoderprocessor on this phone, tools/dolby/dvtest), same for every frame.
    // Upgrade path: per-frame RPU from the processor through JNI.
    static final byte[] RPU = {0, 0, 0, 1, 124, 1, 25, 8, 9, 8, 64, 97, 48, 0, 16, 32, 101, 6, -26, 15, -60, 83, -103, 0, 64, 2, 80, 118, 0, 127, -16, 3, 19, -23, -7, -68, 124, 93, -45, 25, -54, 19, 23, -74, -97, -30, -17, 5, 60, -112, -80, -82, -23, -77, -22, 80, 106, 95, 69, -42, -127, -15, -120, 102, -86, 5, -110, -71, -8, 69, -118, 46, -72, -54, -7, -50, -68, 45, 40, -52, 100, 96, -62, -30, -116, 89, 48, 40, 126, -27, 81, -125, 96, -26, 82, 83, -30, 57, -13, 20, 92, 48, -84, -42, -21, 60, -12, -13, 55, 37, -37, 117, 82, 46, -88, -124, 52, -39, -5, -121, 14, 93, 60, 127, -107, -99, 0, -85, -81, 11, -128, 113, -128, 8, 92, -82, -83, 101, -34, -22, -14, 104, -115, 47, -114, 74, -35, 94, -107, 121, -51, 40, -6, -48, -126, -99, -95, -123, -15, 65, -107, -44, -97, -62, 46, 7, 86, -94, -117, 12, -128, 4, 65, 8, 18, 79, 94, 12, -127, -128, -36, -111, 10, 93, 30, -40, 35, -6, -83, -95, -52, 20, 32, 73, -114, -66, 68, -15, -124, -102, 46, -17, 81, -79, -15, 60, -42, 13, 105, -37, 48, 37, 43, 78, 35, 84, 39, 104, 89, -12, 52, 79, 112, 43, -4, -125, -42, -109, 16, 56, 30, 19, -10, 47, -80, 89, -87, 29, -57, 117, 116, -100, 98, 49, 117, 78, 74, -52, 0, 0, 107, -44, 74, -51, -13, -7, -42, 56, 74, -52, -119, -108, 0, 0, 3, 2, 0, 0, 3, 0, 16, 0, 0, 3, 0, 16, 0, 0, 3, 0, 56, 108, 68, -122, 3, 12, 20, -68, 97, 28, 10, 40, 0, 0, 3, 3, 76, 124, -75, -1, -2, 0, 0, 3, 0, 0, 3, 0, 0, 3, 0, 0, -64, 64, -5, 1, -62, -94, 0, 48, 8, 0, 95, -37, 54, -128, -128, 80, 0, 0, 3, 0, 0, 3, 0, 0, 3, 2, 2, 54, -127, -81, 9, 65, 32, 5, 11, 4, 0, 8, 0, 127, -64, 0, 66, -62, 63, -26, 106, 0, 34, -126, 0, 32, 2, 0, 5, -124, 10, 64, 4, 0, 59, 100, 0, 64, 4, 0, 24, 43, -1, -100, 0, 0, 8, -63, 66, -108, -32, 0, 0, 70, 3, -128, 8, 0, -128, 0, 114, -118, 123, -17, -128};

    static boolean dv(i r) { return r.x0 != null && r.x0.f == 7; }

    // Dolby Vision is offered where the HAL has real HLG (patch_sdk.py halHlg): 1080p 30, and 1080p / 4K at 60,
    // and only with "10-bit color" on and the item in its Dolby Vision state (dv.support reads false otherwise).
    public static boolean want(om.t0 m) {
        if (!m.Se() || !om.t0.tenBitPref() || !com.oplus.camera.configure.CameraConfig.getConfigBooleanValue("com.oplus.feature.video.dv.support")) return false;
        String s = m.h7();
        boolean hd = "video_size_1080p".equals(s);
        return m.Qa() == 30 ? hd : m.Qa() == 60 && (hd || "video_size_4kuhd".equals(s));
    }

    // The Video HDR item has three states with "10-bit color" on: off, HDR (10-bit sensor HDR, the app's "HDR video"
    // side) and Dolby Vision. dolby = the third one.
    // ponytail: not persisted; a new process starts at HDR. Persist it if Dolby Vision should survive a restart.
    static volatile boolean dolby;
    static java.lang.ref.WeakReference<android.app.Activity> act;

    // For CameraConfig.getConfigBooleanValue (patch_app7.py dolby): true = the app takes its Dolby Vision side.
    // "10-bit color" and the Dolby state; true if the setting cannot be read yet.
    public static boolean tenBit() {
        try { return om.t0.tenBitPref() && dolby; } catch (Throwable t) { return true; }
    }

    // For CameraMenuOption.setOptionValue (gq.h.Y, patch_app7.py dolby), a tap on the item: returns the value to set.
    // off -> on (HDR) -> on (Dolby Vision) -> off.
    public static String click(String key, String v, boolean user) {
        try {
            if (!user || !"key_video_dolby".equals(key) || !om.t0.tenBitPref()) return v;
            if ("on".equals(v)) { if (dolby) { dolby = false; rebuild(); } return v; }
            if (!"off".equals(v)) return v;
            dolby = !dolby;
            rebuild();
            return dolby ? "on" : v;
        } catch (Throwable t) { return v; }
    }

    // ponytail: the item's label is built once per activity, so a state change recreates the activity (one blink).
    // Upgrade path: retitle the menu item in place.
    static void rebuild() {
        last = tenBit();
        new android.os.Handler(android.os.Looper.getMainLooper()).post(new DV());
    }

    public void run() {
        android.app.Activity a = act == null ? null : act.get();
        if (a != null && !a.isFinishing()) a.recreate();
    }

    // The Video menu (Dolby Vision or HDR video item) is built once per activity. Called at the start of the camera
    // activity's onResume: when "10-bit color" changed while the activity was paused (Settings), rebuild the activity.
    static boolean seen, last;
    public static void resume(android.app.Activity a) {
        act = new java.lang.ref.WeakReference<>(a);
        boolean t = tenBit();
        if (seen && t != last) { last = t; a.recreate(); return; }
        seen = true; last = t;
    }

    public static void in(i r) {                      // encoder input format: HEVC Main 10, BT.2020 HLG limited
        MediaFormat f = r.h0;
        if (f == null || !dv(r)) return;
        f.setInteger("profile", 2);
        f.removeKey("level");
        f.setInteger("color-standard", 6);
        f.setInteger("color-transfer", 7);
        f.setInteger("color-range", 2);
    }

    public static void out(i r, MediaFormat f) {      // muxer track format
        if (!dv(r) || !"video/hevc".equals(f.getString("mime"))) return;
        f.setString("mime", "video/dolby-vision");
        f.setInteger("profile", 256);
        f.setInteger("level", r.g1);
    }

    public static ByteBuffer sample(i r, int track, ByteBuffer b, MediaCodec.BufferInfo n) {
        if (!dv(r) || track != r.z || (n.flags & MediaCodec.BUFFER_FLAG_CODEC_CONFIG) != 0 || n.size <= 0) return b;
        ByteBuffer o = ByteBuffer.allocateDirect(n.size + RPU.length);
        ByteBuffer s = b.duplicate();
        s.limit(n.offset + n.size).position(n.offset);
        o.put(s).put(RPU).flip();
        n.set(0, o.limit(), n.presentationTimeUs, n.flags);
        return o;
    }
}
