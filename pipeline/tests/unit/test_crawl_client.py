import httpx
import pytest

from juris.crawl.client import CrawlStop, FetchError, PoliteFetcher, canonical_url

pytestmark = pytest.mark.unit

URL = "https://www.dgsi.pt/jstj.nsf/abc/def?OpenDocument"


class Server:
    def __init__(self, *statuses: int) -> None:
        self.statuses = list(statuses)
        self.calls: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        status = self.statuses.pop(0) if self.statuses else 200
        return httpx.Response(status, content=b"<html>ok</html>")


def make(tmp_path, server, **kw):
    sleeps: list[float] = []
    client = httpx.Client(transport=httpx.MockTransport(server))
    fetcher = PoliteFetcher(
        tmp_path, client, contact="x@example.com", sleep=sleeps.append, rand=lambda: 0.5, **kw
    )
    return fetcher, sleeps


def test_canonical_url_drops_highlight_and_fragment():
    assert canonical_url(URL + "&Highlight=0,sinal#top") == URL


def test_second_get_uses_cache_without_request_or_delay(tmp_path):
    server = Server()
    fetcher, sleeps = make(tmp_path, server)
    fetcher.get(URL)
    fetcher.get(URL + "&Highlight=0,x")
    assert len(server.calls) == 1
    assert sleeps == []


def test_delay_is_at_least_2_5_seconds_between_requests(tmp_path):
    server = Server()
    fetcher, sleeps = make(tmp_path, server)
    fetcher.get(URL)
    fetcher.get(URL.replace("def", "ghi"))
    assert len(sleeps) == 1 and sleeps[0] >= 2.5


def test_delay_below_minimum_is_refused(tmp_path):
    with pytest.raises(ValueError):
        PoliteFetcher(tmp_path, httpx.Client(), contact="x", delay_s=1.0)


def test_user_agent_identifies_the_project(tmp_path):
    server = Server()
    fetcher, _ = make(tmp_path, server)
    fetcher.get(URL)
    ua = server.calls[0].headers["user-agent"]
    assert ua.startswith("jurisprudencia-prototype/0.1 (contact: ")


@pytest.mark.parametrize("status", [429, 503])
def test_stops_immediately_on_429_or_503_and_does_not_cache(tmp_path, status):
    server = Server(status)
    fetcher, _ = make(tmp_path, server)
    with pytest.raises(CrawlStop):
        fetcher.get(URL)
    assert not fetcher.cached(URL)


def test_stops_after_three_consecutive_errors_without_retrying(tmp_path):
    server = Server(500, 500, 500)
    fetcher, _ = make(tmp_path, server)
    for n in (1, 2):
        with pytest.raises(FetchError):
            fetcher.get(f"{URL}&n={n}")
    with pytest.raises(CrawlStop):
        fetcher.get(f"{URL}&n=3")
    assert len(server.calls) == 3


def test_success_resets_the_error_counter(tmp_path):
    server = Server(500, 500, 200, 500, 500)
    fetcher, _ = make(tmp_path, server)
    for n in range(5):
        try:
            fetcher.get(f"{URL}&n={n}")
        except FetchError:
            pass
    assert len(server.calls) == 5


def test_max_requests_cap(tmp_path):
    server = Server()
    fetcher, _ = make(tmp_path, server, max_requests=1)
    fetcher.get(URL)
    with pytest.raises(CrawlStop):
        fetcher.get(URL.replace("def", "ghi"))


def test_other_hosts_are_refused(tmp_path):
    server = Server()
    fetcher, _ = make(tmp_path, server)
    with pytest.raises(ValueError):
        fetcher.get("https://example.com/x")
    assert server.calls == []
