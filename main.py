import json
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import re
import datetime

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global session storage
global_session = requests.Session()
global_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

class LoginRequest(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    week: int = None # Optional

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise Exception("Config file not found")
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def get_building_name(room_name):
    prefix = room_name[:2].upper()
    mapping = {
        "SY": "思源楼",
        "SD": "思源东楼",
        "SX": "思源西楼",
        "J9": "第九教学楼",
        "J8": "第八教学楼",
        "JX": "机械楼",
        "YF": "逸夫楼",
        "DQ": "电气楼",
        "TY": "土木楼", # Guessing, can be updated
        "DY": "东校区一教", # Guessing
        "DE": "东校区二教"  # Guessing
    }
    # Handle longer prefixes or specific cases if needed
    return mapping.get(prefix, "其他教学楼")

def calculate_longest_free(slots):
    """
    slots: list of booleans (True=Free, False=Occupied)
    Returns: (max_length, start_index)
    """
    max_len = 0
    current_len = 0
    start_idx = -1
    best_start = -1
    
    for i, is_free in enumerate(slots):
        if is_free:
            if current_len == 0:
                start_idx = i
            current_len += 1
        else:
            if current_len > max_len:
                max_len = current_len
                best_start = start_idx
            current_len = 0
            start_idx = -1
            
    # Check end of list
    if current_len > max_len:
        max_len = current_len
        best_start = start_idx
        
    return max_len, best_start

def format_time_range(day_idx, start_idx, length):
    if start_idx == -1:
        return "无空闲"
    
    days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    
    # start_idx is 0-6 (within the day)
    period_start = start_idx + 1
    period_end = period_start + length - 1
    
    return f"{days[day_idx]} 第{period_start}-{period_end}节"

@app.post("/api/login")
async def login(request: LoginRequest):
    username = request.username
    password = request.password
    
    try:
        # 1. Get CSRF Token
        login_url = "https://aa.bjtu.edu.cn/client/login/"
        r1 = global_session.get(login_url)
        soup = BeautifulSoup(r1.text, 'html.parser')
        csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
        if not csrf_input:
            # Try cookie
            csrf_token = global_session.cookies.get('csrftoken')
        else:
            csrf_token = csrf_input["value"]
            
        if not csrf_token:
             raise HTTPException(status_code=500, detail="Failed to get CSRF token")

        # 2. Post Login
        login_data = {
            "loginname": username,
            "password": password,
            "csrfmiddlewaretoken": csrf_token
        }
        headers = {
            "Referer": login_url
        }
        
        r2 = global_session.post(login_url, data=login_data, headers=headers)
        
        if "用户登录" in r2.text and "注销" not in r2.text:
             # Login likely failed if we are still on login page and not logged in
             # But sometimes it redirects. Let's check if we can access a protected page?
             # Or check for specific error message
             if "用户名或密码错误" in r2.text:
                 raise HTTPException(status_code=401, detail="用户名或密码错误")
             # Assume success if redirected or no error, but let's verify with next step in query
             
        return {"message": "Login successful"}
        
    except Exception as e:
        print(f"Login Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def query_classroom(request: QueryRequest):
    target_week = request.week
    
    try:
        # Use global session
        session = global_session
        
        # Check if logged in by accessing a protected page
        # If not logged in, it usually redirects to login
        base_url = "https://aa.bjtu.edu.cn/classroomtimeholdresult/room_view/?zc=10" # Just to check
        r_check = session.get(base_url)
        if "用户登录" in r_check.text and "注销" not in r_check.text:
             raise HTTPException(status_code=401, detail="Not logged in. Please login first.")

        # ... (Rest of the logic uses 'session' which is now global_session)
        
        # 3. Parse Initial Page to get Buildings
        # We can use r_check if we didn't provide a week, or fetch specific week
        
        url = "https://aa.bjtu.edu.cn/classroomtimeholdresult/room_view/"
        if target_week:
            url += f"?zc={target_week}"
            
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to detect week if not provided
        if target_week is None:
            # ... (existing week detection logic) ...
            # Strategy 1: Check the select element
            select = soup.find("select", id="zc") 
            if select:
                selected_option = select.find("option", selected=True)
                if selected_option:
                    target_week = int(selected_option['value'])
            
            # Strategy 2: Fallback to parsing text if select fails
            if target_week is None:
                chosen = soup.find("a", class_="chosen-single")
                if chosen:
                    text = chosen.get_text(strip=True) 
                    match = re.search(r'\d+', text)
                    if match:
                        target_week = int(match.group())
            
            # Fallback default
            if target_week is None:
                target_week = 10 
        
        # Get Building Options
        building_select = soup.find("select", {"name": "jxlh"})
        buildings_to_scrape = []
        
        if building_select:
            options = building_select.find_all("option")
            for opt in options:
                val = opt.get("value")
                text = opt.get_text(strip=True)
                if val and val.strip(): 
                    buildings_to_scrape.append({"id": val, "name": text})
        else:
            buildings_to_scrape.append({"id": None, "name": "当前教学楼"})

        final_response = {
            "week": target_week,
            "buildings": []
        }
        
        # Determine current day of week (0=Mon, 6=Sun)
        current_weekday = datetime.datetime.now().weekday()
        
        # Scrape each building
        for b in buildings_to_scrape:
            b_id = b["id"]
            b_name = b["name"]
            
            # Fetch building specific page
            if b_id:
                b_url = f"https://aa.bjtu.edu.cn/classroomtimeholdresult/room_view/?zc={target_week}&jxlh={b_id}"
                resp = session.get(b_url)
                soup_b = BeautifulSoup(resp.text, 'html.parser')
            else:
                soup_b = soup 
                
            table = soup_b.find("table", class_="table-bordered")
            if not table:
                continue
                
            rows = table.find_all("tr")
            classroom_rows = rows[2:]
            
            building_rooms = []
            
            for row in classroom_rows:
                cols = row.find_all("td")
                if not cols:
                    continue
                    
                room_name_cell = cols[0]
                room_text = room_name_cell.get_text(strip=True)
                room_name = room_text.split('(')[0].strip()
                
                # Skip if no columns
                if len(cols) < 50:
                    continue
                    
                # Extract ALL slots first
                all_slots = []
                for i in range(1, 50):
                    style = cols[i].get("style", "").lower()
                    is_free = "background-color: #fff" in style or "background-color:#fff" in style
                    all_slots.append(is_free)
                
                # Filter for TODAY only
                # 49 slots = 7 days * 7 periods
                start_index = current_weekday * 7
                end_index = start_index + 7
                today_slots = all_slots[start_index:end_index]
                
                max_len, start_idx = calculate_longest_free(today_slots)
                time_range = format_time_range(current_weekday, start_idx, max_len)
                
                room_data = {
                    "room": room_name,
                    "max_free": max_len,
                    "time_range": time_range,
                    "slots": today_slots # Return only today's slots if needed by frontend, or keep all? 
                                         # Frontend doesn't use 'slots' for display, just max_free and time_range.
                }
                
                # Only add if there is some free time? Or even if 0?
                # User wants "longest continuous free time".
                building_rooms.append(room_data)
            
            if building_rooms:
                # Sort and pick best
                building_rooms.sort(key=lambda x: x["max_free"], reverse=True)
                best_room = building_rooms[0]
                
                final_response["buildings"].append({
                    "building": b_name,
                    "best_room": best_room
                })
            
        # Sort buildings by priority
        # Priority: 思源楼 > 思源东楼/思源西楼 > 逸夫楼 > Others
        priority_map = {
            "思源楼": 0,
            "思源东楼": 1,
            "思源西楼": 1, # Treat East/West as same priority level
            "逸夫楼": 2
        }
        
        def get_priority(item):
            name = item["building"]
            # Check exact match first
            if name in priority_map:
                return priority_map[name]
            # Check partial match if needed, or just default to high number
            for key, val in priority_map.items():
                if key in name:
                    return val
            return 999 # Low priority for others

        final_response["buildings"].sort(key=get_priority)
            
        return final_response

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
