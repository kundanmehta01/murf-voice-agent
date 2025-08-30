# 🎙️ Voice Wave - Advanced AI Assistant

A comprehensive voice-first AI assistant built with FastAPI that provides natural conversations with intelligent features. Talk to your AI assistant and hear personalized responses with multiple character personas, weather information, productivity tools, and much more!

The app features advanced voice streaming, real-time transcription, smart query detection, and a modern responsive UI. It's designed to be resilient with graceful fallbacks when external services are unavailable.

## ✨ Core Features

### 🎤 **Advanced Voice Interaction**
- **Real-time voice streaming** with WebSocket support
- **Instant transcription** using AssemblyAI streaming API
- **High-quality TTS** with Murf voices and streaming audio
- **Voice recording** in browser with automatic processing
- **Multiple audio formats** supported (PCM, WAV)

### 🎭 **Character Personas System**
- **9 Unique Personas**: Default Assistant, Pirate Captain, Cowboy Sheriff, Robot, Wizard, Scientist, Chef, Detective, and Surfer
- **Personalized voices** and speaking styles for each character
- **Session-based persona switching** with persistent memory
- **Character-specific responses** that adapt to context
- **Personality-driven interactions** for weather, productivity, and general queries

### 🌤️ **Smart Weather Integration**
- **Current weather conditions** for any location worldwide
- **Multi-day forecasts** with detailed information
- **Intelligent location detection** from natural language
- **Weather query parsing** ("What's the weather in London?")
- **Persona-themed weather reports** (pirates speak of "seas", cowboys of "riding weather")
- **Location search** with autocomplete suggestions

### ⏰ **Productivity & Time Management**
- **Smart time queries** with timezone support
- **Task management** (add, list, complete tasks with priorities)
- **Pomodoro timers** and productivity sessions
- **Time tracking** for work activities
- **Natural language parsing** ("Remind me to call mom at 3pm")
- **Multiple time zones** and formats supported

### 💬 **Intelligent Conversation**
- **Context-aware responses** using Google Gemini LLM
- **Session-based chat history** with persistence
- **Smart query detection** for weather, time, and productivity
- **Streaming responses** for natural conversation flow
- **Multi-turn conversations** with memory

### 🎨 **Modern User Interface**
- **Responsive design** works on desktop and mobile
- **Real-time audio visualization** during recording
- **Live transcription display** as you speak
- **Persona selector** with character previews
- **Chat history panel** with timestamps
- **Voice controls** and settings management


## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI, Starlette, Uvicorn
- **Data Models**: Pydantic v2, Python dataclasses
- **WebSockets**: Real-time audio streaming and communication
- **Environment**: python-dotenv for configuration
- **Logging**: Comprehensive error handling and debugging

### External Services
- **Speech-to-Text**: AssemblyAI with real-time streaming API
- **Large Language Model**: Google Generative AI (Gemini 1.5)
- **Text-to-Speech**: Murf AI with premium voices
- **Weather Data**: OpenWeatherMap API with geocoding
- **Time Management**: Built-in productivity services

### Frontend
- **UI Framework**: Pure HTML5, CSS3, and Vanilla JavaScript
- **Audio Processing**: Web Audio API, MediaRecorder API
- **Real-time Communication**: WebSocket client
- **Responsive Design**: Modern CSS Grid and Flexbox
- **No Build Tools**: Ready to run out of the box


## 📂 Project Structure

```
.
├─ main.py                           # FastAPI application with all endpoints
├─ personas.py                       # Character persona definitions and system
├─ schemas.py                        # Pydantic models for API requests/responses
├─ config.py                         # Environment configuration and API keys
├─ services/                         # Core service modules
│  ├─ stt.py                         # Speech-to-text (AssemblyAI integration)
│  ├─ tts.py                         # Text-to-speech (Murf integration)
│  ├─ llm.py                         # Large Language Model (Gemini integration)
│  ├─ weather.py                     # Weather service (OpenWeatherMap)
│  ├─ time_productivity.py           # Time management and productivity tools
│  └─ murf_ws.py                     # Murf WebSocket streaming client
├─ utils/                            # Utility modules
│  ├─ logger.py                      # Logging configuration
│  ├─ text.py                        # Text processing and chunking
│  ├─ weather_integration.py         # Weather query detection and formatting
│  ├─ time_productivity_integration.py # Productivity query parsing
│  └─ user_api_keys.py              # User API key management
├─ templates/                        # HTML templates
│  ├─ index.html                     # Main responsive UI
│  ├─ index_modern.html             # Modern UI variant
│  └─ index_backup.html             # Backup UI version
├─ static/                           # Static assets
│  ├─ style.css                      # Main responsive styles
│  └─ style_modern.css              # Modern UI styles
├─ uploads/                          # Runtime audio file uploads
└─ images/                           # Documentation screenshots
```

## 🔄 How It Works

