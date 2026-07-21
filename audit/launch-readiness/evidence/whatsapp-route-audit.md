# WhatsApp route audit

Generated: 2026-07-20

This is a non-messaging, offline audit. `syntax_valid_unconfirmed` means only that a
route can be safely constructed; it does not establish that the account exists, is
monitored, or belongs to the listed business.

## Results

- Directory records: 771
- Explicit, syntactically valid WhatsApp routes: 106
- Invalid explicit routes: 0
- First-party crawl candidates not yet promoted: 0
- Records without a WhatsApp route: 665
- Numbers shared by multiple listings: 4

## Interpretation

The prior website crawl was reconciled by exact normalized business name. A crawl link
is treated as stronger evidence than an ordinary phone number, but it is not called
verified without owner confirmation. No phone number was inferred to be WhatsApp-capable.

A live `wa.me` landing-page probe is intentionally excluded: on 2026-07-20 both an
existing candidate and the impossible control number `+50600000000` returned HTTP 200
and redirected to the same generic send page. That mechanism cannot reliably distinguish
working accounts and would produce false positives.
