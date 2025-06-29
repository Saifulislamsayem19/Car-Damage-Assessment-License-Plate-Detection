# 🚗 Car Damage Assessment & License Plate Detection 

A powerful Flask-based REST API that leverages OpenAI's GPT-4o Vision model to automatically analyze vehicle damage and detect license plates from uploaded images. Perfect for insurance companies, auto repair shops, fleet management, and vehicle inspection services.

![image](https://github.com/user-attachments/assets/8099232a-c4ad-46f0-81bb-721a5f6e26d3)


## ✨ Features

- **🔍 Intelligent Damage Assessment**: Automatically detects and categorizes vehicle damage with severity levels (Minor/Major)
- **🔢 License Plate Recognition**: Extracts license plate numbers with advanced OCR capabilities
- **📊 Comprehensive Analysis**: Single endpoint for complete vehicle inspection (damage + license plate)
- **🖼️ Multi-format Support**: Supports PNG, JPG, JPEG, GIF, BMP, WebP, and AVIF image formats
- **⚡ Fast Processing**: Optimized for quick analysis with detailed results
- **🛡️ Secure File Handling**: Temporary file storage with automatic cleanup
- **📝 Detailed Logging**: Comprehensive error tracking and request logging
- **🌐 CORS Enabled**: Ready for web application integration

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API Key
- Flask and required dependencies

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/car-damage-assessment-api.git
   cd car-damage-assessment-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create a .env file
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000`

## 🔧 API Endpoints

### Health Check
```http
GET /health
```
Returns API status and available endpoints.

### Damage Analysis Only
```http
POST /api/analyze-damage
```
Analyzes uploaded image for vehicle damage.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `image` (file)

**Response:**
```json
{
  "success": true,
  "description": "Minor scratch on front bumper right side",
  "has_damage": true
}
```

### License Plate Detection Only
```http
POST /api/detect-license-plate
```
Extracts license plate number from uploaded image.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `image` (file)

**Response:**
```json
{
  "success": true,
  "plate_number": "ABC123",
  "raw_text": "ABC123",
  "plate_found": true,
  "message": "License plate detected successfully"
}
```

### Full Analysis
```http
POST /api/full-analysis
```
Performs both damage assessment and license plate detection.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `image` (file)

**Response:**
```json
{
  "success": true,
  "damage_analysis": {
    "success": true,
    "description": "Minor scratch on front bumper right side",
    "has_damage": true
  },
  "license_plate": {
    "success": true,
    "plate_number": "ABC123",
    "plate_found": true,
    "message": "License plate detected successfully"
  },
  "timestamp": "unique-request-id"
}
```

## 💡 Usage Examples

### Using cURL

**Full Analysis:**
```bash
curl -X POST \
  http://localhost:5000/api/full-analysis \
  -H 'Content-Type: multipart/form-data' \
  -F 'image=@path/to/your/car-image.jpg'
```

**Damage Analysis Only:**
```bash
curl -X POST \
  http://localhost:5000/api/analyze-damage \
  -H 'Content-Type: multipart/form-data' \
  -F 'image=@path/to/your/car-image.jpg'
```

### Using Python Requests

```python
import requests

url = "http://localhost:5000/api/full-analysis"
files = {"image": open("car_image.jpg", "rb")}

response = requests.post(url, files=files)
result = response.json()

print(f"Damage: {result['damage_analysis']['description']}")
print(f"License Plate: {result['license_plate']['plate_number']}")
```

### Using JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);

fetch('http://localhost:5000/api/full-analysis', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Damage:', data.damage_analysis.description);
    console.log('License Plate:', data.license_plate.plate_number);
});
```

## 🔒 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |

### Application Settings

- **Max File Size**: 5MB
- **Allowed Extensions**: PNG, JPG, JPEG, GIF, BMP, WebP, AVIF
- **Temporary Upload Folder**: `temp_uploads/`
- **Default Port**: 5000

## 🎯 Damage Severity Levels

The API categorizes damage into two severity levels:

- **Minor**: Cosmetic damage (scratches, scuffs, small paint chips, shallow dents)
- **Major**: Structural damage (deep gouges, large dents, cracks, broken parts, frame misalignment)

## 🛠️ Development

### Project Structure
```
car-damage-assessment-api/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── temp_uploads/         # Temporary file storage
├── templates/            # HTML templates (if any)
└── README.md            # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Made with ❤️ for the automotive industry**
