"""
MongoDB utility helpers.
Provides functions to convert BSON documents to model-like dicts and
to build insert-ready dicts from dataclass instances.
"""
from __future__ import annotations
from bson import ObjectId
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def oid(value: str) -> ObjectId:
    """Convert a string id to a BSON ObjectId."""
    return ObjectId(value)


def as_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Normalize MongoDB's naive UTC datetimes for aware datetime arithmetic."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


def doc_to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw MongoDB document to a clean dict:
    - Renames '_id' → 'id' as a string.
    - Leaves all other fields intact.
    """
    if doc is None:
        return {}
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    return result


def model_to_doc(obj) -> Dict[str, Any]:
    """
    Convert a dataclass instance to an insert-ready MongoDB document dict.
    - Strips the 'id' field (not stored; MongoDB uses '_id').
    - Converts datetime objects to UTC-aware datetimes.
    """
    d = {key: value for key, value in asdict(obj).items() if value is not None}
    d.pop("id", None)
    return d


def attach_id(doc: Dict[str, Any], inserted_id) -> Dict[str, Any]:
    """Return a copy of doc with 'id' set from the insert result."""
    doc["id"] = str(inserted_id)
    return doc
