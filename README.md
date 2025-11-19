# BJTU Classroom Availability Query (BJTU 教室空闲查询)

A web application to query classroom availability at Beijing Jiaotong University (BJTU). It automatically scrapes the teaching support platform to find classrooms with the longest continuous free time for each teaching building.

## Features

-   **Auto-Login**: Automatically logs in to the BJTU teaching platform using your credentials.
-   **Auto-Week Detection**: Automatically detects the current academic week.
-   **Multi-Building Support**: Queries all available teaching buildings (e.g., 思源楼, 思源西楼, 逸夫楼, etc.).
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

## Configuration

1.  Create a `config.json` file in the root directory.
2.  Add your BJTU credentials:
    ```json
    {
        "username": "your_student_id",
        "password": "your_password"
    }
    ```
    > **Note**: `config.json` is added to `.gitignore` by default to protect your credentials.

## Usage

1.  **Start the server**:
    ```bash
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
    ```

2.  **Open the application**:
    Open your browser and navigate to `http://localhost:8000`.

3.  **Query**:
    -   Leave the week input empty and click **查询** to automatically detect the current week and find the best rooms for all buildings.
    -   Or enter a specific week number to check a future date.

## Project Structure

-   `main.py`: FastAPI backend handling scraping and logic.
-   `static/`: Frontend assets (HTML, CSS, JS).
-   `config.json`: User credentials (not committed).
-   `requirements.txt`: Python dependencies.

## License

MIT
