"""
Chat component for Prometheus Agent AI Streamlit UI.
"""

import streamlit as st
import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import uuid

class ChatComponent:
    """Chat component for conversational interaction with the AI agent."""
    
    def __init__(self, api_client: httpx.AsyncClient, api_base_url: str):
        """Initialize chat component.
        
        Args:
            api_client: HTTP client for API calls
            api_base_url: Base URL for the API
        """
        self.api_client = api_client
        self.api_base_url = api_base_url
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize session state variables for chat."""
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        if "conversation_id" not in st.session_state:
            st.session_state.conversation_id = str(uuid.uuid4())
        
        if "chat_context" not in st.session_state:
            st.session_state.chat_context = {
                "include_metrics": True,
                "last_query": None,
                "active_alerts": []
            }
    
    def render_chat_interface(self) -> None:
        """Render the main chat interface."""
        st.header("💬 Chat with Prometheus Agent AI")
        
        # Chat configuration
        self._render_chat_settings()
        
        # Chat history
        self._render_chat_history()
        
        # Chat input
        self._render_chat_input()
        
        # Quick actions
        self._render_quick_actions()
        
        # Suggested questions
        self._render_suggested_questions()
    
    def _render_chat_settings(self) -> None:
        """Render chat configuration settings."""
        with st.expander("⚙️ Chat Settings", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                include_metrics = st.checkbox(
                    "Include current metrics context",
                    value=st.session_state.chat_context["include_metrics"],
                    help="Include current system metrics in the conversation context"
                )
                st.session_state.chat_context["include_metrics"] = include_metrics
            
            with col2:
                if st.button("🗑️ Clear Chat History"):
                    st.session_state.chat_messages = []
                    st.session_state.conversation_id = str(uuid.uuid4())
                    st.success("Chat history cleared!")
                    st.rerun()
            
            with col3:
                if st.button("📋 Export Chat"):
                    self._export_chat_history()
    
    def _render_chat_history(self) -> None:
        """Render the chat message history."""
        if not st.session_state.chat_messages:
            st.info("👋 Hi! I'm your AI monitoring assistant. Ask me about your Prometheus metrics, alerts, or system health!")
            return
        
        # Display messages in a container with custom styling
        chat_container = st.container()
        
        with chat_container:
            for i, message in enumerate(st.session_state.chat_messages):
                self._render_message(message, i)
    
    def _render_message(self, message: Dict[str, Any], index: int) -> None:
        """Render a single chat message.
        
        Args:
            message: Message dictionary with role, content, timestamp
            index: Message index for unique keys
        """
        timestamp = message.get("timestamp", datetime.now())
        formatted_time = timestamp.strftime("%H:%M:%S") if isinstance(timestamp, datetime) else str(timestamp)
        
        if message["role"] == "user":
            # User message - right aligned
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                    <div style="background-color: #007ACC; color: white; padding: 10px 15px; 
                                border-radius: 18px 18px 5px 18px; max-width: 70%; 
                                box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <div style="font-size: 14px; margin-bottom: 5px;">
                            <strong>You</strong> <span style="font-size: 12px; opacity: 0.8;">{formatted_time}</span>
                        </div>
                        <div>{message["content"]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Assistant message - left aligned
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                    <div style="background-color: #f0f2f6; color: #262730; padding: 10px 15px; 
                                border-radius: 18px 18px 18px 5px; max-width: 70%; 
                                box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <div style="font-size: 14px; margin-bottom: 5px;">
                            <strong>🤖 Agent</strong> <span style="font-size: 12px; opacity: 0.6;">{formatted_time}</span>
                        </div>
                        <div>{message["content"]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Show suggested actions if available
            if message.get("suggested_actions"):
                st.markdown("**Suggested actions:**")
                for action in message["suggested_actions"]:
                    if st.button(f"🔗 {action}", key=f"action_{index}_{action}"):
                        self._execute_suggested_action(action)
    
    def _render_chat_input(self) -> None:
        """Render chat input area."""
        st.markdown("---")
        
        # Use form to handle enter key submission
        with st.form(key="chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_input(
                    "Ask me anything about your metrics...",
                    placeholder="e.g., 'Show me CPU usage trends' or 'What alerts are currently active?'",
                    label_visibility="collapsed"
                )
            
            with col2:
                submit_button = st.form_submit_button("Send 📤", use_container_width=True)
            
            if submit_button and user_input.strip():
                self._handle_user_message(user_input.strip())
    
    def _render_quick_actions(self) -> None:
        """Render quick action buttons."""
        st.markdown("**Quick Actions:**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 System Health", key="quick_health"):
                self._handle_user_message("Analyze the current system health")
        
        with col2:
            if st.button("🚨 Active Alerts", key="quick_alerts"):
                self._handle_user_message("Show me all active alerts")
        
        with col3:
            if st.button("💻 CPU Usage", key="quick_cpu"):
                self._handle_user_message("What's the current CPU usage across all instances?")
        
        with col4:
            if st.button("💾 Memory Usage", key="quick_memory"):
                self._handle_user_message("Show me memory usage patterns")
    
    def _render_suggested_questions(self) -> None:
        """Render suggested questions for new users."""
        if len(st.session_state.chat_messages) == 0:
            st.markdown("### 💡 Try asking me:")
            
            suggested_questions = [
                "What's the current system health status?",
                "Show me CPU usage for the last hour",
                "Are there any alerts I should be concerned about?",
                "What's the error rate for my HTTP requests?",
                "Help me understand my memory usage patterns",
                "Show me network traffic trends",
                "What metrics should I be monitoring for my application?",
                "Explain the current disk usage situation"
            ]
            
            # Display suggestions in columns
            cols = st.columns(2)
            for i, question in enumerate(suggested_questions):
                col = cols[i % 2]
                with col:
                    if st.button(f"💭 {question}", key=f"suggested_{i}"):
                        self._handle_user_message(question)
    
    def _handle_user_message(self, message: str) -> None:
        """Handle user message and get AI response.
        
        Args:
            message: User's message
        """
        # Add user message to history
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now()
        }
        st.session_state.chat_messages.append(user_message)
        
        # Show typing indicator
        with st.spinner("🤖 Agent is thinking..."):
            try:
                # Get AI response
                response_data = asyncio.run(self._get_ai_response(message))
                
                if response_data and "response" in response_data:
                    assistant_message = {
                        "role": "assistant",
                        "content": response_data["response"],
                        "timestamp": datetime.now(),
                        "suggested_actions": response_data.get("suggested_actions", [])
                    }
                    st.session_state.chat_messages.append(assistant_message)
                else:
                    error_message = {
                        "role": "assistant",
                        "content": "I'm sorry, I encountered an issue processing your request. Please try again.",
                        "timestamp": datetime.now()
                    }
                    st.session_state.chat_messages.append(error_message)
            
            except Exception as e:
                error_message = {
                    "role": "assistant",
                    "content": f"I apologize, but I encountered an error: {str(e)}. Please try your question again.",
                    "timestamp": datetime.now()
                }
                st.session_state.chat_messages.append(error_message)
        
        # Rerun to show the new messages
        st.rerun()
    
    async def _get_ai_response(self, message: str) -> Optional[Dict[str, Any]]:
        """Get AI response from the API.
        
        Args:
            message: User's message
            
        Returns:
            AI response data
        """
        try:
            request_data = {
                "message": message,
                "conversation_id": st.session_state.conversation_id,
                "include_metrics_context": st.session_state.chat_context["include_metrics"]
            }
            
            response = await self.api_client.post(
                f"{self.api_base_url}/api/v1/analysis/chat",
                json=request_data,
                timeout=60.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API request failed with status {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Failed to get AI response: {str(e)}")
            return None
    
    def _execute_suggested_action(self, action: str) -> None:
        """Execute a suggested action.
        
        Args:
            action: Action to execute
        """
        # Map actions to user messages
        action_map = {
            "Check system health": "Analyze the current system health",
            "View active alerts": "Show me all active alerts",
            "Investigate alert": "Help me investigate the most critical alert",
            "Show metrics": "Show me the most important metrics right now",
        }
        
        message = action_map.get(action, action)
        self._handle_user_message(message)
    
    def _export_chat_history(self) -> None:
        """Export chat history to JSON."""
        if not st.session_state.chat_messages:
            st.warning("No chat history to export.")
            return
        
        try:
            # Prepare export data
            export_data = {
                "conversation_id": st.session_state.conversation_id,
                "export_timestamp": datetime.now().isoformat(),
                "messages": []
            }
            
            for message in st.session_state.chat_messages:
                export_message = {
                    "role": message["role"],
                    "content": message["content"],
                    "timestamp": message["timestamp"].isoformat() if isinstance(message["timestamp"], datetime) else str(message["timestamp"])
                }
                export_data["messages"].append(export_message)
            
            # Create download
            json_str = json.dumps(export_data, indent=2)
            st.download_button(
                label="📥 Download Chat History",
                data=json_str,
                file_name=f"prometheus_agent_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"Failed to export chat history: {str(e)}")
    
    def render_chat_sidebar(self) -> None:
        """Render chat-related information in sidebar."""
        with st.sidebar:
            st.markdown("### 💬 Chat Info")
            
            if st.session_state.chat_messages:
                st.metric("Messages", len(st.session_state.chat_messages))
                
                # Show conversation stats
                user_messages = len([m for m in st.session_state.chat_messages if m["role"] == "user"])
                assistant_messages = len([m for m in st.session_state.chat_messages if m["role"] == "assistant"])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("You", user_messages)
                with col2:
                    st.metric("Agent", assistant_messages)
            
            st.markdown("---")
            
            # Context settings
            st.markdown("**Context Settings**")
            if st.session_state.chat_context["include_metrics"]:
                st.success("✅ Metrics context enabled")
            else:
                st.warning("⚠️ Metrics context disabled")
            
            # Conversation ID
            if st.button("🔄 New Conversation"):
                st.session_state.conversation_id = str(uuid.uuid4())
                st.session_state.chat_messages = []
                st.success("Started new conversation!")
                st.rerun()
