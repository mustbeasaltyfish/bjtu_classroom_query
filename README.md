# BJTU Classroom Availability Query (BJTU 教室空闲查询)

北京交通大学教室空闲查询工具。自动抓取教学平台数据，计算并显示各教学楼当天连续空闲时间最长的教室。

## 使用说明 (Usage)

1.  **启动服务**:
    在终端中运行：
    ```bash
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
    ```

2.  **打开应用**:
    在浏览器中访问 `http://localhost:8000`。

3.  **登录**:
    -   首次打开时会弹出登录窗口。
    -   输入你的学号和密码（默认密码通常为身份证后6位）。
    -   登录成功后，系统会自动保存会话。

4.  **查询**:
    -   **自动检测**: 留空周次输入框，直接点击“查询”，系统会自动检测当前周次并显示所有教学楼（思源楼、逸夫楼等）当天连续空闲时间最长的教室。
    -   **指定周次**: 输入特定周次数字可查询未来的空闲情况。

---

## Features

-   **UI Login**: Secure login via a popup modal on the frontend. No configuration file needed.
-   **Current Day Logic**: Calculates the longest continuous free time strictly for the **current day**, avoiding cross-day confusion.
-   **Auto-Week Detection**: Automatically detects the current academic week.
-   **Multi-Building Support**: Queries all available teaching buildings.
-   **Smart Sorting**: Prioritizes results for popular buildings (Siyuan > Siyuan East/West > Yifu).
-   **Modern UI**: Features a responsive, dark-themed interface with glassmorphism effects.

## Prerequisites

-   Python 3.8+
-   A valid BJTU student ID and password.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd bjtu_classroom_query
    ```

2.  **Create and activate a virtual environment** (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Project Structure

-   `main.py`: FastAPI backend handling scraping and logic.
-   `static/`: Frontend assets (HTML, CSS, JS).
-   `requirements.txt`: Python dependencies.

## License

MIT
