"""
Data models for voice-first to-do list application.

Design Philosophy:
- Use frozen dataclasses for immutability (prevents accidental mutations)
- Type hints for all attributes (Python best practice)
- Value objects (TaskId) for type safety instead of raw strings
- Enums for semantic clarity (Priority instead of magic numbers)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from uuid import UUID, uuid4
from typing import Optional


class Priority(IntEnum):
    """
    Priority levels for tasks.
    
    Using IntEnum allows for:
    - Type safety and IDE autocompletion
    - Direct comparison with integers
    - Semantic meaning vs magic numbers
    """
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass(frozen=True)
class TaskId:
    """
    Value object representing a unique task identifier.
    
    Frozen ensures identity cannot be changed.
    Using UUID4 provides collision-free globally unique IDs.
    """
    value: UUID = field(default_factory=uuid4)
    
    def __str__(self) -> str:
        """String representation for API responses and logging."""
        return str(self.value)


@dataclass
class Task:
    """
    Domain model for a Task.
    
    Represents core business entity with immutable-style updates.
    Methods use copy pattern to maintain functional programming principles.
    """
    id: TaskId
    title: str
    priority: Priority = Priority.MEDIUM
    scheduled_time: Optional[datetime] = None
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def mark_complete(self) -> 'Task':
        """
        Create a new Task instance with completed=True.
        
        Returns new instance instead of mutating to prevent bugs.
        Follows functional programming immutability pattern.
        """
        return Task(
            id=self.id,
            title=self.title,
            priority=self.priority,
            scheduled_time=self.scheduled_time,
            completed=True,
            created_at=self.created_at
        )
    
    def reschedule(self, new_time: datetime) -> 'Task':
        """
        Create new Task with updated scheduled_time.
        
        Args:
            new_time: New scheduled datetime
            
        Returns:
            New Task instance with updated scheduled_time
        """
        return Task(
            id=self.id,
            title=self.title,
            priority=self.priority,
            scheduled_time=new_time,
            completed=self.completed,
            created_at=self.created_at
        )
    
    def update_priority(self, new_priority: Priority) -> 'Task':
        """
        Create new Task with updated priority.
        
        Args:
            new_priority: New priority level
            
        Returns:
            New Task instance with updated priority
        """
        return Task(
            id=self.id,
            title=self.title,
            priority=new_priority,
            scheduled_time=self.scheduled_time,
            completed=self.completed,
            created_at=self.created_at
        )


@dataclass(frozen=True)
class LLMFunctionCall:
    """
    Typed representation of LLM function call response.
    
    Frozen for immutability. Validates action on creation.
    """
    action: str
    parameters: dict
    
    def __post_init__(self) -> None:
        """
        Validate that action is one of supported operations.
        
        Raises:
            ValueError: If action is not recognized
        """
        valid_actions = {"create_task", "get_tasks", "update_task", "delete_task"}
        if self.action not in valid_actions:
            raise ValueError(f"Unknown action: {self.action}. Valid actions: {valid_actions}")