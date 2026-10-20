#include <stddef.h>

int main(void) {
    return (int)offsetof(struct { int value; }, value);
}
