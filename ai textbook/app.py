from flask import Flask, send_file, request,render_template_string, render_template, jsonify
import os
import subprocess
from groq import Groq
import shutil
import ast
import re
import openai
import fitz  # PyMuPDF
from fpdf import FPDF
from PyPDF2 import PdfMerger
import json

import pdfplumber
from langchain_ollama.llms import OllamaLLM
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.enums import TA_CENTER
from langchain.prompts import ChatPromptTemplate


from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch





app = Flask(__name__, static_folder="static")



def clear_static_folder():
    """
    Deletes all files in the 'static' folder to ensure a fresh start.
    """
    static_folder = os.path.join(os.getcwd(), "static")
    lessonplan_folder = os.path.join(static_folder, "lessonplans")

    # Ensure the folder exists before attempting to delete
    if os.path.exists(static_folder):
        for filename in os.listdir(static_folder):
            file_path = os.path.join(static_folder, filename)
            try:
                if file_path == lessonplan_folder:
                    continue
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Remove files
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove directories (if any)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")



def latex_to_pdf(latex_code, output_filename="output.pdf", name="sample.tex"):
    """
    Converts LaTeX code into a PDF and saves it in the 'static' folder.

    Parameters:
    latex_code (str): The LaTeX code enclosed in triple backticks.
    output_filename (str): The name of the output PDF file (default is 'output.pdf').

    Returns:
    str: The path to the generated PDF file if successful, else an error message.
    """
    match = re.search(r"```latex\n(.*?)\n```", latex_code, re.DOTALL)
    
    if match:
        latex_code = match.group(1)
    else:
        return "No LaTeX code found."

    # Ensure 'static' directory exists
    static_folder = os.path.join(os.getcwd(), 'static')
    os.makedirs(static_folder, exist_ok=True)

    # File paths
    tex_file = "temp.tex"
    pdf_file = "temp.pdf"
    log_file = "temp.log"
    output_pdf_path = os.path.join(static_folder, output_filename)

    # Write LaTeX content to a temporary .tex file
    with open(tex_file, "w", encoding="utf-8") as f:
       f.write(latex_code)
    #with open(name, "w") as f:
        #f.write(latex_code)
    # Run pdflatex with error handling and log suppression
    try:
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        # Check if the PDF was generated successfully
        if os.path.exists(pdf_file):
            shutil.move(pdf_file, output_pdf_path)  # Move PDF to static folder
        else:
            error_message = f"LaTeX compilation failed. Check {log_file} for details.\nError: {result.stderr}"
            
            # Print the log file content if it exists
            if os.path.exists(log_file):
                with open(log_file, "r") as log:
                    log_content = log.read()
                    error_message += f"\n\nLog File Content:\n{'-'*40}\n{log_content}\n{'-'*40}"
                    print(error_message)
            
            return error_message

    finally:
        # Cleanup temporary files
        for ext in [".aux", ".out", ".tex", ".log"]: # ".tex", ".log"
            try:
                os.remove(f"temp{ext}")
            except FileNotFoundError:
                pass

    return output_pdf_path


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def load_lesson_from_cache(title):
    filename = f"static/lessonplans/{title.replace(' ', '_').lower()}.json"
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading cached lesson plan: {e}")
    return None

def save_lesson_to_cache(title, lessonplan):
    os.makedirs('static/lessonplans', exist_ok=True)
    filename = f"static/lessonplans/{title.replace(' ', '_').lower()}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(lessonplan, file, indent=4, ensure_ascii=False)

    except Exception as e:
        print(f"Error saving lesson plan to cache: {e}")

def generate_lesson_textbook(title="Foundations of Algebra: Exponents and Order of Operations"):
    """
    Generates a structured Python list of lessons for the given title.
    Returns a parsed list of dictionaries.
    """
    promptl = f"""You are an AI that generates Python code. Only output a valid Python list of dictionaries.
Each dictionary represents a chapter, containing a "chapter" key with a string title and a "lessons" key with a list of lesson titles.
The topic is "{title}". Do not add explanations, formatting, or text outside the Python list.
Example output format:
[
    {{"chapter": "Background", "lessons": ["Lesson 1", "Lesson 2"]}},
    {{"chapter": "Advanced Concepts", "lessons": ["Lesson A", "Lesson B"]}}
]
Ensure 6 to 15 lessons per chapter and 10 to 16 chapters. The chapter and lesson should be like the standard textbook structure for high school. Don't repeat lessons

For instance, if the title is Algebra: One Chapter is:

Chapter: quadratics
1	quadratic graph and properties
2	quadratic functions
3	solve quadratic equations by graphing
4	solve quadratic equation by factoring
5	solve quadratic equation using square roots
6	solve quadratic equation by completing the square
7	quadratic formula and the discriminant
8	solve quadratic equations using the quadratic formula
9	compare linear, exponential, and quadratic functions
10	systems of linear and quadratic equations


For instance, if the title is Geometry: The Chapter and lessons are

## First Chapter is Transformations for Geometry
## **Performing Transformations**  
- Euclidean Geometry
- Translations  
- Rotations  
- Reflections  
- Dilations
- Rigid Transformations
- Compositions of Transformations
- Inverses of Transformations
- Vector Transformations

---

## **Transformation Properties and Proofs**  
- Rigid Transformations Overview  
- Dilation and Preserved Properties  
- Properties & Definitions of Transformations  
- Symmetry  
- Proofs with Transformations
- Transformations and Similarity
- Transformations and Congruence
- Linear Transformations in Algebra

---

## **Congruence**  
- Congruence through Transformations  
- Transformations & Congruence  
- Triangle Congruence from Transformations  
- Congruent Triangles  
- Triangle Theorems & Properties  
- Theorems Concerning Triangle Properties  
- Working with Triangles  
- Quadrilateral Properties & Proofs  
- Theorems Concerning Quadrilateral Properties  
- Proofs of General Theorems  
- Geometric Constructions  
- Constructing Lines & Angles  

---

## **Similarity**  
- Defining Similarity  
- Triangle Similarity  
- Introduction to Triangle Similarity  
- Solving Similar Triangles  
- Angle Bisector Theorem  
- Using Similarity for Proofs & Problem Solving  
- Solving Problems with Similar & Congruent Triangles  
- Proving Relationships Using Similarity  
- Solving Modeling Problems with Similar & Congruent Triangles  

---

## **Right Triangles & Trigonometry**  
- Pythagorean Theorem  
- Pythagorean Theorem Proofs  
- Special Right Triangles  
- Trigonometric Ratios  
- Ratios in Right Triangles  
- Trigonometric Ratios  
- Solving for a Side in a Right Triangle Using Trigonometric Ratios  
- Solving for an Angle in a Right Triangle Using Trigonometric Ratios  
- Sine & Cosine of Complementary Angles  
- Applications of Trigonometry  
- Modeling with Right Triangles  

---

## **Analytic Geometry**  
- Coordinate Plane Applications  
- Distance & Midpoints  
- Dividing Line Segments  
- Problem-Solving with Distance on the Coordinate Plane  
- Parallel & Perpendicular Lines  
- Equations of Parallel & Perpendicular Lines  

---

## **Conic Sections**  
- Circles in the Coordinate Plane  
- Graphs of Circles Introduction  
- Standard Equation of a Circle  
- Expanded Equation of a Circle  
- Parabolas  
- Focus and Directrix of a Parabola  

---

## **Circles**  
- Circle Fundamentals  
- Circle Basics  
- Arc Measure  
- Arc Length (from Degrees & Radians)  
- Introduction to Radians  
- Sector & Inscribed Shapes  
- Sectors  
- Inscribed Angles  
- Inscribed Shapes Problem-Solving  
- Proofs with Inscribed Shapes  
- Tangents & Constructions  
- Properties of Tangents  
- Constructing Regular Polygons Inscribed in Circles  
- Constructing Circumcircles & Incircles  
- Constructing a Line Tangent to a Circle  

---

## **Area and Perimeter**
Area of Triangles, Parallelograms, & Trapezoids
Area of Composite Figures
Surface Area of Prisms, Pyramids, & Cylinders
Surface Area of Cones & Spheres
Perimeter of Various Shapes
Real-World Applications of Area & Perimeter

---

## **Solid Geometry**  
- 2D vs. 3D Objects  
- Volume & Surface Area  
- Cavalieri’s Principle & Dissection Methods  
- Volume & Surface Area Calculations  
- Density & Applications  
--
## **Parallel Lines, Lines, and Angles**  
- Parallel & Perpendicular Lines  
- Angle Relationships  
- Corresponding, Alternate Interior, & Alternate Exterior Angles  
- Parallel Lines and Transversals  
- Proving Lines Parallel  
- Angle Relationships in Polygons

---

## **Quadrilaterals**
- Properties of Quadrilaterals
- Parallelograms, Rectangles, Rhombuses & Squares
- Trapezoids & Kites
- Proving Quadrilateral Properties
- Applications of Quadrilaterals

---

## **The Nature of Deductive Reasoning**  
- Introduction to Logic & Reasoning  
- Conditional Statements & Biconditionals  
- Laws of Logic  
- Introduction to Proofs  
- Writing Two-Column and Paragraph Proofs  
- Proof Strategies & Problem-Solving  

---

## **Inequalities in Geometry**  
- Geometric Inequalities  
- Triangle Inequality Theorem  
- Angle-Side Relationships in Triangles  
- Exterior Angle Theorem  
- Applying Inequalities in Geometric Proofs

---

"""

    

    try:

        """
        # ChatCompletion.create(
        response = openai.chat.completions.create(
        model="gpt-4o",  # Use "gpt-4" or "gpt-3.5-turbo" based on your subscription
        messages=[{
            "role": "user", 
            "content": promptl}]

            
        ) """
        # print(response)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": promptl}],
            model="llama-3.3-70b-versatile",
        )

        # raw_output = response.choices[0].message.content.strip()
        raw_output = response.choices[0].message.content.strip()
        raw_output = raw_output.strip("```python").strip("```").strip()

        # Ensure it's valid Python code
        print(raw_output)
        try:
            lesson_data = ast.literal_eval(raw_output)
            return lesson_data
        except (SyntaxError, ValueError):
            print("Error: Model did not return valid Python syntax.")
            return None

    except Exception as e:
        print(f"Error generating lessons: {e}")
        return None




