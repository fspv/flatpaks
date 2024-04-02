# Test run

```sh
export QT_QPA_PLATFORM=wayland  
export QT_QPA_PLATFORMTHEME=gtk3
export ECORE_EVAS_ENGINE=wayland_egl
export ELM_ENGINE=wayland_egl         
export SDL_VIDEODRIVER=wayland          
export _JAVA_AWT_WM_NONREPARENTING=1                                                                 
export MOZ_ENABLE_WAYLAND=1                     

export GTK_IM_MODULE=ibus             
export QT_IM_MODULE=ibus                          
export XMODIFIERS=@im=ibus      

export XDG_CURRENT_DESKTOP=sway                                                                      
APP=$(flatpak info -l org.swaywm.sway)/files
export LD_LIBRARY_PATH="${APP}/lib:${LD_LIBRARY_PATH}"
export PATH="${APP}/bin:${PATH}"
echo "MANDATORY_MANPATH ${APP}/share/man" > ${HOME}/.manpath
export WLR_XWAYLAND=${APP}/bin/Xwayland
export LIBINPUT_QUIRKS_DIR=${APP}/share/libinput

sway --verbose
```

# Known issues

1. Check if drm backend is enabled after build. Common problem is the incorrect location of hwdata pnp.ids, which is fixed by patching meson.build of a corresponding targer
