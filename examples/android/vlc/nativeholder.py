'''
android native widget integration
=======================

The goal of this widget is to integrate any android native widget
The android component will be placed at the right pos/size of the Kivy widget,
as an Underlay (behind the Kivy surface, not above/overlay). The widget must
stay in the right orientation / axis-aligned, or the placement of the android
widget will not work.

Here is the settings to add in buildozer::

	[app:android.meta_data]
	surface.transluent = 1
	surface.depth = 16

.. warning::

	The Kivy's Window.clearcolor will be automatically set to transparent,
	or the widget will not be displayed at all.

.. source code is based on gmap widget https://github.com/tito/kivy-gmaps
	
'''

__all__ = ('AndroidWidgetHolder', 'AndroidSurfaceWidget', 'AndroidTextureWidget', 'bootstrap', 'run_on_ui_thread', 'jPythonActivity')

from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.logger import Logger
from kivy.core.window import Window
from jnius import autoclass, cast, PythonJavaClass, java_method
try:
	bootstrap = 'pygame'
	from android.runnable import run_on_ui_thread
except ImportError:
	bootstrap = 'sdl2'
	class Runnable(PythonJavaClass):
		'''Wrapper around Java Runnable class. This class can be used to schedule a
		call of a Python function into the PythonActivity thread.
		'''

		__javainterfaces__ = ['java/lang/Runnable']
		__runnables__ = []

		def __init__(self, func):
			super(Runnable, self).__init__()
			self.func = func

		def __call__(self, *args, **kwargs):
			self.args = args
			self.kwargs = kwargs
			Runnable.__runnables__.append(self)
			jPythonActivity.mActivity.runOnUiThread(self)

		@java_method('()V')
		def run(self):
			try:
				self.func(*self.args, **self.kwargs)
			except:
				import traceback
				traceback.print_exc()

			Runnable.__runnables__.remove(self)

	def run_on_ui_thread(f):
		'''Decorator to create automatically a :class:`Runnable` object with the
		function. The function will be delayed and call into the Activity thread.
		'''
		def f2(*args, **kwargs):
			Runnable(f)(*args, **kwargs)
		return f2

jPythonActivity = autoclass({'pygame':'org.renpy.android.PythonActivity', 'sdl2':'org.kivy.android.PythonActivity'}[bootstrap])
jLinearLayout   = autoclass('android.widget.LinearLayout')
jAbsoluteLayout = autoclass('android.widget.AbsoluteLayout')
jLayoutParams   = autoclass('android.view.ViewGroup$LayoutParams')
jSurfaceView    = autoclass("android.view.SurfaceView")
jSurfaceHolder  = autoclass('android.view.SurfaceHolder')
jTextureView    = autoclass("android.view.TextureView")

if bootstrap == 'pygame':
	class TouchListener(PythonJavaClass):
		__javacontext__ = 'app'
		__javainterfaces__ = ['org/renpy/android/SDLSurfaceView$OnInterceptTouchListener']

		def __init__(self, listener):
			super(TouchListener, self).__init__()
			self.listener = listener

		@java_method('(Landroid/view/MotionEvent;)Z')
		def onTouch(self, event):
			x = event.getX(0)
			y = event.getY(0)
			return self.listener(x, y)
else:
	print 'WARNING. SDL2 build use stub for TouchListener'   
	class TouchListener():
		def __init__(self, listener):
			pass

