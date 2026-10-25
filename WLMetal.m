#import "WLMetal.h"
#import "WLTheme.h"
#import "wl_seg.h"

static UIColor *C(int r, int g, int b, CGFloat a)
{
    return [UIColor colorWithRed:r / 255.0f green:g / 255.0f blue:b / 255.0f alpha:a];
}

/* ---------- smugi szczotkowania ---------- */

UIImage *WLBrushedOverlay(void)
{
    static UIImage *img;
    if (img) return img;
    const int W = 192, H = 96;
    unsigned int seed = 20241025u;
    UIGraphicsBeginImageContextWithOptions(CGSizeMake(W, H), NO, 0.0f);
    CGContextRef c = UIGraphicsGetCurrentContext();
    for (int row = 0; row < H * 2; row++) {                 /* wiersze co pół punktu = piksel na ekranie retina */
        CGFloat y = row * 0.5f;
        for (int k = 0; k < 3; k++) {
            seed = seed * 1664525u + 1013904223u;
            int x0 = (int)((seed >> 8) % W);
            seed = seed * 1664525u + 1013904223u;
            int len = 24 + (int)((seed >> 8) % 120);
            seed = seed * 1664525u + 1013904223u;
            int shade = (int)((seed >> 12) & 1);
            int a = 3 + (int)((seed >> 16) % 9);             /* 3..11 setnych krycia */
            CGFloat alpha = a / 100.0f * (shade ? 1.0f : 0.8f);
            if (shade) [C(255, 255, 255, alpha) setFill]; else [C(0, 0, 0, alpha) setFill];
            CGContextFillRect(c, CGRectMake(x0, y, len, 0.5f));
            if (x0 + len > W) CGContextFillRect(c, CGRectMake(x0 - W, y, len, 0.5f));   /* zawinięcie: kafelki łączą się bez szwu */
        }
    }
    img = UIGraphicsGetImageFromCurrentImageContext();
    UIGraphicsEndImageContext();
    return img;
}

void WLMetalFill(CGContextRef c, CGRect r, NSArray *colors, const CGFloat *locations, CGFloat texture)
{
    CGColorSpaceRef cs = CGColorSpaceCreateDeviceRGB();
    CGGradientRef g = CGGradientCreateWithColors(cs, (__bridge CFArrayRef)colors, locations);
    CGContextSaveGState(c);
    CGContextClipToRect(c, r);
    CGContextDrawLinearGradient(c, g, CGPointMake(0, r.origin.y), CGPointMake(0, r.origin.y + r.size.height), 0);
    if (texture > 0.0f) {
        CGContextSetAlpha(c, texture);
        [WLBrushedOverlay() drawAsPatternInRect:r];
    }
    CGContextRestoreGState(c);
    CGGradientRelease(g);
    CGColorSpaceRelease(cs);
}

/* ---------- śrubka ---------- */

