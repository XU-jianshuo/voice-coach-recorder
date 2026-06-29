from sqlalchemy.orm import Session

from app.models import Hotword

DEFAULT_HOTWORDS = [
    "车险",
    "驾意险",
    "承运人",
    "续保率",
    "赔付率",
    "费用率",
    "联动率",
    "件均",
    "分公司",
    "中支",
    "专代",
    "司控",
    "统扩",
    "清单",
    "核保",
    "报价",
    "录单",
    "通报",
]


def seed_default_hotwords(db: Session) -> None:
    if db.query(Hotword).count() > 0:
        return
    for word in DEFAULT_HOTWORDS:
        db.add(Hotword(text=word, category="insurance_business", weight=10))
    db.commit()
