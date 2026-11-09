#define _GNU_SOURCE
#include <dlfcn.h>
#include <execinfo.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <unistd.h>

/* Diagnostic interposer: records only the first four pthread_create call stacks.
 * It changes execution timing and is not used for performance measurements. */
int pthread_create(pthread_t *thread, const pthread_attr_t *attr,
                   void *(*start)(void *), void *arg) {
    static int (*next)(pthread_t *, const pthread_attr_t *, void *(*)(void *), void *);
    static _Atomic unsigned count;
    if (!next) next = dlsym(RTLD_NEXT, "pthread_create");
    unsigned n = atomic_fetch_add(&count, 1);
    if (n < 4) {
        void *frames[32];
        int size = backtrace(frames, 32);
        dprintf(STDERR_FILENO, "\nPTHREAD_CREATE_DIAGNOSTIC %u\n", n + 1);
        backtrace_symbols_fd(frames, size, STDERR_FILENO);
    }
    return next(thread, attr, start, arg);
}
