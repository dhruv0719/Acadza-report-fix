import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.config import settings


class RepairDefinition(BaseModel):
    fields: List[str]
    auto: bool
    label: str


class TaxonomyData(BaseModel):
    about: Optional[str] = Field(default=None, alias="_about")
    verdicts: Dict[str, str]
    repairs: Dict[str, RepairDefinition]


class TaxonomyRegistry:
    """Programmatic registry for taxonomy verdicts and repairs.
    
    Reads dynamically from taxonomy.json. Never hardcodes an incomplete list.
    """
    _instance: Optional["TaxonomyRegistry"] = None
    _data: Optional[TaxonomyData] = None

    def __init__(self, path: Optional[Path] = None):
        self.path = path or settings.TAXONOMY_PATH
        self.reload()

    def reload(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Taxonomy file not found at: {self.path}")
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self._data = TaxonomyData.model_validate(raw)

    @property
    def data(self) -> TaxonomyData:
        if self._data is None:
            self.reload()
        return self._data

    def get_verdicts(self) -> Dict[str, str]:
        """Returns dict of verdict_name -> description."""
        return self.data.verdicts

    def get_repairs(self) -> Dict[str, RepairDefinition]:
        """Returns dict of repair_name -> RepairDefinition."""
        return self.data.repairs

    def get_verdict_keys(self) -> List[str]:
        return list(self.data.verdicts.keys())

    def get_repair_keys(self) -> List[str]:
        return list(self.data.repairs.keys())

    def is_valid_verdict(self, verdict: str) -> bool:
        return verdict in self.data.verdicts

    def is_valid_repair(self, repair: str) -> bool:
        return repair in self.data.repairs

    def get_repair(self, repair: str) -> Optional[RepairDefinition]:
        return self.data.repairs.get(repair)

    def is_auto_repair(self, repair: str) -> bool:
        r = self.get_repair(repair)
        return r.auto if r else False

    def get_repair_fields(self, repair: str) -> List[str]:
        r = self.get_repair(repair)
        return r.fields if r else []

    @classmethod
    def get_default(cls) -> "TaxonomyRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

