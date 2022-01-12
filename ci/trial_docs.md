## ci/environment.yml

Connected with creating the testing image for CI

### environment
Environment job builds the `ci/Dockerfile` and pushes the built docker image
into our GitLab registry. Since modifications of this Dockerfile are very rare
this is a _manual_ job which needs to be triggered on GitLab.
Almost all CI jobs run inside this docker image.


## ci/prebuild.yml

### style prebuild
Missing description

### common prebuild
Missing description

### gen prebuild
Missing description

### editor prebuild
Missing description

### yaml prebuild
Missing description

### release commit messages prebuild
Missing description

### changelog prebuild
Missing description


## ci/build.yml

All builds are published as artifacts so they can be downloaded and used.

### core fw regular build
Build of Core into firmware. Regular version.
**Are you looking for Trezor T firmware build? This is most likely it.**

### core fw regular debug build
Build of Core into firmware with enabled _debug_ mode. In debug mode you can
upload mnemonic seed, use debug link etc. which enables device tests. Storage
on the device gets wiped on every start in this firmware.

### core fw btconly build
Build of Core into firmware. Bitcoin-only version.

### core fw btconly debug build
Missing description

### core fw btconly t1 build
Missing description

### core unix regular build
Non-frozen emulator build. This means you still need Python files
present which get interpreted.

### core unix frozen regular build
Build of Core into UNIX emulator. Something you can run on your laptop.
Frozen version. That means you do not need any other files to run it,
it is just a single binary file that you can execute directly.

### core unix frozen btconly debug build
Build of Core into UNIX emulator. Something you can run on your laptop.
Frozen version. That means you do not need any other files to run it,
it is just a single binary file that you can execute directly.
See [Emulator](../core/emulator/index.md) for more info.
Debug mode enabled, Bitcoin-only version.

### core unix frozen debug build
Build of Core into UNIX emulator. Something you can run on your laptop.
Frozen version. That means you do not need any other files to run it,
it is just a single binary file that you can execute directly.
**Are you looking for a Trezor T emulator? This is most likely it.**

### core unix frozen debug build arm
Missing description

### core unix frozen btconly debug t1 build
Missing description

### core macos frozen regular build
Missing description

### crypto build
Build of our cryptographic library, which is then incorporated into the other builds.

### legacy fw regular build
Missing description

### legacy fw regular debug build
Missing description

### legacy fw btconly build
Missing description

### legacy fw btconly debug build
Missing description

### legacy emu regular debug build
Regular version (not only Bitcoin) of above.
**Are you looking for a Trezor One emulator? This is most likely it.**

### legacy emu regular debug build arm
Missing description

### legacy emu btconly debug build
Build of Legacy into UNIX emulator. Use keyboard arrows to emulate button presses.
Bitcoin-only version.


## ci/test.yml

### core unit test
Missing description

### core unit test t1
Missing description

### core device ui test
UI tests for Core. See artifacts for a comprehensive report of UI.
See [tests/ui-tests](../tests/ui-tests.md) for more info.

### core device test
Missing description

### core btconly device test
Missing description

### core monero test
Missing description

### core u2f test
Missing description

### core fido2 test
Missing description

### core click test
Missing description

### core upgrade test
Missing description

### core persistence test
Missing description

### crypto test
Missing description

### legacy test
Missing description

### legacy btconly test
Missing description

### legacy upgrade test
Missing description

### python test
Missing description

### storage test
Missing description

### core unix memory profiler
Missing description

### connect test core
Missing description


## ci/test-hw.yml

### hardware core regular device test
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

### hardware core btconly device test
Also device tests on physical Trezor T but with Bitcoin-only firmware.

### hardware core monero test
Missing description

### hardware legacy regular device test
[Device tests](../tests/device-tests.md) executed on physical Trezor 1.
This works thanks to [tpmb](https://github.com/mmahut/tpmb), which is a small arduino
device capable of pushing an actual buttons on the device.

### hardware legacy btconly device test
Also device tests on physical Trezor 1 but with Bitcoin-only firmware.


## ci/posttest.yml

### core unix coverage posttest
Missing description

### core unix ui changes
Missing description


## ci/deploy.yml

### release core fw regular deploy
Missing description

### release core fw btconly deploy
Missing description

### release core fw regular debug deploy
Missing description

### release core fw btconly debug deploy
Missing description

### release legacy fw regular deploy
Missing description

### release legacy fw btconly deploy
Missing description

### release legacy fw regular debug deploy
Missing description

### release legacy fw btconly debug deploy
Missing description

### release core unix debug deploy
Missing description

### release legacy unix debug deploy
Missing description

### ui tests core fixtures deploy
Missing description


