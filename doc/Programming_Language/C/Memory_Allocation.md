## Dynamic memory allocation: malloc / calloc / realloc / free

All declared in `<stdlib.h>`. All return `void*`, `NULL` on failure — always check.

| Function             | Purpose                                                | Initializes memory?                    | Notes                                                                                            |
| -------------------- | ------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `malloc(size)`        | Allocate one block of `size` bytes                       | No — garbage content                    | Fastest; fine when you write before you read                                                       |
| `calloc(n, size)`     | Allocate `n × size` bytes                                 | Yes — zero-filled                       | Also guards against `n * size` overflow, unlike a manual `malloc(n * size)`                         |
| `realloc(ptr, size)`  | Resize a block to `size` bytes, preserving existing content | Only the newly grown region             | May move the block — always reassign the returned pointer; `realloc(NULL, size)` behaves like `malloc(size)` |
| `free(ptr)`           | Deallocate a block from `malloc`/`calloc`/`realloc`       | n/a                                      | Every successful allocation needs exactly one `free`; double free / use-after-free is undefined behavior |

**Pitfall to remember**: `ptr = realloc(ptr, newSize);` leaks memory on failure — if `realloc` fails it returns `NULL` and leaves the original block untouched, but the assignment just overwrote `ptr` with `NULL`. Use a temporary instead:
```c
void *tmp = realloc(ptr, newSize);
if (tmp) ptr = tmp;
```
