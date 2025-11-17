"""
Voice-First To-Do List Web Application - Streamlit Entry Point

Architecture:
- Streamlit handles UI rendering and real-time updates
- Services layer handles business logic (audio, LLM, tasks)
- Repository layer handles data persistence
- Clean separation of concerns enables testing and maintenance

Main Pipeline:
1. User speaks -> Audio captured by browser
2. Deepgram STT -> Text transcript (200-300ms)
3. GPT-4o-mini -> Intent extraction (500-800ms)
4. TaskService -> CRUD operation (50ms)
5. Repository -> Persistence (<10ms)
6. UI -> Refresh and display results
"""

import streamlit as st
from src.repository import TaskRepository
from src.audio_service import AudioService
from src.llm_service import LLMService
from src.task_service import TaskService
from src.ui_components import render_task_item, render_empty_state, render_debug_panel
from src.models import Priority

st.set_page_config(
    page_title="Voice Todo App",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal CSS for clean UI
st.markdown("""
    <style>
    .main { padding: 20px; }
    .stMetric { text-align: center; }
    </style>
""", unsafe_allow_html=True)


# Service initialization

@st.cache_resource
def get_services() -> tuple:
    """
    Initialize all services once per Streamlit session.
    
    Returns:
        Tuple of (TaskService, AudioService, LLMService)
    
    Design Notes:
    - @st.cache_resource: Only initializes once per session
    - Reduces redundant API client creation
    - Services are thread-safe (no state mutation)
    """
    # Data layer
    repository = TaskRepository()
    
    # Service layer
    task_service = TaskService(repository)
    audio_service = AudioService(api_key=st.secrets["DEEPGRAM_API_KEY"])
    llm_service = LLMService(api_key=st.secrets["OPENAI_API_KEY"])
    
    return task_service, audio_service, llm_service


@st.cache_resource
def init_session_state() -> None:
    """
    Initialize Streamlit session state variables.
    """
    if "transcript" not in st.session_state:
        st.session_state.transcript = ""


# Main app logic

def main() -> None:
    """
    Main application entry point.
    
    Renders UI and orchestrates the voice command pipeline.
    """
    # Page header
    st.markdown("# 🎤 Voice-First Todo List")
    st.markdown("Click the button below and speak your command")
    
    # Initialize services
    task_service, audio_service, llm_service = get_services()
    init_session_state()
    
    # Audio input section
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        audio_data = st.audio_input(
            "Record your command",
            label_visibility="collapsed"
        )
    
    # Process audio when captured
    
    if audio_data:
        process_audio_command(
            audio_data,
            task_service,
            audio_service,
            llm_service
        )
    
    # Display task
    
    st.markdown("## 📋 Your Tasks")
    display_tasks(task_service)
    
    # Debug point
    
    render_debug_panel(
        len(task_service._repository.find_all()),
        st.session_state.transcript
    )


def process_audio_command(
    audio_data,
    task_service: TaskService,
    audio_service: AudioService,
    llm_service: LLMService
) -> None:
    """
    Process voice command through complete pipeline.
    
    Args:
        audio_data: Audio bytes from Streamlit recorder
        task_service: TaskService for CRUD operations
        audio_service: AudioService for STT
        llm_service: LLMService for intent extraction
    """
    try:
        with st.spinner("🔄 Processing..."):
            
            # Transcribe Audio
            
            transcription = audio_service.transcribe(audio_data.getvalue())
            st.session_state.transcript = transcription.transcript
            
            # Check if audio was captured
            if transcription.is_empty:
                st.warning("⚠️ Could not capture audio. Please try again.")
                return
            
            # Show transcript with confidence indicator
            confidence_emoji = "✅" if transcription.confidence > 0.85 else "⚠️"
            st.success(f"📝 {confidence_emoji} *{transcription.transcript}*")
            
            # Extract intent
            
            function_call = llm_service.process_command(transcription.transcript)
            action = function_call.action
            parameters = function_call.parameters
            
            # Execute action
        
            result_message = execute_task_action(action, parameters, task_service)
            st.info(result_message)
    
    except ValueError as e:
        # Expected errors (transcription, LLM processing)
        st.error(f"❌ Error: {e}")
    except Exception as e:
        # Unexpected errors
        st.error(f"❌ Unexpected error: {e}")


def execute_task_action(
    action: str,
    parameters: dict,
    task_service: TaskService
) -> str:
    """
    Execute the appropriate task operation based on LLM intent.
    
    Args:
        action: Action name from LLM (create_task, get_tasks, etc.)
        parameters: Parameters extracted from user command
        task_service: TaskService for operations
        
    Returns:
        User-friendly result message
    """
    try:
        if action == "create_task":
            # Create a new task from parameters
            task = task_service.create_task(**parameters)
            return f"✅ Created task: **{task.title}**"
        
        elif action == "get_tasks":
            # Query tasks with optional filters
            tasks = task_service.get_tasks(**parameters)
            count = len(tasks)
            if count == 0:
                return "📋 No tasks found matching your criteria"
            return f"📋 Found {count} task(s)"
        
        elif action == "update_task":
            # Update task (extract identifier from params)
            identifier = parameters.pop("task_identifier")
            task = task_service.update_task(identifier, **parameters)
            
            if not task:
                return "❌ Task not found"
            
            return f"✏️ Updated: **{task.title}**"
        
        elif action == "delete_task":
            # Delete task by identifier
            identifier = parameters.get("task_identifier")
            if identifier is None:
                return "❌ No task identifier provided"
            # Ensure identifier is a string before passing to the repository
            success = task_service.delete_task(str(identifier))
            
            return "🗑️ Task deleted" if success else "❌ Task not found"
        
        elif action == "respond":
            # Conversational response (LLM didn't recognize as CRUD)
            message = parameters.get("message", "OK")
            return f"💬 {message}"
        
        else:
            return f"❓ Unknown action: {action}"
    
    except Exception as e:
        return f"❌ Failed to execute action: {e}"


def display_tasks(task_service: TaskService) -> None:
    """
    Render all tasks in an organized list.
    
    Args:
        task_service: TaskService to fetch tasks
    """
    tasks = task_service._repository.find_all()
    
    if not tasks:
        render_empty_state()
        return
    
    # Display each task with toggle capability
    for idx, task in enumerate(tasks, 1):
        def on_toggle(task_id):
            """Callback when user clicks task toggle button."""
            t = task_service._repository.find_by_id(task_id)
            if t:
                # Toggle completion status
                task_service.update_task(
                    str(t.id),
                    completed=not t.completed
                )
                # Rerun to refresh UI
                st.rerun()
        
        render_task_item(task, idx, on_toggle)


if __name__ == "__main__":
    main()