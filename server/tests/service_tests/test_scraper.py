from types import SimpleNamespace
import service.scraper as scraper


def make_response(text, status=200):
    return SimpleNamespace(status_code=status, text=text)


def test_scrape_vinted_pool_basic(monkeypatch):
    # Minimal HTML containing two item divs
    html = '''
    <html><body>
      <div class="feed-grid__item"><a href="/itm/1"><img src="https://images1.vinted.net/1.jpg" alt="A"/></a></div>
      <div class="item-box"><a href="https://www.vinted.co.uk/itm/2"><img data-src="https://images1.vinted.net/2.jpg" alt="B"/></a></div>
    </body></html>
    '''

    class FakeRequests:
        def get(self, url, headers=None, impersonate=None, timeout=None):
            return make_response(html, 200)

    monkeypatch.setattr(scraper, 'requests', FakeRequests())
    items = scraper.scrape_vinted_pool('q=1')
    assert isinstance(items, list)
    assert len(items) == 2
    assert items[0]['image_url'].startswith('https://images1.vinted.net')


def test_scraper_handles_bad_status(monkeypatch):
    class BadResp:
        status_code = 403
        text = 'blocked'

    class FakeRequests:
        def get(self, url, headers=None, impersonate=None, timeout=None):
            return BadResp()

    monkeypatch.setattr(scraper, 'requests', FakeRequests())
    from fastapi import HTTPException
    try:
        scraper.scrape_vinted_pool('q=1')
        assert False, "should raise"
    except HTTPException:
        pass


def test_scraper_deduplicates_and_filters_non_vinted_images(monkeypatch):
    html = '''
    <html><body>
      <div class="feed-grid__item"><a href="/itm/1"><img src="https://images1.vinted.net/1.jpg" alt="A"/></a></div>
      <div class="item-box"><a href="https://www.vinted.co.uk/itm/1"><img data-src="https://images1.vinted.net/1.jpg" alt="A"/></a></div>
      <div class="item-box"><a href="/itm/2"><img src="https://example.com/2.jpg" alt="B"/></a></div>
    </body></html>
    '''

    class FakeRequests:
        def get(self, url, headers=None, impersonate=None, timeout=None):
            return make_response(html, 200)

    monkeypatch.setattr(scraper, 'requests', FakeRequests())
    items = scraper.scrape_vinted_pool('q=1')

    assert len(items) == 1
    assert items[0]['url'] == 'https://www.vinted.co.uk/itm/1'
    assert items[0]['title'] == 'A'
