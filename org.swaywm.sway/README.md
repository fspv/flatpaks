# Test run

Run `./test.sh` to test that sway starts up. It should be done after flatpak is successfully built and installed.

# Known issues

1. Check if drm backend is enabled after build. Common problem is the incorrect location of hwdata pnp.ids, which is fixed by patching meson.build of a corresponding targer
