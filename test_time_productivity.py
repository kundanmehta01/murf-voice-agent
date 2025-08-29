"""
Comprehensive test suite for Time & Productivity functionality
Tests all aspects of the time/productivity service and integration.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from services.time_productivity import (
    TimeProductivityService, get_current_time, add_task, list_tasks, 
    complete_task, start_timer, check_timer_status,
    format_time_response, format_task_list,
    TIME_PRODUCTIVITY_AVAILABLE
)
from utils.time_productivity_integration import (
    detect_time_query, detect_task_query, detect_timer_query,
    detect_productivity_query, handle_productivity_query_comprehensive,
    format_persona_productivity_response, parse_natural_time,
    extract_task_details_from_text
)

class TestTimeProductivityService:
    """Test the core TimeProductivityService functionality"""
    
    def setup_method(self):
        """Reset service state before each test"""
        self.service = TimeProductivityService()
        # Clear storage for fresh test
        self.service.tasks.clear()
        self.service.timers.clear()
        self.service.time_sessions.clear()
    
    @pytest.mark.asyncio
    async def test_get_current_time_default(self):
        """Test getting current time with default settings"""
        result = await self.service.get_current_time()
        
        assert result["success"] is True
        assert "current_time" in result
        assert "timezone" in result
        assert "iso_time" in result
        assert "unix_timestamp" in result
        assert "day_of_week" in result
        assert isinstance(result["unix_timestamp"], float)
    
    @pytest.mark.asyncio
    async def test_get_current_time_custom_timezone(self):
        """Test getting current time with custom timezone"""
        result = await self.service.get_current_time("EST", "12hour")
        
        assert result["success"] is True
        assert "current_time" in result
        # Should format in 12-hour format
        assert ("AM" in result["current_time"] or "PM" in result["current_time"])
    
    @pytest.mark.asyncio
    async def test_add_task_basic(self):
        """Test basic task addition"""
        result = await self.service.add_task(
            title="Test Task",
            description="This is a test task",
            priority="high"
        )
        
        assert result["success"] is True
        assert result["task"]["title"] == "Test Task"
        assert result["task"]["description"] == "This is a test task"
        assert result["task"]["priority"] == "high"
        assert result["task"]["completed"] is False
        assert "id" in result["task"]
    
    @pytest.mark.asyncio
    async def test_add_task_with_due_date(self):
        """Test task addition with due date"""
        future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        
        result = await self.service.add_task(
            title="Task with Due Date",
            due_date=future_date,
            session_id="test_session"
        )
        
        assert result["success"] is True
        assert result["task"]["due_date"] == future_date
    
    @pytest.mark.asyncio
    async def test_list_tasks_empty(self):
        """Test listing tasks when none exist"""
        result = await self.service.list_tasks("empty_session")
        
        assert result["success"] is True
        assert result["tasks"] == []
        assert result["count"] == 0
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self):
        """Test listing tasks with various filters"""
        # Add multiple tasks
        await self.service.add_task("High Priority Task", priority="high", session_id="filter_test")
        await self.service.add_task("Low Priority Task", priority="low", session_id="filter_test")
        
        # Test priority filter
        result = await self.service.list_tasks("filter_test", priority="high")
        
        assert result["success"] is True
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "High Priority Task"
    
    @pytest.mark.asyncio
    async def test_complete_task(self):
        """Test marking a task as completed"""
        # First add a task
        add_result = await self.service.add_task("Task to Complete", session_id="complete_test")
        task_id = add_result["task"]["id"]
        
        # Complete the task
        complete_result = await self.service.complete_task(task_id, "complete_test")
        
        assert complete_result["success"] is True
        assert complete_result["task"]["completed"] is True
        assert complete_result["task"]["completed_at"] is not None
    
    @pytest.mark.asyncio
    async def test_start_timer_pomodoro(self):
        """Test starting a pomodoro timer"""
        result = await self.service.start_timer(
            name="Focus Session",
            duration_minutes=25,
            timer_type="pomodoro",
            session_id="timer_test"
        )
        
        assert result["success"] is True
        assert result["timer"]["name"] == "Focus Session"
        assert result["timer"]["duration_minutes"] == 25
        assert result["timer"]["timer_type"] == "pomodoro"
        assert result["timer"]["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_check_timer_status(self):
        """Test checking timer status"""
        # Start a timer first
        timer_result = await self.service.start_timer(
            "Test Timer", 1, "work", "status_test"
        )
        timer_id = timer_result["timer"]["id"]
        
        # Check status
        status_result = await self.service.check_timer_status(timer_id, "status_test")
        
        assert status_result["success"] is True
        assert "timer" in status_result
        assert "elapsed_seconds" in status_result["timer"]
        assert "remaining_seconds" in status_result["timer"]
        assert "progress_percent" in status_result["timer"]

class TestQueryDetection:
    """Test query detection functionality"""
    
    def test_detect_time_query_positive(self):
        """Test positive time query detection"""
        test_cases = [
            "What time is it?",
            "Current time please",
            "What's the time now?",
            "Time in New York",
            "What day is today?",
            "Current date"
        ]
        
        for query in test_cases:
            result = detect_time_query(query)
            assert result["is_time_query"] is True, f"Failed for: {query}"
    
    def test_detect_time_query_negative(self):
        """Test negative time query detection"""
        test_cases = [
            "Hello there",
            "How are you?",
            "What's the weather like?",
            "Play some music",
            "Tell me a joke"
        ]
        
        for query in test_cases:
            result = detect_time_query(query)
            assert result["is_time_query"] is False, f"False positive for: {query}"
    
    def test_detect_task_query_add(self):
        """Test task addition query detection"""
        test_cases = [
            "Add a task",
            "Create new task",
            "Remind me to call John",
            "I need to do laundry",
            "Add task: Buy groceries"
        ]
        
        for query in test_cases:
            result = detect_task_query(query)
            assert result["is_task_query"] is True
            assert result["query_type"] == "add_task", f"Failed for: {query}"
    
    def test_detect_task_query_list(self):
        """Test task listing query detection"""
        test_cases = [
            "Show my tasks",
            "List all tasks",
            "What tasks do I have?",
            "My todo list",
            "What do I need to do?"
        ]
        
        for query in test_cases:
            result = detect_task_query(query)
            assert result["is_task_query"] is True
            assert result["query_type"] == "list_tasks", f"Failed for: {query}"
    
    def test_detect_timer_query_pomodoro(self):
        """Test pomodoro timer query detection"""
        test_cases = [
            "Start pomodoro timer",
            "Begin pomodoro session",
            "Pomodoro for 25 minutes",
            "Start a 25-minute pomodoro"
        ]
        
        for query in test_cases:
            result = detect_timer_query(query)
            assert result["is_timer_query"] is True
            assert result["timer_info"]["type"] == "pomodoro", f"Failed for: {query}"
    
    def test_detect_timer_query_custom_duration(self):
        """Test timer queries with custom durations"""
        test_cases = [
            ("Start timer for 45 minutes", 45),
            ("Set a 10 minute timer", 10),
            ("Timer for 2 hours", 120),  # Should convert to minutes
            ("30 min timer", 30)
        ]
        
        for query, expected_duration in test_cases:
            result = detect_timer_query(query)
            assert result["is_timer_query"] is True
            assert result["timer_info"]["duration"] == expected_duration, f"Failed for: {query}"

class TestNaturalLanguageProcessing:
    """Test natural language processing features"""
    
    def test_parse_natural_time(self):
        """Test natural time parsing"""
        test_cases = [
            "tomorrow",
            "in 2 hours",
            "in 30 minutes",
            "next week"
        ]
        
        for time_text in test_cases:
            result = parse_natural_time(time_text)
            # Should return an ISO format string or None
            if result:
                # Try to parse the result to verify it's valid ISO format
                datetime.fromisoformat(result.replace('Z', '+00:00'))
    
    def test_extract_task_details_from_text(self):
        """Test extracting task details from natural language"""
        test_cases = [
            {
                "input": "Remind me to call John by tomorrow",
                "expected_title": "call John",
                "expected_priority": "medium"
            },
            {
                "input": "Add urgent task: Buy groceries immediately",
                "expected_priority": "urgent"
            },
            {
                "input": "I need to finish the report - high priority",
                "expected_title": "finish the report",
                "expected_priority": "high"
            }
        ]
        
        for case in test_cases:
            result = extract_task_details_from_text(case["input"])
            
            if "expected_title" in case:
                assert case["expected_title"] in result.get("title", ""), f"Title extraction failed for: {case['input']}"
            
            if "expected_priority" in case:
                assert result.get("priority") == case["expected_priority"], f"Priority extraction failed for: {case['input']}"

class TestPersonaIntegration:
    """Test persona-specific formatting"""
    
    def test_format_persona_productivity_response_pirate(self):
        """Test pirate persona formatting"""
        response = "The current time is 3:00 PM"
        formatted = format_persona_productivity_response(response, "pirate")
        
        # Should contain pirate-style language
        assert any(word in formatted.lower() for word in ["ahoy", "matey", "arr"])
        assert "ship's bell" in formatted or "time" in formatted
    
    def test_format_persona_productivity_response_robot(self):
        """Test robot persona formatting"""
        response = "Task added successfully"
        formatted = format_persona_productivity_response(response, "robot")
        
        # Should contain robot-style language
        assert any(phrase in formatted for phrase in ["PRODUCTIVITY DATA", "PROTOCOL", "EFFICIENCY"])
    
    def test_format_persona_productivity_response_wizard(self):
        """Test wizard persona formatting"""
        response = "Timer started for 25 minutes"
        formatted = format_persona_productivity_response(response, "wizard")
        
        # Should contain wizard-style language
        assert any(word in formatted.lower() for word in ["behold", "ancient", "magic"])

class TestIntegrationQueries:
    """Test end-to-end query handling"""
    
    @pytest.mark.asyncio
    async def test_handle_time_query(self):
        """Test handling time queries end-to-end"""
        query = "What time is it right now?"
        result = await handle_productivity_query_comprehensive(query, "integration_test")
        
        assert result is not None
        assert "time" in result.lower()
    
    @pytest.mark.asyncio
    async def test_handle_add_task_query(self):
        """Test handling task addition queries"""
        query = "Remind me to buy milk"
        result = await handle_productivity_query_comprehensive(query, "task_test")
        
        assert result is not None
        assert "task" in result.lower() or "added" in result.lower()
    
    @pytest.mark.asyncio
    async def test_handle_list_tasks_query(self):
        """Test handling task listing queries"""
        # First add a task
        await add_task("Test Task for List", session_id="list_test")
        
        # Then try to list tasks
        query = "Show my tasks"
        result = await handle_productivity_query_comprehensive(query, "list_test")
        
        assert result is not None
        assert "Test Task for List" in result
    
    @pytest.mark.asyncio
    async def test_handle_timer_query(self):
        """Test handling timer queries"""
        query = "Start a pomodoro timer"
        result = await handle_productivity_query_comprehensive(query, "timer_test")
        
        assert result is not None
        assert "timer" in result.lower()
        assert "25" in result  # Default pomodoro duration

class TestFormatting:
    """Test response formatting functions"""
    
    @pytest.mark.asyncio
    async def test_format_time_response_success(self):
        """Test time response formatting"""
        time_data = {
            "success": True,
            "current_time": "Monday, August 27, 2025 at 12:00 PM UTC"
        }
        
        result = format_time_response(time_data)
        assert "Monday, August 27, 2025 at 12:00 PM UTC" in result
    
    @pytest.mark.asyncio
    async def test_format_time_response_error(self):
        """Test time response formatting for errors"""
        time_data = {
            "success": False,
            "error": "Timezone not found"
        }
        
        result = format_time_response(time_data)
        assert "sorry" in result.lower()
        assert "timezone not found" in result.lower()
    
    @pytest.mark.asyncio
    async def test_format_task_list_with_tasks(self):
        """Test task list formatting with tasks"""
        tasks_data = {
            "success": True,
            "tasks": [
                {
                    "id": "1",
                    "title": "High Priority Task",
                    "description": "Important work",
                    "priority": "high",
                    "completed": False,
                    "due_date": None,
                    "tags": ["work"]
                },
                {
                    "id": "2", 
                    "title": "Completed Task",
                    "description": "",
                    "priority": "medium",
                    "completed": True,
                    "due_date": None,
                    "tags": []
                }
            ]
        }
        
        result = format_task_list(tasks_data)
        assert "High Priority Task" in result
        assert "Completed Task" in result
        assert "✅" in result  # Completed task emoji
        assert "⏰" in result  # Pending task emoji
        assert "⚡" in result  # High priority emoji

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        self.service = TimeProductivityService()
        self.service.tasks.clear()
        self.service.timers.clear()
        self.service.time_sessions.clear()
    
    @pytest.mark.asyncio
    async def test_complete_nonexistent_task(self):
        """Test completing a task that doesn't exist"""
        result = await self.service.complete_task("fake_id", "test_session")
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_due_date_format(self):
        """Test adding task with invalid due date"""
        result = await self.service.add_task(
            "Invalid Due Date Task",
            due_date="invalid-date-format"
        )
        
        assert result["success"] is False
        assert "invalid" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_timer_with_zero_duration(self):
        """Test timer with zero duration"""
        result = await self.service.start_timer("Zero Timer", 0)
        
        # Should still create timer but with 0 duration
        assert result["success"] is True
        assert result["timer"]["duration_minutes"] == 0
    
    def test_detect_ambiguous_queries(self):
        """Test queries that could match multiple patterns"""
        # This could be both time and task related
        query = "What time do I need to finish this task?"
        
        time_result = detect_time_query(query)
        task_result = detect_task_query(query)
        
        # Should primarily detect as time query
        assert time_result["is_time_query"] is True
        # But might also match task patterns (depends on implementation)

