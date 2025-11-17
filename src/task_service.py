"""
Task business logic orchestration layer.
"""

from datetime import datetime, timedelta
import re
from typing import Optional, Sequence
from src.models import Task, TaskId, Priority
from src.repository import TaskRepository


class TaskService:
    """
    Orchestrates task operations and business logic.
    
    Responsibilities:
    - Create, read, update, delete tasks
    - Apply business rules (time parsing, filtering)
    - Coordinate with repository
    
    Design Pattern:
    - Service receives repository via dependency injection
    - All operations immutable (return new instances)
    - Type hints on all parameters and returns
    """
    
    def __init__(self, repository: TaskRepository) -> None:
        """
        Initialize task service with repository.
        
        Args:
            repository: TaskRepository instance (injected dependency)
        """
        self._repository = repository
    
    def create_task(
        self,
        title: str,
        scheduled_time: str | None = None,
        priority: int = 2
    ) -> Task:
        """
        Create and persist a new task.
        
        Args:
            title: Task description (required)
            scheduled_time: Natural language time (e.g., 'tomorrow')
            priority: Priority level 1-3 (default: 2=Medium)
            
        Returns:
            Created Task instance with ID and timestamp
        """
        task_id = TaskId()
        parsed_time = self._parse_time(scheduled_time) if scheduled_time else None
        
        task = Task(
            id=task_id,
            title=title.strip(),
            scheduled_time=parsed_time,
            priority=Priority(priority)
        )
        
        self._repository.save(task)
        return task
    
    def get_tasks(
        self,
        tags: list[str] | None = None,
        priority: int | None = None,
        completed: bool | None = None
    ) -> Sequence[Task]:
        """
        Retrieve tasks with optional filtering.
        
        Args:
            tags: Keywords to filter by (AND logic: any tag matches)
            priority: Filter by priority level (1-3)
            completed: Filter by completion status
            
        Returns:
            Tuple of matching Task instances
            
        Filter Logic:
        - All filters are optional (allows "show all tasks")
        - Tags use substring matching for flexibility
        - Returns immutable tuple to prevent external mutations
        
        Example:
            get_tasks(tags=['admin'], priority=3)  # High priority admin tasks
            get_tasks()  # All tasks
        """
        tasks = self._repository.find_all()
        
        # Filter by tags (keywords in task title)
        if tags:
            tasks = tuple(
                t for t in tasks
                if any(tag.lower() in t.title.lower() for tag in tags)
            )
        
        # Filter by priority
        if priority is not None:
            tasks = tuple(t for t in tasks if t.priority.value == priority)
        
        # Filter by completion status
        if completed is not None:
            tasks = tuple(t for t in tasks if t.completed == completed)
        
        return tasks
    
    def update_task(
        self,
        identifier: str,
        **updates
    ) -> Task | None:
        """
        Update task by identifier or index.
        
        Args:
            identifier: Task keywords or index (e.g., '3' or 'about bugs')
            **updates: Keyword args for fields to update
                - scheduled_time: New time (natural language)
                - priority: New priority (1-3)
                - completed: New completion status (bool)
            
        Returns:
            Updated Task instance, or None if not found
    
        Example:
            update_task('3', priority=3)  # Update 3rd task priority
            update_task('bugs', scheduled_time='tomorrow')  # Update by keyword
        """
        task = self._find_task(identifier)
        
        if not task:
            return None
        
        # Apply updates immutably
        updated_task = task
        
        if "scheduled_time" in updates and updates["scheduled_time"]:
            new_time = self._parse_time(updates["scheduled_time"])
            updated_task = updated_task.reschedule(new_time)
        
        if "priority" in updates:
            new_priority = Priority(updates["priority"])
            updated_task = updated_task.update_priority(new_priority)
        
        if "completed" in updates and updates["completed"]:
            updated_task = updated_task.mark_complete()
        
        # Persist the updated task
        self._repository.save(updated_task)
        return updated_task
    
    def delete_task(self, identifier: str) -> bool:
        """
        Delete task by identifier or index.
        
        Args:
            identifier: Task keywords or index
            
        Returns:
            True if deleted, False if not found
        """
        task = self._find_task(identifier)
        
        if not task:
            return False
        
        return self._repository.delete(task.id)
    
    def _find_task(self, identifier: str) -> Task | None:
        """
        Find task by index or keywords.
        
        Args:
            identifier: Either integer index (1-based) or keywords
            
        Returns:
            Task if found, None otherwise
        """
        # Try integer index first (1-based indexing for user friendliness)
        try:
            idx = int(identifier) - 1  # Convert to 0-based
            tasks = list(self._repository.find_all())
            if 0 <= idx < len(tasks):
                return tasks[idx]
        except ValueError:
            # Not an integer, try keyword matching
            pass
        
        # Try keyword matching
        matching = self.get_tasks(tags=[identifier])
        return matching[0] if matching else None
    
    @staticmethod
    def _parse_time(time_str: str) -> datetime:
        """
        Parse natural language time expressions into datetime.
        
        Args:
            time_str: Natural language time (e.g., 'tomorrow', 'in 3 days')
            
        Returns:
            datetime object representing the parsed time
            
        Supported formats:
        - 'tomorrow': Next day at current time
        - 'next week': 7 days from now
        - 'in X days': X days from now
        - 'in X hours': X hours from now
        """
        time_str = time_str.lower().strip()
        now = datetime.now()
        
        # Check each pattern in order
        if "tomorrow" in time_str:
            return now + timedelta(days=1)
        
        if "next week" in time_str:
            return now + timedelta(weeks=1)
        
        # Match "in X days"
        days_match = re.search(r"in\s+(\d+)\s+days?", time_str)
        if days_match:
            return now + timedelta(days=int(days_match.group(1)))
        
        # Match "in X hours"
        hours_match = re.search(r"in\s+(\d+)\s+hours?", time_str)
        if hours_match:
            return now + timedelta(hours=int(hours_match.group(1)))
        
        # Default: return current time if no pattern matched
        return now
