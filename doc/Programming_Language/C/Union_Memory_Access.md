## Unexpected change in union memory access

The following code demonstrate unexpected value change in memory access of a union

```
#include <stdio.h>
int main()
{
    union sf_un {
        short val;  // size = 2
        char ch;    // size = 1
    };
    union sf_un u;
    
    u.val = 258;
    u.ch=4;
    printf("val: %d\n", u.val );    //output 260 little endian machine
    printf("char: %d\n", u.ch );    //output 6 little endian machine 
}
```

**Root Cause**
* union allocates the memory space equal to the size of the biggest member.
* union member accessed the same memory spacem, and may override one another. 
* in this case 258 is　`0x0102`; `02` is overriden by `ch=0x04`; in the end we have `u.val = 0x0104` or `260`