import os
import fitz  # PyMuPDF

def merge_pdfs(lessonplan, output_filename="MergedTextbook.pdf", title="Title Page"):
    static_folder = os.path.join(os.getcwd(), "static")
    merged_pdf = fitz.open()
    toc_tree = []
    visual_toc_entries = []

    page_counter = 0

    # Insert Title Page
    title_path = os.path.join(static_folder, "TitlePage.pdf")
    if os.path.exists(title_path):
        doc = fitz.open(title_path)
        merged_pdf.insert_pdf(doc)
        toc_tree.append([1, title, page_counter])
        visual_toc_entries.append({"title": title, "page": page_counter, "level": 0})
        page_counter += len(doc)

    # Reserve TOC Page (will be updated later)
    toc_page = merged_pdf.new_page(pno=page_counter)
    toc_page_index = page_counter
    page_counter += 1

    # Insert Chapter Overview
    explanation_path = os.path.join(static_folder, "ChapterOverview.pdf")
    if os.path.exists(explanation_path):
        doc = fitz.open(explanation_path)
        toc_tree.append([1, "Chapter Overview", page_counter])
        visual_toc_entries.append({"title": "Chapter Overview", "page": page_counter, "level": 0})
        merged_pdf.insert_pdf(doc)
        page_counter += len(doc)

    # Process Chapters and Lessons
    for chapter_index, chapter in enumerate(lessonplan, start=1):
        chapter_title = f"Chapter {chapter_index}: {chapter['chapter']}"
        toc_tree.append([1, chapter_title, page_counter])
        visual_toc_entries.append({"title": chapter_title, "page": page_counter, "level": 1})
        
        for lesson in chapter['lessons']:
            filename = f"{lesson['lesson']}.pdf"
            file_path = os.path.join(static_folder, filename)
            if os.path.exists(file_path):
                doc = fitz.open(file_path)
                lesson_title = f"Lesson {chapter_index}.{lesson['lesson']}"
                toc_tree.append([2, lesson_title, page_counter])
                visual_toc_entries.append({
                    "title": lesson_title,
                    "page": page_counter,
                    "level": 2
                })
                merged_pdf.insert_pdf(doc)
                page_counter += len(doc)

    # Insert Glossary
    glossary_path = os.path.join(static_folder, "Glossary.pdf")
    if os.path.exists(glossary_path):
        doc = fitz.open(glossary_path)
        toc_tree.append([1, "Glossary", page_counter])
        visual_toc_entries.append({"title": "Glossary", "page": page_counter, "level": 0})
        merged_pdf.insert_pdf(doc)
        page_counter += len(doc)

    # Sort TOC entries by page number
    visual_toc_entries.sort(key=lambda x: x["page"])


    # Shift TOC entry page references forward (TOC was inserted at index 1)
    for entry in visual_toc_entries:
        if entry["page"] >= toc_page_index:
            entry["page"] += 1
    for item in toc_tree:
        if item[2] >= toc_page_index:
            item[2] += 1

    # Recreate TOC page after Title Page
    toc_page = merged_pdf.new_page(pno=1)
    page_width = toc_page.rect.width
    y_position = 100

    # TOC Header
    toc_page.insert_text(
        point=(50,50),
        text="Table of Contents",
        fontsize=18,
        fontname="helv",
        color=(0, 0, 0)
    )
    toc_page.draw_line(
        (50, y_position - 5),
        (page_width - 50, y_position + 18),
        color=(0, 0, 0),
        width=1
    )

    y_position += 40  # Move below the header

    # TOC Entries
    for entry in visual_toc_entries:
        if y_position > 750:
            toc_page = merged_pdf.new_page(pno=page_counter)
            page_counter += 1
            y_position = 100

        indent = 50 + (entry["level"] * 20)
        font_size = 12 if entry["level"] == 0 else 11 if entry["level"] == 1 else 10
        text_color = (0, 0, 0) if entry["level"] < 2 else (0.4, 0.4, 0.4)

        # Entry title
        toc_page.insert_text(
            point=(indent, y_position),
            text=entry["title"],
            fontsize=font_size,
            color=text_color
        )

        # Page number
        page_num_text = str(entry["page"] + 1)
        text_width = fitz.get_text_length(page_num_text, fontname="helv", fontsize=font_size)
        toc_page.insert_text(
            point=(page_width - 50 - text_width, y_position),
            text=page_num_text,
            fontsize=font_size,
            color=text_color
        )

        # Dotted line
        text_end = indent + fitz.get_text_length(entry["title"], fontname="helv", fontsize=font_size)
        toc_page.draw_line(
            (text_end + 5, y_position + 2),
            (text_end + 5, y_position + 2),
            color=(0.7, 0.7, 0.7),
            width=0.5,
            dashes="2 2"
        )

        # Clickable link
        link_rect = fitz.Rect(indent, y_position - 2, page_width - 50, y_position + 12)
        toc_page.insert_link({
            "kind": fitz.LINK_GOTO,
            "from": link_rect,
            "page": entry["page"],
            "to": fitz.Point(0, 0)
        })

        y_position += 18 if entry["level"] == 0 else 20

    # Add bookmarks
    merged_pdf.set_toc(toc_tree)

    # Save final PDF
    output_path = os.path.join(static_folder, output_filename)
    merged_pdf.save(output_path)
    merged_pdf.close()
    print(f"✅ Professional PDF created at: {output_path}")
    return output_path








