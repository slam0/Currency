#import <UIKit/UIKit.h>

/* Elementy "z metalu": szczotkowane aluminium, śrubki, chrom, płyta z wyświetlaczami LCD (cyfry siedmiosegmentowe). */

/* Przezroczysta płytka z poziomymi smugami szczotkowania (do kafelkowania na gradiencie). */
UIImage *WLBrushedOverlay(void);

/* Wypełnia prostokąt pionowym gradientem o kilku przystankach i (gdy texture > 0) smugami szczotkowania. */
void WLMetalFill(CGContextRef c, CGRect r, NSArray *colors, const CGFloat *locations, CGFloat texture);

/* Śrubka z krzyżakiem. variant 0..3 = różne obroty krzyżaka. */
UIImage *WLScrewImage(CGFloat diameter, int variant);

/* Chromowany przycisk (rozciągliwy), jak w iOS 6 – jasny u góry, z "horyzontem" w połowie. */
UIImage *WLChromeImage(void);

/* Płyta (jak front urządzenia): metal albo grafit zależnie od motywu, śrubki w rogach, rowek poziomy. */
@interface WLPlateView : UIView
@property (nonatomic) CGFloat grooveY;           /* 0 = bez rowka */
@end

/* Wyświetlacz LCD z cyframi siedmiosegmentowymi, tekst wyrównany do prawej. */
@interface WLLCDView : UIView
@property (nonatomic, copy) NSString *text;
@property (nonatomic) BOOL showsCursor;          /* migający kursor po prawej, gdy edytujemy */
@end
