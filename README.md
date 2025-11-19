# Awaaz - AI-Powered Pothole Detection and Reporting System

Awaaz is a Django application that uses computer vision to detect potholes, classify severity levels, and streamline the lifecycle of citizen complaints. The platform now includes dedicated experiences for citizens, government officials, and administrators.

## Key Features

- AI-driven severity prediction with confidence scores
- Citizen portal for submitting pothole complaints with images, location, and AI-generated descriptions
- Public feed with filtering, searching, upvoting, and reporting of inaccuracies
- Role-based access: citizen, government, and admin interfaces
- Government users can mark complaints as resolved, leave official updates, and publish announcements
- Custom admin workspace for moderation, user management, and report reviews
- Notification system for warnings, bans, and resolution updates

## Technology Stack

- Backend: Django 5.x, Django REST Framework
- AI/ML: PyTorch, Torchvision
- Frontend: Tailwind CSS, vanilla JavaScript
- Database: SQLite (dev), MongoDB optional for media storage
- Authentication: Django auth with role-based decorators

## Installation

Prerequisites:
- Python 3.10+
- pip
- Git

Steps:

```bash
git clone <repository-url>
cd Awaaz
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Access points:
- Citizen portal: http://127.0.0.1:8000/
- Government dashboard: http://127.0.0.1:8000/gov/
- Custom admin workspace: http://127.0.0.1:8000/custom-admin/

## Usage Guide

### Citizens
1. Visit `/new/` to upload a pothole image.
2. Review AI-generated severity, confidence, and suggested description.
3. Publish the report to the public feed at `/feed/`.
4. Upvote important complaints, leave comments, or flag inaccurate entries.

### Government Officials
1. Log in via credentials provisioned by an admin.
2. Use `/gov/` to view pending and resolved complaints.
3. Mark issues as resolved and add official comments.
4. Publish announcements that appear in the dedicated announcements feed.

### Administrators
1. Sign in at `/custom-admin/`.
2. Moderate complaints, manage reports, promote/demote government users.
3. Issue warnings, temporary bans, or permanent bans with automatic notifications.
4. Monitor government announcements and overall platform health.

## AI Model Overview

- Input: RGB pothole images (JPG/PNG)
- Output: Severity class (minor, moderate, severe, critical) + confidence
- Model: ResNet-based classifier fine-tuned on labeled datasets
- Training script: `src/train/train.py`
- Configurable data augmentation, class balancing, and evaluation metrics

### Model Training

```bash
cd src/train
python train.py \
  --data-dir ../../dataset \
  --epochs 30 \
  --batch-size 32
```

Results (accuracy, confusion matrix, classification reports) are stored under `logs/`.

## Project Structure

```
Awaaz/
├── awaaz_web/          # Django settings and URLs
├── complaints/         # Core web app (models, views, templates)
├── src/                # AI training utilities
├── templates/          # HTML templates (citizen, gov, admin)
├── static/             # CSS, JS, assets
├── media/              # Uploaded complaints
├── requirements.txt
└── manage.py
```

## Configuration Tips

- Set environment variables (or `.env`) for `SECRET_KEY`, `DEBUG`, DB credentials.
- MongoDB is optional; configure `MONGO_URI` if storing media in GridFS.
- Context processor (`complaints.context_processors.role_context`) exposes role flags and unread notifications to templates.

## Deployment Notes

1. Set `DEBUG=False` and configure `ALLOWED_HOSTS`.
2. Collect static files: `python manage.py collectstatic`.
3. Use production-ready WSGI server (Gunicorn/Uvicorn) + reverse proxy.
4. Configure persistent storage for media and, if used, MongoDB.

## Contribution Workflow

1. Fork and create a feature branch.
2. Keep code formatted and linted.
3. Add tests where practical.
4. Submit a pull request with a concise summary.

## Troubleshooting

- **Login Issues**: Ensure the correct role and credentials; admins must be `is_staff`.
- **AI Model Missing**: Confirm checkpoints exist in `checkpoints/`.
- **Static Files Missing**: Run `collectstatic` or ensure Tailwind CDN loads.
- **Database Errors**: Run migrations and confirm SQLite file permissions.

## Roadmap Highlights

- Mobile-first responsive redesign
- Live push notifications per role
- Integration with municipal ticketing systems
- Multi-language interface
- Scheduled retraining with active learning

## License

This project is licensed under the MIT License (see LICENSE).
