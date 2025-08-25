#!/bin/sh

APP=$(flatpak info -l org.swaywm.sway)/files; LD_LIBRARY_PATH="${APP}/lib:${LD_LIBRARY_PATH}" PATH="${APP}/bin:${PATH}" WLR_XWAYLAND=${APP}/bin/Xwayland LIBINPUT_QUIRKS_DIR=${APP}/share/libinput sway --version