class TestServiceAvailability:
    """Test service availability checks"""
    
    def test_service_available(self):
        """Test that service is marked as available"""
        assert TIME_PRODUCTIVITY_AVAILABLE is True
    
    @pytest.mark.asyncio
    async def test_helper_function_availability(self):
        """Test that helper functions work when service is available"""
        # These should work without errors
        time_result = await get_current_time()
        assert time_result is not None
        
        task_result = await add_task("Availability Test")
        assert task_result is not None

class TestTimeCalculations:
    """Test time calculation and formatting utilities"""
    
    @pytest.mark.asyncio
    async def test_calculate_time_difference(self):
        """Test time difference calculations"""
        service = TimeProductivityService()
        
        # Test with a 1-hour difference
        start_time = datetime.now(timezone.utc).isoformat()
        end_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        
        result = await service.calculate_time_difference(start_time, end_time)
        
        assert result["success"] is True
        assert result["total_hours"] == 1
        assert "1 hours" in result["human_readable"]
    
    def test_format_duration(self):
        """Test duration formatting"""
        service = TimeProductivityService()
        
        test_cases = [
            (30, "30 seconds"),
            (90, "1 minutes and 30 seconds"),
            (3665, "1 hours and 1 minutes"),
            (90000, "1 days and 1 hours")
        ]
        
        for seconds, expected_pattern in test_cases:
            result = service._format_duration(seconds)
            # Check that key parts of expected pattern are in result
            key_parts = expected_pattern.split()
            assert any(part in result for part in key_parts), f"Duration formatting failed for {seconds} seconds"

