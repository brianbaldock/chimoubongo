"""Regression checks for rebuilding an already-present #shop section.

Run: python3 tools/test_build_shop_section.py
"""
from build_shop_section import COPY, replace_shop_section

source = '''<nav>
  <a class="nl" href="#shop">Le hangar</a>
  <a class="nl" href="#visit">Visiter</a>
</nav>
<section id="bureau"></section>
<section id="shop"><p>OLD SHOP CONTENT</p></section>
<section id="visit"></section>
<footer><li><a href="#bureau">Attractions</a></li>
          <li><a href="#shop">Le hangar</a></li></footer>
'''

updated = replace_shop_section(source, COPY["index.html"])

assert "OLD SHOP CONTENT" not in updated
assert updated.count('<section id="shop">') == 1
assert updated.count('<section id="visit">') == 1
assert updated.index('<section id="shop">') < updated.index('<section id="visit">')
assert updated.count('href="#shop"') == 2, "existing nav and footer links must not duplicate"
assert updated.count("<form") == updated.count("</form>") == 5
assert 'width="900" height="1200"' in updated

print("OK existing #shop section is rebuilt without duplicate navigation")