### Voice Interaction Flow
1. **Audio Capture**: Browser records audio using MediaRecorder API
2. **Real-time Streaming**: WebSocket sends PCM audio chunks to server
3. **Live Transcription**: AssemblyAI streaming API provides real-time transcripts
4. **Query Analysis**: Smart detection identifies weather, productivity, or general queries
5. **Context Building**: System builds persona-aware prompts with chat history
6. **LLM Processing**: Gemini generates contextual responses with streaming
7. **Audio Generation**: Murf TTS creates high-quality spoken responses
8. **Response Delivery**: Client receives and plays audio with visual feedback

### Smart Query Processing
- **Weather Queries**: "What's the weather in Tokyo?" → Real-time weather data
- **Time Management**: "Add a meeting at 3pm" → Task creation with scheduling
- **General Chat**: Natural conversation with persona-appropriate responses
- **Persona Switching**: "Be a pirate" → Character personality and voice changes

### Session Management
- **Session-based History**: Each conversation maintains context and memory
- **Persona Persistence**: Character selection persists across conversation turns
- **No Database Required**: All data stored in-memory for demo purposes
- **Graceful Fallbacks**: Service failures don't break the user experience



## 🔑 Environment Variables

Create a `.env` file in the project root with the following API keys. The app gracefully handles missing keys by disabling specific features while maintaining core functionality.

### Required API Keys
```env
# Speech Recognition (Required for voice input)
ASSEMBLYAI_API_KEY=your_assemblyai_key_here

# Text-to-Speech (Required for voice output)
MURF_API_KEY=your_murf_api_key_here

# Large Language Model (Required for AI responses)
GEMINI_API_KEY=your_gemini_api_key_here

# Weather Service (Optional - enables weather features)
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Optional Configuration
DEFAULT_PERSONA_ID=default
PORT=8000
```

### Getting API Keys
- **AssemblyAI**: Sign up at [assemblyai.com](https://assemblyai.com) for speech recognition
- **Murf AI**: Get API access at [murf.ai](https://murf.ai) for premium TTS voices
- **Google Gemini**: Create API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenWeatherMap**: Free tier available at [openweathermap.org](https://openweathermap.org/api)

### Service Fallbacks
- **Missing STT**: Voice input disabled, text input still works
- **Missing TTS**: Text responses only, no voice output
- **Missing LLM**: Fallback responses, limited conversation
- **Missing Weather**: Weather queries return apologetic messages


# 🚀 Running Locally (Windows PowerShell)
Prerequisites: Python 3.10+ recommended.

1) Create and activate a virtual environment
```
python -m venv .venv
. .venv\Scripts\Activate.ps1
```

2) Install dependencies
```
pip install fastapi uvicorn[standard] python-dotenv jinja2 assemblyai murf google-generativeai pytz requests httpx websockets
```

**Alternative: Install from requirements.txt (if available)**
```
pip install -r requirements.txt
```

3) Create a .env with your API keys (see above)