class AndroidWidgetHolder(Widget):
	'''Act as a placeholder for an Android widget.
	It will automatically add / remove the android _native_view depending if the widget
	_native_view is set or not. The android _native_view will act as an overlay, so any graphics
	instruction in this area will be covered by the overlay.

	args:
		native_view_factory	- factory to get native view from
		native_view_inializer  - initializer for native view
	props:
		ready	- widget is inited and ready for use
	'''

	ready = BooleanProperty(False)
	_native_view = ObjectProperty(allownone=True)
	'''Must be an Android View
	'''

	def __init__(self, native_view_factory, **kwargs):
		# force Window clearcolor to be transparent.
		Window.clearcolor = (0, 0, 0, 0)

		self._native_view = None
		self._native_view_factory = native_view_factory 											 
		self._parent_layout = None 											 
		self._touch_listener = TouchListener(self._on_touch_listener)
		self._create_native_view_trigger = Clock.create_trigger(self._create_native_view)
		self._reposition_trigger = Clock.create_trigger(self._reposition_view)

		#from kivy.app import App
		#App.get_running_app().bind(on_resume=self._reorder)
		super(AndroidWidgetHolder, self).__init__(**kwargs)

		self._create_native_view_trigger()

	def _get_view_bbox(self):
		x, y = self.to_window(*self.pos)
		w, h = self.size
		return [int(z) for z in [x, Window.height - y - h, w, h]]

	@run_on_ui_thread																		   
	def _create_native_view(self, *args):
		Logger.info('NativeWidget: creating native view')															

		context = jPythonActivity.mActivity
		native_view = self._native_view_factory(context)

		if native_view is None:
			Logger.info('NativeWidget: none from factory')															
			return
		
		x, y, w, h = self._get_view_bbox()

		# XXX we assume it's the default layout from main.xml
		# It could break.
		if bootstrap == 'pygame':
			self._parent_layout = cast(jLinearLayout, jPythonActivity.mView.getParent())
			self._parent_layout.addView(native_view, 0, jLayoutParams(w, h))
		elif bootstrap == 'sdl2':
			jPythonActivity.setTransparentSurface()
			self._parent_layout = cast(jAbsoluteLayout, jPythonActivity.getLayout().getParent())
			self._parent_layout.addView(native_view, 0, jLayoutParams(w, h))
		else:
			raise 'unsupported bootstap {}'.format(bootstrap)


		native_view.setX(x)
		native_view.setY(y)

		Logger.info('NativeWidget: native view added (x=%d, y=%d, w=%d, h=%d)'%(x, y, w, h))

		# we need to differenciate if there is interaction with our holder or not.
		# XXX must be activated only if the _native_view is displayed on the screen!
		if bootstrap == 'pygame':
			jPythonActivity.mView.setInterceptTouchListener(self._touch_listener)
		
		self._native_view = native_view
		self.ready = True
		
	@run_on_ui_thread																		   
	def _reposition_view(self, *args):
		native_view = self._native_view
		if native_view:
			x, y, w, h = self._get_view_bbox()
			Logger.info('NativeWidget: {} {} repositioning to {}'.format(self.pos, self.size, (x, y, w, h)))
			params = native_view.getLayoutParams()
			if not params:
				Logger.info('NativeWidget: repositioning failed')
				return
			params.width = w
			params.height = h
			native_view.setLayoutParams(params)
			native_view.setX(x)
			native_view.setY(y)

	def _remove_view(self, instance, view):
		if self._native_view is not None:
			# XXX probably broken
			layout = cast(jLinearLayout, self._native_view.getParent())
			layout.removeView(self._native_view)
			self._native_view = None
			Logger.info('NativeView: view removed')

	def on_ready(self, instance, ready):
		Logger.info('NativeView: on_ready()')
		pass
	def on_size(self, instance, value):
		Logger.info('NativeWidget: on_size {}'.format(value))
		self._reposition_trigger()											 

	def on_pos(self, instance, value):
		Logger.info('NativeWidget: on_pos {}'.format(value))
		self._reposition_trigger()											 

	#
	# Determine if the touch is going to be for us, or for the android widget.
	# If we find any Kivy widget behind the touch (except us), then avoid the
	# dispatching to the map. The touch will be received by the widget later.
	#

	def _on_touch_listener(self, x, y):
		# invert Y !
		y = Window.height - y
		# x, y are in Window coordinate. Try to select the widget under the
		# touch.
		widget = None
		for child in reversed(Window.children):
			widget = self._pick(child, x, y)
			if not widget:
				continue
		if self is widget:
			return True

	def _pick(self, widget, x, y):
		ret = None
		if widget.collide_point(x, y):
			ret = widget
			x2, y2 = widget.to_local(x, y)
			for child in reversed(widget.children):
				ret = self._pick(child, x2, y2) or ret
		return ret

