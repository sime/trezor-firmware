# CI pipeline
It consists of multiple stages below, each having one or more jobs
Latest CI pipeline of master branch can be seen at [https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/pipelines/master/latest](https://gitlab.com/satoshilabs/trezor/trezor-firmware/-/pipelines/master/latest)
## ENVIRONMENT stage - [file](../ci/environment.yml)

Connected with creating the testing image for CI

Consists of **1 job** below:
- ### [environment](https://github.com/trezor/trezor-firmware/blob/master/ci/environment.yml#L7)
Environment job builds the `ci/Dockerfile` and pushes the built docker image
into our GitLab registry. Since modifications of this Dockerfile are very rare
this is a _manual_ job which needs to be triggered on GitLab.
Almost all CI jobs run inside this docker image.
```sh
wget -nc -P ci/ https://dl-cdn.alpinelinux.org/alpine/v$ALPINE_RELEASE/releases/$ALPINE_ARCH/alpine-minirootfs-$ALPINE_VERSION-$ALPINE_ARCH.tar.gz
echo "${ALPINE_CHECKSUM}  ci/alpine-minirootfs-$ALPINE_VERSION-$ALPINE_ARCH.tar.gz" | sha256sum -c
docker build --tag $CONTAINER_NAME:$CI_COMMIT_SHA --tag $CONTAINER_NAME:latest --build-arg ALPINE_VERSION="$ALPINE_VERSION" --build-arg ALPINE_ARCH="$ALPINE_ARCH" --build-arg NIX_VERSION="$NIX_VERSION" --build-arg FULLDEPS_TESTING=1 ci/
docker push $CONTAINER_NAME:$CI_COMMIT_SHA
docker push $CONTAINER_NAME:latest
```
---
## PREBUILD stage - [file](../ci/prebuild.yml)

Static checks on the code.

Consists of **7 jobs** below:
- ### [style prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L16)
Check the code for style correctness and perform some static code analysis.
Biggest part is the python one - using `flake8`, `isort`, `black`, `pylint` and `pyright`,
also checking Rust files by `rustftm` and C files by `clang-format`.
Changelogs formats are checked
```sh
nix-shell --run "poetry run make style_check"
```
- ### [common prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L25)
Check validity of coin definitions and protobuf files
```sh
nix-shell --run "poetry run make defs_check"
```
- ### [gen prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L32)
Check validity of auto-generated files
```sh
nix-shell --run "poetry run make gen_check"
```
- ### [editor prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L39)
Checking format of .editorconfig files
```sh
nix-shell --run "make editor_check"
```
- ### [yaml prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L46)
All .yml/.yaml files are checked for syntax validity and other correctness
```sh
nix-shell --run "poetry run make yaml_check"
```
- ### [release commit messages prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L53)
Checking the format of release commit messages
```sh
nix-shell --run "ci/check_release_commit_messages.sh"
```
- ### [changelog prebuild](https://github.com/trezor/trezor-firmware/blob/master/ci/prebuild.yml#L70)
Verifying that all commits changing some functionality have a changelog entry
or contain `[no changelog]` in the commit message
```sh
nix-shell --run "ci/check_changelog.sh"
```
---
## BUILD stage - [file](../ci/build.yml)

All builds are published as artifacts so they can be downloaded and used.

Consists of **20 jobs** below:
- ### [core fw regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L20)
Build of Core into firmware. Regular version.
**Are you looking for Trezor T firmware build? This is most likely it.**
```sh
nix-shell --run "poetry run make -C core build_boardloader"
nix-shell --run "poetry run make -C core build_bootloader"
nix-shell --run "poetry run make -C core build_bootloader_ci"
nix-shell --run "poetry run make -C core build_prodtest"
nix-shell --run "poetry run make -C core build_firmware"
nix-shell --run "poetry run make -C core sizecheck"
cp core/build/firmware/firmware.bin trezor-fw-regular-$CORE_VERSION-$CI_COMMIT_SHORT_SHA.bin
```
- ### [core fw regular debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L41)
Build of Core into firmware with enabled _debug_ mode. In debug mode you can
upload mnemonic seed, use debug link etc. which enables device tests. Storage
on the device gets wiped on every start in this firmware.
```sh
nix-shell --run "PYOPT=0 poetry run make -C core build_firmware"
cp core/build/firmware/firmware.bin trezor-fw-regular-debug-$CORE_VERSION-$CI_COMMIT_SHORT_SHA.bin
```
- ### [core fw btconly build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L55)
Build of Core into firmware. Bitcoin-only version.
```sh
nix-shell --run "poetry run make -C core build_firmware"
mv core/build/firmware/firmware.bin core/build/firmware/firmware-bitcoinonly.bin
nix-shell --run "poetry run ./tools/check-bitcoin-only core/build/firmware/firmware-bitcoinonly.bin"
cp core/build/firmware/firmware-bitcoinonly.bin trezor-fw-btconly-$CORE_VERSION-$CI_COMMIT_SHORT_SHA.bin
```
- ### [core fw btconly debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L72)
Missing description
```sh
nix-shell --run "poetry run make -C core build_firmware"
cp core/build/firmware/firmware.bin trezor-fw-btconly-debug-$CORE_VERSION-$CI_COMMIT_SHORT_SHA.bin
```
- ### [core fw btconly t1 build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L95)
Missing description
```sh
nix-shell --run "poetry run make -C core build_firmware"
cp core/build/firmware/firmware.bin trezor-fw-btconly-t1-$CORE_VERSION-$CI_COMMIT_SHORT_SHA.bin
```
- ### [core unix regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L113)
Non-frozen emulator build. This means you still need Python files
present which get interpreted.
```sh
nix-shell --run "poetry run make -C core build_unix"
```
- ### [core unix frozen regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L128)
Build of Core into UNIX emulator. Something you can run on your laptop.
Frozen version. That means you do not need any other files to run it,
it is just a single binary file that you can execute directly.
```sh
nix-shell --run "poetry run make -C core build_unix_frozen"
```
- ### [core unix frozen btconly debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L145)
Build of Core into UNIX emulator. Something you can run on your laptop.
Frozen version. That means you do not need any other files to run it,
it is just a single binary file that you can execute directly.
See [Emulator](../core/emulator/index.md) for more info.
Debug mode enabled, Bitcoin-only version.
```sh
nix-shell --run "poetry run make -C core build_unix_frozen"
mv core/build/unix/trezor-emu-core core/build/unix/trezor-emu-core-bitcoinonly
```
- ### [core unix frozen debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L165)
Build of Core into UNIX emulator. Something you can run on your laptop.
Frozen version. That means you do not need any other files to run it,
it is just a single binary file that you can execute directly.
**Are you looking for a Trezor T emulator? This is most likely it.**
```sh
nix-shell --run "poetry run make -C core build_unix_frozen"
```
- ### [core unix frozen debug build arm](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L178)
Missing description
```sh
nix-shell --run "poetry run make -C core build_unix_frozen"
mv core/build/unix/trezor-emu-core core/build/unix/trezor-emu-core-arm
```
- ### [core unix frozen btconly debug t1 build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L199)
Missing description
```sh
nix-shell --run "poetry run make -C core build_unix_frozen"
mv core/build/unix/trezor-emu-core core/build/unix/trezor-emu-core-bitcoinonly
```
- ### [core macos frozen regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L214)
Missing description
```sh
nix-shell --option system x86_64-darwin --run "poetry run make -C core build_unix_frozen"
export NAME="trezor-emu-core.darwin"
cp -v core/build/unix/trezor-emu-core ./$NAME
chmod +x $NAME
echo '"$(dirname "$BASH_SOURCE")"/trezor-emu-core.darwin' > trezor-emulator.command
chmod u+x trezor-emulator.command
```
- ### [crypto build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L239)
Build of our cryptographic library, which is then incorporated into the other builds.
```sh
nix-shell --run "poetry run make -C crypto"
```
- ### [legacy fw regular build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L262)
Missing description
```sh
nix-shell --run "export PRODUCTION=1 && poetry run legacy/script/cibuild"
nix-shell --run "poetry run legacy/script/setup"
nix-shell --run "export PRODUCTION=0 && poetry run legacy/script/cibuild"
nix-shell --run "poetry run make -C legacy/demo"
mv legacy/firmware/trezor.bin trezor-fw-regular-$LEGACY_VERSION-$CI_COMMIT_SHORT_SHA.bin
```
- ### [legacy fw regular debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L278)
Missing description
```sh
nix-shell --run "export PRODUCTION=1 && poetry run legacy/script/cibuild"
nix-shell --run "poetry run legacy/script/setup"
nix-shell --run "export PRODUCTION=0 && poetry run legacy/script/cibuild"
mv legacy/firmware/trezor.bin trezor-fw-regular-debug-$LEGACY_VERSION-$CI_COMMIT_SHORT_SHA.bin
```
- ### [legacy fw btconly build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L295)
Missing description
```sh
nix-shell --run "export PRODUCTION=1 && poetry run legacy/script/cibuild"
nix-shell --run "poetry run legacy/script/setup"
nix-shell --run "export PRODUCTION=0 && poetry run legacy/script/cibuild"
mv legacy/firmware/trezor.bin legacy/firmware/trezor-bitcoinonly.bin
nix-shell --run "poetry run ./tools/check-bitcoin-only legacy/firmware/trezor-bitcoinonly.bin"
mv legacy/firmware/trezor-bitcoinonly.bin trezor-fw-btconly-$LEGACY_VERSION-$CI_COMMIT_SHORT_SHA.bin
```
- ### [legacy fw btconly debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L314)
Missing description
```sh
nix-shell --run "export PRODUCTION=1 && poetry run legacy/script/cibuild"
nix-shell --run "poetry run legacy/script/setup"
nix-shell --run "export PRODUCTION=0 && poetry run legacy/script/cibuild"
nix-shell --run "poetry run ./tools/check-bitcoin-only legacy/firmware/trezor.bin"
mv legacy/firmware/trezor.bin trezor-fw-btconly-debug-$LEGACY_VERSION-$CI_COMMIT_SHORT_SHA.bin
```
- ### [legacy emu regular debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L335)
Regular version (not only Bitcoin) of above.
**Are you looking for a Trezor One emulator? This is most likely it.**
```sh
nix-shell --run "poetry run legacy/script/cibuild"
```
- ### [legacy emu regular debug build arm](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L350)
Missing description
```sh
nix-shell --run "poetry run legacy/script/cibuild"
mv legacy/firmware/trezor.elf  legacy/firmware/trezor-arm.elf
```
- ### [legacy emu btconly debug build](https://github.com/trezor/trezor-firmware/blob/master/ci/build.yml#L375)
Build of Legacy into UNIX emulator. Use keyboard arrows to emulate button presses.
Bitcoin-only version.
```sh
nix-shell --run "poetry run legacy/script/cibuild"
mv legacy/firmware/trezor.elf legacy/firmware/trezor-bitcoinonly.elf
```
---
## TEST stage - [file](../ci/test.yml)

All the tests run test cases on the freshly built emulators from the previous `BUILD` stage.

Consists of **19 jobs** below:
- ### [core unit test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L15)
Python and rust unit tests, checking TT functionality.
```sh
nix-shell --run "poetry run make -C core test | ts -s"
nix-shell --run "poetry run make -C core test_rust | ts -s"
nix-shell --run "poetry run make -C core clippy | ts -s"
```
- ### [core unit test t1](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L25)
Missing description
```sh
nix-shell --run "poetry run make -C core test_rust | ts -s"
```
- ### [core device ui test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L39)
UI tests for Core. Running device tests and also comparing screens
with the expected UI result.
See artifacts for a comprehensive report of UI.
See [docs/tests/ui-tests](../docs/tests/ui-tests.md) for more info.
```sh
nix-shell --run "poetry run make -C core test_emu_ui | ts -s"
```
- ### [core device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L66)
Device tests for Core.
See [docs/tests/device-tests](../docs/tests/device-tests.md) for more info.
```sh
nix-shell --run "poetry run make -C core test_emu | ts -s"
mv core/src/.coverage core/.coverage.test_emu
```
- ### [core btconly device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L88)
Device tests excluding altcoins, only for BTC.
```sh
nix-shell --run "poetry run make -C core test_emu | ts -s"
```
- ### [core monero test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L109)
Monero tests.
```sh
nix-shell --arg fullDeps true --run "poetry run make -C core test_emu_monero | ts -s"
mv core/src/.coverage core/.coverage.test_emu_monero
```
- ### [core u2f test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L129)
Tests for U2F and HID.
```sh
nix-shell --run "poetry run make -C tests/fido_tests/u2f-tests-hid | ts -s"
nix-shell --run "poetry run make -C core test_emu_u2f | ts -s"
mv core/src/.coverage core/.coverage.test_emu_u2f
```
- ### [core fido2 test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L149)
FIDO2 device tests.
```sh
pgrep trezor-emu-core || true
nix-shell --run "poetry run make -C core test_emu_fido2 | ts -s"
pgrep trezor-emu-core || true
mv core/src/.coverage core/.coverage.test_emu_fido2
```
- ### [core click test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L174)
Click tests.
See [docs/tests/click-tests](../docs/tests/click-tests.md) for more info.
```sh
nix-shell --run "poetry run make -C core test_emu_click | ts -s"
```
- ### [core upgrade test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L193)
Upgrade tests.
See [docs/tests/upgrade-tests](../docs/tests/upgrade-tests.md) for more info.
```sh
nix-shell --run "tests/download_emulators.sh"
nix-shell --run "poetry run pytest --junitxml=tests/junit.xml tests/upgrade_tests | ts -s"
```
- ### [core persistence test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L213)
Persistence tests.
```sh
nix-shell --run "poetry run pytest --junitxml=tests/junit.xml tests/persistence_tests | ts -s"
```
- ### [crypto test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L232)
Missing description
```sh
./crypto/tests/aestst
./crypto/tests/test_check
./crypto/tests/test_openssl 1000
nix-shell --run "cd crypto && ITERS=10 poetry run pytest --junitxml=tests/junit.xml tests | ts -s"
nix-shell --run "CK_TIMEOUT_MULTIPLIER=20 valgrind -q --error-exitcode=1 ./crypto/tests/test_check | ts -s"
```
- ### [legacy test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L260)
Missing description
```sh
nix-shell --run "poetry run legacy/script/test | ts -s"
```
- ### [legacy btconly test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L278)
Missing description
```sh
nix-shell --run "poetry run legacy/script/test | ts -s"
```
- ### [legacy upgrade test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L299)
Missing description
```sh
nix-shell --run "tests/download_emulators.sh"
nix-shell --run "poetry run pytest --junitxml=tests/junit.xml tests/upgrade_tests | ts -s"
```
- ### [python test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L321)
Missing description
```sh
nix-shell --arg fullDeps true --run "unset _PYTHON_SYSCONFIGDATA_NAME && cd python && poetry run tox | ts -s"
```
- ### [storage test](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L350)
Missing description
```sh
nix-shell --run "poetry run make -C storage/tests build | ts -s"
nix-shell --run "poetry run make -C storage/tests tests_all | ts -s"
```
- ### [core unix memory profiler](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L373)
Missing description
```sh
nix-shell --run "poetry run make -C core build_unix_frozen | ts -s"
nix-shell --run "poetry run make -C core test_emu | ts -s"
nix-shell --run "mkdir core/prof/memperf-html"
nix-shell --run "poetry run core/tools/alloc.py --alloc-data=core/src/alloc_data.txt html core/prof/memperf-html"
```
- ### [connect test core](https://github.com/trezor/trezor-firmware/blob/master/ci/test.yml#L397)
Missing description
```sh
/trezor-user-env/run.sh &
nix-shell --run "tests/connect_tests/connect_tests.sh 2.99.99"
```
---
## TEST-HW stage - [file](../ci/test-hw.yml)

Consists of **5 jobs** below:
- ### [hardware core regular device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L25)
[Device tests](../docs/tests/device-tests.md) that run against an actual physical Trezor T.
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
```sh
cd ci/hardware_tests
set -a
source hardware.cfg
set +a
nix-shell --run "cd ../.. && poetry install"
nix-shell --run "poetry run python bootstrap.py tt ../../trezor-*.bin | ts -s"
nix-shell --run "poetry run pytest ../../tests/device_tests | ts -s"
```
- ### [hardware core btconly device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L54)
Also device tests on physical Trezor T but with Bitcoin-only firmware.
```sh
cd ci/hardware_tests
set -a
source hardware.cfg
set +a
nix-shell --run "cd ../.. && poetry install"
nix-shell --run "poetry run python bootstrap.py tt ../../trezor-*.bin | ts -s"
nix-shell --run "poetry run pytest ../../tests/device_tests | ts -s"
```
- ### [hardware core monero test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L83)
Missing description
```sh
cd ci/hardware_tests
set -a
source hardware.cfg
set +a
nix-shell --run "cd ../.. && poetry install"
nix-shell --run "poetry run python bootstrap.py tt ../../trezor-*.bin | ts -s"
nix-shell --arg fullDeps true --run "cd ../../core/tests && ./run_tests_device_emu_monero.sh $TESTOPTS | ts -s"
```
- ### [hardware legacy regular device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L113)
[Device tests](../docs/tests/device-tests.md) executed on physical Trezor 1.
This works thanks to [tpmb](https://github.com/mmahut/tpmb), which is a small arduino
device capable of pushing an actual buttons on the device.
```sh
cd ci/hardware_tests
nix-shell --run "./t1_hw_test.sh | ts -s"
```
- ### [hardware legacy btconly device test](https://github.com/trezor/trezor-firmware/blob/master/ci/test-hw.yml#L137)
Also device tests on physical Trezor 1 but with Bitcoin-only firmware.
```sh
cd ci/hardware_tests
nix-shell --run "./t1_hw_test.sh | ts -s"
```
---
## POSTTEST stage - [file](../ci/posttest.yml)

Consists of **2 jobs** below:
- ### [core unix coverage posttest](https://github.com/trezor/trezor-firmware/blob/master/ci/posttest.yml#L10)
Missing description
```sh
nix-shell --run "poetry run make -C core coverage"
```
- ### [core unix ui changes](https://github.com/trezor/trezor-firmware/blob/master/ci/posttest.yml#L31)
Missing description
```sh
nix-shell --run "cd tests/ui_tests ; poetry run python reporting/report_master_diff.py"
mv tests/ui_tests/reporting/reports/master_diff/ .
```
---
## DEPLOY stage - [file](../ci/deploy.yml)

Consists of **11 jobs** below:
- ### [release core fw regular deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L5)
Missing description
```sh
export VERSION=$(./tools/version.sh core/embed/firmware/version.h)
export NAME="trezor-fw-regular-$VERSION-$CI_COMMIT_SHORT_SHA.bin"
echo "Deploying to ${DEPLOY_DIRECTORY}/$NAME"
mkdir -p "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}"
rsync --delete -va $NAME "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}/$NAME"
```
- ### [release core fw btconly deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L26)
Missing description
```sh
export VERSION=$(./tools/version.sh core/embed/firmware/version.h)
export NAME="trezor-fw-btconly-$VERSION-$CI_COMMIT_SHORT_SHA.bin"
echo "Deploying to ${DEPLOY_DIRECTORY}/$NAME"
mkdir -p "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}"
rsync --delete -va $NAME "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}/$NAME"
```
- ### [release core fw regular debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L47)
Missing description
```sh
export VERSION=$(./tools/version.sh core/embed/firmware/version.h)
export NAME="trezor-fw-regular-debug-$VERSION-$CI_COMMIT_SHORT_SHA.bin"
echo "Deploying to ${DEPLOY_DIRECTORY}/$NAME"
mkdir -p "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}"
rsync --delete -va $NAME "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}/$NAME"
```
- ### [release core fw btconly debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L68)
Missing description
```sh
export VERSION=$(./tools/version.sh core/embed/firmware/version.h)
export NAME="trezor-fw-btconly-debug-$VERSION-$CI_COMMIT_SHORT_SHA.bin"
echo "Deploying to ${DEPLOY_DIRECTORY}/$NAME"
mkdir -p "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}"
rsync --delete -va $NAME "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}/$NAME"
```
- ### [release legacy fw regular deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L91)
Missing description
```sh
export VERSION=$(./tools/version.sh legacy/firmware/version.h)
export NAME="trezor-fw-regular-$VERSION-$CI_COMMIT_SHORT_SHA.bin"
echo "Deploying to ${DEPLOY_DIRECTORY}/$NAME"
mkdir -p "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}"
rsync --delete -va $NAME "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}/$NAME"
```
- ### [release legacy fw btconly deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L112)
Missing description
```sh
export VERSION=$(./tools/version.sh legacy/firmware/version.h)
export NAME="trezor-fw-btconly-$VERSION-$CI_COMMIT_SHORT_SHA.bin"
echo "Deploying to ${DEPLOY_DIRECTORY}/$NAME"
mkdir -p "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}"
rsync --delete -va $NAME "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}/$NAME"
```
- ### [release legacy fw regular debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L133)
Missing description
```sh
export VERSION=$(./tools/version.sh legacy/firmware/version.h)
export NAME="trezor-fw-regular-debug-$VERSION-$CI_COMMIT_SHORT_SHA.bin"
echo "Deploying to ${DEPLOY_DIRECTORY}/$NAME"
mkdir -p "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}"
rsync --delete -va $NAME "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}/$NAME"
```
- ### [release legacy fw btconly debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L154)
Missing description
```sh
export VERSION=$(./tools/version.sh legacy/firmware/version.h)
export NAME="trezor-fw-btconly-debug-$VERSION-$CI_COMMIT_SHORT_SHA.bin"
echo "Deploying to ${DEPLOY_DIRECTORY}/$NAME"
mkdir -p "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}"
rsync --delete -va $NAME "${DEPLOY_BASE_DIR}/${DEPLOY_DIRECTORY}/$NAME"
```
- ### [release core unix debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L177)
Missing description
```sh
export VERSION=$(./tools/version.sh core/embed/firmware/version.h)
DEST="$DEPLOY_PATH/trezor-emu-core-v$VERSION"
DEST_ARM="$DEPLOY_PATH/trezor-emu-core-arm-v$VERSION"
echo "Deploying to $DEST and $DEST_ARM"
nix-shell -p patchelf --run "patchelf --set-interpreter /lib64/ld-linux-x86-64.so.2 core/build/unix/trezor-emu-core"
nix-shell -p patchelf --run "patchelf --set-interpreter /lib/ld-linux-aarch64.so.1 core/build/unix/trezor-emu-core-arm"
rsync --delete -va core/build/unix/trezor-emu-core "$DEST"
rsync --delete -va core/build/unix/trezor-emu-core-arm "$DEST_ARM"
```
- ### [release legacy unix debug deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L202)
Missing description
```sh
export VERSION=$(./tools/version.sh legacy/firmware/version.h)
DEST="$DEPLOY_PATH/trezor-emu-legacy-v$VERSION"
DEST_ARM="$DEPLOY_PATH/trezor-emu-legacy-arm-v$VERSION"
echo "Deploying to $DEST and $DEST_ARM"
nix-shell -p patchelf --run "patchelf --set-interpreter /lib64/ld-linux-x86-64.so.2 legacy/firmware/trezor.elf"
nix-shell -p patchelf --run "patchelf --set-interpreter /lib/ld-linux-aarch64.so.1 legacy/firmware/trezor-arm.elf"
rsync --delete -va legacy/firmware/trezor.elf "$DEST"
rsync --delete -va legacy/firmware/trezor-arm.elf "$DEST_ARM"
```
- ### [ui tests core fixtures deploy](https://github.com/trezor/trezor-firmware/blob/master/ci/deploy.yml#L229)
Missing description
```sh
echo "Deploying to $DEPLOY_PATH"
rsync --delete -va ci/ui_test_records/* "$DEPLOY_PATH"
```
---
