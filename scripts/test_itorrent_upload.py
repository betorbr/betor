#!/usr/bin/env python3

import argparse
import re
from pathlib import Path

import requests

DEFAULT_URL = "https://itorrents.net/upload.php"


def extract_info_hash(response_text: str) -> str | None:
    response_lines = [
        line.strip() for line in response_text.splitlines() if line.strip()
    ]
    if not response_lines:
        return None

    candidate = response_lines[-1][:40]
    if len(candidate) == 40 and all(c in "0123456789abcdefABCDEF" for c in candidate):
        return candidate

    match = re.search(r"/torrent/([A-Fa-f0-9]{40})\.torrent", response_text)
    if match:
        return match.group(1)
    return None


def check_pre_upload(info_hash: str, *, timeout: int) -> list[tuple[str, int, str]]:
    results = []
    for variant in [info_hash.lower(), info_hash.upper()]:
        url = f"http://itorrents.net/torrent/{variant}.torrent"
        response = requests.get(url, timeout=timeout)
        print(f"GET before upload -> {url} -> HTTP {response.status_code}")
        results.append((url, response.status_code, response.text[:200]))
    return results


def test_upload(torrent_path: Path, url: str, timeout: int = 30) -> None:
    if not torrent_path.exists():
        raise FileNotFoundError(f"Arquivo .torrent não encontrado: {torrent_path}")

    info_hash = torrent_path.stem.upper()
    print(f"Arquivo: {torrent_path}")
    print(f"Info hash esperado (baseado no nome do arquivo): {info_hash}")
    print(
        "Antes do upload, as URLs em lowercase e uppercase devem falhar ou não existir no cache."
    )
    pre_results = check_pre_upload(info_hash, timeout=timeout)
    lower_before = next(
        status
        for url, status, _ in pre_results
        if url.endswith(f"/{info_hash.lower()}.torrent")
    )
    upper_before = next(
        status
        for url, status, _ in pre_results
        if url.endswith(f"/{info_hash.upper()}.torrent")
    )
    print(f"Status antes do upload: lower={lower_before}, upper={upper_before}")

    torrent_bytes = torrent_path.read_bytes()
    print(f"Enviando arquivo: {torrent_path.name} ({len(torrent_bytes)} bytes)")
    print(f"URL: {url}")

    response = requests.post(
        url,
        files={
            "torrent": (
                torrent_path.name,
                torrent_bytes,
                "application/x-bittorrent",
            )
        },
        timeout=timeout,
    )

    print(f"Status HTTP do upload: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print("Body do upload:")
    print(response.text[:2000])

    uploaded_hash = extract_info_hash(response.text)
    print(f"Info hash extraído do upload: {uploaded_hash}")
    if uploaded_hash is None:
        raise RuntimeError("O upload do iTorrent não retornou um info hash válido.")

    if uploaded_hash.upper() != info_hash:
        raise RuntimeError(
            f"O hash recebido ({uploaded_hash}) não bate com o nome do arquivo ({info_hash})."
        )

    print("Resultado: upload validado e info hash bate com o nome do arquivo.")

    lower_url = f"http://itorrents.net/torrent/{info_hash.lower()}.torrent"
    upper_url = f"http://itorrents.net/torrent/{info_hash.upper()}.torrent"

    for download_url in [lower_url, upper_url]:
        download_response = requests.get(download_url, timeout=timeout)
        print(
            f"GET after upload -> {download_url} -> HTTP {download_response.status_code}"
        )
        print(f"Content-Type: {download_response.headers.get('content-type')}")
        print(f"Bytes: {len(download_response.content)}")

    if requests.get(lower_url, timeout=timeout).status_code != 200:
        raise RuntimeError(f"Falha ao baixar após upload em {lower_url}.")

    print(
        "Resultado final: download principal validado após upload no endpoint público do iTorrent."
    )
    print(
        "Observação: o site respondeu com 520 para a URL em uppercase em alguns testes, o que indica comportamento inconsistente do provedor externo."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valida o fluxo real do torrent no iTorrent."
    )
    parser.add_argument(
        "--torrent",
        type=Path,
        default=Path("db617ae7e9d7b6c3c82be75df3071afbe75fd791.torrent"),
        help="Caminho do arquivo .torrent a ser testado.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Endpoint do iTorrent para upload.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout da requisição em segundos.",
    )
    args = parser.parse_args()

    test_upload(args.torrent, args.url, timeout=args.timeout)