UIImage *WLScrewImage(CGFloat d, int variant)
{
    static NSMutableDictionary *cache;
    if (!cache) cache = [NSMutableDictionary dictionary];
    variant &= 3;
    NSString *key = [NSString stringWithFormat:@"%d-%d", (int)(d * 2.0f), variant];
    UIImage *hit = [cache objectForKey:key];
    if (hit) return hit;

    static const CGFloat angles[4] = { 0.35f, 1.2f, 2.1f, 2.9f };
    CGFloat pad = 2.0f, s = d + 2 * pad, r = d / 2;
    CGPoint ctr = CGPointMake(s / 2, s / 2);
    UIGraphicsBeginImageContextWithOptions(CGSizeMake(s, s), NO, 0.0f);
    CGContextRef c = UIGraphicsGetCurrentContext();

    /* jasna krawędź od dołu i ciemny rowek wokół */
    [C(255, 255, 255, 0.65f) setFill];
    CGContextFillEllipseInRect(c, CGRectMake(ctr.x - r - 0.6f, ctr.y - r + 0.1f, 2 * r + 1.2f, 2 * r + 1.2f));
    [C(60, 66, 76, 0.92f) setFill];
    CGContextFillEllipseInRect(c, CGRectMake(ctr.x - r - 0.6f, ctr.y - r - 0.6f, 2 * r + 1.2f, 2 * r + 1.2f));

    /* kopuła: światło z lewej góry */
    CGContextSaveGState(c);
    CGContextAddEllipseInRect(c, CGRectMake(ctr.x - r, ctr.y - r, 2 * r, 2 * r));
    CGContextClip(c);
    CGColorSpaceRef cs = CGColorSpaceCreateDeviceRGB();
    NSArray *cols = [NSArray arrayWithObjects:(__bridge id)C(252, 253, 254, 1).CGColor, (__bridge id)C(120, 127, 138, 1).CGColor, nil];
    CGGradientRef g = CGGradientCreateWithColors(cs, (__bridge CFArrayRef)cols, NULL);
    CGPoint light = CGPointMake(ctr.x - 0.35f * r, ctr.y - 0.4f * r);
    CGContextDrawRadialGradient(c, g, light, 0, light, 1.3f * r, kCGGradientDrawsAfterEndLocation);
    CGGradientRelease(g);
    CGColorSpaceRelease(cs);
    CGContextRestoreGState(c);

    /* krzyżak */
    CGContextSaveGState(c);
    CGContextTranslateCTM(c, ctr.x, ctr.y);
    CGContextRotateCTM(c, angles[variant]);
    CGFloat L = 0.72f * r, w = 0.45f;
    [C(255, 255, 255, 0.5f) setFill];
    CGContextFillRect(c, CGRectMake(-L, -w + 0.6f, 2 * L, 2 * w));
    CGContextFillRect(c, CGRectMake(-w, -L + 0.6f, 2 * w, 2 * L));
    [C(58, 64, 76, 1) setFill];
    CGContextFillRect(c, CGRectMake(-L, -w, 2 * L, 2 * w));
    CGContextFillRect(c, CGRectMake(-w, -L, 2 * w, 2 * L));
    CGContextRestoreGState(c);

    [C(70, 76, 88, 1) setStroke];
    CGContextSetLineWidth(c, 0.6f);
    CGContextStrokeEllipseInRect(c, CGRectMake(ctr.x - r, ctr.y - r, 2 * r, 2 * r));

    UIImage *img = UIGraphicsGetImageFromCurrentImageContext();
    UIGraphicsEndImageContext();
    [cache setObject:img forKey:key];
    return img;
}

/* ---------- chrom ---------- */

UIImage *WLChromeImage(void)
{
    static UIImage *img;
    if (img) return img;
    CGFloat w = 24.0f, h = 44.0f;
    UIGraphicsBeginImageContextWithOptions(CGSizeMake(w, h), NO, 0.0f);
    CGContextRef c = UIGraphicsGetCurrentContext();
    CGRect r = CGRectMake(0.5f, 0.5f, w - 1.0f, h - 1.5f);
    UIBezierPath *shape = [UIBezierPath bezierPathWithRoundedRect:r cornerRadius:9.0f];
    CGContextSaveGState(c);
    [shape addClip];
    NSArray *cols = [NSArray arrayWithObjects:C(255, 255, 255, 1), C(244, 246, 248, 1), C(206, 211, 218, 1), C(158, 165, 175, 1), C(188, 194, 202, 1), C(226, 230, 235, 1), nil];
    NSMutableArray *cg = [NSMutableArray array];
    for (UIColor *u in cols) [cg addObject:(__bridge id)u.CGColor];
    static const CGFloat locs[6] = { 0.0f, 0.12f, 0.48f, 0.5f, 0.78f, 1.0f };
    WLMetalFill(c, CGRectMake(0, 0, w, h), cg, locs, 0.0f);
    CGContextRestoreGState(c);
    [C(84, 90, 101, 1) setStroke];
    shape.lineWidth = 1.0f;
    [shape stroke];
    UIBezierPath *inner = [UIBezierPath bezierPathWithRoundedRect:CGRectInset(r, 1.0f, 1.0f) cornerRadius:8.0f];
    [C(255, 255, 255, 0.75f) setStroke];
    inner.lineWidth = 0.8f;
    [inner stroke];
    [C(255, 255, 255, 0.55f) setFill];
    CGContextFillRect(c, CGRectMake(6, h - 1, w - 12, 1));
    UIImage *raw = UIGraphicsGetImageFromCurrentImageContext();
    UIGraphicsEndImageContext();
    img = [raw resizableImageWithCapInsets:UIEdgeInsetsMake(14, 10, 14, 10)];
    return img;
}

