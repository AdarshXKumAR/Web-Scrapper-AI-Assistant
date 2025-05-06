# Web Scrape AI Assistant

A powerful web scraping and content analysis tool that leverages AI models to extract, summarize, and interact with web content. Built with Flask backend and a modern, responsive frontend designed with Tailwind CSS.

![Web Scraper Interface](https://github.com/AdarshXKumAR/Web-Scrapper-AI-Assistant/blob/main/demo1.png)

## Features

- **Dual AI Model Support**: Choose between Gemini and Groq LLMs for content processing
- **URL Scraping**: Direct scraping of any website URL with intelligent content extraction
- **Search Functionality**: Search for topics and automatically fetch relevant web content
- **AI-Powered Summaries**: Generate concise, well-structured summaries of web content
- **Interactive Chat**: Ask questions about the scraped content with AI-powered responses
- **Beautiful UI**: Modern, responsive design with Tailwind CSS and custom animations
- **Robust Error Handling**: Fallback mechanisms and comprehensive error management

![Chat Interface](https://github.com/AdarshXKumAR/Web-Scrapper-AI-Assistant/blob/main/demo2.png)

## Technical Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **AI Models**: 
  - Google's Gemini API
  - Groq's Mixtral model
- **Web Scraping**: BeautifulSoup4, Requests
- **Additional Tools**: dotenv for environment management

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- API keys for Google Gemini and Groq

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AdarshXKumAR/Web-Scrapper-AI-Assistant.git
   cd Web-Scrapper-AI-Assistant
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env.local` file in the root directory with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

### Running the Application

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Usage Guide

1. **Select AI Model**: Choose between Gemini or Groq using the toggle buttons
2. **URL Scraping**:
   - Enter a URL in the input field
   - Alternatively, enter a topic to search for
   - Click "Analyze Content"
3. **Search & Analyze**:
   - Click the "Search & Analyze" tab
   - Enter a search query
   - Click "Search & Analyze" button
4. **Chat with Content**:
   - After content is scraped and analyzed, use the chat interface
   - Ask questions about the content
   - Receive AI-powered responses

## Project Structure

```
web-scrape-ai-assistant/
├── app.py                 # Flask application and backend logic
├── templates/             # HTML templates
│   └── index.html         # Main application interface
├── .env.local             # Environment variables (not in repo)
├── requirements.txt       # Python dependencies
└── screenshots/           # Application screenshots
```

## API Features

- `/scrape` - Endpoint for scraping URLs and topics
- `/search` - Search for content and analyze it
- `/chat` - Ask questions about analyzed content
- `/check-models` - Check available AI models

## Limitations

- Web scraping may be blocked by some websites with anti-scraping measures
- Search functionality depends on public search engines and may be limited
- Large webpages may be truncated due to token limits of AI models

## Future Improvements

- Add support for additional AI models
- Implement content caching for faster responses
- Add PDF and document analysis capabilities
- Implement user authentication and saved content history
- Add export functionality for summaries

## License

MIT License

## Acknowledgements

- [Google Generative AI](https://ai.google.dev/) for Gemini API
- [Groq](https://groq.com/) for their high-performance Mixtral model
- [Tailwind CSS](https://tailwindcss.com/) for the UI framework
- [Lucide Icons](https://lucide.dev/) for beautiful icons

---

`Created with ❤️ by AdarshXKumAR`
