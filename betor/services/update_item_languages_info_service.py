import re
from typing import Optional, Set

import langcodes
import motor.motor_asyncio

from betor.entities import Item, LanguagesInfo, RawItem
from betor.exceptions import ItemNotFound, RawItemNotFound
from betor.repositories import ItemsRepository, RawItemsRepository


class UpdateItemLanguagesInfoService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.items_repository = ItemsRepository(mongodb_client)
        self.raw_items_repository = RawItemsRepository(mongodb_client)

    async def update(self, item_id: str) -> LanguagesInfo:
        item = await self.items_repository.get_by_id(item_id)
        if not item:
            raise ItemNotFound()
        raw_item = await self.raw_items_repository.get(
            item["provider_slug"], item["provider_url"]
        )
        if not raw_item:
            raise RawItemNotFound()
        languages_info = await self.determines_languages_info(item, raw_item)
        await self.items_repository.update_languages_info(item_id, languages_info)
        return languages_info

    async def determines_languages_info(
        self, item: Item, raw_item: RawItem
    ) -> LanguagesInfo:
        languages: Set[str] = set()
        torrent_name = item["torrent_name"] or item["magnet_dn"] or ""
        title_tokens = set(
            re.split(r"[.\-_\[\] ]", (raw_item["title"] or "").lower())
            + re.split(r"[.\-_\[\] ]", (raw_item["translated_title"] or "").lower())
            + re.split(r"[.\-_\[\] ]", (raw_item["raw_title"] or "").lower())
        )
        for value in [torrent_name, *(item["torrent_files"] or [])]:
            if not raw_item["languages"]:
                continue
            tokens = set(re.split(r"[.\-_\[\] ]", value.lower())) - title_tokens - {""}
            for token in tokens:
                language: Optional[langcodes.Language] = None
                try:
                    language = langcodes.get(token)
                except langcodes.LanguageTagError:
                    try:
                        language = langcodes.find(token)
                    except LookupError:
                        pass
                if not language:
                    continue
                language_tag = language.to_tag()
                if language_tag in raw_item["languages"]:
                    languages.add(language_tag)
            if "dual" in tokens and len(raw_item["languages"]) == 2:
                languages.update(raw_item["languages"])
            if "dublado" in tokens and (
                "pt" in raw_item["languages"] or "pt-BR" in raw_item["languages"]
            ):
                languages.add("pt-BR")
        return LanguagesInfo(languages=list(languages))
