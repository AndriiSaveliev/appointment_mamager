# Appointment Manager (Google Vision Version)

This is the Google Vision + GPT version of the Appointment Manager project. It allows you to scan appointment cards or business cards and automatically extract appointment information. Features include OCR with Google Vision API to extract text from images, including printed and handwritten text, GPT parsing to generate structured fields like description, date, time, and location, regex fallback to ensure date, time, and location are captured even if GPT misses them, and a Tkinter GUI that allows the user to review and edit extracted appointment data before saving.

Installation:

1. Clone the repository and switch to the google_vision branch:
git clone https://github.com/YourUsername/appointment_mamager.git
cd appointment_mamager
git checkout google_vision

2. Install dependencies:
pip install -r requirements.txt

3. Set environment variables:
export OPENAI_API_KEY="your_openai_api_key"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/appointmentocr-31a64892c109.json"

Usage:

1. Run the script:
python main.py

2. Select an appointment card image.
3. The Google Vision API will extract text from the image.
4. GPT will parse the extracted text into structured fields: date, time, location, description.
5. A Tkinter GUI will allow you to review and edit the extracted data before saving.
6. All appointments will be printed in the console.

Dependencies:

Python 3.11+, google-cloud-vision, openai, python-dotenv, tkinter (standard library)

Notes:

Billing is required: Google Vision API requires a billing account enabled. Sensitive keys such as .env or JSON key files should not be committed to GitHub.

License:

MIT License