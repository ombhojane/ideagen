import re
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
from pymongo import MongoClient
from bson import ObjectId
import json
import io
from fpdf import FPDF
import os
import uvicorn
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, modify as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


# Configure static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Use environment variables for sensitive information
MONGODB_URI = "mongodb+srv://aminvasudev6:wcw9QsKgW3rUeGA4@waybillcluster.88jnvsg.mongodb.net/?retryWrites=true&w=majority&appName=waybillCluster"

# Configure Gemini
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.9, google_api_key="AIzaSyAYadY3_MQI0_RZU7_1ckpo4k2Vm13BIgU")

# Initialize MongoDB client
client = MongoClient(MONGODB_URI)
db = client["idea_generator"]
ideas_collection = db["ideas"]
reserved_ideas_collection = db["reserved_ideas"]

async def generate_ideas_async(prompt):
    prompt_template = PromptTemplate(
        input_variables=["prompt"],
        template="{prompt}"
    )
    print(prompt_template)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    response = chain.run(prompt)
    return response


def store_idea(idea, metadata):
    idea_doc = {
        "title": idea['title'],
        "description": idea['description'],
        "features": idea['features'],
        "impact": idea['impact'],
        "implementation_steps": idea['implementation_steps'],
        "tech_stack": idea['tech_stack'],
        "metadata": metadata
    }
    result = ideas_collection.insert_one(idea_doc)
    return str(result.inserted_id)

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

@app.post("/chat_with_idea")
async def chat_with_idea(request: Request):
    data = await request.json()
    query = data['query']
    idea = data['idea']
    context = f"""
    User parameters:
    Category: {data['category']}
    Proficiency: {data['proficiency']}
    Time frame: {data['time_frame']}
    Team size: {data['team_size']}
    Technical skills: {', '.join(data['technical_skills'])}
    Project goals: {', '.join(data['project_goals'])}
    Theme: {data['theme']}

    Generated idea:
    {idea}

    User query: {query}

    Please provide a helpful response to the user's query about the generated idea, taking into account the user's parameters and the idea details. 
    Format your response as plain text without any special formatting or markdown. 
    Avoid using asterisks or other symbols for emphasis. 
    Keep your response concise and to the point.
    """

    try:
        response = await generate_ideas_async(context)
        # Process the response to remove any remaining formatting
        processed_response = process_response(response)
        return {"response": processed_response}
    except Exception as e:
        print(f"Error in chat_with_idea: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")

def process_response(response):
    # Remove any asterisks
    response = response.replace('*', '')
    # Remove any markdown-style headers
    response = re.sub(r'#{1,6}\s', '', response)
    # Remove any other markdown formatting you might encounter
    # For example, removing bold and italic formatting:
    response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)
    response = re.sub(r'_(.*?)_', r'\1', response)
    # Add more substitutions as needed
    return response.strip()

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

class IdeaRequest(BaseModel):
    category: str
    proficiency: str
    time_frame: str
    team_size: int
    technical_skills: List[str]
    project_goals: List[str]
    theme: Optional[str] = None

class ReserveIdeaRequest(BaseModel):
    idea_id: str

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "name": "World"})

@app.get("/ideas")
async def ideas(request: Request):
    return templates.TemplateResponse("ideas.html", {"request": request})

@app.get("/timeline")
async def timeline(request: Request):
    return templates.TemplateResponse("timeline.html", {"request": request})

@app.get("/projects")
async def projects(request: Request):
    return templates.TemplateResponse("projects.html", {"request": request})

@app.get("/resume")
async def resume():
    return FileResponse("static/assets/Resume.pdf")

@app.get("/ideagen")
async def ideagen(request: Request):
    return templates.TemplateResponse("ideagen.html", {"request": request})

