"""メルカリ検索スクレイパー（③フリマ実売＝メルカリ平均のソース）。

jp.mercari.com のフロントエンドが使う公開検索API（api.mercari.jp/v2/entities:search）を
直接叩く。ログイン不要・匿名で、リクエストごとに使い捨てのES256鍵で
DPoPトークン（RFC 9449）を自己署名して付ける。ブラウザ不要なのでクラウド実行でも軽い。

- search_closed(): 売り切れを新着順で取得（実際に売れた価格。updated が売却日に近い）
- search_active(): 販売中を価格の安い順で取得（現在の最安売値）

APIが応答しない/ブロックされた場合は MercariError を投げ、呼び出し側で
Yahoo落札相場へフォールバックできるようにする。
"""

import base64
import json
import time
import uuid

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from .base import Listing, make_session, polite_sleep
from ..normalize import extract_loft

API = "https://api.mercari.jp/v2/entities:search"
ITEM_URL = "https://jp.mercari.com/item/{id}"

# プロセス内で使い回す匿名鍵（JWT自体は毎リクエスト新規署名）
_KEY = None

# 連続失敗のサーキットブレーカー。クラウドIPがブロックされた場合に
# 全機種×リトライで時間を浪費しないよう、この回数連続で失敗したら以降は即失敗にする。
_FAIL_STREAK = 0
_FAIL_LIMIT = 5


class MercariError(RuntimeError):
    """API疎通失敗（ネットワーク/ブロック/仕様変更）。0件ヒットでは投げない。"""


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _dpop(url: str, method: str = "POST") -> str:
    """使い捨てES256鍵で自己署名したDPoP JWTを作る（メルカリWeb版と同じ方式）。"""
    global _KEY
    if _KEY is None:
        _KEY = ec.generate_private_key(ec.SECP256R1())
    pub = _KEY.public_key().public_numbers()
    header = {"typ": "dpop+jwt", "alg": "ES256",
              "jwk": {"crv": "P-256", "kty": "EC",
                      "x": _b64url(pub.x.to_bytes(32, "big")),
                      "y": _b64url(pub.y.to_bytes(32, "big"))}}
    payload = {"iat": int(time.time()), "jti": str(uuid.uuid4()),
               "htu": url, "htm": method, "uuid": str(uuid.uuid4())}
    signing_input = (_b64url(json.dumps(header).encode()) + "."
                     + _b64url(json.dumps(payload).encode()))
    der = _KEY.sign(signing_input.encode(), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    return signing_input + "." + _b64url(r.to_bytes(32, "big") + s.to_bytes(32, "big"))


def _search_raw(keyword: str, status: str, sort: str, order: str,
                price_min: int = 0, page_size: int = 120) -> list[dict]:
    body = {
        "userId": "",
        "pageSize": page_size,
        "pageToken": "",
        "searchSessionId": uuid.uuid4().hex,
        "indexRouting": "INDEX_ROUTING_UNSPECIFIED",
        "thumbnailTypes": [],
        "searchCondition": {
            "keyword": keyword,
            "excludeKeyword": "",
            "sort": sort,            # SORT_CREATED_TIME / SORT_PRICE
            "order": order,          # ORDER_DESC / ORDER_ASC
            "status": [status],      # STATUS_SOLD_OUT / STATUS_ON_SALE
            "sizeId": [], "categoryId": [], "brandId": [], "sellerId": [],
            "priceMin": price_min, "priceMax": 0,
            "itemConditionId": [], "shippingPayerId": [],
            "shippingFromArea": [], "shippingMethod": [], "colorId": [],
            "hasCoupon": False, "attributes": [], "itemTypes": [],
            "skuIds": [], "excludeShippingMethodIds": [],
        },
        "serviceFrom": "suruga",
        # 個人間フリマのみ（メルカリShops=事業者は在庫再出品で相場が歪むため除外）
        "defaultDatasets": ["DATASET_TYPE_MERCARI"],
        "withItemBrand": True, "withItemSize": False, "withItemPromotions": True,
        "withItemSizes": True, "withShopname": False, "useDynamicAttribute": True,
        "withSuggestedItems": True, "withOfferPricePromotion": False,
        "withProductSuggest": True, "withParentProducts": False,
        "withProductArticles": False, "withSearchConditionId": False,
        "withAuction": True,
    }
    global _FAIL_STREAK
    if _FAIL_STREAK >= _FAIL_LIMIT:
        raise MercariError(f"連続{_FAIL_STREAK}回失敗中のためスキップ（ブロックの可能性）")
    sess = make_session()
    sess.headers.update({
        "DPoP": _dpop(API),
        "X-Platform": "web",
        "Origin": "https://jp.mercari.com",
        "Referer": "https://jp.mercari.com/",
    })
    last = None
    for attempt in range(2):
        polite_sleep(0.7, "mercari")
        try:
            r = sess.post(API, json=body, timeout=25)
        except Exception as e:
            last = e
            continue
        if r.status_code == 200:
            try:
                items = r.json().get("items", []) or []
            except ValueError as e:
                last = e
                continue
            _FAIL_STREAK = 0
            return items
        last = RuntimeError(f"HTTP {r.status_code}")
        if r.status_code in (429, 403):
            time.sleep(3)
    _FAIL_STREAK += 1
    raise MercariError(f"メルカリ検索失敗: {last}")


def _to_listing(raw: dict, sold: bool) -> Listing | None:
    mid = raw.get("id", "")
    price = raw.get("price")
    title = raw.get("name")
    # メルカリShops(事業者)は在庫再出品で相場が歪むため、個人間フリマのみ採用
    if not mid.startswith("m") or raw.get("itemType") == "ITEM_TYPE_BEYOND":
        return None
    if not price or not title:
        return None
    if sold:
        upd = raw.get("updated") or ""
        day = time.strftime("%Y-%m-%d", time.localtime(int(upd))) if str(upd).isdigit() else ""
        shop = f"メルカリ売切（{day}）" if day else "メルカリ売切"
    else:
        shop = "メルカリ販売中(最安)"
    thumbs = raw.get("thumbnails") or []
    return Listing(
        source="mercari",
        title=title,
        price=int(price),
        url=ITEM_URL.format(id=mid),
        shop=shop,
        is_used=True,
        sold=sold,
        image=thumbs[0] if thumbs else "",
        loft=extract_loft(title),
    )


def search_closed(keyword: str, price_min: int = 0) -> list[Listing]:
    """売り切れ（実際に売れた価格）を「最近売れた順」で返す。

    APIの新着順は出品日時ベースなので、updated（売却に近い更新日時）の
    降順に並べ替えてから返す＝先頭ほど新鮮な実売。
    """
    raws = _search_raw(keyword, "STATUS_SOLD_OUT",
                       "SORT_CREATED_TIME", "ORDER_DESC", price_min)
    def _upd(r):
        u = str(r.get("updated") or "")
        return int(u) if u.isdigit() else 0
    raws.sort(key=_upd, reverse=True)
    out = []
    for raw in raws:
        lst = _to_listing(raw, sold=True)
        if lst:
            out.append(lst)
    return out


def search_active(keyword: str, price_min: int = 0) -> list[Listing]:
    """販売中を価格の安い順で返す（現在の最安売値の把握用）。"""
    out = []
    for raw in _search_raw(keyword, "STATUS_ON_SALE",
                           "SORT_PRICE", "ORDER_ASC", price_min):
        lst = _to_listing(raw, sold=False)
        if lst:
            out.append(lst)
    return out
