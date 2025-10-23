# Awaaz - AI-Powered Pothole Detection and Reporting System

A Django-based web application that uses artificial intelligence to detect, classify, and report potholes in road images, empowering citizens to improve road safety in their communities.

## 🚀 Features

- **🤖 AI-Powered Detection**: Advanced neural network automatically detects and classifies pothole severity
- **📱 Citizen Reporting**: Intuitive interface for uploading images and reporting road issues
- **📊 Severity Classification**: Automatic categorization into minor, moderate, or severe potholes
- **🌍 Public Feed**: View and track all reported potholes with location-based filtering
- **👨‍💼 Admin Dashboard**: Comprehensive administrative interface for managing reports
- **📍 Location-Based Filtering**: Filter reports by specific locations or areas
- **🎯 Personalized AI Text**: Context-aware complaint generation based on severity levels

## 🛠 Technology Stack

- **Backend**: Django 4.0+
- **AI/ML**: PyTorch, Torchvision
- **Image Processing**: Pillow
- **Database**: SQLite (development), MongoDB (production)
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
- **Authentication**: Django's built-in user authentication

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip
- Git

### Setup Instructions

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Awaaz
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run database migrations:**
```bash
python manage.py migrate
```

5. **Create a superuser account:**
```bash
python manage.py createsuperuser
```

6. **Start the development server:**
```bash
python manage.py runserver
```

7. **Access the application:**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - Django admin: http://127.0.0.1:8000/django-admin/

## 🎯 Usage

### For Citizens
1. **Report a Pothole**: 
   - Navigate to `/new/` to upload an image
   - The AI will automatically analyze and classify the pothole
   - Add location details and submit your report

2. **View Reports**: 
   - Visit `/feed/` to see all public reports
   - Filter by severity, location, or search terms
   - Upvote important reports

### For Administrators
1. **Admin Access**: 
   - Login at `/admin/` with admin credentials
   - Manage all reports and system settings
   - Delete inappropriate or resolved reports

2. **Report Management**:
   - View detailed analytics
   - Filter reports by various criteria
   - Export data for analysis

## 🤖 AI Model

The application uses a trained neural network for pothole detection and severity classification:

- **Input**: Road images (JPG, PNG formats)
- **Output**: Severity classification (minor, moderate, severe) with confidence scores
- **Model**: Custom CNN trained on labeled pothole datasets

### Model Training
To retrain or improve the model:

1. Place your training data in the `data/` directory
2. Run the training script: `python src/train/train.py`
3. Update the model checkpoint in `checkpoints/`

## 📁 Project Structure

```
Awaaz/
├── awaaz_web/          # Django project settings
├── complaints/         # Main app for pothole reporting
├── src/               # Source code for AI model
├── templates/         # HTML templates
├── static/           # Static files (CSS, JS)
├── media/            # User uploaded files
├── requirements.txt  # Python dependencies
└── manage.py        # Django management script
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
```

### Model Configuration
Update model settings in `complaints/services.py`:
- Model checkpoint path
- Image preprocessing parameters
- Confidence thresholds

## 🚀 Deployment

### Production Setup
1. Set `DEBUG=False` in settings
2. Configure production database
3. Set up static file serving
4. Use a production WSGI server (Gunicorn)

### Docker Deployment
```bash
docker build -t awaaz-app .
docker run -p 8000:8000 awaaz-app
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📊 Performance

- **Repository Size**: ~21MB (optimized for GitHub)
- **Model Size**: ~50MB
- **Response Time**: <2 seconds for image analysis
- **Supported Formats**: JPG, PNG, JPEG

## 🐛 Troubleshooting

### Common Issues

1. **Model Loading Error**: Ensure model checkpoint exists in `checkpoints/`
2. **Image Upload Issues**: Check file permissions and media directory
3. **Database Errors**: Run `python manage.py migrate`

### Getting Help
- Check the issues section for common problems
- Create a new issue with detailed error information
- Include system information and error logs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django community for the excellent web framework
- PyTorch team for the machine learning library
- Contributors and testers who helped improve the system

## 📈 Roadmap

- [ ] Mobile app development
- [ ] Real-time notifications
- [ ] Integration with municipal systems
- [ ] Advanced analytics dashboard
- [ ] Multi-language support