from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import base64
import uuid
from werkzeug.utils import secure_filename
from openai import OpenAI
import logging
from typing import Dict, Any
import re
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'avif'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize OpenAI client
load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY') 
if not API_KEY:
    logger.error("OPENAI_API_KEY environment variable not set")
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=API_KEY)
MODEL_NAME = "gpt-4o"

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_license_plate_text(text: str) -> str:
    """Clean and format license plate text"""
    if not text:
        return ""
    
    # Remove extra whitespace and convert to uppercase
    cleaned = text.strip().upper()
    
    # Remove common OCR artifacts and non-alphanumeric characters
    cleaned = re.sub(r'[^\w\s]', '', cleaned)

    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove spaces between characters that are likely part of the same plate number
    if len(cleaned.replace(' ', '')) <= 10:  # Typical plate length
        cleaned = cleaned.replace(' ', '')
    
    return cleaned.strip()

def detect_license_plate(image_path: str) -> Dict[str, Any]:
    """
    Reads an image and extracts license plate number using GPT-4o Vision
    """
    try:
        # Load and base64-encode the image
        with open(image_path, "rb") as img_file:
            b64_image = base64.b64encode(img_file.read()).decode("utf-8")

        prompt = (
            "You are an expert in license plate recognition. "
            "Analyze the given image carefully and extract any visible license plate numbers or text. "
            "Look for rectangular plates on vehicles that contain letters, numbers, or a combination of both. "
            "Return ONLY the license plate text/number that you can clearly read. "
            "If you see multiple plates, separate them with commas. "
            "If no license plate is visible or readable, respond with 'NO_PLATE_FOUND'. "
            "Be very careful to read the characters accurately - distinguish between similar characters like 0/O, 1/I, 8/B, 5/S, etc. "
            "Return only the plate text without any additional explanation or formatting."
        )

        # Create chat completion with image input
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a specialized license plate OCR assistant. Return only the plate text or 'NO_PLATE_FOUND'."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                ]}
            ],
            temperature=0,
            max_tokens=50
        )
        
        # Extract the license plate text
        plate_text = response.choices[0].message.content.strip()
        
        # Check if plate was found
        plate_found = plate_text.upper() != 'NO_PLATE_FOUND'
        
        # Clean the text if plate was found
        if plate_found:
            cleaned_text = clean_license_plate_text(plate_text)
            if not cleaned_text:
                plate_found = False
                plate_text = 'NO_PLATE_FOUND'
            else:
                plate_text = cleaned_text
        
        return {
            'success': True,
            'plate_number': plate_text if plate_found else None,
            'raw_text': response.choices[0].message.content.strip(),
            'plate_found': plate_found,
            'message': 'License plate detected successfully' if plate_found else 'No license plate found in image'
        }
        
    except Exception as e:
        logger.error(f"Error detecting license plate: {str(e)}")
        return {
            'success': False,
            'error': f"License plate detection failed: {str(e)}",
            'plate_number': None,
            'plate_found': False,
            'message': 'License plate detection failed due to an error'
        }

def describe_car_damage(image_path: str) -> Dict[str, Any]:
    """
    Reads an image of a car, sends it to GPT-4o Vision, and returns 
    a detailed analysis of any damage found.
    """
    try:
        # Load and base64-encode the image
        with open(image_path, "rb") as img_file:
            b64_image = base64.b64encode(img_file.read()).decode("utf-8")

        # Instructional prompt
        prompt = (
            "You are an expert in vehicle damage assessment. "
            "Analyze the given image carefully and describe any visible damage to the vehicle in **one short, clear sentence**. "
            "Identify and report specific types of damage, such as **dents, scratches, cracks, broken parts, paint damage, paint chips, scuffs, gouges, and frame misalignment.** "
            "Use only these severity levels:\n"
            "- Minor: purely cosmetic damage such as superficial scratches, light scuffs, small paint chips, or shallow dents that do not deform the panel shape.\n"
            "- Major: any deeper or structural damage such as deep gouges, large or warped dents, cracks in glass or plastic, broken or missing parts, frame misalignment, or anything that could impair function.\n"
            "Also mention the **exact location** on the vehicle (e.g., 'rear bumper, left side'). "
            "Your response must follow this format: '<Severity> <type(s) of damage> on the <location>'. "
            "**Examples:**\n"
            "- Minor scratch on front bumper right side.\n"
            "- Moderate dent on left door lower panel.\n"
            "- Major crack on windshield.\n"
            "- Major broken side mirror.\n"
            "- no damage found\n\n"
            "If no damage is visible, respond exactly with: **'no damage found'**. "
            "Be objective and do not describe anything other than visible vehicle damage."
        )

        # Create chat completion with image input
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for car damage inspection."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                ]}
            ],
            temperature=0,
            max_tokens=50
        )
        
        # Extract the analysis
        damage_description = response.choices[0].message.content.strip()
        
        return {
            'success': True,
            'description': damage_description,
            'has_damage': 'no damage found' not in damage_description.lower()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return {
            'success': False,
            'error': f"Analysis failed: {str(e)}",
            'description': 'Analysis failed due to an error',
            'has_damage': False
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze-damage', methods=['POST'])
def analyze_damage():
    """API endpoint to analyze car damage from uploaded image"""
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No image file selected'
            }), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload an image file.'
            }), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Save file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        try:
            # Analyze the image
            result = describe_car_damage(file_path)
            
            # Clean up temporary file
            os.remove(file_path)
            
            return jsonify(result)
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
    except Exception as e:
        logger.error(f"Error in analyze_damage endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/detect-license-plate', methods=['POST'])
def detect_license_plate_endpoint():
    """API endpoint to detect and extract license plate number from uploaded image"""
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No image file selected'
            }), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload an image file.'
            }), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Save file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        try:
            # Detect license plate
            result = detect_license_plate(file_path)
            print("Number plate:", result)
            
            # Clean up temporary file
            os.remove(file_path)
            
            return jsonify(result)
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
    except Exception as e:
        logger.error(f"Error in detect_license_plate endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/full-analysis', methods=['POST'])
def full_analysis():
    """API endpoint to perform both damage analysis and license plate detection"""
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No image file selected'
            }), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload an image file.'
            }), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Save file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        try:
            # Perform both analyses
            damage_result = describe_car_damage(file_path)
            plate_result = detect_license_plate(file_path)
            
            # Clean up temporary file
            os.remove(file_path)
            
            # Combine results
            combined_result = {
                'success': True,
                'damage_analysis': damage_result,
                'license_plate': plate_result,
                'timestamp': str(uuid.uuid4())  
            }
            
            return jsonify(combined_result)
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
    except Exception as e:
        logger.error(f"Error in full_analysis endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Car Damage Assessment & License Plate Detection API',
        'version': '1.1.0',
        'endpoints': {
            'damage_analysis': '/api/analyze-damage',
            'license_plate_detection': '/api/detect-license-plate',
            'full_analysis': '/api/full-analysis'
        }
    })

if __name__ == '__main__':
    # Ensure required environment variables are set
    if not API_KEY:
        print("Error: Please set the OPENAI_API_KEY environment variable")
        exit(1)
    
    print("🚗 Car Damage Assessment & License Plate Detection API Starting...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"🤖 Using OpenAI model: {MODEL_NAME}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)