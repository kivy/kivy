'''
python-mtdev - Python binding to the mtdev library (MIT license)

The mtdev library transforms all variants of kernel MT events to the
slotted type B protocol. The events put into mtdev may be from any MT
device, specifically type A without contact tracking, type A with
contact tracking, or type B with contact tracking. See the kernel
documentation for further details.

'''

import os
from ctypes import cdll, Structure, c_ulong, c_int, c_ushort, \
                   c_void_p, pointer, POINTER, byref

# load library
libmtdev = cdll.LoadLibrary('libmtdev.so.1')

# from linux/input.h
MTDEV_CODE_SLOT          = 0x2f  # MT slot being modified
MTDEV_CODE_TOUCH_MAJOR   = 0x30    # Major axis of touching ellipse
MTDEV_CODE_TOUCH_MINOR   = 0x31    # Minor axis (omit if circular)
MTDEV_CODE_WIDTH_MAJOR   = 0x32    # Major axis of approaching ellipse
MTDEV_CODE_WIDTH_MINOR   = 0x33    # Minor axis (omit if circular)
MTDEV_CODE_ORIENTATION   = 0x34    # Ellipse orientation
MTDEV_CODE_POSITION_X    = 0x35    # Center X ellipse position
MTDEV_CODE_POSITION_Y    = 0x36    # Center Y ellipse position
MTDEV_CODE_TOOL_TYPE     = 0x37    # Type of touching device
MTDEV_CODE_BLOB_ID       = 0x38    # Group a set of packets as a blob
MTDEV_CODE_TRACKING_ID   = 0x39    # Unique ID of initiated contact
MTDEV_CODE_PRESSURE      = 0x3a    # Pressure on contact area
MTDEV_CODE_ABS_X		 = 0x00
MTDEV_CODE_ABS_Y		 = 0x01
MTDEV_CODE_ABS_Z		 = 0x02
MTDEV_CODE_BTN_DIGI		        = 0x140
MTDEV_CODE_BTN_TOOL_PEN		    = 0x140
MTDEV_CODE_BTN_TOOL_RUBBER		= 0x141
MTDEV_CODE_BTN_TOOL_BRUSH		= 0x142
MTDEV_CODE_BTN_TOOL_PENCIL		= 0x143
MTDEV_CODE_BTN_TOOL_AIRBRUSH	= 0x144
MTDEV_CODE_BTN_TOOL_FINGER		= 0x145
MTDEV_CODE_BTN_TOOL_MOUSE		= 0x146
MTDEV_CODE_BTN_TOOL_LENS		= 0x147
MTDEV_CODE_BTN_TOUCH		    = 0x14a
MTDEV_CODE_BTN_STYLUS		    = 0x14b
MTDEV_CODE_BTN_STYLUS2		    = 0x14c
MTDEV_CODE_BTN_TOOL_DOUBLETAP	= 0x14d
MTDEV_CODE_BTN_TOOL_TRIPLETAP	= 0x14e
MTDEV_CODE_BTN_TOOL_QUADTAP	    = 0x14f	# Four fingers on trackpad

MTDEV_TYPE_EV_ABS        = 0x03
MTDEV_TYPE_EV_SYN        = 0x00
MTDEV_TYPE_EV_KEY        = 0x01
MTDEV_TYPE_EV_REL        = 0x02
MTDEV_TYPE_EV_ABS        = 0x03
MTDEV_TYPE_EV_MSC        = 0x04
MTDEV_TYPE_EV_SW         = 0x05
MTDEV_TYPE_EV_LED        = 0x11
MTDEV_TYPE_EV_SND        = 0x12
MTDEV_TYPE_EV_REP        = 0x14
MTDEV_TYPE_EV_FF         = 0x15
MTDEV_TYPE_EV_PWR        = 0x16
MTDEV_TYPE_EV_FF_STATUS  = 0x17

MTDEV_ABS_TRACKING_ID	= 9
MTDEV_ABS_POSITION_X	= 5
MTDEV_ABS_POSITION_Y	= 6
MTDEV_ABS_TOUCH_MAJOR	= 0
MTDEV_ABS_TOUCH_MINOR	= 1
MTDEV_ABS_WIDTH_MAJOR	= 2
MTDEV_ABS_WIDTH_MINOR	= 3
MTDEV_ABS_ORIENTATION	= 4
MTDEV_ABS_SIZE          = 11

