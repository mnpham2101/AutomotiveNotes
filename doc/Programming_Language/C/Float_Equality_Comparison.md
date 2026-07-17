## Float vs double precision mismatch in equality comparison

The following code demonstrates why comparing floating-point values with `==` is unreliable

```c
#include <stdio.h>
int main()
{
    float f = 0.1;
    if (f == 0.1)
        printf("True");
    else
        printf("False");
}
```

**Output**: `False` — even though both sides look like "the same number."

**Root cause**

1. `0.1` has no exact binary representation — `f` stores only the nearest `float` approximation, but exact `==` needs bit-for-bit precision.
2. `f == 0.1` compares a `float` against a `double`: the unsuffixed literal `0.1` is a `double`, a different (more precise) approximation than what got rounded into `f`. Two different approximations of the same decimal value → unequal.

**Clean fix**

Never compare floating-point values with `==`. Compare with a tolerance (epsilon) instead:

```c
#include <stdio.h>
#include <math.h>

int main()
{
    float f = 0.1f;              // f suffix: keeps this a float literal, avoids the mixed-precision round-trip
    if (fabsf(f - 0.1f) < 1e-6f)
        printf("True");
    else
        printf("False");
}
```
- The `f` suffix on `0.1f` makes both sides genuinely `float`, avoiding the mixed float/double comparison entirely.
- `fabsf(a - b) < epsilon` checks "close enough," which is the only meaningful way to compare two values that are fundamentally rounded approximations.
