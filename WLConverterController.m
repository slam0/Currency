#import "WLConverterController.h"
#import "WLStore.h"
#import "WLTheme.h"
#import "WLLang.h"
#import "WLViews.h"
#import "WLRates.h"
#import "WLCurrencies.h"
#import "WLPickerController.h"
#import "wl_core.h"
#import "WLCrash.h"
#import "WLMetal.h"

@interface WLConverterController ()
{
    UITableView *_table;
    UIView *_head;
    WLPlateView *_plate;
    UITextField *_field;                    /* niewidoczne pole tekstowe: zbiera wpisywanie, a kwotę pokazuje wyświetlacz */
    WLLCDView *_amountLCD, *_resultLCD;
    UIButton *_fromButton, *_toButton;
    UILabel *_fromName, *_toName, *_rateLabel, *_statusLabel;
    UIActivityIndicatorView *_spinner;
    NSString *_toast;
    double _lastResult;
    BOOL _hasResult;
}
@end

@implementation WLConverterController

- (id)init
{
    if ((self = [super init])) self.title = GL(@"Przelicznik");
    return self;
}

- (void)dealloc
{
    [[NSNotificationCenter defaultCenter] removeObserver:self];
}

/* ---------- budowa ekranu ---------- */

- (UILabel *)labelAt:(CGRect)f size:(CGFloat)size bold:(BOOL)bold color:(UIColor *)color align:(NSTextAlignment)a
{
    UILabel *l = [[UILabel alloc] initWithFrame:f];
    l.backgroundColor = [UIColor clearColor];
    l.font = bold ? [UIFont boldSystemFontOfSize:size] : [UIFont systemFontOfSize:size];
    l.textColor = color;
    l.textAlignment = a;
    l.autoresizingMask = UIViewAutoresizingFlexibleWidth;
    return l;
}

- (UIButton *)currencyButtonAt:(CGRect)f action:(SEL)action
{
    UIButton *b = WLGelButton(@"", 0, f);
    b.titleLabel.font = [UIFont boldSystemFontOfSize:20.0f];
    b.titleEdgeInsets = UIEdgeInsetsMake(0, -6, 0, 18);
    UIImageView *tri = [[UIImageView alloc] initWithImage:WLTriangleImage()];
    tri.frame = CGRectMake(f.size.width - 24, (f.size.height - 8) / 2, 12, 8);
    tri.alpha = 0.9f;
    [b addSubview:tri];
    [b addTarget:self action:action forControlEvents:UIControlEventTouchUpInside];
    b.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
    return b;
}

