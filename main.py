import json
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import re

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

CONFIG_FILE = "config.json"

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
    Returns: (max_length, start_index, end_index)
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
            
    # Check end of list
    if current_len > max_len:
        max_len = current_len
        best_start = start_idx
        
    return max_len, best_start

def format_time_range(start_idx, length):
    if start_idx == -1:
        return "无空闲"
    
    # 0-48 index
    # Day: index // 7 (0=Mon, 6=Sun)
    # Period: index % 7 (0=1st, 6=7th)
    
    end_idx = start_idx + length - 1
    
    start_day = (start_idx // 7) + 1
    start_period = (start_idx % 7) + 1
    
    end_day = (end_idx // 7) + 1
    end_period = (end_idx % 7) + 1
    
    # Simplified: Assuming continuous block is within a day or spans days?
    # The requirement is "continuous free time". 
    # Usually we care about continuous time within a day. 
    # But if it spans days (e.g. Mon night to Tue morning), is that useful?
    # For simplicity and utility, let's treat it as a continuous block across the week grid.
    # But displaying "Mon Period 7 to Tue Period 1" is valid.
    
    days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    
    return f"{days[start_day-1]} 第{start_period}节 - {days[end_day-1]} 第{end_period}节"

@app.post("/api/query")
def query_classrooms(request: QueryRequest):
    try:
        config = load_config()
        username = config["username"]
        password = config["password"]
        
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        # 1. Login
        login_url = "https://aa.bjtu.edu.cn/client/login/"
        
        # Get login page for CSRF
        r1 = session.get(login_url)
        soup_login = BeautifulSoup(r1.text, 'html.parser')
        csrf_input = soup_login.find("input", {"name": "csrfmiddlewaretoken"})
        csrf_token = csrf_input["value"] if csrf_input else session.cookies.get('csrftoken')
        
        login_data = {
            "loginname": username,
            "password": password,
            "csrfmiddlewaretoken": csrf_token
        }
        
        headers = {
            "Referer": login_url
        }
        
        response = session.post(login_url, data=login_data, headers=headers)
        
        if response.url == login_url or "用户登录" in response.text:
             # Check for failure more robustly
             # If we are still on login page, it failed.
             # But sometimes it redirects to notice page which is success.
             if "用户登录" in response.text and "退出" not in response.text:
                 raise HTTPException(status_code=401, detail="Login failed. Check credentials.")
             
        # 2. Fetch Data
        # If week is not provided, fetch default page to get current week
        target_week = request.week
        
        if target_week is None:
            data_url = "https://aa.bjtu.edu.cn/classroomtimeholdresult/room_view/"
        else:
            data_url = f"https://aa.bjtu.edu.cn/classroomtimeholdresult/room_view/?zc={target_week}"
            
        response = session.get(data_url)
        
        if "用户登录" in response.text:
             raise HTTPException(status_code=401, detail="Login failed. Check credentials.")
             
        # 3. Parse Initial Page to get Buildings
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to detect week if not provided
        if target_week is None:
            # ... (existing week detection logic) ...
            # Strategy 1: Check the select element
            select = soup.find("select", id="zc") # Assuming id is zc based on url param
            if select:
                selected_option = select.find("option", selected=True)
                if selected_option:
                    target_week = int(selected_option['value'])
            
            # Strategy 2: Fallback to parsing text if select fails
            if target_week is None:
                chosen = soup.find("a", class_="chosen-single")
                if chosen:
                    text = chosen.get_text(strip=True) # e.g. "第10周"
                    match = re.search(r'\d+', text)
                    if match:
                        target_week = int(match.group())
            
            # Fallback default
            if target_week is None:
                target_week = 10 # Default fallback
        
        # Get Building Options
        building_select = soup.find("select", {"name": "jxlh"})
        buildings_to_scrape = []
        
        if building_select:
            options = building_select.find_all("option")
            for opt in options:
                val = opt.get("value")
                text = opt.get_text(strip=True)
                if val and val.strip(): # Skip empty value
                    buildings_to_scrape.append({"id": val, "name": text})
        else:
            # Fallback if select not found (shouldn't happen based on debug)
            # Maybe just scrape current page as "Unknown Building"
            buildings_to_scrape.append({"id": None, "name": "当前教学楼"})

        final_response = {
            "week": target_week,
            "buildings": []
        }
        
        # Limit to a few for testing if needed, but user asked for ALL.
        # Scrape each building
        for b in buildings_to_scrape:
            b_id = b["id"]
            b_name = b["name"]
            
            # Fetch building specific page
            if b_id:
                b_url = f"https://aa.bjtu.edu.cn/classroomtimeholdresult/room_view/?zc={target_week}&jxlh={b_id}"
                # Add a small delay to be nice?
                # time.sleep(0.1) 
                resp = session.get(b_url)
                soup_b = BeautifulSoup(resp.text, 'html.parser')
            else:
                soup_b = soup # Use already fetched page
                
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
                    
                slots = []
                for i in range(1, 50):
                    style = cols[i].get("style", "").lower()
                    is_free = "background-color: #fff" in style or "background-color:#fff" in style
                    slots.append(is_free)
                    
                max_len, start_idx = calculate_longest_free(slots)
                time_range = format_time_range(start_idx, max_len)
                
                room_data = {
                    "room": room_name,
                    "max_free": max_len,
                    "time_range": time_range,
                    "slots": slots
                }
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
