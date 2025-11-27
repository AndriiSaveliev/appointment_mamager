from google.cloud import vision
import os

print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

client = vision.ImageAnnotatorClient()
print("Google Vision client created successfully!")