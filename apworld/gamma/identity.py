"""Bind common AP constraints and starting inventory without changing legacy seed identities."""

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any

from gamma_archipelago.configuration import OPTION_NAMES

if TYPE_CHECKING:
    from . import GammaWorld


def _data(value: Any) -> Any:
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    raise TypeError("Unsupported data in Archipelago seed constraints")


def generation_identity(world: "GammaWorld") -> str | None:
    common = {}
    for name in world.options_dataclass.type_hints:
        if name in OPTION_NAMES:
            continue
        option = getattr(world.options, name)
        current = json.dumps(option.value, default=_data, sort_keys=True)
        default = json.dumps(
            type(option).from_any(type(option).default).value, default=_data, sort_keys=True
        )
        if current != default:
            common[name] = json.loads(current)
    starting = world.pool_budget.starting
    if not common and not starting:
        return None
    content = json.dumps(
        {"configuration": world.configuration.digest, "common": common, "starting": starting},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