/* ---------- płyta ---------- */

@implementation WLPlateView

- (id)initWithFrame:(CGRect)f
{
    if ((self = [super initWithFrame:f])) {
        self.opaque = NO;
        self.backgroundColor = [UIColor clearColor];
        self.contentMode = UIViewContentModeRedraw;
        self.layer.shadowColor = [UIColor blackColor].CGColor;
        self.layer.shadowOpacity = 0.42f;
        self.layer.shadowRadius = 4.0f;
        self.layer.shadowOffset = CGSizeMake(0, 2);
    }
    return self;
}

- (void)layoutSubviews
{
    [super layoutSubviews];
    self.layer.shadowPath = [UIBezierPath bezierPathWithRoundedRect:self.bounds cornerRadius:14.0f].CGPath;
}

- (void)drawRect:(CGRect)rect
{
    CGContextRef c = UIGraphicsGetCurrentContext();
    CGRect b = self.bounds;
    const WLPalette *p = WLP();
    UIBezierPath *path = [UIBezierPath bezierPathWithRoundedRect:CGRectInset(b, 0.5f, 0.5f) cornerRadius:14.0f];
    CGContextSaveGState(c);
    [path addClip];
    NSArray *cols = [NSArray arrayWithObjects:(__bridge id)WLRGB(p->plateT, 1).CGColor, (__bridge id)WLRGB(p->plateM, 1).CGColor, (__bridge id)WLRGB(p->plateB, 1).CGColor, nil];
    static const CGFloat locs[3] = { 0.0f, 0.5f, 1.0f };
    WLMetalFill(c, b, cols, locs, p->texAmp);
    CGContextRestoreGState(c);
    [C(70, 76, 88, p->metal || p->light ? 1.0f : 0.9f) setStroke];
    path.lineWidth = 1.0f;
    [path stroke];
    UIBezierPath *inner = [UIBezierPath bezierPathWithRoundedRect:CGRectInset(b, 1.5f, 1.5f) cornerRadius:13.0f];
    [C(255, 255, 255, p->light ? 0.9f : 0.22f) setStroke];
    inner.lineWidth = 1.0f;
    [inner stroke];

    if (self.grooveY > 0.0f) {
        [C(0, 0, 0, p->light ? 0.38f : 0.7f) setFill];
        CGContextFillRect(c, CGRectMake(18, self.grooveY, b.size.width - 36, 1));
        [C(255, 255, 255, p->light ? 0.95f : 0.18f) setFill];
        CGContextFillRect(c, CGRectMake(18, self.grooveY + 1, b.size.width - 36, 1));
    }

    CGFloat d = 9.0f, off = 11.0f, s = d + 4.0f;
    CGPoint pts[4] = { CGPointMake(off, off), CGPointMake(b.size.width - off, off),
                       CGPointMake(off, b.size.height - off), CGPointMake(b.size.width - off, b.size.height - off) };
    for (int i = 0; i < 4; i++) {
        [WLScrewImage(d, i) drawAtPoint:CGPointMake(pts[i].x - s / 2, pts[i].y - s / 2)];
    }
}

@end

/* ---------- wyświetlacz LCD ---------- */

@interface WLLCDView ()
{
    UIView *_cursor;
}
@end

@implementation WLLCDView

