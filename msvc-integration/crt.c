#ifdef _DLL
#error "static CRT requested but dynamic CRT selected"
#endif
int main(void) { return 0; }