@app.post("/generate_ideas")
async def generate_ideas_route(idea_request: IdeaRequest, background_tasks: BackgroundTasks):
    reserved_ideas = get_reserved_ideas()
    reserved_ideas_prompt = "\n".join([f"- {idea['title']}: {idea['description']}" for idea in reserved_ideas])

    exclude_ideas = idea_request.exclude_ideas if hasattr(idea_request, 'exclude_ideas') else []
    exclude_ideas_prompt = "\n".join([f"- {title}" for title in exclude_ideas])

    prompt = f"""
        As an innovative tech project idea generator for university students, create 3 unique and novel project ideas based on the following parameters:
        Category: {idea_request.category}
        Proficiency level: {idea_request.proficiency}
        Time available: {idea_request.time_frame}
        Team size: {idea_request.team_size}
        Technical skills: {', '.join(idea_request.technical_skills)}
        Project goals: {', '.join(idea_request.project_goals)}
        Additional context: {idea_request.theme}
        Focus on creating truly innovative, cutting-edge ideas that push the boundaries of current technology. Consider emerging trends, potential breakthroughs, and interdisciplinary approaches.
        The following ideas have already been reserved and should not be suggested again:
        {reserved_ideas_prompt}
        Additionally, do not suggest any of these previously generated ideas:
        {exclude_ideas_prompt}
        For each idea, provide:
        1. Project title (creative and catchy)
        2. Brief description (2-3 sentences, highlighting its uniqueness)
        3. Key features or components (3-5 bullet points)
        4. Potential impact and benefits
        5. Steps to implement (5-7 high-level steps)
        6. Best tech stack to be used and why (3-5 technologies with brief explanations)
        Format the output as a JSON array with 3 objects, each representing an idea. Use the following structure:
        [
          {{
            "title": "Project Title",
            "description": "Brief description of the project",
            "features": ["Feature 1", "Feature 2", "Feature 3"],
            "impact": "Description of potential impact and benefits",
            "implementation_steps": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
            "tech_stack": [
              {{"name": "Technology 1", "reason": "Reason for using this technology"}},
              {{"name": "Technology 2", "reason": "Reason for using this technology"}},
              {{"name": "Technology 3", "reason": "Reason for using this technology"}}
            ]
          }},
          ...
        ]
        Ensure that each idea is distinct, innovative, and tailored to the specified parameters.
        Note: The output should be a JSON object that details the analysis and recommendations without including the term 'json' or any programming syntax markers.
        """

    # Run the process_and_store_ideas function asynchronously    
    background_tasks.add_task(process_and_store_ideas, prompt, idea_request)
    
    return {"message": "Ideas generation started. Please check back in a few moments."}

async def process_and_store_ideas(prompt, idea_request):
    try:
        ideas_json = await generate_ideas_async(prompt)
        ideas = json.loads(ideas_json)

        for idea in ideas:
            idea_id = store_idea(idea, {
                "category": idea_request.category,
                "proficiency": idea_request.proficiency,
                "time_frame": idea_request.time_frame,
                "technical_skills": idea_request.technical_skills,
                "team_size": idea_request.team_size,
                "project_goals": idea_request.project_goals
            })
            idea['id'] = idea_id
            print(idea)

        app.state.latest_ideas = ideas
    except Exception as e:
        print(f"Error in process_and_store_ideas: {e}")
        app.state.latest_ideas = None


@app.get("/get_latest_ideas")
async def get_latest_ideas():
    if hasattr(app.state, 'latest_ideas'):
        return app.state.latest_ideas
    else:
        return {"message": "No ideas generated yet"}

@app.post("/reserve_idea")
def reserve_idea_route(reserve_request: ReserveIdeaRequest):
    user_id = "example_user_id"  # Replace with actual user authentication
    success = reserve_idea(reserve_request.idea_id, user_id)
    return {"success": success}

@app.get("/download_pdf/{idea_id}")
def download_pdf(idea_id: str):
    idea = ideas_collection.find_one({"_id": ObjectId(idea_id)})
    if idea:
        pdf_content = create_pdf(idea)
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type='application/pdf',
            headers={"Content-Disposition": f"attachment; filename=Idea_{idea_id}.pdf"}
        )
    raise HTTPException(status_code=404, detail="Idea not found")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)