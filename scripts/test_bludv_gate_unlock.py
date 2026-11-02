#!/usr/bin/env python3

import argparse
import re
import time
from urllib.parse import parse_qs, urlparse

import requests

FLARESOLVERR_URL = "https://flaresolverr.betor.top/v1"

EXPECTED_MAGNET = "magnet:?xt=urn:btih:c63e38cc6e205c95e008b63023cc565e61673293&dn=Resident%20Evil%202026%20WEB-DL%201080p%20x264%20DUAL%205.1&xl=2017091988&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80%2Fannounce"


def extract_magnet_from_html(html_content: str) -> str | None:
    match = re.search(r"var\s+u\s*=\s*\"(magnet:\?[^\"]+)\"", html_content)
    if match:
        return match.group(1)

    match_fallback = re.search(r'(magnet:\?[^\s"\']+)', html_content)
    if match_fallback:
        return match_fallback.group(1)

    return None


def test_bludv_gate_unlock(url: str, timeout: int = 45):
    print(f"Iniciando validação do fluxo Bludv Gate Go para: {url}")
    session_id = f"bludv-test-session-{int(time.time())}"

    try:
        requests.post(
            FLARESOLVERR_URL,
            json={"cmd": "sessions.create", "session": session_id},
            timeout=10,
        )
    except Exception:
        pass

    try:
        print("1. Requisitando URL de gate inicial via FlareSolverr...")
        res = requests.post(
            FLARESOLVERR_URL,
            json={"cmd": "request.get", "url": url, "session": session_id},
            timeout=timeout,
        )
        html = res.json().get("solution", {}).get("response", "")

        match = re.search(r"href=\"(https://[^\"]+utm_content=([^\"]+))\"", html)
        if not match:
            raise RuntimeError(
                "Link de parceiro com utm_content não encontrado na página de jump."
            )

        partner_url = match.group(1)
        parsed = urlparse(partner_url)
        codes = parse_qs(parsed.query).get("utm_content")
        if not codes:
            raise RuntimeError("utm_content não encontrado na query string.")
        code = codes[0]
        print(f"   -> Partner URL: {partner_url}")
        print(f"   -> Code extraído: {code}")

        print("2. Visitando página de parceiro...")
        p_res = requests.post(
            FLARESOLVERR_URL,
            json={"cmd": "request.get", "url": partner_url, "session": session_id},
            timeout=timeout,
        )
        print(
            f"   -> Status partner visit: {p_res.json().get('solution', {}).get('status')}"
        )

        print("3. Aguardando 5 segundos (timer de engajamento)...")
        time.sleep(5)

        print("4. Chamando /api/end...")
        api_res = requests.post(
            FLARESOLVERR_URL,
            json={
                "cmd": "request.get",
                "url": f"https://promobr.online/api/end?code={code}",
                "session": session_id,
            },
            timeout=timeout,
        )
        print(
            f"   -> Status API End: {api_res.json().get('solution', {}).get('status')}"
        )

        print("5. Acessando /go/<code> para liberar callback...")
        go_res = requests.post(
            FLARESOLVERR_URL,
            json={
                "cmd": "request.get",
                "url": f"https://promobr.online/go/{code}",
                "session": session_id,
            },
            timeout=timeout,
        )
        go_data = go_res.json().get("solution", {})
        final_url = go_data.get("url")
        print(f"   -> URL final: {final_url}")
        callback_html = go_data.get("response", "")

        magnet = extract_magnet_from_html(callback_html)
        if magnet:
            print(f"\nSUCESSO! Magnet link destravado:\n{magnet}")
            return magnet
        else:
            raise RuntimeError("Magnet link não encontrado no HTML de callback.")

    finally:
        try:
            requests.post(
                FLARESOLVERR_URL,
                json={"cmd": "sessions.destroy", "session": session_id},
                timeout=10,
            )
        except Exception:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validação do fluxo Gate Go do Bludv com FlareSolverr."
    )
    parser.add_argument(
        "--url",
        default="https://bludvfilmes2.xyz/gate/go/4ec7175a6d672816?p=81366",
        help="URL de gate para testar.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=45,
        help="Timeout em segundos.",
    )
    args = parser.parse_args()

    test_bludv_gate_unlock(args.url, timeout=args.timeout)
