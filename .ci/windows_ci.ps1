function raise-only-error{
    Param([scriptblock]$Func)
    # powershell interprets writing to stderr as an error, so only raise error if the return code is none-zero
    try {
      $Func.Invoke()
    } catch {
      if ($LastExitCode -ne 0) {
        throw $_
      } else {
        echo $_
      }
    }
}

function Update-version-metadata {
    $current_time = python -c "from time import time; from os import environ; print(int(environ.get('SOURCE_DATE_EPOCH', time())))"
    $date = python -c "from datetime import datetime; print(datetime.utcfromtimestamp($current_time).strftime('%Y%m%d'))"
    echo "Version date is: $date"
    $git_tag = git rev-parse HEAD
    echo "Git tag is: $git_tag"

    (Get-Content .\kivy\_version.py -Raw) -replace "_kivy_git_hash = ''","_kivy_git_hash = '$git_tag'" `
        -replace "_kivy_build_date = ''","_kivy_build_date = '$date'" | Out-File -filepath .\kivy\_version.py
}

function Generate-sdist {
    python -m pip install cython
    python setup.py sdist --formats=gztar
    python setup.py bdist_wheel --build_examples --universal
    python -m pip uninstall cython -y
}

function Generate-windows-wheels {
    pip wheel --no-deps . -w dist/
}

function Rename-windows-wheels {
    # Set new wheel name, keep default if release (tag)
    # release: Kivy-X.Y.Z-cpAB-cpABm-ARCH.whl (Kivy_examples-X.Y.Z-py2.py3-none-any.whl)
    # nightly: Kivy-X.Y.Z.dev0-cpAB-cpABm-ARCH.whl (Kivy_examples-X.Y.Z.dev0-py2.py3-none-any.whl)
    # archive: Kivy-X.Y.Z.dev0.YYYYMMDD.githash-cpAB-cpABm-ARCH.whl (Kivy_examples-X.Y.Z.dev0.YYYYMMDD.githash-py2.py3-none-any.whl)

    $WHEEL_DATE = python -c "from datetime import datetime;print(datetime.utcnow().strftime('%Y%m%d'))"
    echo "Wheel date is: $WHEEL_DATE"
    $GIT_TAG = git rev-parse --short HEAD
    echo "Git tag is: $GIT_TAG"
    raise-only-error -Func {python -c "import kivy" --config "kivy:log_level:error"}
    $WHEEL_VERSION = python -c "import kivy;print(kivy.__version__)" --config "kivy:log_level:error"
    echo "Kivy version is: $WHEEL_VERSION"
    $TAG_NAME = python -c "import kivy; _, tag, n = kivy.parse_kivy_version(kivy.__version__); print(tag + n) if n is not None else print(tag or 'something')"  --config "kivy:log_level:error"
    echo "Tag is: $TAG_NAME"
    $WHEEL_NAME = "$TAG_NAME.$WHEEL_DATE`.$GIT_TAG-"
    echo "New wheel name is: $WHEEL_NAME"

    $files = Get-ChildItem dist *.whl -Name
    foreach ($WHEEL_DEFAULT in $files){
        $WHEEL_NIGHTLY = $WHEEL_DEFAULT.Replace("$TAG_NAME-", $WHEEL_NAME)
        echo "Copying from default $WHEEL_DEFAULT to nightly $WHEEL_NIGHTLY"
        Copy-Item "dist\$WHEEL_DEFAULT" "dist\$WHEEL_NIGHTLY"
    }
}

function Upload-windows-wheels-to-server($ip) {
    echo "Uploading Kivy*:"
    dir dist
    C:\tools\msys64\usr\bin\bash --login -c ".ci/windows-server-upload.sh $ip dist 'Kivy*' ci/win/kivy/"
}

function Install-kivy-test-run-win-deps {

}

function Install-kivy-test-run-pip-deps {
    python -m pip install pip wheel setuptools --upgrade
    python -m pip install twine
}

function Install-kivy {
    python -m pip install -e .[dev,full]
}

function Install-kivy-wheel {
    $root=(pwd).Path
    ls $root
    ls $root/dist
    cd "$HOME"

    python -m pip install pip wheel setuptools --upgrade

    $version=python -c "import sys; print('{}{}'.format(sys.version_info.major, sys.version_info.minor))"
    $bitness=python -c "import sys; print('win_amd64' if sys.maxsize > 2**32 else 'win32')"
    $kivy_fname=(ls $root/dist/Kivy-*$version*$bitness*.whl | Sort-Object -property @{Expression={$_.name.tostring().Length}} | Select-Object -First 1).name
    $kivy_examples_fname=(ls $root/dist/Kivy_examples-*.whl | Sort-Object -property @{Expression={$_.name.tostring().Length}} | Select-Object -First 1).name
    echo "kivy_fname = $kivy_fname, kivy_examples_fname = $kivy_examples_fname"
    python -m pip install "$root/dist/$kivy_fname[full,dev]" "$root/dist/$kivy_examples_fname"
}

function Install-kivy-sdist {
    $root=(pwd).Path
    cd "$HOME"

    python -m pip install pip wheel setuptools --upgrade

    $kivy_fname=(ls $root/dist/Kivy-*.tar.gz).name
    python -m pip install "$root/dist/$kivy_fname[full,dev]"
}

function Test-kivy {
    python -m pytest --timeout=400 --cov=kivy --cov-report term --cov-branch "$(pwd)/kivy/tests"
}

function Test-kivy-benchmark {
    pytest --pyargs kivy.tests --benchmark-only
}

function Test-kivy-installed {
    cd "$HOME"
    python -c 'import kivy'
    $test_path=python -c 'import kivy.tests as tests; print(tests.__path__[0])'  --config "kivy:log_level:error"
    cd "$test_path"

    echo "[run]`nplugins = kivy.tools.coverage`n" > .coveragerc
    raise-only-error -Func {python -m pytest --timeout=400 .}
}

function Upload-artifacts-to-pypi {
  python -m pip install twine
  twine upload dist/*
}
