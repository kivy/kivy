import argparse
import os
import zipfile

KIVY_DEPS_ROOT = os.environ.get("KIVY_DEPS_ROOT", None)
if not KIVY_DEPS_ROOT:
    print(
        "KIVY_DEPS_ROOT environment variable is not set. "
        "Please set it to the path where iOS frameworks are located."
    )
    raise EnvironmentError("KIVY_DEPS_ROOT environment variable is not set")


def add_ios_frameworks_to_wheels(wheels_path: str):
    frameworks_folder = os.path.join(KIVY_DEPS_ROOT, "dist", "Frameworks")
    if not os.path.exists(frameworks_folder):
        raise FileNotFoundError(
            "Frameworks folder does not exist at path: {}".format(
                frameworks_folder
            )
        )

    ios_frameworks_folders = []
    for item in os.listdir(frameworks_folder):
        item_path = os.path.join(frameworks_folder, item)
        if os.path.isdir(item_path) and item.endswith(".xcframework"):
            ios_frameworks_folders.append(item_path)

    # Add the iOS frameworks to wheels in the specified directory
    if not os.path.exists(wheels_path):
        raise FileNotFoundError(
            "Specified folder does not exist at path: {}".format(wheels_path)
        )

    for wheel in os.listdir(wheels_path):
        if wheel.endswith(".whl"):
            wheel_path = os.path.join(wheels_path, wheel)
            with zipfile.ZipFile(
                wheel_path,
                "a",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=6,
            ) as whl:
                print("Adding iOS frameworks to wheel: {}".format(wheel_path))
                for ios_framework in ios_frameworks_folders:
                    print(
                        "Adding iOS framework {} to wheel".format(
                            ios_framework
                        )
                    )
                    for root, _, files in os.walk(ios_framework):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(
                                file_path, os.path.dirname(ios_framework)
                            )
                            whl.write(
                                file_path, os.path.join(".frameworks", arcname)
                            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Add iOS .xcframework files in .frameworks folder "
            "to all wheels in the specified directory."
        )
    )
    parser.add_argument(
        "wheels_path",
        help=(
            "Path to the directory containing the wheels "
            "to which iOS frameworks should be added."
        ),
    )
    args = parser.parse_args()

    add_ios_frameworks_to_wheels(args.wheels_path)
