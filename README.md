# MiniMe AI – Intelligent Desktop Companion

MiniMe AI is a premium animated desktop companion designed for productivity, habit tracking, and personalized coaching. Combining elements of classic desktop assistants, Tamagotchis, and AI productivity coaches, it floatingly resides in the corner of your screen, reacting dynamically to your workflow.

---

## Technical Stack
- **Core Engine**: Python 3
- **GUI Framework**: PySide6 (Qt for Python)
- **Database Persistence**: SQLite
- **Audio Processing**: Pyttsx3 (TTS) and SpeechRecognition (STT)

## Architectural Design
MiniMe AI follows a clean **MVC (Model-View-Controller) / MVVM** architectural separation:
- **Models**: Handles schema definitions and data encapsulation.
- **Views**: Formats and draws the layout, handles animations (`QPropertyAnimation`), mouse drag events, and rendering.
- **Controllers/Core**: Houses reminders, AI dialogue generation, and emotion mapping engines.
- **Services**: Manages external communication like asynchronous AI queries, thread-isolated speech processing, and system notifications.

---

## Installation & Setup

1. **Clone & Navigate**:
   ```bash
   git clone https://github.com/yourusername/minime-ai.git
   cd minime-ai
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_key_here
   ```

4. **Launch Application**:
   ```bash
   python main.py
   ```
