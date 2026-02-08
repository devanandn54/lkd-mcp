# linkedin_scraper.py - Simple LinkedIn Profile Scraper API
import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get LinkedIn cookie from environment
LINKEDIN_COOKIE = os.getenv('LINKEDIN_COOKIE', '')

class ScrapeRequest(BaseModel):
    profile_url: str

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    method: str
    params: Dict[str, Any]

@app.get("/")
async def health():
    return {"status": "ok", "service": "LinkedIn Scraper"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/scrape")
async def scrape_profile(request: ScrapeRequest):
    """Direct scraping endpoint"""
    try:
        profile_data = await scrape_linkedin_profile(request.profile_url)
        return {"success": True, "data": profile_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """MCP-compatible endpoint"""
    try:
        if request.method == "tools/call":
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments", {})
            
            if tool_name == "get_person_profile":
                profile_url = arguments.get("profile_url")
                if not profile_url:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.id,
                        "error": {"message": "profile_url required"}
                    }
                
                profile_data = await scrape_linkedin_profile(profile_url)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "result": profile_data
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "error": {"message": f"Unknown tool: {tool_name}"}
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"message": f"Unknown method: {request.method}"}
            }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {"message": str(e)}
        }

async def scrape_linkedin_profile(url: str) -> dict:
    """Scrape LinkedIn profile using Playwright"""
    
    if not LINKEDIN_COOKIE:
        raise Exception("LINKEDIN_COOKIE not configured")
    
    # Add anti-ban delay
    await asyncio.sleep(2 + asyncio.get_event_loop().time() % 3)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Set LinkedIn cookie
        await context.add_cookies([{
            'name': 'li_at',
            'value': LINKEDIN_COOKIE,
            'domain': '.linkedin.com',
            'path': '/'
        }])
        
        page = await context.new_page()
        
        try:
            # Navigate to profile
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for profile to load
            await page.wait_for_selector('h1', timeout=10000)
            
            # Extract data
            profile_data = {
                'name': '',
                'headline': '',
                'location': '',
                'about': '',
                'experience': [],
                'education': [],
                'skills': [],
                'url': url
            }
            
            # Name
            try:
                name_el = await page.query_selector('h1')
                if name_el:
                    profile_data['name'] = (await name_el.inner_text()).strip()
            except:
                pass
            
            # Headline
            try:
                headline_el = await page.query_selector('.text-body-medium')
                if headline_el:
                    profile_data['headline'] = (await headline_el.inner_text()).strip()
            except:
                pass
            
            # Location
            try:
                location_el = await page.query_selector('.text-body-small.inline')
                if location_el:
                    profile_data['location'] = (await location_el.inner_text()).strip()
            except:
                pass
            
            # About
            try:
                about_section = await page.query_selector('#about')
                if about_section:
                    about_parent = await about_section.query_selector('..')
                    if about_parent:
                        about_container = await about_parent.query_selector('.inline-show-more-text')
                        if about_container:
                            profile_data['about'] = (await about_container.inner_text()).strip()
            except:
                pass
            
            # Experience
            try:
                exp_items = await page.query_selector_all('#experience ~ .pvs-list__container li')
                for item in exp_items[:5]:  # Top 5 experiences
                    try:
                        text = (await item.inner_text()).strip()
                        if text and len(text) > 10:
                            profile_data['experience'].append(text)
                    except:
                        continue
            except:
                pass
            
            # Education
            try:
                edu_items = await page.query_selector_all('#education ~ .pvs-list__container li')
                for item in edu_items[:3]:  # Top 3 schools
                    try:
                        text = (await item.inner_text()).strip()
                        if text and len(text) > 5:
                            profile_data['education'].append(text)
                    except:
                        continue
            except:
                pass
            
            # Skills
            try:
                skill_items = await page.query_selector_all('.pvs-list__container--skill .pvs-entity__path-text')
                for skill in skill_items[:10]:  # Top 10 skills
                    try:
                        text = (await skill.inner_text()).strip()
                        if text:
                            profile_data['skills'].append(text)
                    except:
                        continue
            except:
                pass
            
            return profile_data
            
        finally:
            await browser.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)