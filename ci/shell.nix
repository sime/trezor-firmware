{ fullDeps ? false
, hardwareTest ? false
 }:

let
  # the last commit from master as of 2022-02-08
  rustOverlay = import (builtins.fetchTarball {
    url = "https://github.com/oxalica/rust-overlay/archive/2eae19e246433530998cbf239d5505b7b87bc854.tar.gz";
    sha256 = "0panx24sqcvx52wza02zsxmpkhg6xld7hklrv7dybc59akqm2ira";
  });
  # the last successful build of nixpkgs-unstable as of 2022-02-06
  nixpkgs = import (builtins.fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/942b0817e898262cc6e3f0a5f706ce09d8f749f1.tar.gz";
    sha256 = "048r0rjwlymixbwqfqygn96jm2czdf7a74qgxl6z2al5h02wd5af";
  }) { overlays = [ rustOverlay ]; };
  moneroTests = nixpkgs.fetchurl {
    url = "https://github.com/ph4r05/monero/releases/download/v0.17.1.9-tests/trezor_tests";
    sha256 = "410bc4ff2ff1edc65e17f15b549bd1bf8a3776cf67abdea86aed52cf4bce8d9d";
  };
  moneroTestsPatched = nixpkgs.runCommandCC "monero_trezor_tests" {} ''
    cp ${moneroTests} $out
    chmod +wx $out
    ${nixpkgs.patchelf}/bin/patchelf --set-interpreter "$(cat $NIX_CC/nix-support/dynamic-linker)" "$out"
    chmod -w $out
  '';
  rustStable = nixpkgs.rust-bin.stable."1.58.1".minimal.override {
    targets = [
      "thumbv7em-none-eabihf" # TT
      "thumbv7m-none-eabi"    # T1
    ];
    # we use rustfmt from nixpkgs because it's built with the nighly flag needed for wrap_comments
    # to use official binary, remove rustfmt from buildInputs and add it to extensions:
    extensions = [ "clippy" ];
  };
  gcc = nixpkgs.gcc11;
  llvmPackages = nixpkgs.llvmPackages_13;
  # see pyright/README.md for update procedure
  pyright = nixpkgs.callPackage ./pyright {};
  # HWI tests need https://github.com/bitcoin/bitcoin/pull/22558
  # remove this once nixpkgs version contains this patch
  bitcoind = (nixpkgs.bitcoind.overrideAttrs (attrs: {
    version = attrs.version + "-taproot-psbt";
    src = nixpkgs.fetchFromGitHub {
      owner = "achow101";
      repo = "bitcoin";
      rev = "taproot-psbt";
      sha256 = "sha256-Am7SVxOTlTUjESk8O7kziwyV2GaBX6pGB1oksYPc1EE=";
    };
  }));
in
with nixpkgs;
stdenvNoCC.mkDerivation ({
  name = "trezor-firmware-env";
  buildInputs = lib.optionals fullDeps [
    bitcoind
    # install other python versions for tox testing
    # NOTE: running e.g. "python3" in the shell runs the first version in the following list,
    #       and poetry uses the default version (currently 3.9)
    python39
    python310
    python38
    python37
  ] ++ [
    SDL2
    SDL2_image
    autoflake
    bash
    check
    curl  # for connect tests
    editorconfig-checker
    gcc
    gcc-arm-embedded
    git
    gitAndTools.git-subrepo
    gnumake
    graphviz
    libffi
    libjpeg
    libusb1
    llvmPackages.clang
    openssl
    pkgconfig
    poetry
    protobuf3_6
    pyright
    rustfmt
    rustStable
    wget
    zlib
    moreutils
  ] ++ lib.optionals (!stdenv.isDarwin) [
    procps
    valgrind
  ] ++ lib.optionals (stdenv.isDarwin) [
    darwin.apple_sdk.frameworks.CoreAudio
    darwin.apple_sdk.frameworks.AudioToolbox
    darwin.apple_sdk.frameworks.ForceFeedback
    darwin.apple_sdk.frameworks.CoreVideo
    darwin.apple_sdk.frameworks.Cocoa
    darwin.apple_sdk.frameworks.Carbon
    darwin.apple_sdk.frameworks.IOKit
    darwin.apple_sdk.frameworks.QuartzCore
    darwin.apple_sdk.frameworks.Metal
    darwin.libobjc
    libiconv
  ] ++ lib.optionals hardwareTest [
    uhubctl
    ffmpeg
    dejavu_fonts
  ];
  LD_LIBRARY_PATH = "${libffi}/lib:${libjpeg.out}/lib:${libusb1}/lib:${libressl.out}/lib";
  NIX_ENFORCE_PURITY = 0;

  # Fix bdist-wheel problem by setting source date epoch to a more recent date
  SOURCE_DATE_EPOCH = 1600000000;

  # Used by rust bindgen
  LIBCLANG_PATH = "${llvmPackages.libclang.lib}/lib";

  # don't try to use stack protector for Apple Silicon (emulator) binaries
  # it's broken at the moment
  hardeningDisable = lib.optionals (stdenv.isDarwin && stdenv.isAarch64) [ "stackprotector" ];

} // (lib.optionalAttrs fullDeps) {
  TREZOR_MONERO_TESTS_PATH = moneroTestsPatched;
})