def generate_table_of_contents(lesson_data, output_filename="table_of_contents.pdf"):
    pdf = FPDF()
    pdf.add_page()
    
    # Use a Unicode font (FreeSerif) instead of Helvetica
    pdf.set_font("Helvetica", size=12)
    pdf.set_font("Helvetica", "B", size=14)
    pdf.set_font("Helvetica", "", size=12)
    pdf.cell(200, 20, "Table of Contents", ln=True, align="C")
    pdf.set_font("Helvetica", size=12)

    
    for chapter_index, chapter in enumerate(lesson_data, start=1):
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(0, 10, f"Chapter {chapter_index}: {chapter['chapter']}", ln=True)
        
        pdf.set_font("Helvetica", size=12)
        for lesson_index, lesson in enumerate(chapter['lessons'], start=1):

            pdf.cell(10)  # Indentation for lesson titles
            pdf.cell(0, 8, f"{lesson_index}. {lesson["lesson"]}", ln=True)

    output_path = f"static/{output_filename}"
    pdf.output(output_path)
    print(f"Table of Contents PDF generated at: {output_path}")
    return output_path



# This function will generate the LaTeX document and then create a PDF
def generate_pdf_lesson(title, lesson, index, selected_sections, practice_problem_count):
    """
    Generates a LaTeX document for the lesson 'Exponents and Order of Operations'
    using Groq API and then converting it to a PDF.
    """
    print(title, lesson)
    latex_prompt = f"""
    Generate a LaTeX document on the topic {{lesson}}.
    This is generated for the beginner so make sure everything is easy to understand like a textbook.
    Use the article class. Make sure the LaTeX compiles correctly.
    Output ONLY valid LaTeX code starting with \\documentclass.
    """
    latex_prompt += "\n```latex\n"
    latex_prompt += f"""
    \\documentclass{{article}}
    \\usepackage[a4paper, margin=1.27cm]{{geometry}}
    \\usepackage{{amsmath, amssymb, }} % For advanced mathematical symbols
    \\usepackage{{graphicx, tikz, pgfplots{{compat=1.18}} }}
    \\pgfplotsset{{compat=1.18}}
    \\usepackage{{hyperref, booktabs}} % For creating hyperlinks within the document.
    \\usepackage[T1]{{fontenc}}
    \\usepackage{{wasysym}}
    \\usepackage{{mathptmx}}

    \\usepackage[utf8]{{inputenc}}

    \\usepackage{{enumitem}}

    \\usepackage{{amsthm}}
    \\newtheorem{{solution}}{{Solution}}
    \\usepackage{{tcolorbox}}
    \\usepackage{{fancyhdr}}
    \\usepackage{{longtable}}
    \\usepackage{{lmodern}}

    \\title{{ {title} }}
    \\author{{}}
    \\date{{}}

    \\begin{{document}}

    \\maketitle
    """
    if "concepts" in selected_sections:
        latex_prompt += f"""
    \\section*{{Facts and Concepts}}
    \\subsection*{{Introduction to the Topic}}
    Begin by introducing the topic with a clear definition and basic notation. Provide any necessary formulas, theorems, or principles relevant to the topic. Content should span at least one full page with detailed insights.

    \\begin{{itemize}}
        \\item \\textbf{{Definition:}} {{insert detailed definition}}
        \\item \\textbf{{Notation:}} {{list relevant symbols or terms}}
        \\item \\textbf{{Formulas:}}
    \\end{{itemize}}

    \\subsection*{{Examples}}
    Provide several examples of how the formulas or principles are applied.
    """

    if "graph" in selected_sections:
        latex_prompt += f"""
    \section*{{Graphical Representation}}
    This section includes small graph on {{lesson}} to illustrate key concepts. Use LaTeX commands and packages such as `TikZ`, `graphicx`, and `pgfplots` (compat=1.18) to create professional-quality graphs.

    **Guidelines:**
    - Create small graph functions that demonstrate key concepts, transformations, and behaviors relevant to the lesson.
    - Ensure the `pgfplots` package is installed and compatible with your LaTeX distribution (e.g., `compat=1.18`).
    - Provide a brief description of each graph explaining its purpose and key insights.

    **Example:**
    Below is an example of a simple plot using `pgfplots`:

    \begin{{tikzpicture}}
        \begin{{axis}}[
            title={{Example Graph: Quadratic Function}},
            xlabel={{x-axis (Input)}},
            ylabel={{y-axis (Output)}},
            grid=major,
            width=8cm,
            height=6cm,
            axis lines=middle,
            enlargelimits=true,
            legend pos=north west
        ]
        \addplot[domain=-2:2, samples=100, color=blue, thick] {{x^2}}; % Example: y = x^2
        \legend{{$y = x^2$}}
        \end{{axis}}
    \end{{tikzpicture}}

    *Description:* The graph above illustrates the function \( y = x^2 \), showing how the output increases quadratically as the input moves away from zero.

    **Additional Notes:**
    - Use `$...$` for inline math and `\[...\]` for display math.
    - Always provide a title, labeled axes, and a legend (if applicable).
    - If you encounter issues with `pgfplots`, ensure:
        1. The package is correctly installed.
        2. You are using a compatible version (e.g., `compat=1.18`).
        3. Adjust compatibility settings if needed to match your LaTeX distribution.

    **Advanced Tip:** For more complex visualizations, explore additional TikZ libraries or use external tools like matplotlib to generate LaTeX-compatible plots.
    """

    if "strategies" in selected_sections:
        latex_prompt += f"""
        \\section*{{Strategies and Procedures}}
        - Use problem-solving techniques that ensure accuracy when applying the rules.
        - Subsection: Compare traditional vs. alternative approaches, highlighting their advantages and limitations.

        \\subsection*{{Step-by-Step Approach}}
        Provide a detailed guide on how to solve the problem in different ways. Offer step-by-step instructions for a systematic approach.

        \\begin{{itemize}}
            \\item \\textbf{{Approach 1:}} {{insert strategy}}
            \\item \\textbf{{Approach 2:}} {{insert strategy}}
            \\item \\textbf{{Approach 3:}} {{insert strategy}}
            \\item \\textbf{{Approach 4:}} {{insert strategy}}
            \\item \\textbf{{Approach 5:}} {{insert strategy}}
        \\end{{itemize}}

        \\subsection*{{Common Mistakes and Misconceptions}}
        Include a list of common errors and tips on how to avoid them.

        

        \\begin{{itemize}}
            \\item \\textbf{{Mistake 1:}} {{insert mistake}} \\quad \\textbf{{Correction:}} {{insert correction}}
            \\item \\textbf{{Mistake 2:}} {{insert mistake}} \\quad \\textbf{{Correction:}} {{insert correction}}
            \\item \\textbf{{Mistake 3:}} {{insert mistake}} \\quad \\textbf{{Correction:}} {{insert correction}}
            \\item \\textbf{{Mistake 4:}} {{insert mistake}} \\quad \\textbf{{Correction:}} {{insert correction}}
            \\item \\textbf{{Mistake 5:}} {{insert mistake}} \\quad \\textbf{{Correction:}} {{insert correction}}
        \\end{{itemize}}
        """
    if "rationale" in selected_sections:
        latex_prompt += f"""
            \\section*{{Rationales}}
            Explain the reasoning behind each step for {lesson}

                - Demonstrate how each step connects to the overall solution.
                - Compare different approaches and justify why a particular method is effective
                - Explain the logical reasoning behind each step in the process.
                - Provide a breakdown of the underlying principles or theories.
                - Provide detailed explanations for each point
                - Discuss the mathematical or logical reasoning behind the approach.

            \\subsection{{Why Do the Steps Work?}}
            Explain the underlying mathematical principles that make the problem-solving method valid.  Refer to relevant axioms, theorems, or definitions. Include citations if appropriate.

            \\subsection{{Step-by-Step Logical Connections (Procedural Reasoning)}}
            Demonstrate the logical flow from one step to the next. Explain how each step builds upon the previous one to move closer to the solution.  Focus on the "why" behind each action.

            \\subsection{{Mathematical Justification}}
            Provide a more formal mathematical justification for the method or a specific step, if appropriate. This could involve a symbolic derivation or a more rigorous proof.

            \\subsection*{{Alternative Approaches (Comparative Analysis)}}
            Discuss alternative methods for solving the same problem and justify why the chosen method is preferred (or under what circumstances an alternative method might be better).
            """
    if "vocab" in selected_sections:
       latex_prompt += f"""
        \\section*{{Vocabulary Table}}
        Create a vocabulary table.
        Position the table to the left correctly.
        Adjust row height for readability
        Adjust column spacing
        \\renewcommand{{\arraystretch}}{{1.5}} % Increase row height
        \\setlength{{\tabcolsep}}{{10pt}} % Adjust column spacing

        \\begin{{flushleft}} % Align table to the left
        \\begin{{tabular}}{{|p{{3cm}}|p{{10cm}}|}} % Adjust column widths
            \\hline
            \\textbf{{Term}} & \textbf{{Definition}} \\
            \\hline
            Term 1 & Insert definition here. \\
            Term 2 & Insert definition here. \\
            Term 3 & Insert definition here. \\
            Term 4 & Insert definition here. \\
            \\hline
        \\end{{tabular}}
        \\end{{flushleft}}

        \\end{{document}}
        """
    if "mastering" in selected_sections:
        latex_prompt += f"""
        \\section*{{Mastering This Lesson}}  
        To fully grasp this lesson: {lesson}, it is important to understand the following key concepts: 

        In order to master the lesson, you need to know the following facts, strategies, procedures, and rationales and then list what they are and explain how they relate to the lesson

        \\subsection*{{Facts}}  
        \\begin{{itemize}}  
            \\item \\textbf{{Fact 1:}} {{Explain how this fact is relevant to the lesson.}}  
            \\item \\textbf{{Fact 2:}} {{Explain another essential fact.}}
            \\item \\textbf{{Fact 3:}} {{Explain another essential fact.}} 
        \\end{{itemize}}  

        \\subsection*{{Strategies}}  
        \\begin{{itemize}}  
            \\item \\textbf{{Strategy 1:}} {{Describe a problem-solving technique.}}  
            \\item \\textbf{{Strategy 2:}} {{Describe another useful strategy.}}
            \\item \\textbf{{Strategy 3:}} {{Describe another useful strategy.}}  
        \\end{{itemize}}  

        \\subsection*{{Procedures}}  
        \\begin{{itemize}}  
            \\item \\textbf{{Procedure 1:}} {{Step-by-step process for solving a problem.}}  
            \\item \\textbf{{Procedure 2:}} {{Another structured approach.}}  
            \\item \\textbf{{Procedure 3:}} {{Another structured approach.}} 
        \\end{{itemize}}  

        \\subsection*{{Rationales}}  
        \\begin{{itemize}}  
            \\item \\textbf{{Rationale 1:}} {{Explain why a particular strategy or procedure works.}}  
            \\item \\textbf{{Rationale 2:}} {{Provide additional reasoning.}}  
            \\item \\textbf{{Rationale 3:}} {{Provide additional reasoning.}}
        \\end{{itemize}} 
        """ 

    

    
    if "hist" in selected_sections:
        latex_prompt += f"""
            \\section*{{Historical Context}}
            Show the history of the {lesson}, including the origins, notable contributors, and the introduction of modern notation.


            \\begin{{itemize}}
                \\item \\textbf{{Origin:}} {{insert origin\}}
                \\item \\textbf{{Modern Notation:}} {{insert a detailed, step-by-step explanation of how to solve this specific exponent problem, including justification for each step}}
            \\end{{itemize}}
            """
        
    if "realworld" in selected_sections:
        latex_prompt += f"""
        \\section*{{Real-World Applications}}
        This section provides examples of how the {lesson} is applied in different fields, making the concepts more relatable and practical. We'll cover finance, science, and technology, including equations and example problems.
        
        \\subsection*{{Applications Across Different Fields}}
        \\begin{{itemize}}
            \\item \\textbf{{Field 1:}} {{Explain how the topic applies to finance. Include an equation if applicable.}}
            \\item \\textbf{{Field 1:}} {{Describe how this concept is used in physics, chemistry, or engineering with a mathematical formula.}}
            \\item \\textbf{{Field 1:}} {{Illustrate an application in genetics, population dynamics, or bioinformatics.}}
            \\item \\textbf{{Field 1:}} {{Showcase its relevance in data science, AI, or software engineering.}}
        \\end{{itemize}}

        \\subsection*{{Example Problems and Equations}}
        Below are practical problems to demonstrate how this {lesson} is used in real-world scenarios. 

        \\begin{{itemize}}
            \\item \\textbf{{Example Problem 1:}} {{Describe a real-world problem related to the topic and provide an equation.}}
            \\item \\textbf{{Example Problem 2:}} {{Describe another practical problem with an explanation.}}
            \\item \\textbf{{Example Problem 3:}} {{Introduce a scenario in finance/science with a mathematical solution.}}
            \\item \\textbf{{Example Problem 4:}} {{Provide a physics/biology-based application with relevant calculations.}}
        \\end{{itemize}}
        """
    # latex_prompt2 = f"""Add the rest of these sections in Latex format."""
    if "initial" in selected_sections:
        latex_prompt += f"""
    \\section*{{Case Study: {lesson}}}
        % Introduce a real-world or theoretical case study related to {lesson}. Set the stage for the rest of the document by offering an in-depth analysis of the scenario. 
        You MUST generate context, key challenges, and the relevance of the case study in relation to the core concepts discussed later.
        Provide an engaging, clear, and well-structured case study that illustrates the practical applications and importance of the {lesson}. 
        Use a narrative format with paragraphs to highlight key points, challenges, and learning outcomes.
        """
    if "examples" in selected_sections:
        latex_prompt += f"""
        \\section*{{Examples and Demonstrations}}
        {{You MUST generate various examples and the step-by-step procedure to help student understand the concepts on {lesson}.}}
        """
    if "applications" in selected_sections:
        latex_prompt += f"""
        \\section*{{Applications Activity}}
        You MUST generate activities on {lesson} that contextualize the learning and focus on problem-solving. Each activity includes a clear description and learning objective.
        \\begin{{itemize}}
            \\item \\textbf{{Description: }} {{insert learning activity }}
            \\item \\textbf{{Objective:}} {{Insert activity learning objective here}}
        \\end{{itemize}}
        """
    if "assessment" in selected_sections:
        latex_prompt += f"""
        \\section*{{Assessment Strategies}}
        You MUST generate strategies for formative and summative assessments on {lesson}. 
        Offer different ways to test knowledge and provide real-time feedback.
        Suggest different ways to test knowledge, such as quizzes, practical exercises, Self-check exercises, or problem-solving activities.
        """
    if "additional" in selected_sections:
        latex_prompt += f"""
        \\section*{{Additional Resources}}
        % To deepen your understanding of the concepts covered in this lesson, explore the following resources. These resources offer a variety of learning experiences, including websites, video tutorials, and interactive tools.

        \\subsection*{{Recommended Online Resources}}
        You MUST generate  a list of reputable websites that offer further information, practice problems, and tutorials on {lesson}. For each resource, include a brief description of its content and focus.

        \\subsection*{{Video Tutorials}}
        List relevant video tutorials or channels that explain key concepts and demonstrate problem-solving techniques for {lesson}. Include links to the videos or channels and a short summary of their approach.

        \\subsection*{{Interactive Tools}}
        Recommend interactive tools, simulations, or software that allow users to explore {lesson} in a hands-on manner. Include links and a description of how these tools can be used to enhance learning.

        Each of these resources provides a different learning experience, allowing you to explore {lesson} effectively.
        """
    if "theoretical" in selected_sections:
        latex_prompt += f"""        
        \\section*{{Theoretical Background}}
        
        % You MUST generate a section where it provide a comprehensive theoretical background on {lesson}, including key concepts, foundational principles, and relevant mathematical formulations. Ensure clarity by incorporating definitions, theorems, and examples where appropriate. Explain how these concepts apply to real-world scenarios and their significance in understanding {lesson}.
        """
    if "principles" in selected_sections:
        latex_prompt += f"""         
        \\section*{{Underlying Principles}}
        You MUST generate the fundamental mathematical principles of the lesson
        % Introduce the {lesson} and explain why understanding these principles is important in paragraph format.

        \\noindent
        % A deep understanding of the fundamental mathematical principles behind {lesson} is essential for mastering the topic. These principles provide the theoretical foundation for problem-solving and real-world applications.

        \\subsection*{{Key Principles of {lesson}}}
        general introduction to the core principles
        Explain the significance of these principles and how they relate to the lesson
        {{Insert a general introduction to the core principles of the lesson. Explain their significance and how they contribute to understanding the topic.}}

        \\subsection*{{Principle 1: {{Insert Principle Name}}}}
        Provide a detailed explanation of this principle, including formulas if necessary
        {{Provide a detailed explanation of this principle. Describe its role in the lesson, its mathematical formulation (if applicable), and how it is used in practice.}}

        \\subsection*{{Principle 2: {{Insert Principle Name}}}}
        // Explain another core principle and how it differs from or complements the previous principle
        {{Explain another core principle relevant to {{lesson}}. Discuss its applications and how it differs from or complements the previous principle. Provide any necessary equations or examples.}}


        \\subsection*{{Principle 3: {{Insert Principle Name}}}}

        Highlight an additional important principle and its real-world applications

        {{Introduce an additional important principle. Highlight its theoretical background and real-world applications related to {{lesson}}.}}


        \\subsection*{{Connecting the Principles to Applications}}
        Explain how these principles are applied in different fields like science, finance, and technology
        Understanding these principles allows us to apply{lesson} effectively in various contexts, including **{{real-world applications such as physics, finance, computer science, or engineering}}**. By grasping these fundamental concepts, learners can solve complex problems with a clear logical framework.
        """
    if "practice" in selected_sections:
        latex_prompt += f"""
    \\section*{{Practice Problems}}
    You MUST generate exactly {practice_problem_count} math problems using this EXACT format:

    \\begin{{enumerate}}[label=(\\arabic*)]
    % PROBLEMS START
    {''.join(f'\\item Problem {{}} statement here.\\n' for _ in range(practice_problem_count))}
    % PROBLEMS END
    \\end{{enumerate}}

    Follow these rules STRICTLY:
    1. Place ALL \\item commands INSIDE the enumerate environment
    2. Use $...$ for inline math and \\[...\\] for display math
    3. No empty lines between \\item commands
    4. Never put text outside the enumerate environment
    """
        
        
    if "answer" in selected_sections:
        latex_prompt += f"""
    \\section*{{18. Practice Problems Solved Step by Step}}
    Provide solutions and step-by-step explanations for all the practice problems from the previous section.
    Use LaTeX commands for mathematical notations (e.g., \\pi for π).

    For example, if the lesson topic is Euclidean geometry:
    \\begin{{itemize}}
        \\item \\textbf{{Problem:}} The side \( AB \) in the rectangle \( ABCD \) is twice the side \( BC \). A point \( P \) is taken on the side \( AB \) so that \( BP = \\frac{{4}}{{5}} AB \). Show that \( BD \) is perpendicular to \( CP \).
        \\item \\textbf{{Solution:}} 
        \\begin{{enumerate}}
            \\item First, calculate the coordinates of point \( P \) based on the given ratio.
            \\item Use the slope formula to find the slopes of lines \( BD \) and \( CP \).
            \\item Verify that the product of their slopes equals -1, proving they are perpendicular.
        \\end{{enumerate}}
    \\end{{itemize}}

    Below is the structure for solving problems:
    \\begin{{itemize}}
        {''.join(f'\\item \\textbf{{Problem {i+1}:}} Insert problem statement here.\n\\item \\textbf{{Solution:}} Insert solution here.\n' for i in range(practice_problem_count))}
    \\end{{itemize}}
    """

    latex_prompt += "\n \end{document} ```latex\n"

    

    try:

        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": latex_prompt}],
            model="llama-3.3-70b-versatile",
        )
        '''if any(section in selected_sections for section in ["answer", "practice", "initial", "examples and Demonstrations", "applications", "assessment", "additional", "theoretical", "principles"]):
            latex_content2 = response.choices[0].message.content
        
            latex_prompt += f"""Add the sections into 
            Latex code: 
            {latex_content2}
            """
            response = client.chat.completions.create(
            messages=[{"role": "user", "content": latex_prompt2}],
            model="llama-3.3-70b-versatile",
            "Case Study", "Axamples and Demonstrations", "Applications Activity", "Assessment Strategies", "Additional Resouces", "theoretical Background", " Underlying Principles"
        )'''

        latex_content = response.choices[0].message.content
        # print(latex_prompt)

        prompt2 = f"""
        Improve have following LaTeX {lesson} document by:
        - Fix any LaTeX errors in the lesson like /pi for mathematical notations.
        - Use LaTeX commands for mathematical notations (e.g., \\pi for π).
        - For each Section, add more detail on {lesson}. Give Half page length of information based on the section.
        - For each section, Give half a page of explanation
        - For each section, space out bullet points and add more information.

        Follow these rules STRICTLY:
        1. Place ALL \\item commands INSIDE the enumerate environment
        2. Use $...$ for inline math and \\[...\\] for display math
        3. No empty lines between \\item commands
        4. Never put text outside the enumerate environment
    
        LaTeX Code:
        {latex_content}
        """
        if "answer" in selected_sections:
            prompt2 += f"""
    At the end of lesson, add Practice Problems Solved Step by Step Section
    Provide solutions and step-by-step explanations for all the practice problems from the previous section.You MUST generate exactly {practice_problem_count} Solutions.
    
    Use LaTeX commands for mathematical notations (e.g., \\pi for π).
    """
        if "theoretical" in selected_sections:
            prompt2 += f"""        
        \\section*{{Theoretical Background}}
       % You MUST generate a section where it provide a comprehensive theoretical background on {lesson}, including key concepts, foundational principles, and relevant mathematical formulations. Ensure clarity by incorporating definitions, theorems, and examples where appropriate. Explain how these concepts apply to real-world scenarios and their significance in understanding {lesson}.
        """
        if "principles" in selected_sections:
            prompt2 += f"""         
        \\section*{{Underlying Principles}}
        You MUST generate the fundamental mathematical principles of the lesson
        % Introduce the {lesson} and explain why understanding these principles is important in paragraph format.

        \\noindent
        % A deep understanding of the fundamental mathematical principles behind {lesson} is essential for mastering the topic. These principles provide the theoretical foundation for problem-solving and real-world applications.

        \\subsection*{{Key Principles of {lesson}}}
        general introduction to the core principles
        Explain the significance of these principles and how they relate to the lesson
        {{Insert a general introduction to the core principles of the lesson. Explain their significance and how they contribute to understanding the topic.}}

        \\subsection*{{Principle 1: {{Insert Principle Name}}}}
        Provide a detailed explanation of this principle, including formulas if necessary
        {{Provide a detailed explanation of this principle. Describe its role in the lesson, its mathematical formulation (if applicable), and how it is used in practice.}}

        \\subsection*{{Principle 2: {{Insert Principle Name}}}}
        // Explain another core principle and how it differs from or complements the previous principle
        {{Explain another core principle relevant to {{lesson}}. Discuss its applications and how it differs from or complements the previous principle. Provide any necessary equations or examples.}}


        \\subsection*{{Principle 3: {{Insert Principle Name}}}}

        Highlight an additional important principle and its real-world applications

        {{Introduce an additional important principle. Highlight its theoretical background and real-world applications related to {{lesson}}.}}


        \\subsection*{{Connecting the Principles to Applications}}
        Explain how these principles are applied in different fields like science, finance, and technology
        Understanding these principles allows us to apply{lesson} effectively in various contexts, including **{{real-world applications such as physics, finance, computer science, or engineering}}**. By grasping these fundamental concepts, learners can solve complex problems with a clear logical framework.
        """
        if "practice" in selected_sections:
            prompt2 += f"""
        At the end of lesson, add Practice Problems Section
    You MUST generate exactly {practice_problem_count} math problems using this EXACT format:

    """
        if "vocab" in selected_sections:
           prompt2 += f"""
        \\section*{{Vocabulary Table}}
        Create a vocabulary table.
        Position the table to the left correctly.
        Adjust row height for readability
        Adjust column spacing
        \\renewcommand{{\arraystretch}}{{1.5}} % Increase row height
        \\setlength{{\tabcolsep}}{{10pt}} % Adjust column spacing

        \\begin{{flushleft}} % Align table to the left
        \\begin{{tabular}}{{|p{{3cm}}|p{{10cm}}|}} % Adjust column widths
            \\hline
            \\textbf{{Term}} & \textbf{{Definition}} \\
            \\hline
            Term 1 & Insert definition here. \\
            Term 2 & Insert definition here. \\
            Term 3 & Insert definition here. \\
            Term 4 & Insert definition here. \\
            \\hline
        \\end{{tabular}}
        \\end{{flushleft}}

        \\end{{document}}
        """
        if "mastering" in selected_sections:
            prompt2 += f"""
        \\section*{{Mastering This Lesson}} 
        Add a Mastering This Lesson Section on {lesson}

        \\subsection*{{Facts}}  
        \\begin{{itemize}}  
            \\item \\textbf{{Fact 1:}} {{Explain how this fact is relevant to the lesson.}}  
            \\item \\textbf{{Fact 2:}} {{Explain another essential fact.}}
            \\item \\textbf{{Fact 3:}} {{Explain another essential fact.}} 
        \\end{{itemize}}  

        \\subsection*{{Strategies}}  
        \\begin{{itemize}}  
            \\item \\textbf{{Strategy 1:}} {{Describe a problem-solving technique.}}  
            \\item \\textbf{{Strategy 2:}} {{Describe another useful strategy.}}
            \\item \\textbf{{Strategy 3:}} {{Describe another useful strategy.}}  
        \\end{{itemize}}  

        \\subsection*{{Procedures}}  
        \\begin{{itemize}}  
            \\item \\textbf{{Procedure 1:}} {{Step-by-step process for solving a problem.}}  
            \\item \\textbf{{Procedure 2:}} {{Another structured approach.}}  
            \\item \\textbf{{Procedure 3:}} {{Another structured approach.}} 
        \\end{{itemize}}  

        \\subsection*{{Rationales}}  
        \\begin{{itemize}}  
            \\item \\textbf{{Rationale 1:}} {{Explain why a particular strategy or procedure works.}}  
            \\item \\textbf{{Rationale 2:}} {{Provide additional reasoning.}}  
            \\item \\textbf{{Rationale 3:}} {{Provide additional reasoning.}}
        \\end{{itemize}} 
        """ 

        if "examples" in selected_sections:
            prompt2 += f"""
        \\section*{{Examples and Demonstrations}}
        You MUST generate various examples to help you understand the concepts on {lesson} step by step. For each example show the step-by-step procedure and give the answer at the end in detail. Show steps to solve a basic problem on {lesson} to demonstrate the fundamental principles of the topic. Step by step, we will break down the solution and discuss how each part connects to the larger concept. In this example, walk through a more intricate problem in {lesson}, guiding you through each stage and explaining the rationale behind every decision. This will provide a deeper understanding and help you apply the theory in a more challenging context. Show multiple steps and cover advanced concepts in {lesson}. We will guide you through it step by step, helping you to understand the nuances of the subject and how the theory is applied in a more complex scenario.
        """
        if "applications" in selected_sections:
            prompt2 += f"""
        \\section*{{Applications Activity}}
        You MUST generate activities on {lesson} that contextualize the learning and focus on problem-solving. Each activity includes a clear description and learning objective.
        """
        
        if "realworld" in selected_sections:
            prompt2 += f"""
        Add a Historical Context Section
        This section provides examples of how the {lesson} is applied in different fields, making the concepts more relatable and practical. We'll cover finance, science, and technology, including equations and example problems.
        
        """
        if "initial" in selected_sections:
            prompt2 += f"""
    Add a Case Study Section
    % Introduce a real-world or theoretical case study related to {lesson}. Set the stage for the rest of the document by offering an in-depth analysis of the scenario. 
    You MUST generate context, key challenges, and the relevance of the case study in relation to the core concepts discussed later.
    Provide an engaging, clear, and well-structured case study that illustrates the practical applications and importance of the {lesson}. 
    Use a narrative format with paragraphs to highlight key points, challenges, and learning outcomes.
    """
        if "additional" in selected_sections:
            prompt2 += f"""
        Add a Additional Resources Section.
        To deepen your understanding of the concepts covered in this lesson, explore the following resources.
        """
        if "assessment" in selected_sections:
            prompt2 += f"""
        \\section*{{Assessment Strategies}}
        You MUST generate strategies for formative and summative assessments on {lesson}. 
        Offer different ways to test knowledge and provide real-time feedback.
        Suggest different ways to test knowledge, such as quizzes, practical exercises, Self-check exercises, or problem-solving activities.
        """

        if "hist" in selected_sections:
            prompt2 += f"""
            Add a Historical Context Section
            Show the history of the {lesson}, including the origins, notable contributors, and the introduction of modern notation.
            """

        if "concepts" in selected_sections:
            prompt2 += f"""
        Add more Details to the Facts and Concepts Section
    """

        if "strategies" in selected_sections:
            prompt2 += f"""
        Add more Detail to the Strategies and Procedures Section
        """
        if "rationale" in selected_sections:
            prompt2 += f"""
            
            Add more Details Rationales Section
            """

        # Second API call using latex_content from the first response
        second_response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt2}],
        model="llama-3.3-70b-versatile",
)

        refined_latex_content = second_response.choices[0].message.content
       

        # Convert the generated LaTeX content to PDF
        pdf_filename = f"{sanitize_filename(lesson)}.pdf"
        latex_to_pdf(refined_latex_content, pdf_filename, f"{sanitize_filename(title)}.tex")
        return pdf_filename
    
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