- (id)initWithFrame:(CGRect)f
{
    if ((self = [super initWithFrame:f])) {
        self.opaque = NO;
        self.backgroundColor = [UIColor clearColor];
        self.contentMode = UIViewContentModeRedraw;
        _cursor = [[UIView alloc] initWithFrame:CGRectZero];
        _cursor.hidden = YES;
        _cursor.userInteractionEnabled = NO;
        [self addSubview:_cursor];
    }
    return self;
}

- (void)setText:(NSString *)t
{
    if ((t == _text) || [t isEqualToString:_text]) return;
    _text = [t copy];
    [self setNeedsDisplay];
}

- (void)setShowsCursor:(BOOL)on
{
    _showsCursor = on;
    [_cursor.layer removeAllAnimations];
    _cursor.alpha = 1.0f;
    _cursor.hidden = !on;
    if (on) {
        [UIView animateWithDuration:0.5 delay:0.0 options:UIViewAnimationOptionRepeat | UIViewAnimationOptionAutoreverse | UIViewAnimationOptionAllowUserInteraction
                         animations:^{ _cursor.alpha = 0.08f; } completion:nil];
    }
}

- (void)layoutSubviews
{
    [super layoutSubviews];
    CGRect b = self.bounds;
    CGFloat h = (b.size.height - 8 - 14) * 0.8f;
    _cursor.backgroundColor = WLRGB(WLP()->lcdOn, 1);
    _cursor.frame = CGRectMake(b.size.width - 4 - 12, (b.size.height - h) / 2, 2.5f, h);
}

static void SegPath(CGContextRef c, int seg, float x, float y, float w, float h, float t, float g)
{
    float p[12];
    wl_seg_poly(seg, x, y, w, h, t, g, p);
    CGContextMoveToPoint(c, p[0], p[1]);
    for (int k = 1; k < 6; k++) CGContextAddLineToPoint(c, p[2 * k], p[2 * k + 1]);
    CGContextClosePath(c);
}

