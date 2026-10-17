# Join the blobs extract-files.py split into 20 MiB parts (GitHub refuses files over 100 MB)
for parts in vendor/oplus/camera-blobs/proprietary/system_ext/priv-app/*/*.apk.part00; do
    [ -f "$parts" ] || continue
    cat "${parts%.part00}".part* > "${parts%.part00}"
done
