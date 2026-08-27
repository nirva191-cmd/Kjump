[title]
kjum
[package]
package.name = kjum
package.domain = org.espacio
source.include_exts = py,png,jpg,kv,atlas,json
source.include_dir = .
source.exclude_exts = spec
source.exclude_dirs = tests bin venv
version = 1.0
requirements = python3,pygame,numpy
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.sdk = 30
android.ndk = 25b
android.accept_sdk_license = True
