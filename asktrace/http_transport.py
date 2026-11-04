"""Fixed-destination HTTP transport: never forward API credentials on redirects."""

from urllib.request import HTTPRedirectHandler, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def urlopen(request, timeout):
    # A 3xx becomes HTTPError, handled as a terminal provider failure by adapters.
    return build_opener(NoRedirect()).open(request, timeout=timeout)
