# Valdo Asset Manager

A lightweight, full-stack Asset Management System built with Streamlit, SQLite, and Docker.

## Features
- **Asset Registry**: Manage inventory with 30+ attribute columns.
- **Master Data**: Centralized catalog for asset types.
- **Smart Automation**: Auto-increment IDs (Tags/Serials) and bulk creation.
- **Reporting**: Excel export with preserved formatting.
- **Security**: Login system and Nginx reverse proxy.

## 🚀 Quick Start (Docker)

The easiest way to run the application is using Docker.

1.  **Start the Application**:
    ```bash
    docker compose up --build -d
    ```

2.  **Access**:
    Open [http://localhost](http://localhost) in your browser.

3.  **Login**:
    - **Username**: `admin`
    - **Password**: `admin`

4.  **Stop**:
    ```bash
    docker compose down
    ```

## 🛠️ Local Development (Python)

If you want to run it without Docker:

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run**:
    ```bash
    streamlit run app.py
    ```
    Access at `http://localhost:8501`.
