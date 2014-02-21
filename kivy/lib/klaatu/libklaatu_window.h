#ifndef __libklaatu_window_h_
#define __libklaatu_window_h_
#define VALUE_TO_STRING(x) #x
#define VALUE(x) VALUE_TO_STRING(x)
#define VAR_NAME_VALUE(var) #var "="  VALUE(var)
unsigned int klaatu_get_window(int w, int h);
void klaatu_get_display_size(int* w, int* h);


#endif
