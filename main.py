from tkinter import Tk, filedialog, Label, Entry, Button
from google.cloud import vision
import openai
import os
from dotenv import load_dotenv
import json
import re
from datetime import datetime

load_dotenv()

# -------------------------
# OpenAI API key
# -------------------------
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Set OPENAI_API_KEY in environment variables.")
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
# Google Vision OCR
# -------------------------
def google_vision_ocr(image_path):
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as f:
        content = f.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    else:
        return ""

# -------------------------
# Extract date, time, description via regex
# -------------------------
def parse_fields_from_text(text):
    text_clean = text.replace("\n", " ").replace("  ", " ").strip()

    # Date regex (MM-DD-YYYY or Month D YYYY or Month D)
    date_match = re.search(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+\s\d{1,2}(?:\s\d{4})?)\b', text_clean)
    if date_match:
        date_str = date_match.group()
        if not re.search(r'\b\d{4}\b', date_str):
            current_year = datetime.now().year
            date = f"{date_str} {current_year}"
        else:
            date = date_str
    else:
        date = ""

    # Time regex (HH:MM AM/PM or H AM/PM)
    time_match = re.search(r'\b\d{1,2}(:\d{2})?\s*(AM|PM|am|pm|A\.M\.|P\.M\.)\b', text_clean)
    time = time_match.group() if time_match else ""

    # Remove date and time from description
    description = text_clean
    for part in [date, time]:
        if part:
            description = description.replace(part, "")

    # Remove URLs
    description = re.sub(r'https?://\S+', '', description)
    # Remove phone numbers
    description = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '', description)
    # Remove names / known words
    description = re.sub(r'\b(Name|Date|Time|Davyd)\b', '', description, flags=re.IGNORECASE)
    # Remove addresses (numbers + street keywords)
    description = re.sub(r'\d+\s\w+(?:\s\w+)?\s(St\.?|Rd\.?|Ave\.?)', '', description, flags=re.IGNORECASE)

    # Extract key appointment words
    appointment_words = re.findall(r'\b(APPOINTMENT|DENTAL|HEALTH|VISIT|CHECKUP)\b', description, flags=re.IGNORECASE)
    seen = set()
    unique_words = []
    for w in appointment_words:
        w_upper = w.upper()
        if w_upper not in seen:
            seen.add(w_upper)
            unique_words.append(w_upper)
    description = " ".join(unique_words)
    if not description:
        description = "General appointment"

    return {"date": date, "time": time, "description": description}

# -------------------------
# GPT for location only
# -------------------------
def parse_location_with_gpt(text):
    prompt = f"""
You are an assistant that extracts the location (clinic/hospital/office name + city) from OCR text.
Return ONLY a single string containing the location.
If you cannot find it, return an empty string.

OCR Text:
\"\"\"{text}\"\"\"
"""
    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    try:
        location = response.choices[0].message.content.strip()
    except:
        location = ""
    return location

# -------------------------
# GUI
# -------------------------
def show_edit_form(user, data):
    root = Tk()
    root.title("Edit Appointment Details")

    Label(root, text="Date:").grid(row=0, column=0)
    date_entry = Entry(root, width=30)
    date_entry.grid(row=0, column=1)
    date_entry.insert(0, data.get("date") or "")

    Label(root, text="Time:").grid(row=1, column=0)
    time_entry = Entry(root, width=30)
    time_entry.grid(row=1, column=1)
    time_entry.insert(0, data.get("time") or "")

    Label(root, text="Location:").grid(row=2, column=0)
    location_entry = Entry(root, width=50)
    location_entry.grid(row=2, column=1)
    location_entry.insert(0, data.get("location") or "")

    Label(root, text="Description:").grid(row=3, column=0)
    description_entry = Entry(root, width=50)
    description_entry.grid(row=3, column=1)
    description_entry.insert(0, data.get("description") or "")

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

    # Google Vision OCR
    ocr_text = google_vision_ocr(file_path)
    print("\nText extracted from image:")
    print(ocr_text)

    # Parse fields without GPT
    parsed_data = parse_fields_from_text(ocr_text)

    # GPT only for location
    parsed_data["location"] = parse_location_with_gpt(ocr_text)

    print("\nParsed data:")
    print(parsed_data)

    # GUI to confirm/edit
    show_edit_form(user, parsed_data)

    print("\nAll appointments:")
    for a in user.appointments:
        print(a)

if __name__ == "__main__":
    main()