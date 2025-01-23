import os
import subprocess
from configparser import ConfigParser

current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', 'unknown').lower()
is_wayland_x11 = os.environ.get('XDG_SESSION_TYPE', 'x11').lower()
DEFAULT_SCALE_FACTOR = 1.0


def _get_wayland_scale_factor(monitor: int = 0) -> int:
    try:
        # Run wl-info command to get output information
        result = subprocess.check_output(['wayland-info', '-i', 'wl_output'])
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running wl-info: {e}")
        return DEFAULT_SCALE_FACTOR
    except FileNotFoundError:
        print('Wavland-info command not found, returning 1.0')
        return DEFAULT_SCALE_FACTOR

    result = result.decode('utf-8').split('\n')
    scales = []
    for line in result:
        # if line.startswith('name'):
        #     name = line.split(':')[-1]
        if 'x:' in line and 'y:' in line and 'scale:' in line:
            scales.append(float(line.split(' ')[-1][:-1]))
    return scales[monitor]


def _get_kde_scale_factor(monitor: int = 0) -> int:
    config = ConfigParser()
    config_path = os.path.expanduser('~/.config/kdeglobals')
    if os.path.exists(config_path):
        config.read(config_path)
        if config.has_option('KScreen', 'ScaleFactor'):
            return float(config.get('KScreen', 'ScaleFactor'))
        if config.has_option('KScreen', 'ScreenScaleFactors'):
            monitors = config.get('KScreen', 'ScreenScaleFactors')
            scales = []
            for m in monitors.split(';'):
                if m.strip():
                    name, scale = m.split('=')
                    scales.append(float(scale))
            return scales[monitor]
    return DEFAULT_SCALE_FACTOR


def _get_gnome_scale_factor(monitor: int = 0) -> int:
    return parse_monitors_xml(monitor=monitor)


def _get_gsettings_scale_factor():
    try:
        result = subprocess.run(
            ['gsettings', 'get',
             'org.gnome.desktop.interface', 'scaling-factor'],
            capture_output=True, text=True, check=True)
        scale = float(result.stdout.strip().split()[1])
        return scale if scale > 0 else 1.0
    except subprocess.CalledProcessError:
        return DEFAULT_SCALE_FACTOR


def parse_monitors_xml(monitor: int = 0) -> int:
    monitors_path = os.path.join(
        os.path.expanduser('~'), '.config', 'monitors.xml')
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(monitors_path)
        root = tree.getroot()

        # Dictionary to hold scaling factors for each monitor
        scaling_factors = {}

        logical_monitor = root.findall(
            './/configuration/logicalmonitor')[monitor]
        # Get the monitor identifier
        mmonitor = logical_monitor.find('monitor')
        if mmonitor is not None:
            connector = mmonitor.get('connector')
            vendor = mmonitor.get('vendor')
            product = mmonitor.get('product')
            serial = mmonitor.get('serial')
            monitor_id = f"{connector}_{vendor}_{product}_{serial}"

            # Get the scale factor
            scale = logical_monitor.find('scale')
            if scale is not None:
                scaling_factors[monitor_id] = float(scale.text)
            else:
                scaling_factors[monitor_id] = DEFAULT_SCALE_FACTOR

            # Check if this is the primary monitor
            primary = logical_monitor.find('primary')
            if primary is not None and primary.text.lower() == 'yes':
                scaling_factors[monitor_id] = (
                    scaling_factors[monitor_id], True)
            else:
                scaling_factors[monitor_id] = (
                    scaling_factors[monitor_id], False)

        print(scaling_factors)
        monitors = [float(scaling_factors[x][0]) for x in scaling_factors]
        print(monitors)
        return monitors[monitor]
    except FileNotFoundError:
        print("monitors.xml file not found at the expected location.")
        return DEFAULT_SCALE_FACTOR
    except ET.ParseError:
        print("Error parsing the XML file.")
        return DEFAULT_SCALE_FACTOR


def get_desktop_scale_factor(monitor: int = 0) -> int:
    if is_wayland_x11 == 'wayland':
        sf = _get_wayland_scale_factor(monitor=monitor)
        if sf:
            print(sf, type(sf), 'monitor', monitor)
            return sf

    try:
        return {
            'kde': _get_kde_scale_factor(monitor=monitor),
            'gnome': _get_gnome_scale_factor(monitor=monitor)}[current_desktop]
    except KeyError:
        print('Unknown Desktop, using DEFAULT_SCALE_FACTOR')
    return DEFAULT_SCALE_FACTOR