- (void)viewDidLoad
{
    [super viewDidLoad];
    WLCrumb(@"przelicznik: budowa ekranu");
    self.view.backgroundColor = WLBackgroundColor();
    _head = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 320, 282)];
    _head.autoresizingMask = UIViewAutoresizingFlexibleWidth;

    /* płyta z wyświetlaczami (współrzędne wewnątrz płyty) */
    _plate = [[WLPlateView alloc] initWithFrame:CGRectMake(8, 8, 304, 198)];
    _plate.autoresizingMask = UIViewAutoresizingFlexibleWidth;
    _plate.grooveY = 99.0f;
    [_head addSubview:_plate];

    UILabel *lab1 = [self labelAt:CGRectMake(26, 11, 200, 14) size:10.0f bold:YES color:WLSubtleColor() align:NSTextAlignmentLeft];
    lab1.text = [GL(@"Kwota") uppercaseStringWithLocale:WLLocale()];
    lab1.autoresizingMask = UIViewAutoresizingFlexibleRightMargin;
    WLStyleShadow(lab1);
    [_plate addSubview:lab1];
    UILabel *lab2 = [self labelAt:CGRectMake(26, 116, 200, 14) size:10.0f bold:YES color:WLSubtleColor() align:NSTextAlignmentLeft];
    lab2.text = [GL(@"Wynik") uppercaseStringWithLocale:WLLocale()];
    lab2.autoresizingMask = UIViewAutoresizingFlexibleRightMargin;
    WLStyleShadow(lab2);
    [_plate addSubview:lab2];

    /* kwota: wyświetlacz + niewidoczne pole; dotknięcie wyświetlacza otwiera klawiaturę */
    _amountLCD = [[WLLCDView alloc] initWithFrame:CGRectMake(16, 26, 190, 46)];
    _amountLCD.autoresizingMask = UIViewAutoresizingFlexibleWidth;
    [_amountLCD addGestureRecognizer:[[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(focusAmount)]];
    [_plate addSubview:_amountLCD];

    _field = [[UITextField alloc] initWithFrame:CGRectMake(-80, 0, 60, 30)];
    _field.borderStyle = UITextBorderStyleNone;
    _field.keyboardType = UIKeyboardTypeDecimalPad;
    _field.keyboardAppearance = UIKeyboardAppearanceAlert;
    _field.delegate = self;
    _field.inputAccessoryView = WLKeyboardToolbar(self, @selector(dismissKeyboard));
    [_field addTarget:self action:@selector(amountChanged) forControlEvents:UIControlEventEditingChanged];
    [_head addSubview:_field];

    _fromButton = [self currencyButtonAt:CGRectMake(214, 26, 82, 46) action:@selector(pickFrom)];
    [_plate addSubview:_fromButton];
    _fromName = [self labelAt:CGRectMake(20, 76, 250, 16) size:12.0f bold:NO color:WLSubtleColor() align:NSTextAlignmentLeft];
    _fromName.autoresizingMask = UIViewAutoresizingFlexibleRightMargin;
    WLStyleShadow(_fromName);
    [_plate addSubview:_fromName];

    UIButton *swap = WLGelButton(@"", 1, CGRectMake(126, 84, 52, 30));
    [swap setImage:WLSwapImage() forState:UIControlStateNormal];
    [swap addTarget:self action:@selector(swapCurrencies) forControlEvents:UIControlEventTouchUpInside];
    swap.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin | UIViewAutoresizingFlexibleRightMargin;
    [_plate addSubview:swap];

    /* wynik: wyświetlacz; dotknięcie kopiuje wynik do schowka */
    _resultLCD = [[WLLCDView alloc] initWithFrame:CGRectMake(16, 131, 190, 46)];
    _resultLCD.autoresizingMask = UIViewAutoresizingFlexibleWidth;
    [_resultLCD addGestureRecognizer:[[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(copyResult)]];
    [_plate addSubview:_resultLCD];

    _toButton = [self currencyButtonAt:CGRectMake(214, 131, 82, 46) action:@selector(pickTo)];
    [_plate addSubview:_toButton];
    _toName = [self labelAt:CGRectMake(20, 181, 250, 14) size:12.0f bold:NO color:WLSubtleColor() align:NSTextAlignmentLeft];
    _toName.autoresizingMask = UIViewAutoresizingFlexibleRightMargin;
    WLStyleShadow(_toName);
    [_plate addSubview:_toName];

    _rateLabel = [self labelAt:CGRectMake(12, 216, 296, 20) size:15.0f bold:YES color:WLTextColor() align:NSTextAlignmentCenter];
    WLStyleShadow(_rateLabel);
    [_head addSubview:_rateLabel];

    _statusLabel = [self labelAt:CGRectMake(12, 238, 296, 40) size:12.0f bold:NO color:WLSubtleColor() align:NSTextAlignmentCenter];
    _statusLabel.numberOfLines = 3;
    WLStyleShadow(_statusLabel);
    [_head addSubview:_statusLabel];

    _table = [[UITableView alloc] initWithFrame:self.view.bounds style:UITableViewStylePlain];
    _table.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    _table.dataSource = self;
    _table.delegate = self;
    _table.rowHeight = 56;
    _table.tableHeaderView = _head;
    WLStyleTable(_table);
    [self.view addSubview:_table];

    _spinner = [[UIActivityIndicatorView alloc] initWithActivityIndicatorStyle:WLSpinnerStyle()];
    [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(ratesChanged) name:WLRatesDidChangeNotification object:nil];
    [self updateBarButton];
    WLCrumb(@"przelicznik: ekran zbudowany");
}

- (void)viewWillAppear:(BOOL)animated
{
    [super viewWillAppear:animated];
    _field.text = [WLStore shared].amountText;
    [self update];
}

- (void)viewWillDisappear:(BOOL)animated
{
    [super viewWillDisappear:animated];
    [[WLStore shared] save];
}

/* ---------- działania ---------- */

- (void)dismissKeyboard { [_field resignFirstResponder]; }
- (void)focusAmount { [_field becomeFirstResponder]; }

- (void)textFieldDidBeginEditing:(UITextField *)tf { _amountLCD.showsCursor = YES; }
- (void)textFieldDidEndEditing:(UITextField *)tf { _amountLCD.showsCursor = NO; }

- (void)amountChanged
{
    [WLStore shared].amountText = _field.text;
    [self update];
}

- (BOOL)textField:(UITextField *)tf shouldChangeCharactersInRange:(NSRange)range replacementString:(NSString *)s
{
    NSString *t = [tf.text stringByReplacingCharactersInRange:range withString:s];
    return [t length] <= 16;
}

- (void)swapCurrencies
{
    WLStore *st = [WLStore shared];
    NSString *a = st.fromCode;
    st.fromCode = st.toCode;
    st.toCode = a;
    [self update];
}

- (void)pickCurrencyForFrom:(BOOL)isFrom
{
    [_field resignFirstResponder];
    WLStore *st = [WLStore shared];
    WLPickerController *p = [[WLPickerController alloc] init];
    p.selectedCode = isFrom ? st.fromCode : st.toCode;
    __weak WLConverterController *me = self;
    p.onPick = ^(NSString *code) {
        if (isFrom) st.fromCode = code; else st.toCode = code;
        [me.navigationController popViewControllerAnimated:YES];
    };
    [self.navigationController pushViewController:p animated:YES];
}

- (void)pickFrom { [self pickCurrencyForFrom:YES]; }
- (void)pickTo { [self pickCurrencyForFrom:NO]; }

- (void)showToast:(NSString *)text
{
    _toast = [text copy];
    [self updateStatus];
    NSString *mine = _toast;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(2.0 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        if (_toast == mine) { _toast = nil; [self updateStatus]; }
    });
}

