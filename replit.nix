{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.replitPackages.prybar
    pkgs.replitPackages.stderred
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.python311Full
      pkgs.stdenv.cc.cc.lib
    ];
    PYTHONHOME = "${pkgs.python311Full}";
    PYTHONBIN = "${pkgs.python311Full}/bin/python3.11";
    LANG = "en_US.UTF-8";
    STDERREDBIN = "${pkgs.replitPackages.stderred}/bin/stderred";
    PRYBAR_PYTHON_BIN = "${pkgs.replitPackages.prybar}/bin/prybar-python3";
    PRYBAR_PYTHON_LIBRARY = "${pkgs.python311Full}/lib/libpython3.11.so.1.0";
  };
}
