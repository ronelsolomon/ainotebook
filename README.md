Math Genius Learning Portal

This is a Flask-based web application that generates detailed math lesson plans in PDF format using LaTeX and the Groq API.

Features

Converts user-provided math topics into comprehensive lesson plans in LaTeX.

Generates structured lesson plans including explanations, graphs, practice problems, historical context, and real-world applications.

Uses pdflatex to compile LaTeX content into PDFs.

Provides a simple web interface for users to request and download lesson plans.

Prerequisites

Python 3.13

Flask

Groq API key

LaTeX distribution (including pdflatex)

Node.js (optional, for additional front-end development)

Installation

Clone this repository:

git clone git@github.com:MyEdMaster-education/MyEdMaster-contents.git
cd MyEdMaster-contents

Create a virtual environment and activate it:

python -m venv new_env
source new_env/bin/activate  # On macOS/Linux
new_env\Scripts\activate  # On Windows

Install dependencies:

pip install -r requirements.txt

Ensure pdflatex is installed and accessible:

which pdflatex  # On macOS/Linux
where pdflatex  # On Windows

If not installed, install a LaTeX distribution like TeX Live or MiKTeX.

Set up your Groq API key:

export GROQ_API_KEY="your_api_key_here"

Running the Application

Start the Flask server:

flask run --port 5003

If port 5003 is in use, choose a different port by running:

flask run --port 5004

Usage

Open http://localhost:5003 in your browser.

Enter a math topic in the input field and click "Ask Genius".

The system generates a PDF lesson plan, which can be viewed inline or downloaded.

Troubleshooting

Permission denied (publickey) when using GitHub

ssh -T git@github.com

If access is denied, ensure you have added your SSH key to GitHub.

Port 5000 is in use
Find and kill the process using:

lsof -i :5000
kill -9 <PID>

Or use a different port for Flask.

Flask command not found

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
which flask

Ensure Flask is installed in the correct environment.

Folder Structure

MyEdMaster-contents/
│── static/         # Stores generated PDFs and stylesheets
│── templates/      # HTML templates for rendering pages
│── app.py          # Main Flask application
│── requirements.txt # Python dependencies
│── README.md       # Documentation

Contributing

Fork the repository and create a new branch.

Make changes and commit with meaningful messages.

Submit a pull request for review.

License

This project is licensed under the MIT License.
