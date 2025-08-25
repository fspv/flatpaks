# Build
```sh
sudo apt-get install flatpak-builder
```

or
```sh
nix-shell -p flatpak-builder
```

And then run this

```sh
flatpak install org.freedesktop.Sdk
git config --global protocol.file.allow always

./build.sh org.swaywm.sway
```

# Dependency versions upgrades
To automatically fetch the latest versions of all the dependencies, please run:

```sh
virtualenv .venv
.venv/bin/python check_versions.py org.swaywm.sway/org.swaywm.sway.yaml
```

It is not very precise, for example, it can tell that `xcb-util-0.4.1` is different from `xcb-util-0.4.1-gitlab`. Also it doesn't work for some types of repos. But it is good enough as a starting point.

Keep in mind that you don't always want to update to the absolute latest version, as they might be incompatible. But in most of the cases it is a good idea.

# Debug

To list all the files, that go into the final package you can do this

```sh
find "$(flatpak info --show-location org.swaywm.sway)" -type f | sed "s|^$(flatpak info --show-location org.swaywm.sway)/||"

```