# Step 1: Extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# Step 2: Preprocess the extracted text (clean up unwanted characters)
def preprocess_text(text):
    # Remove extra whitespaces and unwanted characters
    text = re.sub(r'\s+', ' ', text)  # Collapse multiple whitespaces
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text



from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

import re


def generate_glossary(text):
    """
    Generate glossary using a language model with improved prompt engineering.
    """
    # Initialize the language model (replace with your preferred LLM)
    model = OllamaLLM(model="llama3.2")

    

    glossary = {}
    
    # Iterate through each section to generate glossaries
    
    model_prompt = f"""
        You are an expert at creating glossaries for a textbook. Extract key terms, definitions, and concepts for the following text:
        
        Text: {text}
        
        Instructions:
        1. Identify key terms and concepts related to the topic.
        2. Provide brief definitions or explanations for each term.
        3. Include multi-word expressions if relevant.
        4. Output should be in "term: definition" format like shoe: wear on foot
        """
        
    prompt = ChatPromptTemplate.from_template(model_prompt)
    chain = LLMChain(llm=model, prompt=prompt)
        
        # Generate glossary for each section
    response = chain.run({"text": text})
        
        # Add glossary terms to the dictionary
    
    
    return response


# Step 4: Create glossary entries from the model response
def create_glossary_entries(response):
    glossary = {}
    # Assuming response contains key: value pairs separated by a colon
    entries = response.split('\n')
    for entry in entries:
        parts = entry.split(":", 1)  # Split on the first colon only
        if len(parts) == 2:
            term, definition = parts
            glossary[term.strip()] = definition.strip()
    return glossary


