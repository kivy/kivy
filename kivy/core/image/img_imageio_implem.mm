#include "img_imageio_implem.h"

/*
* KivyImageIOProviderSupportedExtensionList
*/

KivyImageIOProviderSupportedExtensionList::KivyImageIOProviderSupportedExtensionList()
{
    this->extensions = [[NSMutableArray alloc] init];
}

KivyImageIOProviderSupportedExtensionList::~KivyImageIOProviderSupportedExtensionList()
{
}

void KivyImageIOProviderSupportedExtensionList::add(NSString *extension)
{
    if (![this->extensions containsObject:extension])
    {
        [this->extensions addObject:extension];
    }
}

int KivyImageIOProviderSupportedExtensionList::count()
{
    return [this->extensions count];
}

char *KivyImageIOProviderSupportedExtensionList::get(int index)
{
    NSString *extension = [this->extensions objectAtIndex:index];
    return (char *)[extension UTF8String];
}

void KivyImageIOProviderSupportedExtensionList::clear()
{
    [this->extensions removeAllObjects];
}

/*
* KivyImageIOProvider
*/

KivyImageIOProvider::KivyImageIOProvider()
{
    this->supported_source_image_extensions = new KivyImageIOProviderSupportedExtensionList();
    this->load_supported_source_extensions();
}

KivyImageIOProvider::~KivyImageIOProvider()
{
    delete this->supported_source_image_extensions;
}

void KivyImageIOProvider::load_supported_source_extensions()
{
    this->supported_source_image_extensions->clear();

    CFArrayRef type_identifiers = CGImageSourceCopyTypeIdentifiers();

    for (CFIndex i = 0; i < CFArrayGetCount(type_identifiers); i++)
    {
        CFStringRef uti = (CFStringRef)CFArrayGetValueAtIndex(type_identifiers, i);
        NSArray *uti_extensions;

        if (@available(macOS 11.0, iOS 14.0, tvOS 14.0, watchOS 7.0, *))
        {
            UTType *uttype = [UTType typeWithIdentifier:(NSString *)uti];
            uti_extensions = uttype.tags[@"public.filename-extension"];
        }
        else
        {
            // UTTypeCopyAllTagsWithClass is deprecated, we're leaving this here
            // for compatibility with older versions of macOS and iOS
            uti_extensions = CFBridgingRelease(
                UTTypeCopyAllTagsWithClass(uti, kUTTagClassFilenameExtension));
        }

        for (NSString *extension in uti_extensions)
        {
            this->supported_source_image_extensions->add(extension);
        }
    }
}