- (void)drawRect:(CGRect)rect
{
    CGContextRef c = UIGraphicsGetCurrentContext();
    CGRect b = self.bounds;
    const WLPalette *p = WLP();

    /* wpuszczona rama: ciemna u góry, jasna u dołu; pod nią jasna kreska od światła */
    CGRect frame = CGRectMake(1, 1, b.size.width - 2, b.size.height - 2);
    UIBezierPath *rim = [UIBezierPath bezierPathWithRoundedRect:CGRectInset(b, 0.5f, 0.5f) cornerRadius:9.5f];
    [C(255, 255, 255, p->light ? 0.6f : 0.14f) setStroke];
    rim.lineWidth = 1.0f;
    [rim stroke];
    UIBezierPath *fp = [UIBezierPath bezierPathWithRoundedRect:frame cornerRadius:9.0f];
    CGContextSaveGState(c);
    [fp addClip];
    NSArray *fc = [NSArray arrayWithObjects:(__bridge id)WLRGB(p->lcdFrameT, 1).CGColor, (__bridge id)WLRGB(p->lcdFrameB, 1).CGColor, nil];
    WLMetalFill(c, frame, fc, NULL, 0.0f);
    CGContextRestoreGState(c);

    /* szkło */
    CGRect glass = CGRectInset(frame, 3, 3);
    UIBezierPath *gp = [UIBezierPath bezierPathWithRoundedRect:glass cornerRadius:6.5f];
    CGContextSaveGState(c);
    [gp addClip];
    NSArray *gc = [NSArray arrayWithObjects:(__bridge id)WLRGB(p->lcdT, 1).CGColor, (__bridge id)WLRGB(p->lcdB, 1).CGColor, nil];
    WLMetalFill(c, glass, gc, NULL, 0.0f);
    /* cień wewnętrzny u góry */
    NSArray *sc = [NSArray arrayWithObjects:(__bridge id)C(0, 0, 0, 0.36f).CGColor, (__bridge id)C(0, 0, 0, 0.08f).CGColor, (__bridge id)C(0, 0, 0, 0.0f).CGColor, nil];
    static const CGFloat sl[3] = { 0.0f, 0.22f, 0.4f };
    WLMetalFill(c, glass, sc, sl, 0.0f);

    /* cyfry */
    NSString *text = self.text ? self.text : @"";
    int cells[48]; float xs[48]; float tw = 0;
    int n = wl_seg_layout([text UTF8String], cells, xs, 48, &tw);
    CGFloat padL = 10.0f, padR = 14.0f, padV = 7.0f;
    CGFloat availW = glass.size.width - padL - padR, availH = glass.size.height - 2 * padV;
    CGFloat ch = availH;
    if (tw > 0.01f && availW / tw < ch) ch = availW / tw;
    CGFloat t = ch * WL_SEG_THICK, gap = t * 0.10f;
    CGFloat x0 = glass.origin.x + glass.size.width - padR - tw * ch;
    CGFloat y0 = glass.origin.y + (glass.size.height - ch) / 2;
    CGFloat cy = y0 + ch / 2, slant = 0.10f;
    CGContextSaveGState(c);
    CGContextConcatCTM(c, CGAffineTransformMake(1, 0, -slant, 1, slant * cy, 0));
    UIColor *on = WLRGB(p->lcdOn, 1);
    UIColor *off = WLRGB(p->lcdOn, p->lcdOffAlpha);
    CGFloat cw = WL_SEG_DIGIT_W * ch;
    /* nieaktywne segmenty ("ósemki" w tle) */
    [off setFill];
    for (int i = 0; i < n; i++) {
        if (cells[i] >= '0' && cells[i] <= '9') {
            for (int s = 0; s < 7; s++) { SegPath(c, s, x0 + xs[i] * ch, y0, cw, ch, t, gap); CGContextFillPath(c); }
        }
    }
    /* aktywne: jasne albo z poświatą (ciemny wyświetlacz) */
    CGContextSaveGState(c);
    if (!p->light) CGContextSetShadowWithColor(c, CGSizeMake(0, 0), 6.0f, WLRGB(p->lcdOn, 0.85f).CGColor);
    [on setFill];
    for (int i = 0; i < n; i++) {
        int ch_ = cells[i];
        CGFloat cx = x0 + xs[i] * ch;
        if ((ch_ >= '0' && ch_ <= '9') || ch_ == '-') {
            int mask = wl_seg_mask(ch_);
            for (int s = 0; s < 7; s++) {
                if (mask & (1 << s)) { SegPath(c, s, cx, y0, cw, ch, t, gap); CGContextFillPath(c); }
            }
        } else if (ch_ == '.' || ch_ == ',') {
            CGFloat dd = t * 1.15f, dx = cx + (WL_SEG_DOT_W * ch - dd) / 2, dy = y0 + ch - dd;
            CGContextFillRect(c, CGRectMake(dx, dy, dd, dd));
            if (ch_ == ',') {
                CGContextMoveToPoint(c, dx + dd * 0.2f, dy + dd);
                CGContextAddLineToPoint(c, dx + dd, dy + dd);
                CGContextAddLineToPoint(c, dx + dd * 0.2f - dd * 0.45f, dy + dd * 2.0f);
                CGContextClosePath(c);
                CGContextFillPath(c);
            }
        }
    }
    CGContextRestoreGState(c);
    CGContextRestoreGState(c);

    /* połysk szkła: jaśniejsza górna połowa */
    CGRect upper = CGRectMake(glass.origin.x, glass.origin.y, glass.size.width, glass.size.height * 0.5f);
    NSArray *gl = [NSArray arrayWithObjects:(__bridge id)C(255, 255, 255, p->light ? 0.27f : 0.16f).CGColor, (__bridge id)C(255, 255, 255, p->light ? 0.08f : 0.03f).CGColor, nil];
    WLMetalFill(c, upper, gl, NULL, 0.0f);
    CGContextRestoreGState(c);
    [C(0, 0, 0, 0.6f) setStroke];
    gp.lineWidth = 0.8f;
    [gp stroke];
}

@end
