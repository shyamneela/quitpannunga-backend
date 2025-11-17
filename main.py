from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from supabase import create_client, Client
import io
import csv
import pandas as pd
from datetime import datetime

app = FastAPI()

# ✅ Supabase connection
SUPABASE_URL = "https://dxnnsamsreqrxqipweni.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR4bm5zYW1zcmVxcnhxaXB3ZW5pIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1NDU5OTksImV4cCI6MjA3NzEyMTk5OX0.DFIXFpSuU9oOB9ben6qRWABbZ1AaA0XyYgW8Ex21cnw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ✅ Helper: Create HTML table
def make_table(title, data, table_name):
    if not data:
        return f"<h3>{title}</h3><p>No records found.</p>"
    headers = data[0].keys()
    rows = "".join([
        "<tr>" + "".join(f"<td>{row[h]}</td>" for h in headers) + "</tr>"
        for row in data
    ])
    header_row = "".join([f"<th>{h}</th>" for h in headers])
    return f"""
        <div style="margin-bottom:40px;">
            <h3 style='color:#2E7D32; display:flex; justify-content:space-between; align-items:center;'>
                {title}
                <div>
                    <a href="/download/{table_name}" 
                       style="background:#2E7D32;color:white;padding:6px 10px;border-radius:5px;text-decoration:none;font-size:14px;margin-right:6px;">
                       ⬇️ CSV
                    </a>
                    <a href="/download_excel/{table_name}" 
                       style="background:#1E88E5;color:white;padding:6px 10px;border-radius:5px;text-decoration:none;font-size:14px;">
                       📘 Excel
                    </a>
                </div>
            </h3>
            <table border='1' style='border-collapse:collapse;width:100%;margin-top:10px;'>
                <thead style='background:#C8E6C9'>{header_row}</thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    """


@app.get("/", response_class=HTMLResponse)
def home():
    return "<h2>✅ Admin API is running</h2><a href='/admin'>Go to Admin Dashboard</a>"


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard():
    tables = [
        ("Users", "users"),
        ("Substance Scores", "user_substance_scores"),
     #   ("Reminders", "reminders"),
     #   ("Notifications", "notifications_log"),
        ("Mood Check-ins", "mood_checkin"),
        ("Hydration Logs", "hydration_log")
    ]

    html_sections = []
    for title, table_name in tables:
        try:
            response = supabase.table(table_name).select("*").execute()
            data = response.data
            html_sections.append(make_table(title, data, table_name))
        except Exception as e:
            html_sections.append(f"<h3>{title}</h3><p style='color:red;'>⚠️ Error fetching data: {e}</p>")

    return f"""
    <html>
    <head>
        <title>QuitPannunga Admin</title>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: #f1f8e9;
                color: #1b5e20;
                padding: 40px;
            }}
            table {{
                font-size: 14px;
            }}
            th, td {{
                padding: 8px 10px;
                border: 1px solid #9ccc65;
                text-align: left;
            }}
            a:hover {{
                opacity: 0.85;
            }}
        </style>
    </head>
    <body>
        <h1>🧾 QuitPannunga Admin Dashboard</h1>
        <p>Live Supabase data — click ⬇️ CSV or 📘 Excel to export any table.</p>
        {"".join(html_sections)}
    </body>
    </html>
    """


# ✅ CSV Download Route
@app.get("/download/{table_name}")
def download_csv(table_name: str):
    try:
        response = supabase.table(table_name).select("*").execute()
        data = response.data
        if not data:
            return Response("No data found", media_type="text/plain")

        headers = data[0].keys()
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

        output.seek(0)
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{table_name}_{today}.csv"

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return Response(f"Error exporting table: {e}", media_type="text/plain")


# ✅ Excel Download Route
@app.get("/download_excel/{table_name}")
def download_excel(table_name: str):
    try:
        response = supabase.table(table_name).select("*").execute()
        data = response.data
        if not data:
            return Response("No data found", media_type="text/plain")

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Data")

        output.seek(0)
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{table_name}_{today}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return Response(f"Error exporting Excel: {e}", media_type="text/plain")