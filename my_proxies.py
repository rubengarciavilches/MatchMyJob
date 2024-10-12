import requests
import sys
from typing import List

import common

logger = common.get_logger()


def get_proxies() -> List[str]:
    # ProxyScrape API URL to fetch HTTP proxies
    url = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"

    response = requests.get(url)
    if response.status_code == 200:
        proxy_list = response.text.splitlines()
        logger.info(f"Found {len(proxy_list)} proxies from ProxyScrape")
        return proxy_list
    else:
        logger.error(f"Failed to fetch proxies: {response.status_code}")
        return []


def _verify_proxies(
    proxies, max_proxies: int = 100, test_url="https://httpbin.org/ip", timeout=1
) -> List[str]:
    working_proxies = []
    total_proxies = len(proxies)

    for i, proxy in enumerate(proxies):
        proxy_dict = {
            "http": f"http://{proxy}",
        }

        try:
            response = requests.get(test_url, proxies=proxy_dict, timeout=timeout)
            if response.status_code == 200:
                working_proxies.append(proxy)

            sys.stdout.write(
                f"\rChecking proxy {i + 1}/{total_proxies}: {proxy} (working: {len(working_proxies)})"
            )
            sys.stdout.flush()

            if len(working_proxies) >= max_proxies:
                break
        except requests.exceptions.RequestException:
            sys.stdout.write(
                f"\rChecking proxy {i + 1}/{total_proxies}: {proxy} (working: {len(working_proxies)})"
            )
            sys.stdout.flush()

    sys.stdout.write(
        f"\rFinished checking {total_proxies} proxies. {len(working_proxies)} working proxies found.\n"
    )
    sys.stdout.flush()

    return working_proxies


def get_verified_proxies(max_proxies: int = 100) -> List[str]:
    proxies = get_proxies()
    valid_proxies = _verify_proxies(proxies, max_proxies)

    if valid_proxies:
        logger.info(f"Found {len(valid_proxies)} valid proxies.")
    else:
        logger.error("No valid proxies found, exiting.")
        exit()

    return valid_proxies
