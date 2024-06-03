# Get VS location via vswhere
$vswhere = & "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.Component.MSBuild -property installationPath

# Print the VS location
Write-Host "Visual Studio location: $vswhere"

# Set the environment variables via vcvarsall.bat
$vcvars_path = "$vswhere\VC\Auxiliary\Build\vcvars64.bat"
Write-Host "vcvarsall path: $vcvars_path"

# Escape the path
$vcvars_path = "`"$vcvars_path`""

# Call the .bat file from the PowerShell script
cmd /c "$vcvars_path&set" | ForEach-Object {
    if ($_ -match "=") {
        $v = $_.split("=", 2);
        Set-Item -Force -Path "ENV:\$($v[0])" -Value "$($v[1])";
        Write-host "Setting $($v[0]) to $($v[1])"
    }
};

write-host "`nVisual Studio Command Prompt variables set." -ForegroundColor Yellow


# windows SDL3
$WINDOWS__SDL3__VERSION = "3.1.2"
$WINDOWS__SDL3__URL="https://github.com/libsdl-org/SDL/archive/refs/heads/main.tar.gz"
$WINDOWS__SDL3__FOLDER="SDL-main"

# windows SDL3_image
$WINDOWS__SDL3_IMAGE__URL="https://github.com/libsdl-org/SDL_image/archive/refs/heads/main.tar.gz"
$WINDOWS__SDL3_IMAGE__FOLDER="SDL_image-main"

# windows SDL3_mixer
$WINDOWS__SDL3_MIXER__URL="https://github.com/libsdl-org/SDL_mixer/archive/refs/heads/main.tar.gz"
$WINDOWS__SDL3_MIXER__FOLDER="SDL_mixer-main"

# windows SDL3_ttf
$WINDOWS__SDL3_TTF__URL="https://github.com/libsdl-org/SDL_ttf/archive/refs/heads/main.tar.gz"
$WINDOWS__SDL3_TTF__FOLDER="SDL_ttf-main"

# Delete the old kivy-dependencies folder, if it exists
Remove-Item -Recurse -Force kivy-dependencies -ErrorAction SilentlyContinue

# Create the kivy-dependencies folder
New-Item -ItemType Directory -Path kivy-dependencies

# Create the kivy-dependencies/download folder
New-Item -ItemType Directory -Path kivy-dependencies/download

# Download the dependencies
Write-Host "Downloading the dependencies..."
Write-Host "-- SDL3, url: $WINDOWS__SDL3__URL"
Invoke-WebRequest -Uri $WINDOWS__SDL3__URL -OutFile "kivy-dependencies/download/SDL3-$WINDOWS__SDL3__VERSION.tar.gz"
Invoke-WebRequest -Uri $WINDOWS__SDL3_IMAGE__URL -OutFile "kivy-dependencies/download/SDL_image-main.tar.gz"
Invoke-WebRequest -Uri $WINDOWS__SDL3_MIXER__URL -OutFile "kivy-dependencies/download/SDL_mixer-main.tar.gz"
Invoke-WebRequest -Uri $WINDOWS__SDL3_TTF__URL -OutFile "kivy-dependencies/download/SDL_ttf-main.tar.gz"

# Create the build folder for the dependencies
New-Item -ItemType Directory -Path kivy-dependencies/build  

# Create the dist folder for the dependencies
New-Item -ItemType Directory -Path kivy-dependencies/dist

# Save dist folder full path
$dist_folder = (Get-Item -Path ".\kivy-dependencies\dist").FullName

Write-Host "Extracting the dependencies..."
cd kivy-dependencies/build

# Extract the dependencies
tar -xf "../download/SDL3-$WINDOWS__SDL3__VERSION.tar.gz"
tar -xf "../download/SDL_image-main.tar.gz"
tar -xf "../download/SDL_mixer-main.tar.gz"
tar -xf "../download/SDL_ttf-main.tar.gz"

# Move into the SDL3 folder
Write-Host "-- Build SDL3"
cd "SDL-main"
cmake -S . -B build -DCMAKE_INSTALL_PREFIX="$dist_folder" -DCMAKE_BUILD_TYPE=Release -GNinja
cmake --build build/ --config Release --verbose --parallel
cmake --install build/ --config Release

cd ..

# Move into the SDL_mixer folder
Write-Host "-- Build SDL_mixer"
cd "SDL_mixer-main"
./external/Get-GitModules.ps1
cmake -B build -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_BUILD_TYPE=Release -DSDL3MIXER_VENDORED=ON  -DSDL3_DIR="$dist_folder/cmake"  -DCMAKE_INSTALL_PREFIX="$dist_folder" -GNinja
cmake --build build/ --config Release --parallel --verbose
cmake --install build/ --config Release
cd ..

# Move into the SDL_image folder
Write-Host "-- Build SDL_image"
cd "SDL_image-main"
./external/Get-GitModules.ps1
cmake -B build -DBUILD_SHARED_LIBS=ON -DCMAKE_BUILD_TYPE=Release -DSDL3IMAGE_TIF_VENDORED=ON -DSDL3IMAGE_WEBP_VENDORED=ON -DSDL3IMAGE_JPG_VENDORED=ON -DSDL3IMAGE_PNG_VENDORED=ON -DSDL3IMAGE_TIF_SHARED=OFF -DSDL3IMAGE_WEBP_SHARED=OFF  -DSDL3IMAGE_VENDORED=OFF -DSDL3_DIR="$dist_folder/cmake"  -DCMAKE_INSTALL_PREFIX="$dist_folder" -DCMAKE_POLICY_DEFAULT_CMP0141=NEW -GNinja
cmake --build build/ --config Release --parallel --verbose
cmake --install build/ --config Release
cd ..

# Move into the SDL_ttf folder
Write-Host "-- Build SDL_ttf"
cd "SDL_ttf-main"
./external/Get-GitModules.ps1
cmake -B build-cmake -DBUILD_SHARED_LIBS=ON -DSDL3TTF_HARFBUZZ=ON -DFT_DISABLE_PNG=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_BUILD_TYPE=Release -DSDL3TTF_VENDORED=ON -DSDL3_DIR="$dist_folder/cmake"  -DCMAKE_INSTALL_PREFIX="$dist_folder" -GNinja
cmake --build build-cmake --config Release --verbose
cmake --install build-cmake/ --config Release --verbose
cd ..
