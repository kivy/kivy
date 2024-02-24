#include <CoreServices/CoreServices.h>
#include <Foundation/Foundation.h>
#include <UniformTypeIdentifiers/UniformTypeIdentifiers.h>

class KivyImageIOProviderSupportedExtensionList {
    public:
        KivyImageIOProviderSupportedExtensionList();
        ~KivyImageIOProviderSupportedExtensionList();
        void add(NSString* extension);
        char* get(int index);
        int count();
        void clear();
    private:
        NSMutableArray* extensions;
};

class KivyImageIOProvider {
    public:
        KivyImageIOProvider();
        ~KivyImageIOProvider();
        KivyImageIOProviderSupportedExtensionList* supported_source_image_extensions;
    private:
        void load_supported_source_extensions();
};