from tkinter import Tk, filedialog, Label, Entry, Button
import easyocr
import openai
import json
import os
import re
from dotenv import load_dotenv

# -------------------------
# Load OpenAI API key
# -------------------------
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("API key not found. Create a .env file with OPENAI_API_KEY.")
openai.api_key = openai_api_key

# -------------------------
# AppointmentCard class
# -------------------------
class AppointmentCard:
    def __init__(self, date, time, location, description):
        self.date = date
        self.time = time
        self.location = location
        self.description = description

    def __str__(self):
        return f"{self.date} {self.time} | {self.location} | {self.description}"

# -------------------------
# User class
# -------------------------
class User:
    def __init__(self, name):
        self.name = name
        self.appointments = []

    def add_appointment(self, appointment):
        self.appointments.append(appointment)
        print(f"Appointment added: {appointment}")

# -------------------------
# OCR Scanner
# -------------------------
class OCRScanner:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])

    def scan(self, image_path):
        result = self.reader.readtext(image_path)
        text = " ".join([t[1] for t in result])
        return text

# -------------------------
# Preprocess OCR text
# -------------------------
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9: /.,-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# -------------------------
# Extract date/time via regex
# -------------------------
def extract_date_time(text):
    time_match = re.search(r'\b\d{1,2}[:.]\d{2}\s*(AM|PM|am|pm)\b', text)
    time = time_match.group() if time_match else ""

    date_match = re.search(r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2} \d{4}\b)|(\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b)', text)
    date = date_match.group() if date_match else ""

    return date, time

# -------------------------
# Extract location via improved regex
# -------------------------
def extract_location(text):
    match = re.search(r'([A-Z\s]*(CLINIC|DENTAL|HOSPITAL)[A-Z\s]*)', text, re.IGNORECASE)
    return match.group().strip() if match else ""

# -------------------------
# GPT parser for description
# -------------------------
def parse_text_with_gpt(text):
    prompt = f"""
You are an assistant that extracts appointment information from text.
Recognize:
- description (purpose of appointment)
Return JSON with keys: date, time, location, description.
Text: {text}
"""
    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        data = json.loads(response.choices[0].message.content)
    except:
        data = {"date": "", "time": "", "location": "", "description": ""}
    return data

# -------------------------
# GUI form
# -------------------------
def show_edit_form(user, initial_data):
    root = Tk()
    root.title("Edit Appointment Details")

    Label(root, text="Date:").grid(row=0, column=0)
    date_entry = Entry(root, width=30)
    date_entry.grid(row=0, column=1)
    date_entry.insert(0, initial_data.get("date") or "")

    Label(root, text="Time:").grid(row=1, column=0)
    time_entry = Entry(root, width=30)
    time_entry.grid(row=1, column=1)
    time_entry.insert(0, initial_data.get("time") or "")

    Label(root, text="Location:").grid(row=2, column=0)
    location_entry = Entry(root, width=30)
    location_entry.grid(row=2, column=1)
    location_entry.insert(0, initial_data.get("location") or "")

    Label(root, text="Description:").grid(row=3, column=0)
    description_entry = Entry(root, width=50)
    description_entry.grid(row=3, column=1)
    description_entry.insert(0, initial_data.get("description") or "")

    def add_appointment():
        appt = AppointmentCard(
            date_entry.get(),
            time_entry.get(),
            location_entry.get(),
            description_entry.get()
        )
        user.add_appointment(appt)
        root.destroy()

    Button(root, text="Add Appointment", command=add_appointment).grid(row=4, column=1)
    root.mainloop()

# -------------------------
# Main
# -------------------------
def main():
    user = User("Andrii")

    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select an appointment card image",
        filetypes=[("Image files", "*.jpg *.jpeg *.png")]
    )
    if not file_path:
        print("No file selected.")
        return

    # OCR
    scanner = OCRScanner()
    ocr_text = scanner.scan(file_path)
    print("\nText extracted from image:")
    print(ocr_text)

    # Preprocess text
    clean_text_data = preprocess_text(ocr_text)

    # Extract date, time, location
    date, time = extract_date_time(ocr_text)
    location = extract_location(ocr_text)

    # GPT parsing (description)
    parsed_data = parse_text_with_gpt(clean_text_data)

    # Fill missing fields from regex
    if not parsed_data.get("date"):
        parsed_data["date"] = date
    if not parsed_data.get("time"):
        parsed_data["time"] = time
    if not parsed_data.get("location"):
        parsed_data["location"] = location

    # If description is empty, fill with default
    if not parsed_data.get("description"):
        parsed_data["description"] = "General appointment"

    print("\nParsed data from GPT + regex fallback:")
    print(parsed_data)

    # GUI for editing
    show_edit_form(user, parsed_data)

    # Display all appointments
    print("\nAll appointments for the user:")
    for a in user.appointments:
        print(a)

if __name__ == "__main__":
    main()