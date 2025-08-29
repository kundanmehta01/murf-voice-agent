# 🎭 AI Persona System - Day 24 Feature

## Overview

The AI Voice Agent now supports multiple personas! Each persona has a distinct personality, speaking style, and voice, making conversations more engaging and character-driven.

## Available Personas

| Persona | Emoji | Description | Voice | Personality Traits |
|---------|--------|-------------|-------|--------------------|
| **Default Assistant** | 🤖 | A helpful and professional AI assistant | Natalie (US) | helpful, professional, concise |
| **Captain Blackbeard** | 🏴‍☠️ | A swashbuckling pirate captain | Ryan (US) | adventurous, bold, treasure-hunting, nautical |
| **Sheriff Sam** | 🤠 | A wise old cowboy sheriff from the Wild West | Ryan (US) | wise, calm, experienced, frontier-minded |
| **ALEX-9000** | 🤖 | A logical and efficient AI robot from the future | Ryan (US) | logical, precise, efficient, technical |
| **Merlin the Wise** | 🧙‍♂️ | An ancient and mystical wizard with vast knowledge | Natalie (US) | wise, mystical, patient, insightful |
| **Dr. Elena Bright** | 🔬 | An enthusiastic scientist who loves discovery | Natalie (US) | curious, methodical, enthusiastic, educational |
| **Chef Giuseppe** | 👨‍🍳 | A passionate Italian chef who loves cooking | Natalie (US) | passionate, warm, expressive, culinary-focused |
| **Inspector Holmes** | 🕵️ | A sharp-minded detective who solves mysteries | Ryan (US) | analytical, observant, methodical, mysterious |
| **Kai the Wave Rider** | 🏄‍♂️ | A laid-back surfer dude who goes with the flow | Ryan (US) | laid-back, optimistic, friendly, beach-loving |

## How It Works

### Frontend Interface
- **Persona Selector**: Choose your preferred AI character from the dropdown menu
- **Current Persona Display**: Shows the active persona with emoji and name
- **Dynamic Updates**: Chat history updates to reflect the current persona

### Backend Integration
- **Session-based**: Each session can have its own persona
- **Voice Matching**: Each persona uses an appropriate voice (male/female)
- **System Prompts**: Unique prompts guide each persona's responses
- **API Endpoints**: Full REST API for persona management

## API Endpoints

### List Available Personas
```http
GET /personas
```
Response:
```json
{
  "personas": [
    {
      "id": "pirate",
      "name": "Captain Blackbeard",
      "description": "A swashbuckling pirate captain...",
      "emoji": "🏴‍☠️",
      "speaking_style": "Pirate accent with nautical terms",
      "personality_traits": ["adventurous", "bold", "treasure-hunting", "nautical"]
    }
  ]
}
```

### Get Session Persona
```http
GET /agent/persona/{session_id}
```
Response:
```json
{
  "session_id": "abc123",
  "persona_id": "pirate",
  "persona_name": "Captain Blackbeard",
  "persona_emoji": "🏴‍☠️",
  "persona_description": "A swashbuckling pirate captain..."
}
```

### Set Session Persona
```http
POST /agent/persona/{session_id}
Content-Type: multipart/form-data

persona_id=pirate
```
Response:
```json
{
  "session_id": "abc123",
  "persona_id": "pirate",
  "persona_name": "Captain Blackbeard",
  "persona_emoji": "🏴‍☠️",
  "message": "Persona changed to Captain Blackbeard 🏴‍☠️"
}
```

## Example Conversations

### 🏴‍☠️ Captain Blackbeard (Pirate)
**User**: "What should I do today?"
**Blackbeard**: "Arr, matey! Today be a fine day for adventure! Why not set sail and explore new waters? Maybe ye could learn somethin' new - knowledge be the greatest treasure, ye know! Or gather yer crew and plan yer next grand voyage. The seas be callin', and there's always treasure to be found! Arr!"

### 🤠 Sheriff Sam (Cowboy)
**User**: "What should I do today?"
**Sheriff**: "Well, partner, I reckon today's a mighty fine day to tackle whatever's been weighin' on your mind. Maybe take a ride out into the fresh air, do some honest work with your hands, or help a neighbor in need. That's what we do out here on the frontier - we take care of our own and make the most of each day the good Lord gives us."

### 🧙‍♂️ Merlin the Wise (Wizard)
**User**: "What should I do today?"
**Merlin**: "Ah, seeker of wisdom! The ancient runes speak of opportunity in this day. Perhaps 'tis time to delve into knowledge most profound - read a tome, learn a new skill, or contemplate the mysteries of existence. The path to enlightenment begins with a single step, and each day offers chances to grow in wisdom and understanding. What calls to thy spirit today?"

## Configuration

### Environment Variables
You can set a default persona using the environment variable:
```bash
DEFAULT_PERSONA_ID=pirate  # Sets Captain Blackbeard as default
```

### Adding Custom Personas
To add new personas, modify `personas.py`:

```python
"your_persona": Persona(
    id="your_persona",
    name="Your Character Name",
    description="Character description",
    system_prompt="You are [character description]...",
    voice_id="en-US-natalie",  # or "en-US-ryan"
    speaking_style="Your speaking style description",
    emoji="🎭",
    personality_traits=["trait1", "trait2", "trait3"]
)
```

## Technical Implementation

### Files Added/Modified
- `personas.py` - Core persona definitions and management
- `config.py` - Added persona configuration support
- `utils/text.py` - Enhanced prompt building with persona context
- `main.py` - Added persona API endpoints and integration
- `templates/index.html` - Added persona selection UI
- `static/style.css` - Added persona selector styling

### Session Management
- Each session maintains its own persona selection
- Personas persist throughout the session
- Switching personas updates the conversation context immediately
- Voice changes are applied to subsequent TTS generation

## Testing

Run the persona test suite:
```bash
python test_personas.py
```

The test verifies:
- ✅ Persona configuration loading
- ✅ Voice ID mapping
- ✅ System prompt generation
- ✅ Prompt building with persona context
- ✅ Session persona management

## Usage Tips

1. **Character Consistency**: Each persona maintains character throughout the conversation
2. **Voice Matching**: Personas automatically use appropriate voices
3. **Session Isolation**: Different browser sessions can use different personas
4. **Real-time Switching**: Change personas mid-conversation for varied responses
5. **Memory Persistence**: Chat history is maintained when switching personas

## Future Enhancements

Potential improvements for the persona system:
- Custom persona creation through the UI
- Persona-specific conversation starters
- Advanced personality customization
- Integration with different TTS providers for more voice options
- Persona-based conversation analytics

---

**Day 24 Complete**: Your AI voice agent now has personality! 🎭✨
