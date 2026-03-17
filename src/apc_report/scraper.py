"""APC web interface scraping logic."""

from __future__ import annotations

import logging
import re
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .constants import EXPECTED_COLUMNS
from .models import DeviceConfig
from .utils import is_date_string, normalize_dataframe

LOGGER = logging.getLogger(__name__)
TOKEN_RE = re.compile(r"NMC/(.*?)/")


class ApcScrapeError(RuntimeError):
    """Raised when APC scraping fails."""


class ApcClient:
    def __init__(self, device: DeviceConfig) -> None:
        self.device = device
        self.session = requests.Session()

    def login(self) -> str:
        payload = {
            "prefLanguage": "00000000",
            "login_username": self.device.username,
            "login_password": self.device.password,
            "submit": "Log On",
        }
        response = self.session.post(
            f"{self.device.url}/Forms/login1",
            data=payload,
            verify=self.device.verify_tls,
            timeout=30,
        )
        response.raise_for_status()
        if "Log On" in response.text:
            raise ApcScrapeError(f"Login failed for device '{self.device.name}'.")
        match = TOKEN_RE.search(response.url)
        if not match:
            raise ApcScrapeError(f"Could not extract APC NMC session token for '{self.device.name}'.")
        return match.group(1)

    def logout(self, token: str) -> None:
        try:
            response = self.session.get(
                f"{self.device.url}/NMC/{token}/logout.htm",
                verify=self.device.verify_tls,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.warning("Logout failed for %s: %s", self.device.name, exc)

    def _fetch_page(self, url: str) -> BeautifulSoup:
        response = self.session.get(url, verify=self.device.verify_tls, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")

    @staticmethod
    def _find_last_page(soup: BeautifulSoup) -> int:
        next_link = soup.find("a", string=">>")
        if not next_link or "href" not in next_link.attrs:
            return 1
        match = re.search(r"page=(\d+)", next_link["href"])
        if not match:
            return 1
        return int(match.group(1)) + 1

    @staticmethod
    def _extract_rows(table: BeautifulSoup) -> Iterable[list[str]]:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            row_data = [cell.get_text(strip=True).replace("\xa0", " ") for cell in cells]
            if row_data and is_date_string(row_data[0]):
                yield row_data

    def collect_dataframe(self) -> pd.DataFrame:
        token = self.login()
        try:
            base_url = f"{self.device.url}/NMC/{token}/dataweb.htm"
            first_page = self._fetch_page(base_url)
            page_count = self._find_last_page(first_page)
            LOGGER.info("Discovered %s page(s) for device %s", page_count, self.device.name)

            rows: list[list[str]] = []
            for page_index in range(page_count):
                page_url = base_url if page_index == 0 else f"{base_url}?page={page_index}"
                soup = first_page if page_index == 0 else self._fetch_page(page_url)
                table = soup.find("table", {"class": "logData table table-hover"})
                if table is None:
                    LOGGER.warning("No telemetry table found on page %s for device %s", page_index, self.device.name)
                    continue
                rows.extend(self._extract_rows(table))

            if not rows:
                raise ApcScrapeError(f"No telemetry rows were collected for device '{self.device.name}'.")

            frame = pd.DataFrame(rows, columns=EXPECTED_COLUMNS)
            return normalize_dataframe(frame)
        finally:
            self.logout(token)
