#include "run_length_encoding.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>

/**
 * Dynamic growing buffer structure for single-pass stream accumulation.
 */
typedef struct {
    char *data;
    size_t len;
    size_t cap;
} dyn_buffer_t;

static bool buf_init(dyn_buffer_t *buf, size_t initial_cap)
{
    buf->data = malloc(initial_cap);
    if (!buf->data)
        return false;
    buf->len = 0;
    buf->cap = initial_cap;
    buf->data[0] = '\0';
    return true;
}

static bool buf_reserve(dyn_buffer_t *buf, size_t additional)
{
    if (buf->len + additional + 1 > buf->cap) {
        size_t new_cap = buf->cap ? buf->cap * 2 : 16;
        while (new_cap < buf->len + additional + 1)
            new_cap *= 2;
        char *new_data = realloc(buf->data, new_cap);
        if (!new_data)
            return false;
        buf->data = new_data;
        buf->cap = new_cap;
    }
    return true;
}

static bool buf_append_char(dyn_buffer_t *buf, char c)
{
    if (!buf_reserve(buf, 1))
        return false;
    buf->data[buf->len++] = c;
    buf->data[buf->len] = '\0';
    return true;
}

static bool buf_append_uint(dyn_buffer_t *buf, size_t n)
{
    char temp[32];
    int written = snprintf(temp, sizeof(temp), "%zu", n);
    if (written < 0 || !buf_reserve(buf, (size_t)written))
        return false;
    memcpy(buf->data + buf->len, temp, (size_t)written);
    buf->len += (size_t)written;
    buf->data[buf->len] = '\0';
    return true;
}

static bool buf_append_repeat(dyn_buffer_t *buf, char c, size_t count)
{
    if (!buf_reserve(buf, count))
        return false;
    memset(buf->data + buf->len, c, count);
    buf->len += count;
    buf->data[buf->len] = '\0';
    return true;
}

/**
 * Approach 2: Single-pass streaming run-length encoder.
 */
char *encode(const char *text)
{
    if (text == NULL)
        return NULL;
    if (*text == '\0')
        return calloc(1, 1);

    dyn_buffer_t buf;
    if (!buf_init(&buf, 16))
        return NULL;

    const char *p = text;
    while (*p) {
        char ch = *p;
        size_t run_len = 0;
        while (*p == ch) {
            run_len++;
            p++;
        }
        if (run_len > 1) {
            if (!buf_append_uint(&buf, run_len)) {
                free(buf.data);
                return NULL;
            }
        }
        if (!buf_append_char(&buf, ch)) {
            free(buf.data);
            return NULL;
        }
    }

    return buf.data;
}

/**
 * Approach 2: Single-pass streaming run-length decoder.
 */
char *decode(const char *data)
{
    if (data == NULL)
        return NULL;
    if (*data == '\0')
        return calloc(1, 1);

    dyn_buffer_t buf;
    if (!buf_init(&buf, 16))
        return NULL;

    const char *p = data;
    while (*p) {
        size_t count = 0;
        bool has_count = false;
        while (isdigit((unsigned char)*p)) {
            has_count = true;
            count = count * 10 + (*p - '0');
            p++;
        }
        if (!*p)
            break;
        char ch = *p++;
        size_t repeats = has_count ? count : 1;
        if (!buf_append_repeat(&buf, ch, repeats)) {
            free(buf.data);
            return NULL;
        }
    }

    return buf.data;
}
