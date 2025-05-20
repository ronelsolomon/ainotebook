

---

# 📘 Math Genius Learning Portal

> A complete AI-powered platform that generates a full, interactive math textbook—starting from a single user topic—using Groq's LLM, LaTeX, and Flask.

---

## 🧠 What It Does

This web app generates a **high-school-level math textbook** by:

1. Accepting a user-defined math topic (e.g. *Quadratics*, *Transformations*, *Trigonometry*)
2. Using **Groq’s LLaMA 3 API** to:
   - Break it into **chapters and lessons**
   - Write explanations, examples, applications, and vocabulary
3. Converting all this into **LaTeX documents**
4. Compiling them into a structured, clickable PDF textbook

You can preview the content in-browser, choose sections (like *Practice Problems*, *Graphs*, *Case Studies*, etc.), and then generate a full downloadable textbook.

---

## ✨ Key Features

- 🎓 **AI-Generated Curriculum**: Breaks down any topic into a traditional chapter-lesson structure with explanations.
- 🧾 **PDF Compilation**: Automatically generates a title page, table of contents, lesson pages, and a glossary using LaTeX.
- 💡 **Interactive UI**: Beautiful HTML/CSS frontend for exploring chapters and customizing the PDF output.
- 🧪 **Live Preview**: Preview selected chapters, explanations, and final PDFs within the web interface.
- ⚙️ **Drag & Sort**: Organize lessons via drag-and-drop using SortableJS.

---

## 🖥️ Frontend UI

The main user interface is written in HTML + JavaScript with embedded Flask routes and `fetch()` calls. It allows:

- Topic entry via `<textarea>`
- Full lesson browsing (including explanations and nested lessons)
- Section toggles: checkboxes for `Vocabulary`, `Practice`, `Examples`, etc.
- Inline PDF viewing via `<iframe>`

Here’s the HTML view:
> You can find the full HTML code in `templates/self_assessment.html`  
> (or copy from [this snippet](#) if not using templating)

```html
<h1>Welcome to Ask the Math Genius! 🤓</h1>
<textarea placeholder="Enter a math topic..."></textarea>
<button onclick="askLLM()">Ask Genius</button>
```

Selected lessons and chapters render like:

```html
📘 Chapter: Quadratics
  🔹 Lesson: Solve by Factoring
     - Explanation: This method uses the zero-product property...
```

PDFs are shown in real-time in a built-in viewer:

```html
<iframe id="pdfViewer" src=""></iframe>
```

---

## 📂 Folder Structure

```
MyEdMaster-contents/
├── static/               # Generated PDFs (TitlePage, Chapter PDFs, Glossary)
│   └── lessonplans/      # Cached JSON from past queries
├── templates/
│   └── self_assessment.html  # Main UI
├── app.py                # Core backend logic (Flask + Groq API)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## 🔧 Backend Components

| Function                     | Description |
|-----------------------------|-------------|
| `generate_lesson_textbook()`| Uses LLaMA-3 to generate textbook outline |
| `generate_pdf_lesson()`     | Creates LaTeX + compiles each lesson into a PDF |
| `merge_pdfs()`              | Combines all sections (title, TOC, lessons, glossary) |
| `generate_glossary()`       | Extracts terms from PDF text using LLM |
| `generate_table_of_contents()` | Creates clickable TOC inside merged PDF |
| `create_title_page()`       | Builds title PDF with cover styling |

---

## 📦 Setup Instructions

### 🐍 Python Setup

```bash
git clone git@github.com:MyEdMaster-education/MyEdMaster-contents.git
cd MyEdMaster-contents
python -m venv venv
source venv/bin/activate     # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 🔑 Groq API Key

```bash
export GROQ_API_KEY="your_api_key"  # on Windows: set GROQ_API_KEY=...
```

### 🧪 Check `pdflatex`

Make sure `pdflatex` is installed:

```bash
which pdflatex       # or where pdflatex on Windows
```

Install [TeX Live](https://www.tug.org/texlive/) or [MiKTeX](https://miktex.org/) if missing.

---

## 🚀 Run the App

```bash
flask run --port 5003
```

Visit: [http://localhost:5003](http://localhost:5003)

---

## 🎯 Example Use

1. Type: `"Functions and Graphs"`
2. AI generates:
   - 12 chapters like *Linear Functions*, *Transformations*, *Quadratics*
   - Each chapter has 6–10 lessons
   - You get:
     - LaTeX content for each
     - A full clickable PDF with visual design

---

## 🛠️ Customize Textbook Sections

Choose any:
- 📘 **Concepts**
- 📈 **Graph Representations**
- 🧠 **Mastering Tips**
- 🧮 **Practice Problems**
- 📊 **Real-World Use**
- 🧪 **Case Studies**
- 📚 **Glossary & Resources**

---

## 🤝 Contributing

Pull requests welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Submit a descriptive PR

---

## 📄 License

This project is MIT-licensed.

---


