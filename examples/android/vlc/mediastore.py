__all__ = ('query_storage_video')

from android.runnable import run_on_ui_thread
from jnius import autoclass, cast

jPythonActivity   = autoclass('org.renpy.android.PythonActivity')
jMediaStoreVideoMedia  = autoclass('android.provider.MediaStore$Video$Media')
jMediaStoreMediaColumns  = autoclass('android.provider.MediaStore$MediaColumns')

def query_storage_video(maxCount=None):
	result = []
#	print('AndroidMediaStore: query_storage_video...')
	cursor = jPythonActivity.mActivity.getContentResolver().query(
					jMediaStoreVideoMedia.EXTERNAL_CONTENT_URI,
					[jMediaStoreMediaColumns.DATA],
					None, None, None)
	if cursor:
#		print("AndroidMediaStore: N: {}".format(cursor.getCount()))
		while (maxCount is None or len(res) < maxCount) and cursor.moveToNext():
			s = cursor.getString(0)
#			print("AndroidMediaStore: VIDEO: {}".format(s))
			result.append(s)
		cursor.close()
	return result

def test():
	print query_storage_video()
	
if __name__ == '__main__':
	test()
