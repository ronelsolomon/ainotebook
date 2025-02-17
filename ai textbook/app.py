from flask import Flask, send_file, request,render_template_string, render_template, jsonify
import os
import subprocess
from groq import Groq

import re

# API key
client = Groq(
    api_key="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",
)

app = Flask(__name__, static_folder="static")

# Function to convert LaTeX code to PDF
def latex_to_pdf(latex_code, output_filename="output.pdf"):
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
        print(latex_code)
    else:
        print("No LaTeX code found.")

    # Path to the 'static' folder where the PDF will be saved
    static_folder = os.path.join(os.getcwd(), 'static')

    # Ensure the static folder exists
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    # Full path to the output PDF file in the static folder
    output_pdf_path = os.path.join(static_folder, output_filename)


    with open("temp.tex", "w") as f:
        f.write(latex_code)

    subprocess.run(["pdflatex", "temp.tex"])
    # Move the generated PDF to the static folder
    subprocess.run(["mv", "temp.pdf", output_pdf_path])
    

# This function will generate the LaTeX document and then create a PDF
def generate_pdf_lesson(title="Foundations of Algebra: Exponents and Order of Operations"):
    """
    Generates a LaTeX document for the lesson 'Exponents and Order of Operations'
    using Groq API and then converting it to a PDF.
    """
    promptl = f"""
    Generate a comprehensive LaTeX document on the topic "{title}" with proper formatting, mathematical notations, and interactive elements. 

    Page width margin: 1.27 cm


   The output should be meticulously structured, with each section spanning at least half a page of well-detailed content. Sections must be distinctly separated, ensuring clear readability and logical progression of information.


   Give more than 10 practice problems at the end.
    
    

    1. **Title and Metadata**
       - Title: "{title}"
       - Author: (leave blank)
       - Date: (leave blank)

    2. **Facts and Concepts**
       - Introduction to topic (definition, notation, etc.)
       - Include necessary formulas, theorems, or principles relevant to the topic with many Examples.
       - Give more explanations and examples on the topic
       - Cheat sheet-style summary for quick reference.
       - Content should span at least one full page with detailed insights.

    3. **Graphical Representation**
       - Graph More than 3 functions on the topic using  TikZ, graphicx, pgfplots(compat=1.18), tikzpicture
       - Graph functions that illustrate key concepts, demonstrating various cases, transformations, and behaviors relevant to the topic.
       - Step-by-step visualization of the calculations
       - Provide step-by-step visualizations that illustrate calculations, transformations, and intermediate steps involved in solving problems related to the topic.
       - Provide a word description for each graph

    4. **Strategies and Procedures**
       - Step-by-step approach to solving topics in different ways
       - Use problem-solving techniques that ensure accuracy in applying the rules.
       - subsection: Compare traditional vs. alternative approaches, highlighting their advantages and limitations.
       - Common mistakes and misconceptions with words in detail and  how to avoid them
       - Provide detailed explanations for each example
       - Include varying levels of difficulty to cater to different learning stages

    5. **Vocabulary Table**
       - Include an expanded table of key terms on the topic, etc.

    6. **Historical Context**
       - The origins of the topic
       - The introduction of modern notation on the topic
       -  Fun Facts & Trivia 
       – Include how the topic appears in movies, books, or art

    7. **Real-World Applications**
       - Financial applications: Show example problems and equations
       - Scientific applications: Show example problems and equations
       - Biological application: Show example problems and equations
       - Provide detailed explanations for each example
       - Highlight practical use cases to make the concept relatable.
       - Include practice problems with 3cm space for answers

    8. **Initial explanation**
       - Start with a clear and engaging introduction to the topic.
       - Provide context: Explain why the topic is relevant and how it connects to previous knowledge.
       - Define key concepts: Break down complex terms and ideas into simple, digestible explanations.
       - Present the learning objectives and the expected outcomes.
       - Set the tone: Create an inviting environment where students feel encouraged to ask questions and explore.
       - Use real-world analogies to make abstract concepts relatable.

    9. **Examples and demonstrations**
       - Present varied examples: Include a range of examples from basic to advanced, ensuring that different levels of learners can follow along.
       - Step-by-step demonstrations: Guide students through solving problems or applying concepts, pausing to explain each step.
       - Use visual aids (diagrams, charts, animations) to make concepts more tangible.
       - Encourage active participation: Ask questions to engage students and let them predict the next steps before revealing the solution.
       - Link theory to practice: Show how concepts are used in real-world situations, or how they fit into a broader context.
       - Provide interactive practice problems for students to solve in groups or individually, promoting hands-on learning.

    10. **Applications Activity**
       - Contextualize learning: Create activities where students can apply concepts to real-world scenarios.
       - Focus on problem-solving: Present students with authentic problems that require the application of the lesson’s content.
       - Organize activities in different formats (group discussions, case studies, role-playing, simulations) to cater to diverse learning styles.
       - Encourage collaboration: Promote teamwork in solving challenges and sharing insights.
       - Foster critical thinking: Push students to think creatively and consider alternative solutions to problems.
       - Reflect and debrief: After the activity, encourage students to discuss what worked, what didn’t, and how the lesson’s concepts were applied.
       - Provide real-time feedback and guidance during the activity to ensure students stay on track and fully understand the topic.


    11. **Common Misconceptions Table**
       - A table highlighting common student mistakes and how to correct them
       - all words on the page

    12. **Assessment Strategies**
       - Formative and summative assessments
       - Suggest different ways to test knowledge, such as quizzes, practical exercises, Self-check exercises, or problem-solving activities.
       -Provide detailed explanations for each point
       - Subsection: Hands-on Activities: Suggest real-world experiments or interactive activities that allow students to explore concepts physically

    13. **Additional Resources**
       - Websites, video tutorials, interactive tools
       -Provide detailed explanations for each resource

    14. **Rationales**
       - Why do the Steps Work?
       - Demonstrate how each step connects to the overall solution.
       - Compare different approaches and justify why a particular method is effective
       - Explain the logical reasoning behind each step in the process.
       - Provide a breakdown of the underlying principles or theories.
       - Provide detailed explanations for each point
       - Discuss the mathematical or logical reasoning behind the approach.

       

    15. **Comparison Table**
        - Create a structured comparison table comparing different methods, strategies, or approaches related to the topic. 
        - Highlight differences in efficiency, accuracy, and applicability in words.
    

    16. **Practice Problems solved step by step**
       - Showcase how to solve problems one by one
       - Give More than 3 examples
       - Give the solution and answer
       - Give the answer
       - Give spaces for the questions

    17. **Practice Problems**
       - Give more than 10 problems 
       - Give Test problems with increasing difficulty
       - Provide answers on the next page

Format the response as a complete LaTeX document with:
- At least three graphs using TikZ, graphicx, pgfplots(compat=1.18)
- Use visual aids (diagrams, tables, charts) if necessary to enhance comprehension
- At least three tables (one for vocabulary, one for common misconceptions, comparison table) Add more!
- Show the whole table and graph centered no words cut from the page
- Detailed examples and explanations
- Space out each bullet point and use \\item
- use geometry, amsmath, amssymb
- LaTeX-friendly mathematical notations
- Give no latex errors



    """

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": promptl}],
            model="llama-3.3-70b-versatile",
        )

        latex_content = response.choices[0].message.content
        print(latex_content)

        # Convert the generated LaTeX content to PDF
        pdf_filename = f"{title.replace(' ', '_')}.pdf"
        latex_to_pdf(latex_content, pdf_filename)

        # Return the path of the generated PDF file
        return pdf_filename
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None


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
def generate_pdf():
    # Generate the PDF file
    try:
        print("Hello")
        title = request.json.get("question", "").strip()
        if not title:
            return jsonify({"answer": "Please ask a question! 😅"}), 400


    # title = "Foundations of Algebra: Exponents and Order of Operations"
        pdf_path = generate_pdf_lesson(title)

        if pdf_path:
        # Serve the PDF file as a downloadable file or display it inline
            return jsonify({"pdf_url": f"/static/{pdf_path}"})

    except Exception as e:
        print(f"Error: {e}")
        return ({"answer": "An error occurred while processing your request. Please try again later!"}), 500

if __name__ == '__main__':
    app.run(debug=True)