class timeval(Structure):
    _fields_ = [
        ('tv_sec', c_ulong),
        ('tv_usec', c_ulong)
    ]

class input_event(Structure):
    _fields_ = [
        ('time', timeval),
        ('type', c_ushort),
        ('code', c_ushort),
        ('value', c_int)
    ]

class input_absinfo(Structure):
    _fields_ = [
        ('value', c_int),
        ('minimum', c_int),
        ('maximum', c_int),
        ('fuzz', c_int),
        ('flat', c_int),
        ('resolution', c_int)
    ]

class mtdev_caps(Structure):
    _fields_ = [
        ('has_mtdata', c_int),
        ('has_slot', c_int),
        ('has_abs', c_int * MTDEV_ABS_SIZE),
        ('slot', input_absinfo),
        ('abs', input_absinfo * MTDEV_ABS_SIZE)
    ]

class mtdev(Structure):
    _fields_ = [
        ('caps', mtdev_caps),
        ('state', c_void_p)
    ]

# binding
mtdev_open = libmtdev.mtdev_open
mtdev_open.argtypes = [POINTER(mtdev), c_int]
mtdev_get = libmtdev.mtdev_get
mtdev_get.argtypes = [POINTER(mtdev), c_int, POINTER(input_event), c_int]
mtdev_idle = libmtdev.mtdev_idle
mtdev_idle.argtypes = [POINTER(mtdev), c_int, c_int]
mtdev_close = libmtdev.mtdev_close
mtdev_close.argtypes = [POINTER(mtdev)]


class Device:
    def __init__(self, filename):
        self._filename = filename
        self._fd = -1
        self._device = mtdev()

        self._fd = os.open(filename, os.O_NONBLOCK | os.O_RDONLY)
        ret = mtdev_open(pointer(self._device), self._fd)
        if ret != 0:
            os.close(self._fd)
            self._fd = -1
            raise Exception('Unable to open device')

    def close(self):
        '''Close the mtdev converter
        '''
        if self._fd == -1:
            return
        mtdev_close(POINTER(self._device))
        os.close(self._fd)
        self._fd = -1

    def idle(self, ms):
        '''Check state of kernel device
        
        :Parameters:
            `ms` : int
                Number of milliseconds to wait for activity

        :Return:
            Return True if the device is idle, i.e, there are no fetched events
            in the pipe and there is nothing to fetch from the device.
        '''
        if self._fd == -1:
            raise Exception('Device closed')
        return bool(mtdev_idle(pointer(self._device), self._fd, ms))


    def get(self):
        if self._fd == -1:
            raise Exception('Device closed')
        ev = input_event()
        if mtdev_get(pointer(self._device), self._fd, byref(ev), 1) <= 0:
            return None
        return ev

    def has_mtdata(self):
        '''Return True if the device has multitouch data.
        '''
        if self._fd == -1:
            raise Exception('Device closed')
        return bool(self._device.caps.has_mtdata)

    def has_slot(self):
        '''Return True if the device has slot information.
        '''
        if self._fd == -1:
            raise Exception('Device closed')
        return bool(self._device.caps.has_slot)

    def has_abs(self, index):
        '''Return True if the device has abs data.

        :Parameters:
            `index` : int
                One of const starting with a name ABS_MT_
        '''
        if self._fd == -1:
            raise Exception('Device closed')
        if index < 0 or index >= MTDEV_ABS_SIZE:
            raise IndexError('Invalid index')
        return bool(self._device.caps.has_abs[index])

    def get_max_abs(self):
        '''Return the maximum number of abs information available.
        '''
        return MTDEV_ABS_SIZE

    def get_slot(self):
        '''Return the slot data.
        '''
        if self._fd == -1:
            raise Exception('Device closed')
        if self._device.caps.has_slot == 0:
            return
        return self._device.caps.slot

    def get_abs(self, index):
        '''Return the abs data.

        :Parameters:
            `index` : int
                One of const starting with a name ABS_MT_
        '''
        if self._fd == -1:
            raise Exception('Device closed')
        if index < 0 or index >= MTDEV_ABS_SIZE:
            raise IndexError('Invalid index')
        return self._device.caps.abs[index]


