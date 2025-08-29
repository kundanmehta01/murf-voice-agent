"""
Time & Productivity Management Service
Provides time/date information, task management, and productivity tools for the voice agent.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pytz
from utils.logger import logger

# Global availability flag
TIME_PRODUCTIVITY_AVAILABLE = True

# In-memory storage for tasks (in production, this would be a database)
TASKS_STORAGE = {}
TIMERS_STORAGE = {}
TIME_TRACKING_STORAGE = {}

@dataclass
class Task:
    """Task/reminder data model"""
    id: str
    title: str
    description: str = ""
    due_date: Optional[str] = None
    priority: str = "medium"  # low, medium, high, urgent
    completed: bool = False
    created_at: str = ""
    completed_at: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

@dataclass
class Timer:
    """Timer data model for pomodoro/time tracking"""
    id: str
    name: str
    duration_minutes: int
    start_time: str
    end_time: Optional[str] = None
    is_active: bool = True
    timer_type: str = "pomodoro"  # pomodoro, break, work, custom
    
@dataclass
class TimeSession:
    """Time tracking session"""
    id: str
    task_name: str
    start_time: str
    end_time: Optional[str] = None
    duration_minutes: Optional[float] = None
    notes: str = ""

class TimeProductivityService:
    """Main service class for time and productivity features"""
    
    def __init__(self):
        self.tasks = TASKS_STORAGE
        self.timers = TIMERS_STORAGE
        self.time_sessions = TIME_TRACKING_STORAGE
    
    # ==== TIME & DATE FUNCTIONS ====
    
    async def get_current_time(self, timezone_str: str = "UTC", format_str: str = "default") -> Dict[str, Any]:
        """Get current time in specified timezone"""
        try:
            if timezone_str.upper() == "UTC":
                tz = timezone.utc
            else:
                try:
                    tz = pytz.timezone(timezone_str)
                except pytz.exceptions.UnknownTimeZoneError:
                    # Try common timezone abbreviations
                    timezone_mapping = {
                        "EST": "US/Eastern",
                        "PST": "US/Pacific",
                        "CST": "US/Central",
                        "MST": "US/Mountain",
                        "GMT": "GMT",
                        "CET": "Europe/Berlin",
                        "JST": "Asia/Tokyo",
                        "IST": "Asia/Kolkata"
                    }
                    if timezone_str.upper() in timezone_mapping:
                        tz = pytz.timezone(timezone_mapping[timezone_str.upper()])
                    else:
                        tz = timezone.utc  # Fallback to UTC
            
            now = datetime.now(tz)
            
            # Format options
            if format_str == "iso":
                formatted_time = now.isoformat()
            elif format_str == "12hour":
                formatted_time = now.strftime("%I:%M %p on %B %d, %Y")
            elif format_str == "24hour":
                formatted_time = now.strftime("%H:%M on %B %d, %Y")
            else:  # default
                formatted_time = now.strftime("%A, %B %d, %Y at %I:%M %p %Z")
            
            return {
                "success": True,
                "current_time": formatted_time,
                "timezone": str(tz),
                "iso_time": now.isoformat(),
                "unix_timestamp": now.timestamp(),
                "day_of_week": now.strftime("%A"),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error getting current time: {e}")
            return {"success": False, "error": str(e)}
    
    async def calculate_time_difference(self, start_time: str, end_time: str = None) -> Dict[str, Any]:
        """Calculate time difference between two timestamps"""
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.now(timezone.utc) if end_time is None else datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            diff = end_dt - start_dt
            total_seconds = diff.total_seconds()
            
            days = diff.days
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return {
                "success": True,
                "total_days": days,
                "total_hours": int(hours),
                "total_minutes": int(minutes),
                "total_seconds": int(seconds),
                "total_seconds_precise": total_seconds,
                "human_readable": self._format_duration(total_seconds)
            }
            
        except Exception as e:
            logger.error(f"Error calculating time difference: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_duration(self, total_seconds: float) -> str:
        """Format duration in human-readable format"""
        if total_seconds < 60:
            return f"{int(total_seconds)} seconds"
        elif total_seconds < 3600:
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            return f"{minutes} minutes and {seconds} seconds"
        elif total_seconds < 86400:
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours} hours and {minutes} minutes"
        else:
            days = int(total_seconds // 86400)
            hours = int((total_seconds % 86400) // 3600)
            return f"{days} days and {hours} hours"
    
    # ==== TASK MANAGEMENT FUNCTIONS ====
    
    async def add_task(self, title: str, description: str = "", due_date: str = None, 
                      priority: str = "medium", tags: List[str] = None, session_id: str = "default") -> Dict[str, Any]:
        """Add a new task/reminder"""
        try:
            import uuid
            task_id = str(uuid.uuid4())
            
            # Validate due_date if provided
            if due_date:
                try:
                    # Try to parse the due_date to validate it
                    datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    return {"success": False, "error": "Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}
            
            task = Task(
                id=task_id,
                title=title,
                description=description,
                due_date=due_date,
                priority=priority.lower() if priority else "medium",
                tags=tags or []
            )
            
            # Store by session
            if session_id not in self.tasks:
                self.tasks[session_id] = {}
            
            self.tasks[session_id][task_id] = task
            
            return {
                "success": True,
                "task": asdict(task),
                "message": f"Task '{title}' added successfully"
            }
            
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_tasks(self, session_id: str = "default", filter_completed: bool = None, 
                        priority: str = None) -> Dict[str, Any]:
        """List tasks with optional filters"""
        try:
            if session_id not in self.tasks:
                return {"success": True, "tasks": [], "count": 0}
            
            tasks = list(self.tasks[session_id].values())
            
            # Apply filters
            if filter_completed is not None:
                tasks = [t for t in tasks if t.completed == filter_completed]
            
            if priority:
                tasks = [t for t in tasks if t.priority.lower() == priority.lower()]
            
            # Sort by priority and due_date
            priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
            tasks.sort(key=lambda t: (
                priority_order.get(t.priority, 2),
                t.due_date or "9999-12-31",
                t.created_at
            ))
            
            return {
                "success": True,
                "tasks": [asdict(t) for t in tasks],
                "count": len(tasks)
            }
            
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return {"success": False, "error": str(e)}
    
    async def complete_task(self, task_id: str, session_id: str = "default") -> Dict[str, Any]:
        """Mark a task as completed"""
        try:
            if session_id not in self.tasks or task_id not in self.tasks[session_id]:
                return {"success": False, "error": "Task not found"}
            
            task = self.tasks[session_id][task_id]
            task.completed = True
            task.completed_at = datetime.now(timezone.utc).isoformat()
            
            return {
                "success": True,
                "task": asdict(task),
                "message": f"Task '{task.title}' marked as completed"
            }
            
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return {"success": False, "error": str(e)}
    
    # ==== TIMER & PRODUCTIVITY FUNCTIONS ====
    
    async def start_timer(self, name: str, duration_minutes: int, timer_type: str = "pomodoro", 
                         session_id: str = "default") -> Dict[str, Any]:
        """Start a productivity timer (pomodoro, work session, etc.)"""
        try:
            import uuid
            timer_id = str(uuid.uuid4())
            
            timer = Timer(
                id=timer_id,
                name=name,
                duration_minutes=duration_minutes,
                start_time=datetime.now(timezone.utc).isoformat(),
                timer_type=timer_type.lower()
            )
            
            # Store by session
            if session_id not in self.timers:
                self.timers[session_id] = {}
            
            self.timers[session_id][timer_id] = timer
            
            return {
                "success": True,
                "timer": asdict(timer),
                "message": f"{timer_type.title()} timer '{name}' started for {duration_minutes} minutes"
            }
            
        except Exception as e:
            logger.error(f"Error starting timer: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_timer_status(self, timer_id: str = None, session_id: str = "default") -> Dict[str, Any]:
        """Check status of active timers"""
        try:
            if session_id not in self.timers:
                return {"success": True, "active_timers": [], "count": 0}
            
            timers = self.timers[session_id]
            
            if timer_id:
                # Check specific timer
                if timer_id not in timers:
                    return {"success": False, "error": "Timer not found"}
                
                timer = timers[timer_id]
                status = await self._get_timer_status(timer)
                return {"success": True, "timer": status}
            else:
                # Check all active timers
                active_timers = []
                for timer in timers.values():
                    if timer.is_active:
                        status = await self._get_timer_status(timer)
                        active_timers.append(status)
                
                return {
                    "success": True,
                    "active_timers": active_timers,
                    "count": len(active_timers)
                }
                
        except Exception as e:
            logger.error(f"Error checking timer status: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_timer_status(self, timer: Timer) -> Dict[str, Any]:
        """Get detailed status of a timer"""
        start_time = datetime.fromisoformat(timer.start_time)
        now = datetime.now(timezone.utc)
        elapsed = (now - start_time).total_seconds()
        total_duration = timer.duration_minutes * 60
        
        remaining = max(0, total_duration - elapsed)
        progress_percent = min(100, (elapsed / total_duration) * 100)
        
        is_finished = remaining <= 0
        if is_finished and timer.is_active:
            timer.is_active = False
            timer.end_time = now.isoformat()
        
        return {
            **asdict(timer),
            "elapsed_seconds": int(elapsed),
            "remaining_seconds": int(remaining),
            "progress_percent": round(progress_percent, 1),
            "is_finished": is_finished,
            "time_left_formatted": self._format_duration(remaining) if remaining > 0 else "Finished!"
        }
    
    async def start_time_tracking(self, task_name: str, session_id: str = "default") -> Dict[str, Any]:
        """Start tracking time for a task"""
        try:
            import uuid
            session_track_id = str(uuid.uuid4())
            
            time_session = TimeSession(
                id=session_track_id,
                task_name=task_name,
                start_time=datetime.now(timezone.utc).isoformat()
            )
            
            if session_id not in self.time_sessions:
                self.time_sessions[session_id] = {}
            
            self.time_sessions[session_id][session_track_id] = time_session
            
            return {
                "success": True,
                "session": asdict(time_session),
                "message": f"Started tracking time for '{task_name}'"
            }
            
        except Exception as e:
            logger.error(f"Error starting time tracking: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_time_tracking(self, session_track_id: str, notes: str = "", 
                                session_id: str = "default") -> Dict[str, Any]:
        """Stop time tracking session"""
        try:
            if session_id not in self.time_sessions or session_track_id not in self.time_sessions[session_id]:
                return {"success": False, "error": "Time tracking session not found"}
            
            time_session = self.time_sessions[session_id][session_track_id]
            if time_session.end_time:
                return {"success": False, "error": "Session already stopped"}
            
            end_time = datetime.now(timezone.utc)
            start_time = datetime.fromisoformat(time_session.start_time)
            duration = (end_time - start_time).total_seconds() / 60  # in minutes
            
            time_session.end_time = end_time.isoformat()
            time_session.duration_minutes = round(duration, 2)
            time_session.notes = notes
            
            return {
                "success": True,
                "session": asdict(time_session),
                "message": f"Time tracking stopped. Duration: {self._format_duration(duration * 60)}"
            }
            
        except Exception as e:
            logger.error(f"Error stopping time tracking: {e}")
            return {"success": False, "error": str(e)}

# Create global service instance
time_service = TimeProductivityService()

# ==== HELPER FUNCTIONS ====

async def get_current_time(timezone_str: str = "UTC", format_str: str = "default"):
    """Get current time in specified timezone"""
    return await time_service.get_current_time(timezone_str, format_str)

async def add_task(title: str, description: str = "", due_date: str = None, 
                  priority: str = "medium", tags: List[str] = None, session_id: str = "default"):
    """Add a new task"""
    return await time_service.add_task(title, description, due_date, priority, tags, session_id)

async def list_tasks(session_id: str = "default", filter_completed: bool = None, priority: str = None):
    """List tasks with filters"""
    return await time_service.list_tasks(session_id, filter_completed, priority)

async def complete_task(task_id: str, session_id: str = "default"):
    """Complete a task"""
    return await time_service.complete_task(task_id, session_id)

async def start_timer(name: str, duration_minutes: int, timer_type: str = "pomodoro", session_id: str = "default"):
    """Start a productivity timer"""
    return await time_service.start_timer(name, duration_minutes, timer_type, session_id)

async def check_timer_status(timer_id: str = None, session_id: str = "default"):
    """Check timer status"""
    return await time_service.check_timer_status(timer_id, session_id)

async def start_time_tracking(task_name: str, session_id: str = "default"):
    """Start time tracking"""
    return await time_service.start_time_tracking(task_name, session_id)

async def stop_time_tracking(session_id: str, notes: str = "", session_id_param: str = "default"):
    """Stop time tracking"""
    return await time_service.stop_time_tracking(session_id, notes, session_id_param)

def format_time_response(time_data: Dict[str, Any]) -> str:
    """Format time data for display"""
    if not time_data.get("success"):
        return f"Sorry, I couldn't get the time information: {time_data.get('error', 'Unknown error')}"
    
    return f"The current time is {time_data['current_time']}"

def format_task_list(tasks_data: Dict[str, Any]) -> str:
    """Format task list for display"""
    if not tasks_data.get("success"):
        return f"Sorry, I couldn't get your tasks: {tasks_data.get('error', 'Unknown error')}"
    
    tasks = tasks_data.get("tasks", [])
    if not tasks:
        return "You don't have any tasks at the moment."
    
    response = f"Here are your {len(tasks)} task(s):\n\n"
    
    for i, task in enumerate(tasks, 1):
        status = "✅" if task["completed"] else "⏰"
        priority_emoji = {"urgent": "🔥", "high": "⚡", "medium": "📋", "low": "📝"}.get(task["priority"], "📋")
        
        response += f"{status} {priority_emoji} **{task['title']}**"
        
        if task["description"]:
            response += f" - {task['description']}"
        
        if task["due_date"]:
            try:
                due_dt = datetime.fromisoformat(task["due_date"].replace('Z', '+00:00'))
                response += f" (Due: {due_dt.strftime('%m/%d/%Y %I:%M %p')})"
            except:
                response += f" (Due: {task['due_date']})"
        
        response += f" [{task['priority']} priority]"
        
        if task["tags"]:
            response += f" Tags: {', '.join(task['tags'])}"
        
        response += "\n"
    
    return response.strip()
