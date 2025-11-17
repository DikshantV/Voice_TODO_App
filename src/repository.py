"""
Repository pattern for task data persistence.

Design Philosophy:
- Abstraction layer between business logic and storage
- Single repository for in-memory storage (no DB needed for assignment)
- Interface-like approach (easy to swap implementations later)
- Type hints for all operations
"""

from typing import Optional, Sequence
from src.models import Task, TaskId


class TaskRepository:
    """
    In-memory task repository.
    
    Responsible for:
    - Persisting tasks (in this case, in memory)
    - CRUD operations on task storage
    - Query capabilities
    
    This pattern makes it easy to:
    - Swap to database later without changing business logic
    - Test in isolation with mock repositories
    - Keep data access centralized
    """
    
    def __init__(self) -> None:
        """Initialize empty task storage using UUID strings as keys."""
        self._tasks: dict[str, Task] = {}
    
    def save(self, task: Task) -> None:
        """
        Store or update a task.
        
        Args:
            task: Task instance to persist
            
        Thought Process:
        - Upsert pattern: saves new or overwrites existing
        - Idempotent: calling twice with same task has same result
        """
        self._tasks[str(task.id)] = task
    
    def find_by_id(self, task_id: TaskId) -> Optional[Task]:
        """
        Retrieve task by its unique identifier.
        
        Args:
            task_id: TaskId value object
            
        Returns:
            Task if found, None otherwise
            
        Pythonic: Uses Optional to indicate nullable return explicitly
        """
        return self._tasks.get(str(task_id))
    
    def find_all(self) -> Sequence[Task]:
        """
        Retrieve all tasks.
        
        Returns:
            Tuple of Task instances (immutable sequence)
            
        Thought Process:
        - Returns tuple (immutable) not list to prevent external mutations
        - Pythonic: Sequence type hint allows flexibility in return type
        """
        return tuple(self._tasks.values())
    
    def delete(self, task_id: TaskId) -> bool:
        """
        Delete a task by ID.
        
        Args:
            task_id: TaskId of task to delete
            
        Returns:
            True if task was deleted, False if not found
            
        Thought Process:
        - Boolean return indicates success/failure clearly
        - Idempotent: deleting twice returns True then False (not error)
        """
        if str(task_id) in self._tasks:
            del self._tasks[str(task_id)]
            return True
        return False