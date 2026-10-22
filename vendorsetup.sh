# Join the blobs extract-files.py split into 20 MiB parts (GitHub refuses files over 100 MB).
# Covers every split APK under camera-blobs (app, priv-app, or any other location).
for parts in $(find vendor/oplus/camera-blobs -name '*.apk.part00' 2>/dev/null); do
    cat "${parts%.part00}".part* > "${parts%.part00}"
done