def create_pdf_glossary(glossary, output_path):
    """
    Create a PDF with a formatted glossary.
    - Glossary entries will have bold terms and proper spacing.
    - Includes a title "Glossary" at the top of the document.
    """
    # Create a PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    
    # Get styles for formatting
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = TA_CENTER
    bold_style = styles["BodyText"]
    bold_style.textColor = colors.black
    
    # Add "Glossary" as the title
    elements = []
    elements.append(Paragraph("Glossary", title_style))
    elements.append(Spacer(1, 20))  # Add space below the title
    glossary = {term: definition for term, definition in list(glossary.items())[:-1]}
    # Add glossary terms and definitions
    for term, definition in glossary.items():
        term = re.sub(r'\*\*(.*?)\*\*', r'\1', term)
        formatted_entry = f"<b>{term}:</b> {definition}"  # Make the term bold
        elements.append(Paragraph(formatted_entry, bold_style))
        elements.append(Spacer(1, 10))  # Add space between entries
    
    # Build the PDF document
    doc.build(elements)



# 2. Merge PDFs
def merge_with_glossary(main_pdf, glossary_pdf, output_path):
    merger = PdfMerger()
    merger.append(main_pdf)
    merger.append(glossary_pdf)
    merger.write(output_path)
    merger.close()
    print(f"Merged PDF with glossary saved to: {output_path}")


