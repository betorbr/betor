from enum import StrEnum


class QualityEnum(StrEnum):
    unknown = "Unknown"
    sdtv = "SDTV"
    webrip_480p = "WEBRip-480p"
    webdl_480p = "WEBDL-480p"
    dvd = "DVD"
    bluray_480p = "Bluray-480p"
    bluray_576p = "Bluray-576p"
    hdtv_720p = "HDTV-720p"
    hdtv_1080p = "HDTV-1080p"
    raw_hd = "Raw-HD"
    webrip_720p = "WEBRip-720p"
    webdl_720p = "WEBDL-720p"
    bluray_720p = "Bluray-720p"
    webrip_1080p = "WEBRip-1080p"
    webdl_1080p = "WEBDL-1080p"
    bluray_1080p = "Bluray-1080p"
    bluray_1080p_remux = "Bluray-1080p Remux"
    hdtv_2160p = "HDTV-2160p"
    webrip_2160p = "WEBRip-2160p"
    webdl_2160p = "WEBDL-2160p"
    bluray_2160p = "Bluray-2160p"
    bluray_2160p_remux = "Bluray-2160p Remux"


class ItemsSortEnum(StrEnum):
    inserted_at_asc = "inserted_at"
    inserted_at_desc = "-inserted_at"
    updated_at_asc = "updated_at"
    updated_at_desc = "-updated_at"
