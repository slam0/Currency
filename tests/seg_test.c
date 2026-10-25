/* Testy geometrii cyfr: gcc -Wall wl_seg.c tests/seg_test.c -o seg_test && ./seg_test */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "../wl_seg.h"

static int fails = 0, checks = 0;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("BŁĄD (linia %d): %s\n", __LINE__, #c); } } while (0)

static int popcount(int v) { int c = 0; while (v) { c += v & 1; v >>= 1; } return c; }

int main(void)
{
    int i, s;
    float pts[12];
    int cells[40]; float xs[40]; float tw;
    int n;

    /* liczba segmentów w cyfrach */
    CHECK(popcount(wl_seg_mask('0')) == 6 && popcount(wl_seg_mask('1')) == 2 && popcount(wl_seg_mask('7')) == 3);
    CHECK(popcount(wl_seg_mask('8')) == 7 && popcount(wl_seg_mask('4')) == 4 && popcount(wl_seg_mask('9')) == 6);
    CHECK(wl_seg_mask('-') == 64 && wl_seg_mask('x') == 0 && wl_seg_mask(' ') == 0);
    /* każda cyfra jest inna */
    for (i = 0; i < 10; i++) { int j; for (j = i + 1; j < 10; j++) CHECK(wl_seg_mask('0' + i) != wl_seg_mask('0' + j)); }

    /* segmenty leżą w komórce i mają dodatnią powierzchnię */
    for (s = 0; s < 7; s++) {
        int k, ok = 1;
        float area = 0;
        wl_seg_poly(s, 10, 20, 0.56f * 100, 100, 11.5f, 1.5f, pts);
        for (k = 0; k < 6; k++) {
            if (pts[2 * k] < 10 - 0.01f || pts[2 * k] > 10 + 56.01f || pts[2 * k + 1] < 20 - 0.01f || pts[2 * k + 1] > 120.01f) ok = 0;
            { int k2 = (k + 1) % 6; area += pts[2 * k] * pts[2 * k2 + 1] - pts[2 * k2] * pts[2 * k + 1]; }
        }
        CHECK(ok);
        CHECK(fabsf(area) > 50.0f);
    }

    /* układ napisu */
    n = wl_seg_layout("1 234,56", cells, xs, 40, &tw);
    CHECK(n == 8);
    CHECK(cells[0] == '1' && cells[1] == ' ' && cells[2] == '2' && cells[5] == ',' && cells[7] == '6');
    { int k, mono = 1; for (k = 1; k < n; k++) if (xs[k] <= xs[k - 1]) mono = 0; CHECK(mono); }
    CHECK(tw > 0 && tw < 10);
    n = wl_seg_layout("1\xC2\xA0" "234,56", cells, xs, 40, &tw);                 /* twarda spacja */
    CHECK(n == 8 && cells[1] == ' ');
    n = wl_seg_layout("\xE2\x80\x94", cells, xs, 40, &tw);                         /* "—" */
    CHECK(n == 1 && cells[0] == '-' && fabsf(tw - WL_SEG_DIGIT_W) < 1e-5f);
    n = wl_seg_layout("", cells, xs, 40, &tw);
    CHECK(n == 0 && tw == 0.0f);
    n = wl_seg_layout(0, cells, xs, 40, &tw);
    CHECK(n == 0);
    n = wl_seg_layout("   12", cells, xs, 40, &tw);                               /* odstępy na początku pomijane */
    CHECK(n == 2 && xs[0] == 0.0f);
    n = wl_seg_layout("12345678901234567890", cells, xs, 5, &tw);                 /* limit komórek */
    CHECK(n == 5);
    n = wl_seg_layout("1a2", cells, xs, 40, &tw);                                  /* litery pomijane */
    CHECK(n == 2);
    n = wl_seg_layout("\xC5", cells, xs, 40, &tw);                                 /* ucięty bajt UTF-8 nie wychodzi poza napis */
    CHECK(n == 1);

    printf("%s: %d sprawdzeń, %d błędów\n", fails ? "NIE ZDAŁO" : "OK", checks, fails);
    return fails ? 1 : 0;
}
