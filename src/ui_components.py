"""
Reusable Streamlit UI components.
"""

import streamlit as st
from src.models import Task, Priority
from typing import Callable


def render_task_item(task: Task, idx: int, on_toggle: Callable) -> None:
    """
    Render a single task card with interactive elements.
    
    Args:
        task: Task instance to display
        idx: Position in task list (1-based for user display)
        on_toggle: Callback function when task is marked complete
    """
    # Choose priority icon based on level
    priority_icon = (
        "🔴" if task.priority == Priority.HIGH else
        "🟡" if task.priority == Priority.MEDIUM else
        "🔵"
    )
    
    # Choose status icon
    status_icon = "✅" if task.completed else "⏳"
    
    # Format scheduled date or show "No deadline"
    scheduled = (
        task.scheduled_time.strftime("%Y-%m-%d")
        if task.scheduled_time
        else "No deadline"
    )
    
    # Create two-column layout
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Display task info with icons and formatting
        st.markdown(
            f"**{idx}. {task.title}**  "
            f"{priority_icon} P{task.priority} | 📅 {scheduled} | {status_icon}"
        )
    
    with col2:
        # Toggle button with unique key
        if st.button("✓", key=f"toggle_{task.id}"):
            on_toggle(task.id)


def render_empty_state() -> None:
    """
    Render helpful message when no tasks exist.
    
    Provides examples to guide user on how to use the app.
    """
    st.info(
        "🎤 No tasks yet.\n\n"
        "Try saying:\n"
        "- 'Create a task to prepare presentation'\n"
        "- 'Show me all administrative tasks'\n"
        "- 'Delete the 3rd task'"
    )


def render_debug_panel(task_count: int, last_transcript: str) -> None:
    """
    Render collapsible debug information panel.
    
    Args:
        task_count: Total number of tasks
        last_transcript: Most recent voice command
    """
    with st.expander("📊 Debug Info"):
        st.metric("Total Tasks", task_count)
        st.write(f"**Last Transcript:** {last_transcript or 'None'}")