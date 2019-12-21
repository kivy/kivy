function Generate-sdist {
    python setup.py sdist --formats=gztar
    python setup.py bdist_wheel --build_examples --universal
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
    # powershell interprets writing to stderr as an error, so only raise error if the return code is none-zero
    try {
      python -c "import kivy" --config "kivy:log_level:error"
    } catch {
      if ($LastExitCode -ne 0) {
        throw $_
      } else {
        echo $_
      }
    }
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
    python -m pip install pip wheel setuptools cython --upgrade
    # workaround for https://github.com/pyinstaller/pyinstaller/issues/4265 until next release
    python -m pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
}

function Install-kivy {
    $old=(pwd).Path
    cmd /c mklink /d "$HOME\kivy" "$old"
    cd "$HOME\kivy"
    python -m pip install -e .[dev,full]
    cd "$old"
}

function Test-kivy {
    python -m pytest --cov=kivy --cov-report term --cov-branch "$(pwd)/kivy/tests"
}
