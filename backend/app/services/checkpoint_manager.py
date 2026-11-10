import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.models.investigation import InvestigatorResponse

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages persistent checkpoints for investigated question groups."""

    def __init__(self, checkpoint_path: Optional[Path] = None):
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.path = checkpoint_path or (project_root / "data" / "investigation_checkpoints.json")
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading checkpoints from {self.path}: {e}")
                self._cache = {}

    def has_checkpoint(self, question_id: str) -> bool:
        return question_id in self._cache and bool(self._cache[question_id].get("completed"))

    def get_checkpoint(self, question_id: str) -> Optional[InvestigatorResponse]:
        if not self.has_checkpoint(question_id):
            return None
        try:
            data = self._cache[question_id]["response"]
            return InvestigatorResponse.model_validate(data)
        except Exception as e:
            logger.error(f"Error deserializing checkpoint for {question_id}: {e}")
            return None

    def save_checkpoint(self, response: InvestigatorResponse) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache[response.question_id] = {
            "question_id": response.question_id,
            "completed": True,
            "response": response.model_dump(),
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2)
        logger.info(f"Checkpoint saved for question {response.question_id}")

    def get_all_responses(self) -> List[InvestigatorResponse]:
        responses = []
        for qid in self._cache:
            resp = self.get_checkpoint(qid)
            if resp:
                responses.append(resp)
        return responses

