"""Refuse to fetch addresses that only the server's own network can reach.

Search results are untrusted. Without this check a result could point the
fetcher at localhost, the Docker network, or a cloud metadata address.
A hostname that resolves differently on a later request is not covered.
"""

import ipaddress
import socket
from urllib.parse import urlsplit


def is_public_url(url: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False
    if not addresses:
        return False
    return all(ipaddress.ip_address(item[4][0]).is_global for item in addresses)
