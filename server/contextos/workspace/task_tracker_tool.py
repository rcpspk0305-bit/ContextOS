from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TaskItem(BaseModel):
    id: str
    description: str
    completed: bool = False

class TaskTrackerTool:
    """
    Task state and acceptance criteria tracker adapted from OpenHands software-agent-sdk.
    """

    def __init__(self, task_description: str, checklist: Optional[List[str]] = None):
        self.task_description = task_description
        self.items: List[TaskItem] = [
            TaskItem(id=f"item_{i+1}", description=desc)
            for i, desc in enumerate(checklist or [])
        ]
        self.current_item_index: int = 0

    def mark_completed(self, item_id: str) -> str:
        for idx, item in enumerate(self.items):
            if item.id == item_id:
                item.completed = True
                if idx == self.current_item_index:
                    self.current_item_index = min(len(self.items) - 1, idx + 1)
                return f"Task item {item_id} marked as completed."
        raise ValueError(f"Task item {item_id} not found.")

    def get_progress_summary(self) -> Dict[str, Any]:
        completed = [item.description for item in self.items if item.completed]
        remaining = [item.description for item in self.items if not item.completed]
        current = self.items[self.current_item_index].description if self.items else self.task_description

        return {
            "task_description": self.task_description,
            "total_items": len(self.items),
            "completed_count": len(completed),
            "completed_items": completed,
            "current_item": current,
            "remaining_items": remaining,
            "all_done": len(remaining) == 0 and len(self.items) > 0,
        }
