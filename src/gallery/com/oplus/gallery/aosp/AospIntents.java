package com.oplus.gallery.aosp;

import android.content.Intent;
import android.net.Uri;
import android.os.Environment;
import android.provider.DocumentsContract;

import java.io.File;

/** Turns intents that only OPLUS system apps answer into ones a stock Android device can resolve. */
public final class AospIntents {

    private static final String AUTHORITY = "com.android.externalstorage.documents";

    private AospIntents() {
    }

    public static Intent adapt(Intent intent) {
        if (intent == null) {
            return null;
        }
        String action = intent.getAction();
        if ("oplus.intent.action.filemanager.BROWSER_FILE".equals(action)
                || "oppo.filemanager.intent.action.BROWSER_FILE".equals(action)) {
            Intent folder = browseFolder(intent.getStringExtra("CurrentDir"));
            return folder != null ? folder : intent;
        }
        return intent;
    }

    /** "Open with" for a folder of shared storage; null when the path is not on the primary volume. */
    private static Intent browseFolder(String dir) {
        if (dir == null) {
            return null;
        }
        // The details panel passes the file itself, the "saved to" snackbar its folder.
        File file = new File(dir);
        if (file.isFile() && file.getParent() != null) {
            dir = file.getParent();
        }
        String root = Environment.getExternalStorageDirectory().getPath();
        if (!dir.equals(root) && !dir.startsWith(root + "/")) {
            return null;
        }
        String relative = dir.length() > root.length() ? dir.substring(root.length() + 1) : "";
        while (relative.endsWith("/")) {
            relative = relative.substring(0, relative.length() - 1);
        }
        Uri uri = DocumentsContract.buildDocumentUri(AUTHORITY, "primary:" + relative);
        Intent view = new Intent(Intent.ACTION_VIEW);
        view.setDataAndType(uri, DocumentsContract.Document.MIME_TYPE_DIR);
        return Intent.createChooser(view, null);
    }
}
