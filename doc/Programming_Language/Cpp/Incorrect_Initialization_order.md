## Incorrect synchronization orders
The following code demonstrate errors caused by incorrect initialization order

```
#include <atomic>
#include <mutex>
#include <queue>
#include <thread>
#include <iostream>

struct Worker
{
    Worker() 
        : t ([this] (std::stop_token st)
        {
            while (!st.stop_requested())
            {
                std::lock_guard<std::mutex> lock (m);
                q.push(1);
                std::cout<<"loop runs "<<std::this_thread::get_id()<<std::endl;
            }
        })
    {}
    std::jthread t;
    std::mutex m;
    std::queue<int> q;
};

int main()
{
    Worker w1;
    Worker w2;
    Worker w3;
    std::cout<<"program stops"<<std::endl;
}
```

**Output errors**: 
```
loop runs loop runs 124000783435456
loop runs 124000783435456
loop runs 124000783435456

loop runs 124000775042752
loop runs 124000775042752
loop runs 124000775042752

program stops124000783435456
loop runs 
124000766650048loop runs 124000775042752

loop runs 124000775042752
loop runs 124000775042752
loop runs 124000775042752
loop runs 124000783435456
loop runs 124000783435456
loop runs 124000783435456

```

**Root cause analysis**

1. **Construction order** — members construct in declaration order:
   ```cpp
   std::jthread t;      // 1st: constructed -> thread starts running now
   std::mutex m;        // 2nd
   std::queue<int> q;   // 3rd
   ```
   - Thread `t` is created first and immediately accesses mutex `m` and queue `q` while they are still being constructed. May cause undefined behavior.

2. **Destruction order** — reverse of declaration order:
   ```cpp
   ~q();   // 1st: destroyed
   ~m();   // 2nd: destroyed
   ~t();   // 3rd: jthread dtor -> request_stop() + join()
   ```
   - `m` and `q` are destroyed first, before thread `t`, which may still be using them, causing undefined behavior.
   - Fix: declare `m` and `q` before `t`, so the thread starts last and stops/joins first.

3. **Is this a race condition?** Yes — but not between workers:
   - **Not cross-worker**: each `Worker`'s `m`/`q` are private to that instance, so `w1` and `w2` never touch each other's memory.
   - **Within a single worker**: `m`/`q` are shared between two threads — `main` (constructs/destroys them) and that worker's own spawned thread `t` (uses them concurrently). Unsynchronized access to the same object, with one side destroying it, is a data race regardless of other workers.
   - **`std::cout`**: genuinely shared across every worker's thread plus `main`, with no lock protecting it — a real cross-worker race, and why output lines interleave/merge.

**Clean fix**

Declare `m` and `q` before `t` so the thread is constructed last (after its dependencies exist) and destroyed first (its destructor calls `request_stop()` + `join()`, so the thread has fully exited before `m`/`q` are torn down):

```cpp
struct Worker
{
    std::mutex m;
    std::queue<int> q;
    std::jthread t{ [this] (std::stop_token st)
        {
            while (!st.stop_requested())
            {
                std::lock_guard<std::mutex> lock (m);
                q.push(1);
                std::cout << "loop runs " << std::this_thread::get_id() << std::endl;
            }
        } };
};
```

This removes both the construction-order and destruction-order undefined behavior. It does **not** fix the separate `std::cout` race — that needs its own shared lock (e.g. a `static inline std::mutex coutMutex;`), kept apart from `m` since it protects a different, globally-shared resource rather than this worker's own queue.

**Clean fix for the `std::cout` race**

`std::cout` is shared by every `Worker` instance, so it needs one lock shared across all of them — a `static` (or `static inline`) mutex, not a per-instance member — locked separately from `m` since it guards a different resource:

```cpp
struct Worker
{
    static inline std::mutex coutMutex;
    std::mutex m;
    std::queue<int> q;
    std::jthread t{ [this] (std::stop_token st)
        {
            while (!st.stop_requested())
            {
                {
                    std::lock_guard<std::mutex> lock (m);
                    q.push(1);
                }
                std::lock_guard<std::mutex> coutLock (coutMutex);
                std::cout << "loop runs " << std::this_thread::get_id() << std::endl;
            }
        } };
};
```

- `coutMutex` is `static`, so all `Worker` instances lock the *same* mutex — that's what actually serializes the writes; a per-instance mutex would only stop a worker from racing itself.
- The `q.push(1)` critical section is scoped in its own block so `m` is released before acquiring `coutMutex` — avoids holding two locks longer than necessary and keeps each mutex tied to exactly the resource it protects.