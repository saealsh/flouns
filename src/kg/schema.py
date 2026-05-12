"""تعريف بنية رسم المعرفة (schema): أنواع العقد والعلاقات.

الفلسفة:
- العقد (Nodes) لها أنواع محددة: Speaker, Person, Location, Organization, Event, Keyword
- العلاقات (Edges) لها أنواع محددة: SPOKE_IN, MET_AT, AGREED_WITH, إلخ
- كل عقدة لها id فريد يُبنى من النوع + الاسم القياسي (لتسهيل دمج البيانات عبر المكالمات)

أنواع العقد:
- **Call**: مكالمة كاملة (id = call_id من ASR)
- **Speaker**: متحدث مُعرَّف (id من registry: SPK_01 إلخ)
- **Person**: شخص مذكور في النص (قد يطابق Speaker أو لا)
- **Location**: مكان
- **Organization**: منظمة
- **Date / Time**: زمن مذكور
- **Money**: مبلغ
- **Keyword**: كلمة مفتاحية أو مصطلح watchlist
- **Event**: حدث (فعل + مشاركون)

أنواع العلاقات:
- **PARTICIPATED_IN**: Speaker → Call
- **MENTIONED_IN**: Person/Location/... → Call
- **MENTIONED**: Speaker → Person/Location/... (من نطق باسمه)
- **IDENTIFIED_AS**: Speaker → Person (المتحدث = شخص معروف)
- **MET_AT**: Person → Location
- **MET_WITH**: Person → Person
- **AGREED_WITH**: Person → Person
- **SENT_TO**: Person → Person/Organization
- **OCCURRED_ON**: Event → Date/Time
- **OCCURRED_AT**: Event → Location
- **HAS_ACTOR**: Event → Person
- **MATCHES_WATCHLIST**: Call → Keyword
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    CALL = "Call"
    SPEAKER = "Speaker"
    PERSON = "Person"
    LOCATION = "Location"
    ORGANIZATION = "Organization"
    DATE = "Date"
    TIME = "Time"
    MONEY = "Money"
    KEYWORD = "Keyword"
    EVENT = "Event"
    PHONE = "Phone"
    EMAIL = "Email"


class EdgeType(str, Enum):
    # علاقات مع المكالمة
    PARTICIPATED_IN = "PARTICIPATED_IN"      # Speaker → Call
    MENTIONED_IN = "MENTIONED_IN"            # Entity → Call

    # علاقات هوية
    IDENTIFIED_AS = "IDENTIFIED_AS"          # Speaker → Person
    SAME_AS = "SAME_AS"                      # Entity → Entity (coreference)

    # علاقات ذكر
    MENTIONED = "MENTIONED"                  # Speaker → Entity

    # علاقات أحداث
    HAS_ACTOR = "HAS_ACTOR"                  # Event → Person
    OCCURRED_AT = "OCCURRED_AT"              # Event → Location
    OCCURRED_ON = "OCCURRED_ON"              # Event → Date/Time
    INVOLVED_KEYWORD = "INVOLVED_KEYWORD"    # Event → Keyword

    # علاقات Person → Person
    MET_WITH = "MET_WITH"
    AGREED_WITH = "AGREED_WITH"
    CALLED = "CALLED"
    SENT_TO = "SENT_TO"
    RECEIVED_FROM = "RECEIVED_FROM"

    # علاقات Person → Location
    WENT_TO = "WENT_TO"
    ARRIVED_AT = "ARRIVED_AT"
    MET_AT = "MET_AT"

    # علاقات watchlist
    MATCHES_WATCHLIST = "MATCHES_WATCHLIST"  # Call → Keyword


# خريطة من نوع NER إلى NodeType
NER_TO_NODE_TYPE: dict[str, NodeType] = {
    "PERSON": NodeType.PERSON,
    "LOCATION": NodeType.LOCATION,
    "ORGANIZATION": NodeType.ORGANIZATION,
    "DATE": NodeType.DATE,
    "TIME": NodeType.TIME,
    "MONEY": NodeType.MONEY,
    "KEYWORD": NodeType.KEYWORD,
    "PHONE": NodeType.PHONE,
    "EMAIL": NodeType.EMAIL,
}


# خريطة من علاقة في events.py إلى EdgeType
ACTION_TO_EDGE: dict[str, EdgeType] = {
    "meet_at": EdgeType.MET_AT,
    "meet_with": EdgeType.MET_WITH,
    "meet_on": EdgeType.OCCURRED_ON,
    "agree_with": EdgeType.AGREED_WITH,
    "agree_on": EdgeType.OCCURRED_ON,
    "agree_at": EdgeType.OCCURRED_AT,
    "call_with": EdgeType.CALLED,
    "call_on": EdgeType.OCCURRED_ON,
    "send_to": EdgeType.SENT_TO,
    "send_at": EdgeType.OCCURRED_AT,
    "send_on": EdgeType.OCCURRED_ON,
    "send_with": EdgeType.SENT_TO,
    "receive_from": EdgeType.RECEIVED_FROM,
    "receive_at": EdgeType.OCCURRED_AT,
    "receive_on": EdgeType.OCCURRED_ON,
    "go_to": EdgeType.WENT_TO,
    "go_at": EdgeType.WENT_TO,
    "go_on": EdgeType.OCCURRED_ON,
    "arrive_at": EdgeType.ARRIVED_AT,
    "arrive_on": EdgeType.OCCURRED_ON,
    "deliver_to": EdgeType.SENT_TO,
    "deliver_at": EdgeType.OCCURRED_AT,
}


@dataclass
class Node:
    """عقدة في رسم المعرفة."""

    id: str                      # معرّف فريد (Type:NormalizedName)
    type: NodeType
    label: str                   # النص المعروض
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "label": self.label,
            "properties": self.properties,
        }


@dataclass
class Edge:
    """علاقة بين عقدتين."""

    source: str                  # id العقدة المصدر
    target: str                  # id العقدة الهدف
    type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "properties": self.properties,
        }


def make_node_id(node_type: NodeType, normalized_name: str) -> str:
    """توليد معرّف فريد للعقدة.

    تطبيع: استبدال المسافات والرموز، الحفاظ على الحروف العربية.

    Examples:
        make_node_id(NodeType.PERSON, "أحمد محمد") → "Person:احمد_محمد"
        make_node_id(NodeType.LOCATION, "الرياض") → "Location:الرياض"
    """
    # نُنظّف الاسم: مسافات → underscore، نزيل علامات الترقيم
    clean = normalized_name.strip()
    clean = clean.replace(" ", "_")
    # نزيل الأحرف غير المسموحة (نُبقي على العربية، الإنجليزية، الأرقام، _)
    import re
    clean = re.sub(r"[^\u0600-\u06FF\w_]", "", clean)
    return f"{node_type.value}:{clean}"
