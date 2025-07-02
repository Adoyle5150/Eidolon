# Eidolon - Personal AI Assistant

⚡ **Local, Private, Powerful Desktop AI**

Eidolon is a sophisticated, locally-run AI assistant that combines advanced capabilities into a single, integrated desktop application. Built with **PyQt6** and **QML** for a modern interface, it runs **entirely on your machine with no cloud dependencies**, ensuring privacy and full local control.

---

## ✨ Core Features

✅ **Local AI Processing**

* **Local LLM Integration:** Runs DeepSeek-R1-Distill-Llama-8B via llama.cpp
* **No Cloud Dependencies:** Full privacy with all processing on your device
* **Customizable Identity:** Configurable assistant personality and behavior
* **Real-time Chat Interface:** Modern QML GUI with animated typing effects

✅ **Advanced Memory System**

* **Vector Memory (FAISS):** Semantic search with sentence transformers
* **Core Memory:** Persistent identity and behavior rules (JSON)
* **Chat History:** Auto-saving with searchable retrieval
* **Vision Memory:** Screen activity context tracking and recall

✅ **Intelligent Web Search**

* **Multi-Engine Search:** DuckDuckGo & Bing fallback
* **Content Extraction:** Readability parsing for clean data
* **Smart Summarization:** AI-powered content relevance scoring
* **Caching:** Optimized performance with intelligent caching
* **Progress Tracking:** Real-time search status in the UI

✅ **Computer Vision System**

* **Screen Capture:** Auto screenshots at intervals
* **OCR Integration:** Tesseract-based screen text extraction
* **Context Analysis:** Active application/window interpretation
* **Smart Responses:** Context-based suggestions
* **Vision Memory:** Persistent pattern recognition

✅ **Local Automation Commands**

* **System Control:** Mouse/keyboard automation
* **Text-to-Speech:** Voice output using pyttsx3
* **Web Browser Control:** URL opening and navigation
* **File System Access:** Listing and file operations
* **System Info:** Time, date, IP retrieval

✅ **Modern User Interface**

* **Frameless Design:** Clean, adaptive UI
* **Sidebar Navigation:** Collapsible chat history panel
* **Code Highlighting:** Syntax highlighting in replies
* **Clipboard Integration:** One-click response copying
* **Responsive Layout:** Adapts to various screen sizes

---

## 🔧 Technical Architecture

**Backend:**

* PyQt6/QML bridge for seamless Python-QML communication
* Threaded processing for non-blocking UI
* Real-time assistant state tracking (ready/thinking/typing)
* Robust error handling and graceful fallback

**Data Management:**

* All data stored in a dedicated `data/` folder
* Human-readable JSON configuration and memory storage
* Automatic backups for chat history and memory
* Git-friendly structure for clean version control

**Performance:**

* GPU acceleration via CUDA for LLM inference
* FAISS-based memory optimization
* Caching layers for web and search data
* Background processing for smooth user experience

---

## 🎯 Use Cases

✅ **Development & Coding**: Code review, debugging, language explanation, structure analysis, real-time error checks

✅ **Research & Information**: Live web search with summarization, current events, academic research, multi-source synthesis

✅ **Productivity & Automation**: Screen monitoring, context suggestions, workflow optimization, automated tasks

✅ **Personal Assistant**: Natural conversations, local file/system management, voice interactions, personalized behavior

---

## 🛠️ System Requirements

* OS: Windows 10/11 (Linux/macOS planned)
* RAM: 8GB minimum (16GB recommended)
* Storage: 10GB for models/data
* GPU: Optional CUDA support for faster inference
* Dependencies: Python 3.8+, PyQt6, llama.cpp, Tesseract OCR

---

## 🔮 Future Roadmap

* Tier 4-5 advanced features
* Vision-language models for advanced screen understanding
* UI layout recognition with Donut/LayoutLM
* Screen interaction and action automation
* Predictive learning loops for advanced assistance

---

## 📸 Screenshots

*(Add clean screenshots or GIFs of the Eidolon interface in action here)*

---

## 📥 Installation

```bash
git clone https://github.com/YourUser/Eidolon.git
cd Eidolon
pip install -r requirements.txt
python main.py
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork and submit pull requests.

---

## 📜 License

MIT License

---

This README provides a **clean, professional structure** for your GitHub repo, making it clear, skimmable, and ready for presentation.
