/*
 * Cyfry siedmiosegmentowe (wyświetlacz jak w kalkulatorze) - sama geometria, w czystym C, żeby dało się ją przetestować.
 *
 * Segmenty:   aaa
 *            f   b
 *             ggg
 *            e   c
 *             ddd
 */
#ifndef WL_SEG_H
#define WL_SEG_H

#ifdef __cplusplus
extern "C" {
#endif

/* Maska segmentów (bit 0 = a ... bit 6 = g) dla '0'-'9' i '-'; 0 dla reszty. */
int wl_seg_mask(int ch);

/* Rodzaj znaku: 0 cyfra albo minus (pełna komórka), 1 kropka lub przecinek (wąska), 2 odstęp (wąski), -1 nieobsługiwany. */
int wl_seg_kind(int ch);

/* Wierzchołki jednego segmentu (0..6 = a..g) w komórce x,y,w,h; grubość kreski t, szczelina g.
   Wypełnia 6 punktów (12 liczb). */
void wl_seg_poly(int seg, float x, float y, float w, float h, float t, float g, float *pts);

/* Ułożenie napisu (UTF-8 jest sprowadzone do bajtów ASCII; NBSP = 0xC2 0xA0 liczy się jako odstęp):
   dla wysokości cyfry 1.0 zwraca łączną szerokość i wypełnia wiersz komórek.
   cells[i] = znak ASCII, xs[i] = lewa krawędź komórki. Zwraca liczbę komórek (maks. n). */
int wl_seg_layout(const char *text, int *cells, float *xs, int n, float *total_width);

#define WL_SEG_DIGIT_W 0.56f     /* szerokość komórki cyfry przy wysokości 1 */
#define WL_SEG_GAP     0.16f     /* odstęp między komórkami */
#define WL_SEG_DOT_W   0.17f     /* szerokość komórki kropki */
#define WL_SEG_SPACE_W 0.28f     /* szerokość odstępu */
#define WL_SEG_THICK   0.115f    /* grubość kreski */

#ifdef __cplusplus
}
#endif

#endif