- (void)copyResult
{
    if (!_hasResult) return;
    [UIPasteboard generalPasteboard].string = WLEditNumber(_lastResult);
    [self showToast:GL(@"Wynik skopiowany")];
}

- (void)refreshTapped
{
    if (![[WLRates shared] refreshNow] && !([WLRates shared].loading)) [self showToast:GL(@"Kursy są aktualne (pobrane przed chwilą)")];
}

- (void)updateBarButton
{
    if ([WLRates shared].loading) {
        [_spinner startAnimating];
        self.navigationItem.rightBarButtonItem = [[UIBarButtonItem alloc] initWithCustomView:_spinner];
    } else {
        self.navigationItem.rightBarButtonItem = WLBarButton(GL(@"Odśwież"), self, @selector(refreshTapped));
    }
}

- (void)ratesChanged
{
    [self updateBarButton];
    if (self.isViewLoaded) [self update];
}

/* ---------- odświeżanie widoku ---------- */

- (void)updateStatus
{
    WLRates *r = [WLRates shared];
    NSString *text;
    UIColor *color = WLSubtleColor();
    if (_toast) {
        text = _toast;
    } else if (r.loading) {
        text = GL(@"Pobieram kursy…");
    } else if (![r hasRates]) {
        text = r.errorText ? r.errorText : GL(@"Brak kursów. Połącz się z internetem i dotknij Odśwież.");
        color = WLRGB(WLP()->danger, 1);
    } else {
        NSDate *d = [r updatedDate] ? [r updatedDate] : [r fetchedDate];
        text = [NSString stringWithFormat:GL(@"Kursy z %@ · %@"), d ? WLDateString([d timeIntervalSince1970]) : @"?", [r sourceName]];
        if (r.errorText) {
            text = [text stringByAppendingFormat:@"\n%@", r.errorText];
            color = WLRGB(WLP()->danger, 1);
        } else if ([r fetchedAgeDays] >= 3) {
            text = [text stringByAppendingFormat:@"\n%@", GL(@"Kursy mogą być nieaktualne")];
            color = WLRGB(WLP()->danger, 1);
        }
    }
    _statusLabel.text = text;
    _statusLabel.textColor = color;
}