###########################################################################################################
#
#    for android.view.View inherited
#
###########################################################################################################

class AndroidNativeViewWidget(Widget):
	def __init__(self, **kwargs):
		self._nativeHolder = None															   
		super(AndroidNativeViewWidget, self).__init__(**kwargs)

		self._nativeHolder = nativeHolder = AndroidWidgetHolder(self.native_view_factory, **kwargs)
		self.add_widget(nativeHolder)
		self.bind(
				size=nativeHolder.setter('size'),
				pos=nativeHolder.setter('pos'))

	def native_view_factory(self, context):
		raise "native_view_factory(self, context)  must be defined in AndroidNativeViewWidget inherited classes"

	def get_native_pos(self):
		return (self._nativeHolder.x - self.x, self._nativeHolder.y - self.y) 
	def get_native_size(self):
		return self._nativeHolder.size
	def set_native_pos(self, pos):
		self._nativeHolder.pos = (pos[0] + self.x, pos[1] + self.y)
	def set_native_size(self, size):
		self._nativeHolder.size = size

###########################################################################################################
#
#    for android.view.SurfaceView inherited
#
###########################################################################################################

class SurfaceHolderCallbacksRedirector(PythonJavaClass):
	'''
	Interface used to know exactly when the Surface used will be created and changed.
	'''
	__javainterfaces__ = ['android.view.SurfaceHolder$Callback']
	__javacontext__ = 'app'

	def __init__(self, host):
		super(SurfaceHolderCallbacksRedirector, self).__init__()
		self._host = host

	# abstract void surfaceChanged (SurfaceHolder holder, int format, int width, int height)
	@java_method('(Landroid/view/SurfaceHolder;III)V')
	def surfaceChanged(self, holder, fmt, width, height):
		Logger.info('SurfaceHolderCallback: surfaceChanged')
		try: self._host.on_surface_changed(holder, fmt, width, height)
		except AttributeError: pass

	# abstract void surfaceCreated (SurfaceHolder holder)
	@java_method('(Landroid/view/SurfaceHolder;)V')
	def surfaceCreated(self, holder):
		Logger.info('SurfaceHolderCallback: surfaceCreated')
		try: self._host.on_surface_created(holder)
		except AttributeError: pass

	# abstract void surfaceDestroyed (SurfaceHolder holder)
	@java_method('(Landroid/view/SurfaceHolder;)V')
	def surfaceDestroyed(self, holder):
		Logger.info('SurfaceHolderCallback: surfaceDestroyed')
		try: self._host.on_surface_destroyed(holder)
		except AttributeError: pass


class AndroidSurfaceWidget(AndroidNativeViewWidget):
	def __init__(self, **kwargs):
		self.surfaceView = None															   
		super(AndroidSurfaceWidget, self).__init__(**kwargs)

	def native_view_factory(self, context):
		# create a fake surfaceview
		self.surfaceView = surfaceView = jSurfaceView(context)
		Logger.info('AndroidSurfaceWidget: surfaceView created')

		self.populate_surface_view(surfaceView, context) # must be defined in inherited classes
		Logger.info('AndroidSurfaceWidget: surfaceView populated')

		# set callbacks
		self._surfaceHolderCallbacksRedirector = SurfaceHolderCallbacksRedirector(self)
		surfaceView.getHolder().addCallback(self._surfaceHolderCallbacksRedirector)
		Logger.info('AndroidSurfaceWidget: surfaceView callbacks activated')

		return surfaceView

	def populate_surface_view(self, surfaceView, context):
		raise "populate_surface_view(self, surfaceView, context)  must be defined in AndroidSurfaceWidget inherited classes"

	def on_surface_created(self, surfaceHolder):
		Logger.info('AndroidSurfaceWidget: _on_surface_created')
		pass
	def on_surface_changed(self, surfaceHolder, fmt, width, height):
		# internal, called when the android SurfaceView is ready
		Logger.info('AndroidSurfaceWidget: _on_surface_changed (%d, %d), %x'%(width, height, fmt))
		pass
	def on_surface_destroyed(self, surfaceHolder):
		Logger.info('AndroidSurfaceWidget: _on_surface_destroyed')
		pass

