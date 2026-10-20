package com.oplus.gallery.aosp;

import android.app.Activity;
import android.content.Intent;
import android.util.Log;

import com.oplus.gallery.sharepage.viewmodel.ShareInnerViewModel;

import kotlin.Unit;
import kotlin.jvm.functions.Function1;

/** "More" in the share sheet opens Android's share sheet with the gallery's prepared share intent. */
public final class AospShare implements Function1<Object, Object> {

    private static final String TAG = "AospShare";

    private final Activity mActivity;
    private final ShareInnerViewModel mViewModel;

    private AospShare(Activity activity, ShareInnerViewModel viewModel) {
        mActivity = activity;
        mViewModel = viewModel;
    }

    /** Prepares the selected items the way an app tap does (D0), then shows the chooser. */
    public static void more(Activity activity, ShareInnerViewModel viewModel) {
        if (activity == null || viewModel == null) {
            return;
        }
        viewModel.D0(activity, ShareInnerViewModel.DownloadTriggerType.TRIGGER_RESOLVE_INFO,
                new AospShare(activity, viewModel));
    }

    @Override
    public Object invoke(Object selectedItems) {
        Intent prepared = mViewModel.w0;
        if (selectedItems == null || prepared == null) {
            return Unit.INSTANCE;
        }
        // G0 sets a component on w0 for split-screen shares; the chooser needs the bare intent.
        Intent send = new Intent(prepared);
        send.setComponent(null);
        send.setPackage(null);
        try {
            mActivity.startActivity(Intent.createChooser(send, null));
        } catch (RuntimeException e) {
            Log.w(TAG, "cannot start the chooser", e);
        }
        return Unit.INSTANCE;
    }
}