- (void)setButton:(UIButton *)b code:(NSString *)code
{
    [b setTitle:code forState:UIControlStateNormal];
}

- (void)update
{
    WLCrumb(@"przelicznik: odświeżanie");
    WLStore *st = [WLStore shared];
    WLRates *r = [WLRates shared];
    NSString *from = st.fromCode, *to = st.toCode;
    [self setButton:_fromButton code:from];
    [self setButton:_toButton code:to];
    _fromName.text = WLCurrencyName(from);
    _toName.text = WLCurrencyName(to);

    NSString *txt = [_field.text stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceCharacterSet]];
    double amt = [txt length] ? WLParseNumber(txt) : 0.0;
    double out = 0.0;
    _hasResult = amt >= 0.0 && [r convert:amt from:from to:to result:&out];
    _lastResult = out;
    _amountLCD.text = [txt length] ? txt : @"0";
    _resultLCD.text = _hasResult ? WLMoneyString(out) : @"—";

    double one;
    if ([r convert:1.0 from:from to:to result:&one]) {
        _rateLabel.text = [NSString stringWithFormat:@"1 %@ = %@ %@", from, WLRateString(one), to];
    } else {
        _rateLabel.text = @"";
    }
    [self updateStatus];
    WLCrumb(@"przelicznik: lista");
    [_table reloadData];
    WLCrumb(@"przelicznik: gotowy");
}

/* ---------- lista ulubionych ---------- */

- (NSArray *)rowCodes
{
    NSMutableArray *a = [NSMutableArray array];
    WLStore *st = [WLStore shared];
    for (NSString *c in st.favorites) {
        if (![c isEqualToString:st.fromCode] && [[WLRates shared] hasCode:c]) [a addObject:c];
    }
    return a;
}

- (NSInteger)tableView:(UITableView *)t numberOfRowsInSection:(NSInteger)s { return (NSInteger)[[self rowCodes] count]; }
- (CGFloat)tableView:(UITableView *)t heightForHeaderInSection:(NSInteger)s { return 26; }

- (UIView *)tableView:(UITableView *)t viewForHeaderInSection:(NSInteger)s
{
    NSString *right = nil;
    if ([[WLRates shared] hasRates]) {
        double amt = WLParseNumber(_field.text);
        right = [NSString stringWithFormat:@"%@ %@", amt >= 0 ? WLMoneyString(amt) : @"0", [WLStore shared].fromCode];
    }
    return WLHeaderForTitle(GL(@"Ulubione waluty"), right);
}

- (UITableViewCell *)tableView:(UITableView *)t cellForRowAtIndexPath:(NSIndexPath *)ip
{
    WLCell *c = [WLCell cellForTable:t identifier:@"fav"];
    WLStore *st = [WLStore shared];
    NSString *code = [[self rowCodes] objectAtIndex:(NSUInteger)ip.row];
    NSString *txt = [_field.text stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceCharacterSet]];
    double amt = [txt length] ? WLParseNumber(txt) : 0.0;
    double out = 0.0, one = 0.0;
    BOOL ok = amt >= 0.0 && [[WLRates shared] convert:amt from:st.fromCode to:code result:&out];
    c.textLabel.text = [NSString stringWithFormat:@"%@ %@", ok ? WLMoneyString(out) : @"—", code];
    if ([[WLRates shared] convert:1.0 from:st.fromCode to:code result:&one]) {
        c.detailTextLabel.text = [NSString stringWithFormat:@"%@ · 1 %@ = %@ %@", WLCurrencyName(code), st.fromCode, WLRateString(one), code];
    } else {
        c.detailTextLabel.text = WLCurrencyName(code);
    }
    c.accessoryType = [code isEqualToString:st.toCode] ? UITableViewCellAccessoryCheckmark : UITableViewCellAccessoryNone;
    return c;
}

- (void)tableView:(UITableView *)t didSelectRowAtIndexPath:(NSIndexPath *)ip
{
    [t deselectRowAtIndexPath:ip animated:YES];
    [WLStore shared].toCode = [[self rowCodes] objectAtIndex:(NSUInteger)ip.row];
    [self update];
}

@end
