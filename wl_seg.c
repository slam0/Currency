#include "wl_seg.h"

int wl_seg_mask(int ch)
{
    /* bity: a=1 b=2 c=4 d=8 e=16 f=32 g=64 */
    static const int digits[10] = {
        1 + 2 + 4 + 8 + 16 + 32,          /* 0 */
        2 + 4,                            /* 1 */
        1 + 2 + 8 + 16 + 64,              /* 2 */
        1 + 2 + 4 + 8 + 64,               /* 3 */
        2 + 4 + 32 + 64,                  /* 4 */
        1 + 4 + 8 + 32 + 64,              /* 5 */
        1 + 4 + 8 + 16 + 32 + 64,         /* 6 */
        1 + 2 + 4,                        /* 7 */
        127,                              /* 8 */
        1 + 2 + 4 + 8 + 32 + 64           /* 9 */
    };
    if (ch >= '0' && ch <= '9') return digits[ch - '0'];
    if (ch == '-') return 64;
    return 0;
}

int wl_seg_kind(int ch)
{
    if ((ch >= '0' && ch <= '9') || ch == '-') return 0;
    if (ch == '.' || ch == ',') return 1;
    if (ch == ' ') return 2;
    return -1;
}

static void hbar(float *p, float x0, float x1, float cy, float t)
{
    float h = t * 0.5f;
    p[0] = x0;     p[1] = cy;
    p[2] = x0 + h; p[3] = cy - h;
    p[4] = x1 - h; p[5] = cy - h;
    p[6] = x1;     p[7] = cy;
    p[8] = x1 - h; p[9] = cy + h;
    p[10] = x0 + h; p[11] = cy + h;
}

static void vbar(float *p, float cx, float y0, float y1, float t)
{
    float h = t * 0.5f;
    p[0] = cx;     p[1] = y0;
    p[2] = cx + h; p[3] = y0 + h;
    p[4] = cx + h; p[5] = y1 - h;
    p[6] = cx;     p[7] = y1;
    p[8] = cx - h; p[9] = y1 - h;
    p[10] = cx - h; p[11] = y0 + h;
}

void wl_seg_poly(int seg, float x, float y, float w, float h, float t, float g, float *pts)
{
    float xl = x + t * 0.5f, xr = x + w - t * 0.5f;
    float ys = y + t * 0.5f, yb = y + h - t * 0.5f, ym = y + h * 0.5f;
    switch (seg) {
        case 0: hbar(pts, xl + g, xr - g, ys, t); break;               /* a */
        case 1: vbar(pts, xr, ys + g, ym - g, t); break;               /* b */
        case 2: vbar(pts, xr, ym + g, yb - g, t); break;               /* c */
        case 3: hbar(pts, xl + g, xr - g, yb, t); break;               /* d */
        case 4: vbar(pts, xl, ym + g, yb - g, t); break;               /* e */
        case 5: vbar(pts, xl, ys + g, ym - g, t); break;               /* f */
        default: hbar(pts, xl + g, xr - g, ym, t); break;              /* g */
    }
}

int wl_seg_layout(const char *text, int *cells, float *xs, int n, float *total_width)
{
    const unsigned char *p = (const unsigned char *)text;
    int count = 0;
    float x = 0.0f;
    int first = 1;
    while (p && *p && count < n) {
        int ch = *p, kind;
        if (ch == 0xC2 && p[1] == 0xA0) { ch = ' '; p += 2; }
        else if (ch >= 0x80) {                      /* inny znak spoza ASCII (np. "—"): jak minus */
            int len = ch >= 0xF0 ? 4 : (ch >= 0xE0 ? 3 : (ch >= 0xC0 ? 2 : 1));
            int i;
            for (i = 1; i < len; i++) if (!p[i]) { len = i; break; }
            p += len;
            ch = '-';
        } else p++;
        kind = wl_seg_kind(ch);
        if (kind < 0) continue;
        if (kind == 0) {
            if (!first) x += WL_SEG_GAP;
            cells[count] = ch; xs[count] = x; count++;
            x += WL_SEG_DIGIT_W;
        } else if (kind == 1) {
            x += WL_SEG_GAP * 0.5f;
            cells[count] = ch; xs[count] = x; count++;
            x += WL_SEG_DOT_W;
        } else {
            if (first) continue;                    /* odstęp na początku pomijamy */
            x += WL_SEG_SPACE_W;
            cells[count] = ' '; xs[count] = x; count++;
        }
        first = 0;
    }
    *total_width = x;
    return count;
}
