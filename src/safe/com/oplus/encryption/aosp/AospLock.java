package com.oplus.encryption.aosp;

import android.app.KeyguardManager;
import android.app.admin.DevicePolicyManager;
import android.content.Context;
import android.content.Intent;

/**
 * Private Safe unlocks with the "privacy password" of OPLUS Settings. That does not exist on AOSP, so the
 * device's own screen lock takes its place: both report success with RESULT_OK.
 */
public final class AospLock {

    private static final String CONFIRM = "oplus.intent.action.settings.PRIVACY_PWD_CONFIRM";
    private static final String CHOOSE = "com.oplus.settings.privacy.ChooseGenericPrivacy";

    private AospLock() {
    }

    /** Stands in for the query of oplus.provider.settings.PrivacyStateProvider. */
    public static boolean hasLock(Context context) {
        if (context == null) {
            return false;
        }
        KeyguardManager km = context.getSystemService(KeyguardManager.class);
        return km != null && km.isDeviceSecure();
    }

    /** Packages Private Safe insists on before it offers to move a file back out of the safe. */
    public static boolean isStandIn(String packageName) {
        return "com.oneplus.filemanager".equals(packageName);
    }

    public static Intent adapt(Context context, Intent intent) {
        if (context == null || intent == null) {
            return intent;
        }
        if (CONFIRM.equals(intent.getAction())) {
            KeyguardManager km = context.getSystemService(KeyguardManager.class);
            Intent confirm = km != null ? km.createConfirmDeviceCredentialIntent(null, null) : null;
            return confirm != null ? confirm : intent;
        }
        if (intent.getComponent() != null && CHOOSE.equals(intent.getComponent().getClassName())) {
            return new Intent(DevicePolicyManager.ACTION_SET_NEW_PASSWORD);
        }
        return intent;
    }
}
