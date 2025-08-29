"""
Time & Productivity Integration Utilities
Handles query detection and persona-specific formatting for time/productivity features.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from utils.logger import logger
from services.time_productivity import (
    get_current_time, add_task, list_tasks, complete_task,
    start_timer, check_timer_status, start_time_tracking,
    format_time_response, format_task_list,
    TIME_PRODUCTIVITY_AVAILABLE
)

def detect_time_query(user_input: str) -> Dict[str, Any]:
    """Detect if user input is asking for time/date information"""
    
    time_keywords = [
        r'what.*time',
        r'current time',
        r'time.*now',
        r'what.*date',
        r'current date',
        r'today.*date',
        r'day.*today',
        r'what day',
        r'timezone',
        r'time zone',
        r'clock',
        r'hour',
        r'minute'
    ]
    
    # Timezone detection
    timezone_patterns = [
        r'time in ([a-zA-Z/]+)',
        r'time.*([A-Z]{2,4})',  # EST, PST, etc.
        r'timezone.*([a-zA-Z/]+)',
        r'([A-Z]{2,4}) time'
    ]
    
    query_lower = user_input.lower().strip()
    
    # Check for time query patterns
    is_time_query = any(re.search(pattern, query_lower) for pattern in time_keywords)
    
    # Extract timezone if mentioned
    timezone_str = "UTC"
    for pattern in timezone_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            timezone_str = match.group(1)
            break
    
    # Determine format preference
    format_str = "default"
    if "12 hour" in query_lower or "12-hour" in query_lower:
        format_str = "12hour"
    elif "24 hour" in query_lower or "24-hour" in query_lower:
        format_str = "24hour"
    elif "iso" in query_lower:
        format_str = "iso"
    
    return {
        "is_time_query": is_time_query,
        "timezone": timezone_str,
        "format": format_str,
        "original_query": user_input
    }

def detect_task_query(user_input: str) -> Dict[str, Any]:
    """Detect if user input is related to task management"""
    
    add_task_keywords = [
        r'add.*task',
        r'create.*task', 
        r'new task',
        r'remind me',
        r'set.*reminder',
        r'schedule.*task',
        r'todo.*add',
        r'need to do',
        r'add to.*list'
    ]
    
    list_task_keywords = [
        r'list.*tasks',
        r'show.*tasks',
        r'my tasks',
        r'todo.*list',
        r'what.*tasks',
        r'pending.*tasks',
        r'task.*status',
        r'what do i need',
        r'schedule.*today'
    ]
    
    complete_task_keywords = [
        r'complete.*task',
        r'finish.*task',
        r'done.*task',
        r'mark.*complete',
        r'task.*done',
        r'finished.*task'
    ]
    
    query_lower = user_input.lower().strip()
    
    # Detect query type
    is_add_task = any(re.search(pattern, query_lower) for pattern in add_task_keywords)
    is_list_tasks = any(re.search(pattern, query_lower) for pattern in list_task_keywords)
    is_complete_task = any(re.search(pattern, query_lower) for pattern in complete_task_keywords)
    
    query_type = None
    if is_add_task:
        query_type = "add_task"
    elif is_list_tasks:
        query_type = "list_tasks"
    elif is_complete_task:
        query_type = "complete_task"
    
    # Extract task information for add operations
    task_info = {}
    if is_add_task:
        # Try to extract task title from common patterns
        patterns = [
            r'remind me to (.+)',
            r'add.*task.*["\'](.+)["\']',
            r'task.*["\'](.+)["\']',
            r'need to (.+)',
            r'add.*task.*: (.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                task_info["title"] = match.group(1).strip()
                break
        
        # Extract priority
        priority_map = {
            "urgent": ["urgent", "asap", "immediately"],
            "high": ["high", "important", "priority"],
            "medium": ["medium", "normal"],
            "low": ["low", "when i can", "sometime"]
        }
        
        for priority, keywords in priority_map.items():
            if any(keyword in query_lower for keyword in keywords):
                task_info["priority"] = priority
                break
    
    return {
        "is_task_query": any([is_add_task, is_list_tasks, is_complete_task]),
        "query_type": query_type,
        "task_info": task_info,
        "original_query": user_input
    }

def detect_timer_query(user_input: str) -> Dict[str, Any]:
    """Detect if user input is related to timers/productivity"""
    
    timer_keywords = [
        r'start.*timer',
        r'pomodoro',
        r'set.*timer',
        r'timer.*minutes',
        r'work.*session',
        r'focus.*time',
        r'break.*timer',
        r'timer.*status',
        r'time.*tracking',
        r'track.*time'
    ]
    
    query_lower = user_input.lower().strip()
    
    is_timer_query = any(re.search(pattern, query_lower) for pattern in timer_keywords)
    
    # Extract timer details
    timer_info = {}
    
    # Extract duration in minutes
    duration_patterns = [
        r'(\d+)\s*minutes?',
        r'(\d+)\s*mins?',
        r'(\d+)\s*hour',  # Convert hours to minutes
        r'for (\d+)'
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, query_lower)
        if match:
            duration = int(match.group(1))
            if "hour" in pattern:
                duration *= 60  # Convert hours to minutes
            timer_info["duration"] = duration
            break
    
    # Detect timer type
    if "pomodoro" in query_lower:
        timer_info["type"] = "pomodoro"
        if "duration" not in timer_info:
            timer_info["duration"] = 25  # Default pomodoro duration
    elif "break" in query_lower:
        timer_info["type"] = "break"
        if "duration" not in timer_info:
            timer_info["duration"] = 5  # Default break duration
    elif "work" in query_lower or "focus" in query_lower:
        timer_info["type"] = "work"
    else:
        timer_info["type"] = "custom"
    
    return {
        "is_timer_query": is_timer_query,
        "timer_info": timer_info,
        "original_query": user_input
    }

def detect_productivity_query(user_input: str) -> Dict[str, Any]:
    """Master function to detect any time/productivity related query"""
    
    time_query = detect_time_query(user_input)
    task_query = detect_task_query(user_input)
    timer_query = detect_timer_query(user_input)
    
    # Determine primary query type
    query_type = None
    if time_query["is_time_query"]:
        query_type = "time"
    elif task_query["is_task_query"]:
        query_type = "task"
    elif timer_query["is_timer_query"]:
        query_type = "timer"
    
    return {
        "is_productivity_query": any([time_query["is_time_query"], task_query["is_task_query"], timer_query["is_timer_query"]]),
        "query_type": query_type,
        "time_info": time_query,
        "task_info": task_query,
        "timer_info": timer_query,
        "original_query": user_input
    }

async def handle_productivity_query(query_info: Dict[str, Any], session_id: str = "default") -> Optional[str]:
    """Handle productivity-related queries and return formatted response"""
    
    if not query_info.get("is_productivity_query") or not TIME_PRODUCTIVITY_AVAILABLE:
        return None
    
    try:
        query_type = query_info.get("query_type")
        
        if query_type == "time":
            # Handle time queries
            time_info = query_info["time_info"]
            time_data = await get_current_time(
                timezone_str=time_info["timezone"], 
                format_str=time_info["format"]
            )
            return format_time_response(time_data)
        
        elif query_type == "task":
            # Handle task queries
            task_info = query_info["task_info"]
            task_query_type = task_info.get("query_type")
            
            if task_query_type == "add_task":
                # Extract task details
                task_details = task_info.get("task_info", {})
                title = task_details.get("title", "New Task")
                priority = task_details.get("priority", "medium")
                
                result = await add_task(
                    title=title,
                    priority=priority,
                    session_id=session_id
                )
                
                if result["success"]:
                    return f"✅ Task added successfully: '{title}' with {priority} priority"
                else:
                    return f"Sorry, I couldn't add the task: {result.get('error', 'Unknown error')}"
            
            elif task_query_type == "list_tasks":
                tasks_data = await list_tasks(session_id=session_id, filter_completed=False)
                return format_task_list(tasks_data)
            
            elif task_query_type == "complete_task":
                # For simplicity, we'll need the user to specify which task
                return "To complete a task, please tell me the specific task title or use the web interface to select it."
        
        elif query_type == "timer":
            # Handle timer queries
            timer_info = query_info["timer_info"]["timer_info"]
            duration = timer_info.get("duration", 25)
            timer_type = timer_info.get("type", "pomodoro")
            
            result = await start_timer(
                name=f"{timer_type.title()} Session",
                duration_minutes=duration,
                timer_type=timer_type,
                session_id=session_id
            )
            
            if result["success"]:
                return f"⏰ {timer_type.title()} timer started for {duration} minutes! I'll help you stay focused."
            else:
                return f"Sorry, I couldn't start the timer: {result.get('error', 'Unknown error')}"
        
        return None
        
    except Exception as e:
        logger.error(f"Error handling productivity query: {e}")
        return None

def format_persona_productivity_response(response: str, persona_id: str) -> str:
    """Format productivity responses according to persona personality"""
    
    if not response:
        return response
    
    # Persona-specific formatting styles
    persona_styles = {
        "pirate": {
            "prefixes": ["Ahoy matey! ", "Shiver me timbers! ", "Arr, ye landlubber! "],
            "time_words": {"time": "ship's bell", "timer": "hourglass", "task": "treasure hunt"},
            "suffixes": [" Arr!", " Set sail!", " Yo ho ho!"]
        },
        "cowboy": {
            "prefixes": ["Well partner, ", "Howdy there, ", "Listen up, partner! "],
            "time_words": {"time": "time on the range", "timer": "pocket watch", "task": "chore"},
            "suffixes": [" Happy trails!", " Giddy up!", " That's how we do it in the West!"]
        },
        "robot": {
            "prefixes": ["PRODUCTIVITY DATA ANALYSIS: ", "TIME MANAGEMENT PROTOCOL ACTIVATED: ", "EFFICIENCY OPTIMIZATION: "],
            "time_words": {"time": "temporal coordinates", "timer": "chronometer", "task": "objective"},
            "suffixes": [" End transmission.", " Protocol complete.", " Data processed."]
        },
        "wizard": {
            "prefixes": ["Behold, young apprentice! ", "The ancient scrolls reveal: ", "By the power of time magic, "],
            "time_words": {"time": "temporal enchantment", "timer": "mystical hourglass", "task": "quest"},
            "suffixes": [" The prophecy is fulfilled!", " So the magic speaks!", " Time bends to our will!"]
        },
        "detective": {
            "prefixes": ["My investigation reveals: ", "The evidence shows: ", "Case analysis indicates: "],
            "time_words": {"time": "temporal evidence", "timer": "stopwatch", "task": "case"},
            "suffixes": [" The case is clear!", " Elementary, my dear Watson!", " Justice prevails!"]
        }
    }
    
    # Default style for unknown personas
    default_style = {
        "prefixes": [""],
        "time_words": {},
        "suffixes": [""]
    }
    
    style = persona_styles.get(persona_id, default_style)
    
    # Apply persona transformations
    formatted_response = response
    
    # Replace common words with persona-specific terms
    for standard, persona_word in style["time_words"].items():
        formatted_response = re.sub(
            rf'\b{standard}\b', 
            persona_word, 
            formatted_response, 
            flags=re.IGNORECASE
        )
    
    # Add prefix and suffix
    if style["prefixes"]:
        import random
        prefix = random.choice(style["prefixes"])
        if not formatted_response.startswith(prefix.strip()):
            formatted_response = prefix + formatted_response
    
    if style["suffixes"]:
        import random
        suffix = random.choice(style["suffixes"])
        if not formatted_response.endswith(suffix.strip()):
            formatted_response = formatted_response.rstrip(".!") + suffix
    
    return formatted_response

# ==== SMART TIME PARSING ====

def parse_natural_time(time_text: str) -> Optional[str]:
    """Parse natural language time expressions into ISO format"""
    
    time_text_lower = time_text.lower().strip()
    now = datetime.now(timezone.utc)
    
    # Common patterns
    patterns = {
        r'tomorrow': lambda: now + timedelta(days=1),
        r'next week': lambda: now + timedelta(weeks=1),
        r'in (\d+) hours?': lambda m: now + timedelta(hours=int(m.group(1))),
        r'in (\d+) days?': lambda m: now + timedelta(days=int(m.group(1))),
        r'in (\d+) minutes?': lambda m: now + timedelta(minutes=int(m.group(1))),
        r'next monday': lambda: now + timedelta(days=(7-now.weekday())),
        r'this friday': lambda: now + timedelta(days=(4-now.weekday()) % 7),
    }
    
    for pattern, time_func in patterns.items():
        match = re.search(pattern, time_text_lower)
        if match:
            try:
                if callable(time_func):
                    if match.groups():
                        result_time = time_func(match)
                    else:
                        result_time = time_func()
                    return result_time.isoformat()
            except Exception as e:
                logger.error(f"Error parsing natural time '{time_text}': {e}")
                continue
    
    return None

def extract_task_details_from_text(user_input: str) -> Dict[str, Any]:
    """Extract detailed task information from natural language"""
    
    task_details = {}
    
    # Extract title patterns
    title_patterns = [
        r'remind me to (.+?)(?:by|before|at|on|\.|$)',
        r'add.*task.*["\'](.+)["\']',
        r'need to (.+?)(?:by|before|at|on|\.|$)',
        r'task.*: (.+?)(?:by|before|at|on|\.|$)',
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            task_details["title"] = match.group(1).strip()
            break
    
    # Extract priority
    if any(word in user_input.lower() for word in ["urgent", "asap", "immediately"]):
        task_details["priority"] = "urgent"
    elif any(word in user_input.lower() for word in ["important", "high", "priority"]):
        task_details["priority"] = "high"
    elif any(word in user_input.lower() for word in ["low", "when i can", "sometime"]):
        task_details["priority"] = "low"
    else:
        task_details["priority"] = "medium"
    
    # Extract due date/time
    time_patterns = [
        r'by (.+?)(?:\.|$)',
        r'before (.+?)(?:\.|$)',
        r'at (.+?)(?:\.|$)',
        r'on (.+?)(?:\.|$)',
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            time_text = match.group(1).strip()
            parsed_time = parse_natural_time(time_text)
            if parsed_time:
                task_details["due_date"] = parsed_time
            break
    
    return task_details

# ==== COMPREHENSIVE QUERY HANDLER ====

async def handle_productivity_query_comprehensive(user_input: str, session_id: str = "default") -> Optional[str]:
    """Comprehensive handler for all productivity queries"""
    
    if not TIME_PRODUCTIVITY_AVAILABLE:
        return None
    
    try:
        # Detect all query types
        productivity_query = detect_productivity_query(user_input)
        
        if not productivity_query["is_productivity_query"]:
            return None
        
        query_type = productivity_query["query_type"]
        
        if query_type == "time":
            time_info = productivity_query["time_info"]
            time_data = await get_current_time(
                timezone_str=time_info["timezone"],
                format_str=time_info["format"]
            )
            return format_time_response(time_data)
        
        elif query_type == "task":
            task_info = productivity_query["task_info"]
            task_query_type = task_info.get("query_type")
            
            if task_query_type == "add_task":
                # Enhanced task extraction
                extracted_details = extract_task_details_from_text(user_input)
                
                if not extracted_details.get("title"):
                    return "I'd be happy to add a task for you! Please tell me what task you'd like me to add."
                
                result = await add_task(
                    title=extracted_details["title"],
                    due_date=extracted_details.get("due_date"),
                    priority=extracted_details.get("priority", "medium"),
                    session_id=session_id
                )
                
                if result["success"]:
                    due_info = ""
                    if extracted_details.get("due_date"):
                        try:
                            due_dt = datetime.fromisoformat(extracted_details["due_date"])
                            due_info = f" (due {due_dt.strftime('%B %d at %I:%M %p')})"
                        except:
                            due_info = f" (due {extracted_details['due_date']})"
                    
                    return f"✅ Perfect! I've added '{extracted_details['title']}' to your task list with {extracted_details.get('priority', 'medium')} priority{due_info}."
                else:
                    return f"Sorry, I couldn't add that task: {result.get('error', 'Unknown error')}"
            
            elif task_query_type == "list_tasks":
                tasks_data = await list_tasks(session_id=session_id, filter_completed=False)
                return format_task_list(tasks_data)
        
        elif query_type == "timer":
            timer_info = productivity_query["timer_info"]["timer_info"]
            duration = timer_info.get("duration", 25)
            timer_type = timer_info.get("type", "pomodoro")
            
            result = await start_timer(
                name=f"{timer_type.title()} Session",
                duration_minutes=duration,
                timer_type=timer_type,
                session_id=session_id
            )
            
            if result["success"]:
                return f"⏰ {timer_type.title()} timer started for {duration} minutes! Time to focus and be productive!"
            else:
                return f"Sorry, I couldn't start the timer: {result.get('error', 'Unknown error')}"
        
        return None
        
    except Exception as e:
        logger.error(f"Error handling comprehensive productivity query: {e}")
        return None
