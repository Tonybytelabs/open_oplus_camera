# Blob dependencies
PRODUCT_PACKAGES += \
    android.hardware.graphics.common-V3-ndk.vendor

# Dexpreopt
PRODUCT_DEXPREOPT_SPEED_APPS += \
    OplusCamera

# Framework
PRODUCT_BOOT_JARS += \
    oplus-support-wrapper

# Init
PRODUCT_PACKAGES += \
    init.oplus.camera.rc

# Permissions
PRODUCT_PACKAGES += \
    OplusPermissions

PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/default-permissions/oplus_scanner_default_grant_permissions_list.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/default-permissions/oplus_scanner_default_grant_permissions_list.xml \
    $(LOCAL_PATH)/configs/permissions/oplus_google_lens_config.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/oplus_google_lens_config.xml \
    $(LOCAL_PATH)/configs/permissions/privapp-permissions-oplus.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp-permissions-oplus.xml \
    $(LOCAL_PATH)/configs/sysconfig/hiddenapi-package-oplus-whitelist.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/sysconfig/hiddenapi-package-oplus-whitelist.xml

# Properties
PRODUCT_PRODUCT_PROPERTIES += \
    persist.sys.oplus.anim_level=2 \
    persist.vendor.camera.privapp.list=com.oplus.camera \
    ro.com.google.lens.oem_camera_package=com.oplus.camera \
    ro.com.google.lens.oem_image_package=com.oneplus.gallery


# Photo
$(call soong_config_set,camera,package_name,com.oplus.packageName)

# Video
$(call soong_config_set_bool,camera,override_format_from_reserved,true)

# Inherit the extracted blobs (open_oplus_camera_blobs, made by extract-files.py)
$(call inherit-product, vendor/oplus/camera-blobs/camera-blobs-vendor.mk)

# SEpolicy
include vendor/oplus/camera/sepolicy/SEPolicy.mk