4) Start the API server
```
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

5) Open the UI
- Navigate to http://127.0.0.1:8000
- Click “Start Talking”, speak, then click again to stop and send
- Toggle auto-stream if you want continuous turns

Note: On first use, your browser will ask for microphone permission.


## 🌐 API Reference

### Core Endpoints
- **GET** `/` → Main application UI
- **POST** `/agent/chat/{session_id}` → Main conversation endpoint with full AI processing
- **GET** `/agent/history/{session_id}` → Retrieve chat history for session
- **DELETE** `/agent/history/{session_id}` → Clear chat history
- **WebSocket** `/ws/audio` → Real-time audio streaming and transcription

### Persona Management
- **GET** `/personas` → List all available character personas
- **GET** `/agent/persona/{session_id}` → Get current session persona
- **POST** `/agent/persona/{session_id}` → Set persona for session

### Weather Services
- **GET** `/weather/status` → Check weather service availability
- **GET** `/weather/current/{location}` → Current weather conditions
- **GET** `/weather/forecast/{location}` → Multi-day weather forecast
- **GET** `/weather/search?query={query}` → Location search and suggestions

### Time & Productivity
- **GET** `/time/status` → Check time service availability
- **GET** `/time/current` → Get current time with timezone support
- **POST** `/tasks/{session_id}` → Add new task/reminder
- **GET** `/tasks/{session_id}` → List tasks for session
- **PATCH** `/tasks/{session_id}/{task_id}/complete` → Mark task as completed
- **POST** `/timers/{session_id}` → Start productivity timer (Pomodoro, etc.)
- **GET** `/timers/{session_id}` → Check timer status

### Audio Processing
- **POST** `/generate-tts` → Generate speech from text
- **POST** `/upload-audio` → Upload audio file
- **POST** `/transcribe/file` → Transcribe uploaded audio
- **GET** `/voices` → List available TTS voices
- **POST** `/tts/echo` → Simple transcription echo test
- **POST** `/llm/query` → Direct LLM query with optional TTS

### API Key Management & Testing
- **POST** `/config/api-keys` → Save user-provided API keys
- **GET** `/config/api-keys/status` → Check API key status
- **DELETE** `/config/api-keys` → Clear user API keys
- **POST** `/test/{service}` → Test individual API keys (assemblyai, murf, gemini, openweather)

### Debug & Diagnostics
- **GET** `/debug/environment` → System and environment information
- **GET** `/debug/assemblyai-test` → Detailed AssemblyAI connection test
- **WebSocket** `/ws` → Simple WebSocket echo test

**Note**: All endpoints include graceful error handling and fallbacks when external services are unavailable.


##  UI Features



### Key UI Features
- **🎤 Voice Recording**: Large, accessible record button with visual feedback
- **👥 Persona Selector**: Easy switching between 9 unique AI characters
- **💬 Live Chat**: Real-time conversation display with timestamps
- **🌊 Audio Visualization**: Waveform display during recording
- **📱 Mobile Responsive**: Full functionality on all device sizes
- **🎨 Modern Design**: Clean, intuitive interface with smooth animations
- **⚡ Real-time Updates**: Live transcription and streaming responses


## 🔧 Advanced Features

### WebSocket Audio Streaming
- **Real-time Processing**: Audio is processed as you speak, not after recording
- **Low Latency**: Minimal delay between speech and transcription
- **Streaming Responses**: AI responses begin playing while still being generated
- **Session Persistence**: WebSocket maintains session context across interactions

### Intelligent Query Detection
- **Natural Language Understanding**: Automatically detects weather, time, and productivity queries
- **Context Preservation**: Maintains conversation flow while handling special requests
- **Multi-modal Responses**: Combines real-time data with conversational AI

### Persona System Deep Dive
- **Voice Matching**: Each persona uses appropriate voice characteristics
- **Response Styling**: Personalities affect how information is presented
- **Contextual Adaptation**: Weather reports, time announcements, and productivity guidance adapt to character
- **Session Memory**: Persona choice persists throughout conversation

### API Key Management
- **Runtime Configuration**: Add API keys without restarting the server
- **Service Testing**: Built-in endpoints to validate API key functionality
- **Graceful Degradation**: Missing services don't break core functionality
- **User-specific Keys**: Support for session-based API key management

## 🛠 Troubleshooting

### Common Issues
- **Microphone blocked**: Re-enable permissions in browser settings (chrome://settings/content/microphone)
- **No audio response**: Check Murf API key and TTS service status
- **Transcription not working**: Verify AssemblyAI API key in environment
- **Weather queries failing**: Ensure OpenWeatherMap API key is configured
- **CORS issues**: Use `http://127.0.0.1:8000` instead of `localhost:8000`

### Debug Endpoints
- Visit `/debug/environment` to check system status and API key configuration
- Use `/debug/assemblyai-test` for detailed speech recognition diagnostics
- Test individual services with `/test/{service_name}` endpoints

### Performance Optimization
- **WebSocket Connection**: Use `/ws/audio` for lowest latency voice interaction
- **Audio Quality**: 16kHz, 16-bit PCM provides best balance of quality and performance
- **Chunked Responses**: Long AI responses are automatically split for better streaming




---

## 🎯 Use Cases

- **Personal Assistant**: Voice-controlled scheduling, reminders, and information lookup
- **Weather Companion**: Get detailed weather information in your preferred character style
- **Productivity Coach**: Pomodoro timers, task management, and time tracking with personality
- **Educational Tool**: Learn through interactive conversations with different character perspectives
- **Entertainment**: Enjoy conversations with unique AI personalities from pirates to wizards
- **Accessibility**: Voice-first interface for hands-free computer interaction
- **Development Platform**: Extensible foundation for building advanced voice AI applications

## 🚀 Recent Updates 

- ✅ **Complete Persona System**: 9 unique characters with distinct personalities and voices
- ✅ **Advanced Weather Integration**: Real-time weather data with intelligent query detection
- ✅ **Productivity Suite**: Task management, timers, and time tracking with natural language
- ✅ **WebSocket Streaming**: Real-time audio processing and response streaming
- ✅ **Responsive UI**: Modern, mobile-friendly interface with audio visualization
- ✅ **API Key Management**: Runtime configuration and service testing capabilities
- ✅ **Smart Query Detection**: Automatic parsing of weather, time, and productivity requests
- ✅ **Enhanced Error Handling**: Comprehensive fallbacks and diagnostic endpoints
- ✅ **Session Persistence**: Maintain context, personas, and history across interactions
- ✅ **Multi-service Integration**: Seamless coordination between STT, LLM, TTS, and data services

## 💝 Credits & Acknowledgments

Built with love using:
- **[AssemblyAI](https://assemblyai.com)** for world-class speech recognition
- **[Murf AI](https://murf.ai)** for premium text-to-speech voices
- **[Google Gemini](https://deepmind.google/technologies/gemini/)** for advanced language understanding
- **[OpenWeatherMap](https://openweathermap.org)** for comprehensive weather data
- **[FastAPI](https://fastapi.tiangolo.com)** for the robust backend framework

Special thanks to the Murf-AI ,open-source community and the amazing APIs that make this project possible!

---

**🌟 Star this repo if you found it helpful! Contributions and feedback welcome.**
