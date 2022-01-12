## [ci/environment.yml](../ci/environment.yml)

Connected with creating the testing image for CI

### [environment](https://github.com/trezor/trezor-firmware/blob/master/ci/environment.yml#L7)
Environment job builds the `ci/Dockerfile` and pushes the built docker image
into our GitLab registry. Since modifications of this Dockerfile are very rare
this is a _manual_ job which needs to be triggered on GitLab.
Almost all CI jobs run inside this docker image.

---
## [ci/prebuild.yml](../ci/prebuild.yml)

### [style prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L10)
Missing description

### [common prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L18)
Missing description

### [gen prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L24)
Missing description

### [editor prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L30)
Missing description

### [yaml prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L36)
Missing description

### [release commit messages prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L42)
Missing description

### [changelog prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L57)
Missing description

---
## [ci/build.yml](../ci/build.yml)

All builds are published as artifacts so they can be downloaded and used.

### [core fw regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L20)
Build of Core into firmware. Regular version.
**Are you looking for Trezor T firmware build? This is most likely it.**

### [core fw regular debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L41)
Build of Core into firmware with enabled _debug_ mode. In debug mode you can
upload mnemonic seed, use debug link etc. which enables device tests. Storage
on the device gets wiped on every start in this firmware.

### [core fw btconly build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L55)
Build of Core into firmware. Bitcoin-only version.

### [core fw btconly debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L72)
Missing description

### [core fw btconly t1 build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L95)
Missing description

### [core unix regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L113)
Non-frozen emulator build. This means you still need Python files
present which get interpreted.

### [core unix frozen regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L128)
Build of Core into UNIX emulator. Something you can run on your laptop.
Frozen version. That means you do not need any other files to run it,
it is just a single binary file that you can execute directly.

### [core unix frozen btconly debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L145)
Build of Core into UNIX emulator. Something you can run on your laptop.
Frozen version. That means you do not need any other files to run it,
it is just a single binary file that you can execute directly.
See [Emulator](../core/emulator/index.md) for more info.
Debug mode enabled, Bitcoin-only version.

### [core unix frozen debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L165)
Build of Core into UNIX emulator. Something you can run on your laptop.
Frozen version. That means you do not need any other files to run it,
it is just a single binary file that you can execute directly.
**Are you looking for a Trezor T emulator? This is most likely it.**

### [core unix frozen debug build arm](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L178)
Missing description

### [core unix frozen btconly debug t1 build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L199)
Missing description

### [core macos frozen regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L214)
Missing description

### [crypto build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L239)
Build of our cryptographic library, which is then incorporated into the other builds.

### [legacy fw regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L262)
Missing description

### [legacy fw regular debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L278)
Missing description

### [legacy fw btconly build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L295)
Missing description

### [legacy fw btconly debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L314)
Missing description

### [legacy emu regular debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L335)
Regular version (not only Bitcoin) of above.
**Are you looking for a Trezor One emulator? This is most likely it.**

### [legacy emu regular debug build arm](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L350)
Missing description

### [legacy emu btconly debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L375)
Build of Legacy into UNIX emulator. Use keyboard arrows to emulate button presses.
Bitcoin-only version.

---
## [ci/test.yml](../ci/test.yml)

### [core unit test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L12)
Missing description

### [core unit test t1](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L22)
Missing description

### [core device ui test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L34)
UI tests for Core. See artifacts for a comprehensive report of UI.
See [tests/ui-tests](../tests/ui-tests.md) for more info.

### [core device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L59)
Missing description

### [core btconly device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L80)
Missing description

### [core monero test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L100)
Missing description

### [core u2f test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L119)
Missing description

### [core fido2 test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L138)
Missing description

### [core click test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L161)
Missing description

### [core upgrade test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L178)
Missing description

### [core persistence test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L197)
Missing description

### [crypto test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L216)
Missing description

### [legacy test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L244)
Missing description

### [legacy btconly test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L262)
Missing description

### [legacy upgrade test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L283)
Missing description

### [python test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L305)
Missing description

### [storage test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L334)
Missing description

### [core unix memory profiler](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L357)
Missing description

### [connect test core](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L381)
Missing description

---
## [ci/test-hw.yml](../ci/test-hw.yml)

### [hardware core regular device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L25)
[Device tests](../tests/device-tests.md) that run against an actual physical Trezor T.
The device needs to have special bootloader, found in `core/embed/bootloader_ci`, that
makes it possible to flash firmware without confirmation on the touchscreen.

All hardware tests are run nightly on the `master` branch, as well as on push to branches
with whitelisted prefix. If you want hardware tests ran on your branch, make sure its
name starts with `hw/`.

Currently it's not possible to run all regular TT tests without getting into
a state where the micropython heap is too fragmented and allocations fail
(often manifesting as a stuck test case). For that reason some tests are
skipped.
See also: https://github.com/trezor/trezor-firmware/issues/1371

### [hardware core btconly device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L54)
Also device tests on physical Trezor T but with Bitcoin-only firmware.

### [hardware core monero test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L83)
Missing description

### [hardware legacy regular device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L113)
[Device tests](../tests/device-tests.md) executed on physical Trezor 1.
This works thanks to [tpmb](https://github.com/mmahut/tpmb), which is a small arduino
device capable of pushing an actual buttons on the device.

### [hardware legacy btconly device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L137)
Also device tests on physical Trezor 1 but with Bitcoin-only firmware.

---
## [ci/posttest.yml](../ci/posttest.yml)

### [core unix coverage posttest](https://github.com/trezor/trezor-firmware/blob/master/ci/posttest.yml#L10)
Missing description

### [core unix ui changes](https://github.com/trezor/trezor-firmware/blob/master/ci/posttest.yml#L31)
Missing description

---
## [ci/deploy.yml](../ci/deploy.yml)

### [release core fw regular deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L5)
Missing description

### [release core fw btconly deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L26)
Missing description

### [release core fw regular debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L47)
Missing description

### [release core fw btconly debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L68)
Missing description

### [release legacy fw regular deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L91)
Missing description

### [release legacy fw btconly deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L112)
Missing description

### [release legacy fw regular debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L133)
Missing description

### [release legacy fw btconly debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L154)
Missing description

### [release core unix debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L177)
Missing description

### [release legacy unix debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L202)
Missing description

### [ui tests core fixtures deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L229)
Missing description

---