def create_title_page(title: str, author: str):
    output_path = f"static/TitlePage.pdf"
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 150, title)

    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, height - 200, f"by {author} ✨")

    c.showPage()
    c.save()
    print(f"Title page created at: {output_path}")


from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import black, lightgrey

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, lightgrey

def generate_lesson_pdf(lessonplan, output_path="lesson_plan.pdf"):
    c = canvas.Canvas(output_path, pagesize=LETTER)
    width, height = LETTER
    margin = 1 * inch
    y = [height - margin]  # Using list so we can modify it inside nested function

    def draw_text(text, font="Helvetica", size=12, line_spacing=14):
        c.setFont(font, size)
        max_width = width - 2 * margin

        words = text.split()
        line = ""

        for word in words:
            test_line = f"{line} {word}".strip()
            text_width = pdfmetrics.stringWidth(test_line, font, size)
            if text_width <= max_width:
                line = test_line
            else:
                if y[0] < margin:
                    c.showPage()
                    y[0] = height - margin
                    c.setFont(font, size)
                c.drawString(margin, y[0], line)
                y[0] -= line_spacing
                line = word

        if line:
            if y[0] < margin:
                c.showPage()
                y[0] = height - margin
                c.setFont(font, size)
            c.drawString(margin, y[0], line)
            y[0] -= line_spacing

    for chapter in lessonplan:
        # Chapter Header Background
        c.setFillColor(lightgrey)
        c.rect(margin, y[0] - 24, width - 2 * margin, 22, fill=True, stroke=False)
        c.setFillColor(black)

        # Chapter Title
        chapter_title = f"📘 Chapter: {chapter['chapter']}"
        draw_text(chapter_title, font="Helvetica-Bold", size=14, line_spacing=18)

        # Chapter Explanation
        chapter_expl = chapter.get('explanation', '')
        if chapter_expl:
            draw_text(f"➤ {chapter_expl}", font="Helvetica-Oblique", size=11, line_spacing=14)
        
        y[0] -= 10  # Space after chapter explanation

        # Lessons
        for lesson in chapter['lessons']:
            lesson_title = f"   🔹 {lesson['lesson']}"
            lesson_expl = lesson.get('explanation', '')
            
            draw_text(lesson_title, font="Helvetica-Bold", size=12, line_spacing=16)

            for line in lesson_expl.split("\n"):
                draw_text(f"      {line}", font="Helvetica", size=11, line_spacing=14)

            y[0] -= 10  # Space after lesson

        y[0] -= 20  # Space after chapter

    c.save()
    print(f"✅ PDF saved to {output_path}")









