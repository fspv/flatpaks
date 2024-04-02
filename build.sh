#!/bin/bash

SRC_DIR=$1
FLATPAK_BUILD_DIR=flatpak_build/
APPIMAGE_BUILD_DIR=appimage_build/
APPIMAGE_URL=https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage

function build_flatpak() {
    DIR=$1
    mkdir -p ${DIR}
    flatpak-builder \
        --install \
        -v \
        --user \
        --force-clean \
        --state-dir=${DIR}/flatpak-builder \
        --repo=${DIR}/flatpak-repo \
        ${DIR}/flatpak-target ${SRC_DIR}/${SRC_DIR}.yaml
    flatpak build-bundle ${DIR}/flatpak-repo sway.flatpak org.swaywm.sway
}

function build_appimage() {
    DIR=$1
    mkdir -p ${DIR}

    TMP_DIR=$(mktemp -d)
    wget ${APPIMAGE_URL} -O ${TMP_DIR}/appimagetool
    chmod +x ${TMP_DIR}/appimagetool

    ${TMP_DIR}/appimagetool $DIR

    rm -rf ${TMP_DIR}
}

build_flatpak ${FLATPAK_BUILD_DIR}

# rm -rf ${APPIMAGE_BUILD_DIR}
# cp -R ${FLATPAK_BUILD_DIR}/flatpak-target/files ${APPIMAGE_BUILD_DIR}
# cp ${SRC_DIR}/*.desktop ${APPIMAGE_BUILD_DIR}
# cp ${SRC_DIR}/*.svg ${APPIMAGE_BUILD_DIR}
# ln -sf $(cat ${SRC_DIR}/app) ${APPIMAGE_BUILD_DIR}/AppRun
# ln -sf .. ${APPIMAGE_BUILD_DIR}/app

# build_appimage ${APPIMAGE_BUILD_DIR}
