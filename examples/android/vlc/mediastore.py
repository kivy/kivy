__all__ = ('query_storage_video')

from jnius import autoclass, cast

try:
    bootstrap = 'pygame'
    import android.runnable
except ImportError:
    bootstrap = 'sdl2'

if bootstrap == 'sdl2':
    print 'WARNING: query_storage_video() stub used'
    def query_storage_video(maxCount=None):
        return []
else:
    jPythonActivity = autoclass(
            'org.renpy.android.PythonActivity')
    jMediaStoreVideoMedia = autoclass(
            'android.provider.MediaStore$Video$Media')
    jMediaStoreMediaColumns = autoclass(
            'android.provider.MediaStore$MediaColumns')

    def query_storage_video(maxCount=None):
        cursor = jPythonActivity.mActivity.getContentResolver().query(
                        jMediaStoreVideoMedia.EXTERNAL_CONTENT_URI,
                        [jMediaStoreMediaColumns.DATA],
                        None, None, None)
        if not cursor:
            return []
        result = []
        while (maxCount is None or len(res) < maxCount) and cursor.moveToNext():
            s = cursor.getString(0)
            result.append(s)
        cursor.close()
        return result

def test():
    print query_storage_video()
    
if __name__ == '__main__':
    test()
