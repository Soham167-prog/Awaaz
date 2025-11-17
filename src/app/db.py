import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, TypeVar, Type, Union
from datetime import datetime
from .models import (
    Complaint, Report, User, 
    ComplaintStatus, ReportStatus, UserStatus,
    ComplaintCategory, ReportReason
)

T = TypeVar('T')

class Database:
    def __init__(self, db_dir: str = 'data'):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(exist_ok=True)
        self.complaints_file = self.db_dir / 'complaints.json'
        self.reports_file = self.db_dir / 'reports.json'
        self.users_file = self.db_dir / 'users.json'
        self._initialize_files()

    def _initialize_files(self):
        for file in [self.complaints_file, self.reports_file, self.users_file]:
            if not file.exists():
                file.write_text('[]')

    def _read_file(self, file_path: Path, model: Type[T]) -> List[T]:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return [model(**item) for item in data]
        except json.JSONDecodeError:
            return []

    def _write_file(self, file_path: Path, data: List[Any]):
        with open(file_path, 'w') as f:
            json.dump([item.dict() for item in data], f, default=str)

    # Complaint methods
    def create_complaint(self, complaint: Complaint) -> Complaint:
        complaints = self._read_file(self.complaints_file, Complaint)
        complaints.append(complaint)
        self._write_file(self.complaints_file, complaints)
        return complaint

    def get_complaint(self, complaint_id: str) -> Optional[Complaint]:
        complaints = self._read_file(self.complaints_file, Complaint)
        for complaint in complaints:
            if complaint.id == complaint_id:
                return complaint
        return None

    def update_complaint(self, complaint_id: str, **updates) -> Optional[Complaint]:
        complaints = self._read_file(self.complaints_file, Complaint)
        for i, complaint in enumerate(complaints):
            if complaint.id == complaint_id:
                updated = complaint.dict()
                updated.update(updates)
                complaints[i] = Complaint(**updated)
                self._write_file(self.complaints_file, complaints)
                return complaints[i]
        return None

    def get_complaints(
        self, 
        user_id: Optional[str] = None,
        status: Optional[ComplaintStatus] = None,
        category: Optional[ComplaintCategory] = None,
        limit: int = 50
    ) -> List[Complaint]:
        complaints = self._read_file(self.complaints_file, Complaint)
        
        if user_id:
            complaints = [c for c in complaints if c.created_by == user_id]
        if status:
            complaints = [c for c in complaints if c.status == status]
        if category:
            complaints = [c for c in complaints if c.category == category]
            
        return sorted(complaints, key=lambda x: x.created_at, reverse=True)[:limit]

    # Report methods
    def create_report(self, report: Report) -> Report:
        reports = self._read_file(self.reports_file, Report)
        complaints = self._read_file(self.complaints_file, Complaint)
        users = self._read_file(self.users_file, User)
        
        # Add report to reports
        reports.append(report)
        self._write_file(self.reports_file, reports)
        
        # Update complaint's reports list
        for complaint in complaints:
            if complaint.id == report.complaint_id:
                complaint.add_report(report.id)
                # Update the complaint in the database
                self._write_file(self.complaints_file, complaints)
                
                # Increment reported_by_others count for the user who created the complaint
                for user in users:
                    if user.id == complaint.created_by:
                        user.increment_reported_count()
                        self._write_file(self.users_file, users)
                        break
                break
                
        return report

    def get_reports(
        self, 
        complaint_id: Optional[str] = None, 
        status: Optional[ReportStatus] = None,
        reported_by: Optional[str] = None
    ) -> List[Report]:
        reports = self._read_file(self.reports_file, Report)
        
        if complaint_id:
            reports = [r for r in reports if r.complaint_id == complaint_id]
        if status:
            reports = [r for r in reports if r.status == status]
        if reported_by:
            reports = [r for r in reports if r.reported_by == reported_by]
            
        return reports

    def update_report(self, report_id: str, **updates) -> Optional[Report]:
        reports = self._read_file(self.reports_file, Report)
        for i, report in enumerate(reports):
            if report.id == report_id:
                updated = report.dict()
                updated.update(updates)
                reports[i] = Report(**updated)
                self._write_file(self.reports_file, reports)
                return reports[i]
        return None

    # User methods
    def create_user(self, user: User) -> User:
        users = self._read_file(self.users_file, User)
        users.append(user)
        self._write_file(self.users_file, users)
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        users = self._read_file(self.users_file, User)
        for user in users:
            if user.id == user_id:
                return user
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        users = self._read_file(self.users_file, User)
        for user in users:
            if user.username.lower() == username.lower():
                return user
        return None

    def update_user(self, user_id: str, **updates) -> Optional[User]:
        users = self._read_file(self.users_file, User)
        for i, user in enumerate(users):
            if user.id == user_id:
                updated = user.dict()
                updated.update(updates)
                users[i] = User(**updated)
                self._write_file(self.users_file, users)
                return users[i]
        return None

    def warn_user(self, user_id: str, reason: str = None) -> Optional[User]:
        user = self.get_user(user_id)
        if not user:
            return None
            
        warnings = user.warnings + 1
        status = user.status
        
        if warnings >= 5:
            status = UserStatus.BANNED
        elif warnings >= 3:
            status = UserStatus.TEMPORARILY_SUSPENDED
        elif warnings >= 1:
            status = UserStatus.WARNED
            
        return self.update_user(
            user_id,
            warnings=warnings,
            status=status,
            last_warning=datetime.now(),
            warning_reason=reason
        )

    def ban_user(self, user_id: str, reason: str = None) -> Optional[User]:
        return self.update_user(
            user_id, 
            status=UserStatus.BANNED,
            banned_at=datetime.now(),
            ban_reason=reason
        )
        
    def get_user_complaints(self, user_id: str) -> List[Complaint]:
        """Get all complaints created by a user"""
        return self.get_complaints(user_id=user_id)
        
    def get_user_reports(self, user_id: str) -> List[Report]:
        """Get all reports submitted by a user"""
        return self.get_reports(reported_by=user_id)

# Initialize database
db = Database()