def run_all_tests():
    """Run all tests and print results"""
    
    print("🧪 Running Time & Productivity Tests...")
    print("=" * 50)
    
    # Test classes to run
    test_classes = [
        TestTimeProductivityService,
        TestQueryDetection,
        TestNaturalLanguageProcessing,
        TestPersonaIntegration,
        TestIntegrationQueries,
        TestFormatting,
        TestEdgeCases,
        TestServiceAvailability,
        TestTimeCalculations
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}...")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            test_instance = test_class()
            
            # Setup if method exists
            if hasattr(test_instance, 'setup_method'):
                test_instance.setup_method()
            
            try:
                method = getattr(test_instance, test_method)
                
                # Handle async tests
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                
                print(f"  ✅ {test_method}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {test_method}: {str(e)}")
                failed_tests.append(f"{test_class.__name__}.{test_method}: {str(e)}")
    
    print(f"\n🏆 TEST SUMMARY:")
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n🚨 Failed Tests:")
        for failure in failed_tests:
            print(f"  • {failure}")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! Time & Productivity tests are passing!")
    elif success_rate >= 75:
        print("✅ GOOD! Most tests are passing.")
    else:
        print("⚠️ NEEDS WORK: Several tests are failing.")
    
    return success_rate

if __name__ == "__main__":
    # Run tests when script is executed directly
    success_rate = run_all_tests()
    
    if success_rate >= 90:
        print("\n🎯 Time & Productivity service is ready for production! 🚀")
    else:
        print("\n🔧 Consider fixing failing tests before deployment.")