def generate_explanation(text):
    model = OllamaLLM(model="llama3.2")
    
    model_prompt = f"""
    You are a highly knowledgeable math expert and educator. 
    Please provide a clear, concise, and complete definition or explanation of the following math topic or concept in one sentence: {text}.
    Your response should include:
    - A brief definition of the concept.


    Please ensure your response is detailed and complete, even if the topic is abstract or unfamiliar.
    """
    
    prompt = ChatPromptTemplate.from_template(model_prompt)
    
    chain = prompt | model

    detailed_response = chain.invoke({"text": text})

    return detailed_response.split("\n")[0] or ""


@app.route('/')
def home():
    return render_template('self_assessment.html')


@app.route('/search')
def about():
    """
    Render the about.html template.

    Returns:
        HTML: The rendered about page.
    """
    return render_template('search_bar.html')

@app.route("/ask", methods=["POST"])
def tableofContent():
    try:
        data = request.get_json()
        title = data.get("question", "").strip()
        # clear_static_folder()
        if not title:
            return jsonify({"error": "Please enter a question!"}), 400

        cached_lessonplan = load_lesson_from_cache(title)
        if cached_lessonplan:
            return jsonify({
                "status": "success (from cache)",
                "title": title,
                "lessons": cached_lessonplan
            })

        

        # Generate lesson plan
        lessonplan = generate_lesson_textbook(title)
        # save_lesson_to_cache(title, lessonplan)
        print("Trial")

        # Validate lesson plan structure
        if not isinstance(lessonplan, list) or len(lessonplan) == 0:
            return jsonify({"error": "Failed to generate lesson plan"}), 500

        for chapter in lessonplan:
            if not isinstance(chapter, dict) or 'lessons' not in chapter:
                return jsonify({"error": "Invalid chapter structure"}), 500
            chapter["explanation"] = generate_explanation(chapter["chapter"])  # Explain the chapter
            print(chapter["explanation"])

            for i, lesson in enumerate(chapter["lessons"]):
                lesson_explanation = generate_explanation(lesson)
                print(lesson_explanation)
                if lesson_explanation is None:
                    return jsonify({"error": "Failed to generate lesson explanation"}), 500
                chapter["lessons"][i] = {"lesson": lesson, "explanation": lesson_explanation}
        print("Sucess")
        save_lesson_to_cache(title, lessonplan)  
        return jsonify({
            "status": "success",
            "title": title,
            "lessons": lessonplan
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500
        #return render_template('lesson_plan.html', title=title, lessonplan=lessonplan)
        '''
        generate_table_of_contents(lessonplan, "table_of_contents.pdf")
        for chapter in lessonplan[2:3]:
            # print(f"Chapter: {chapter['chapter']}")
    
        # Loop through each lesson in the chapter
            for lesson in chapter['lessons']:
                # print(f"  - {lesson}")
                lessons = chapter["chapter"] + ":"  + lesson
                pdf_path = generate_pdf_lesson(lessons, lesson)
                print(lesson)

        merged_pdf_path = merge_pdfs(f"""{title}Textbook.pdf""")
        
        if merged_pdf_path and os.path.exists(merged_pdf_path):
            return jsonify({"pdf_url": f"/static/{title}Textbook.pdf"})
        else:
            return jsonify({"error": "PDF file was not created successfully."}), 500'''

    except Exception as e:
        print(f"Error: {e}")
        return ({"answer": "An error occurred while processing your request. Please try again later!"}), 500





@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        lessonplan = data.get('lessonplan', [])
        title = data.get('title', '')
        selected_sections = data.get('selected_sections', [])
        practice_problem_count = data.get('practice_problem_count', 10)

        print(title)
        
        if not lessonplan or not title:
            return jsonify({"error": "Missing lesson plan or title"}), 400

        # If lessonplan is a string (JSON), parse it
        if isinstance(lessonplan, str):
            try:
                lessonplan = json.loads(lessonplan)
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid JSON for lesson plan"}), 400

        print(lessonplan)
        clear_static_folder()
        author = "MathTutor"
        create_title_page(title, author)

        generate_table_of_contents(lessonplan, "table_of_contents.pdf")

        generate_lesson_pdf(lessonplan, output_path="static/ChapterOverview.pdf")
        pdf_index = 0
        lesson_links = {}
        for chapter in lessonplan:
            for lesson in chapter['lessons']:
                lesson_title = f"{chapter['chapter']}: {lesson["lesson"]}"

                generate_pdf_lesson(lesson_title, lesson["lesson"], pdf_index, selected_sections, practice_problem_count)
                pdf_index += 1
        
        main_pdf_path = f"static/{title}Content.pdf"
        glossary_pdf_path = "static/glossary.pdf"
        final_merged_path = f"static/{title}Textbook.pdf"



        text = extract_text_from_pdf("static/ChapterOverview.pdf")
        if text:
            preprocessed_text = preprocess_text(text)
            glossary_response = generate_glossary(preprocessed_text)
            glossary = create_glossary_entries(glossary_response)
    
            # Generate the PDF glossary
            create_pdf_glossary(glossary, glossary_pdf_path)
            print(f"Glossary PDF created at: {glossary_pdf_path}")
        else:
            print("Failed to extract text from the PDF.")
        print("Finished")
        # merge_with_glossary(main_pdf_path, glossary_pdf_path, final_merged_path)
        merged_pdf_path = merge_pdfs(lessonplan,f"{title}Textbook.pdf", title)
        
        if merged_pdf_path and os.path.exists(merged_pdf_path):
            return jsonify({"pdf_url": f"/static/{title}Textbook.pdf"})
        else:
            return jsonify({"error": "PDF file was not created successfully."}), 500

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)







