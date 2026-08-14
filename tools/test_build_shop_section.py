"""Regression checks for rebuilding the #shop content fragment.

Since the multi-page split the shop is its own page and build_shop_section
emits only the section; chrome belongs to tools/build_site.py. The thing worth
guarding now is that a rebuild is self-contained and cannot smuggle nav,
footer or a storefront token into the fragment.

Run: python3 tools/test_build_shop_section.py
"""
from build_shop_section import COPY, replace_shop_section

source = '<section id="shop"><p>OLD SHOP CONTENT</p></section>\n'

for lang in ("fr", "en"):
    updated = replace_shop_section(source, COPY[lang])

    assert "OLD SHOP CONTENT" not in updated, f"{lang}: stale content survived"
    assert updated.count('<section id="shop">') == 1, f"{lang}: one shop section"
    assert updated.count("<form") == updated.count("</form>") == 5, f"{lang}: five forms"
    assert 'width="900" height="1200"' in updated, f"{lang}: image dimensions"
    assert "ptkn_" not in updated, f"{lang}: token leak"
    # The fragment must stay a fragment: chrome is generated, never embedded.
    for stray in ("<nav", "<footer", "<html", "<body", "class=\"topbar\"", "class=\"shopbar\""):
        assert stray not in updated, f"{lang}: fragment must not contain {stray}"

# A fragment that is not the shop section must be refused rather than silently
# overwritten, which is what would happen if the fragment paths ever got mixed up.
try:
    replace_shop_section("<section id=\"visit\"></section>", COPY["fr"])
except AssertionError:
    pass
else:
    raise SystemExit("FAIL: non-shop fragment was accepted")

print("OK #shop fragment rebuilds self-contained, and non-shop input is refused")