###########################################################################################################
#
#    for android.view.TextureView inherited
#
###########################################################################################################

class SurfaceTextureListenerRedirector(PythonJavaClass):
	__javainterfaces__ = ['android/view/TextureView$SurfaceTextureListener']
	__javacontext__ = 'app'

	def __init__(self, host): 
		self._host = host
		super(SurfaceTextureListenerRedirector, self).__init__()

	#abstract void onSurfaceTextureAvailable (SurfaceTexture surface, int width, int height)
	@java_method('(Landroid/graphics/SurfaceTexture;II)V')
	def onSurfaceTextureAvailable(self, surfaceTexture, width, height):
		Logger.info('SurfaceTextureListener: SurfaceTextureAvailable')
		try: self._host.on_surface_texture_available(surfaceTexture, width, height)
		except AttributeError: pass

	#abstract void onSurfaceTextureSizeChanged (SurfaceTexture surface, int width, int height)
	@java_method('(Landroid/graphics/SurfaceTexture;II)V')
	def onSurfaceTextureSizeChanged(self, surfaceTexture, width, height):
		Logger.info('SurfaceTextureListener: SurfaceTextureSizeChanged')
		try: self._host.on_surface_texture_size_changed(surfaceTexture, width, height)
		except AttributeError: pass

	#abstract void onSurfaceTextureUpdated (SurfaceTexture surface)
	@java_method('(Landroid/graphics/SurfaceTexture;)V')
	def onSurfaceTextureUpdated(self, surfaceTexture):
		Logger.info('SurfaceTextureListener: SurfaceTextureUpdated')
		try: self._host.on_surface_texture_updated(surfaceTexture)
		except AttributeError: pass

	#abstract boolean onSurfaceTextureDestroyed (SurfaceTexture surface)
	@java_method('(Landroid/graphics/SurfaceTexture;)Z')
	def onSurfaceTextureDestroyed(self, surfaceTexture):
		Logger.info('SurfaceTextureListener: SurfaceTextureDestroyed')
		if self._onSurfaceTextureDestroyedCallback: return self._onSurfaceTextureDestroyedCallback(surfaceTexture)
		try: self._host.on_surface_texture_destroyed(surfaceTexture)
		except AttributeError: pass
		return True


class AndroidTextureWidget(AndroidNativeViewWidget):
	def __init__(self, **kwargs):
		self.textureView = None															   
		super(AndroidTextureWidget, self).__init__(**kwargs)

	def native_view_factory(self, context):
		# Create a fake TextureView
		self.textureView = textureView = jTextureView(context)

		self.populate_texture_view(textureView, context)

		# set callbacks
		self._surfaceTextureListenerRedirector = SurfaceTextureListenerRedirector(
					onSurfaceTextureAvailable = self.on_texture_available,
					onSurfaceTextureSizeChangedCallback = self.on_texture_resize,
					onSurfaceTextureUpdatedCallback = self.on_texture_update,
					onSurfaceTextureDestroyedCallback = self.on_texture_destroy,
				)
		textureView.setSurfaceTextureListener(self._surfaceTextureListenerRedirector)
		return textureView

	def populate_texture_view(self, textureView, context):
		raise "populate_texture_view(self, textureView, context)  must be defined in AndroidTextureWidget child classes"

	def on_texture_available(self, surfaceTexture, width, height):
		Logger.info('AndroidTextureWidget: on_texture_available (%d, %d)'%(width, height))
		pass
	def on_texture_resize(self, surfaceTexture, width, height):
		Logger.info('AndroidTextureWidget: on_texture_resize (%d, %d)'%(width, height))
		pass
	def on_texture_update(self, surfaceTexture):
		Logger.info('AndroidTextureWidget: on_texture_update')
		pass
	def on_texture_destroy(self, surfaceTexture):
		Logger.info('AndroidTextureWidget: on_texture_destroy')
		self.destroy_video_player(surfaceTexture)
		pass
