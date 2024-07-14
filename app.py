from flask import Flask, render_template, request, jsonify, send_file
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pymongo import MongoClient
from bson import ObjectId
import json
import base64
from fpdf import FPDF
import io

app = Flask(__name__)

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)

# Initialize MongoDB client
client = MongoClient("mongodb+srv://aminvasudev6:wcw9QsKgW3rUeGA4@waybillCluster.88jnvsg.mongodb.net/?retryWrites=true&w=majority&appName=waybillCluster")
db = client["idea_generator"]
ideas_collection = db["ideas"]
reserved_ideas_collection = db["reserved_ideas"]


def generate_ideas(prompt):
    prompt_template = PromptTemplate(
        input_variables=["prompt"],
        template="{prompt}"
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    response = chain.run(prompt)
    return response

def store_idea(idea, metadata):
    idea_doc = {
        "title": idea['title'],
        "description": idea['description'],
        "features": idea['features'],
        "impact": idea['impact'],
        "metadata": metadata
    }
    return ideas_collection.insert_one(idea_doc).inserted_id

def reserve_idea(idea_id, user_id):
    idea = ideas_collection.find_one({"_id": ObjectId(idea_id)})
    if idea:
        reserved_idea = {
            "idea_id": idea_id,
            "user_id": user_id,
            "title": idea['title'],
            "description": idea['description'],
            "features": idea['features'],
            "impact": idea['impact'],
            "metadata": idea['metadata']
        }
        reserved_ideas_collection.insert_one(reserved_idea)
        return True
    return False

def get_reserved_ideas():
    return list(reserved_ideas_collection.find({}, {"title": 1, "description": 1}))

def create_pdf(idea):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt=idea['title'], ln=1, align='C')
    pdf.multi_cell(0, 10, txt=f"Description: {idea['description']}")
    pdf.cell(200, 10, txt="Key Features:", ln=1)
    for feature in idea['features']:
        pdf.cell(200, 10, txt=f"- {feature}", ln=1)
    pdf.multi_cell(0, 10, txt=f"Potential Impact: {idea['impact']}")
    
    return pdf.output(dest='S').encode('latin-1')

@app.route('/')
def home():
    return render_template('index.html', name='World')

@app.route('/ideas')
def ideas():
    return render_template('ideas.html')

@app.route('/timeline')
def timeline():
    return render_template('timeline.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/resume')
def resume():
    return render_template('/static/assets/Resume.pdf')

@app.route('/ideagen')
def ideagen():
    return render_template('ideagen.html')

@app.route('/generate_ideas', methods=['POST'])
def generate_ideas_route():
    data = request.json
    category = data['category']
    proficiency = data['proficiency']
    time_frame = data['time_frame']
    team_size = data['team_size']
    technical_skills = data['technical_skills']
    project_goals = data['project_goals']
    theme = data['theme']

    reserved_ideas = get_reserved_ideas()
    reserved_ideas_prompt = "\n".join([f"- {idea['title']}: {idea['description']}" for idea in reserved_ideas])

    prompt = f"""
    As an innovative tech project idea generator for university students, create 3 unique and novel project ideas based on the following parameters:
    Category: {category}
    Proficiency level: {proficiency}
    Time available: {time_frame}
    Team size: {team_size}
    Technical skills: {', '.join(technical_skills)}
    Project goals: {', '.join(project_goals)}
    Additional context: {theme}

    Focus on creating truly innovative, cutting-edge ideas that push the boundaries of current technology. Consider emerging trends, potential breakthroughs, and interdisciplinary approaches.

    The following ideas have already been reserved and should not be suggested again:
    {reserved_ideas_prompt}

    For each idea, provide:
    1. Project title (creative and catchy)
    2. Brief description (2-3 sentences, highlighting its uniqueness)
    3. Key features or components (3-5 bullet points)
    4. Potential impact and benefits

    Format the output as a JSON array with 3 objects, each representing an idea. Use the following structure:
    [
      {{
        "title": "Project Title",
        "description": "Brief description of the project",
        "features": ["Feature 1", "Feature 2", "Feature 3"],
        "impact": "Description of potential impact and benefits",
      }},
      ...
    ]
    Ensure that each idea is distinct, innovative, and tailored to the specified parameters.
    Note: The output should be a JSON object that details the analysis and recommendations without including the term 'json' or any programming syntax markers.
    """

    print("Prompt:")
    print(prompt)
    ideas_json = generate_ideas(prompt)
    print("Ideas:")
    print(ideas_json)
    ideas = json.loads(ideas_json)

    for idea in ideas:
        idea_id = store_idea(idea, {
            "category": category,
            "proficiency": proficiency,
            "time_frame": time_frame,
            "technical_skills": technical_skills,
            "team_size": team_size,
            "project_goals": project_goals
        })
        idea['id'] = str(idea_id)

    return jsonify(ideas)

@app.route('/reserve_idea', methods=['POST'])
def reserve_idea_route():
    data = request.json
    idea_id = data['idea_id']
    user_id = "example_user_id"  # Replace with actual user authentication
    success = reserve_idea(idea_id, user_id)
    return jsonify({"success": success})

@app.route('/download_pdf/<idea_id>')
def download_pdf(idea_id):
    idea = ideas_collection.find_one({"_id": ObjectId(idea_id)})
    if idea:
        pdf_content = create_pdf(idea)
        return send_file(
            io.BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Idea_{idea_id}.pdf"
        )
    return "Idea not found", 404


if __name__ == '__main__':
    app.run(debug=True)