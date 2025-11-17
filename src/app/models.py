from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ComplaintCategory(str, Enum):
    ROAD_ISSUE = "road_issue"
    INFRASTRUCTURE = "infrastructure"
    SANITATION = "sanitation"
    OTHER = "other"

class ComplaintStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"

class ReportReason(str, Enum):
    FALSE_INFORMATION = "false_information"
    DUPLICATE = "duplicate"
    INAPPROPRIATE = "inappropriate"
    OTHER = "other"

class ReportStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class Complaint(BaseModel):
    id: str
    title: str
    description: str
    category: ComplaintCategory
    location: Dict[str, Any]  # Could include lat, lng, address, etc.
    images: List[str]  # List of image paths or URLs
    created_by: str  # User ID
    created_at: datetime
    status: ComplaintStatus = ComplaintStatus.PENDING
    upvotes: int = 0
    downvotes: int = 0
    reports: List[str] = []  # List of report IDs
    
    def add_report(self, report_id: str):
        if report_id not in self.reports:
            self.reports.append(report_id)
    
    def remove_report(self, report_id: str):
        if report_id in self.reports:
            self.reports.remove(report_id)

class Report(BaseModel):
    id: str
    complaint_id: str
    reason: ReportReason
    description: str
    reported_by: str  # User ID
    reported_at: datetime
    status: ReportStatus = ReportStatus.PENDING
    admin_notes: Optional[str] = None
    action_taken: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None  # Admin ID

class UserStatus(str, Enum):
    ACTIVE = "active"
    WARNED = "warned"
    TEMPORARILY_SUSPENDED = "temporarily_suspended"
    BANNED = "banned"

class User(BaseModel):
    id: str
    username: str
    email: str
    status: UserStatus = UserStatus.ACTIVE
    warnings: int = 0
    created_at: datetime
    last_login: Optional[datetime] = None
    reported_complaints: List[str] = Field(default_factory=list)  # IDs of complaints reported by this user
    reported_by_others: int = 0  # Number of times this user's complaints were reported
    
    def add_reported_complaint(self, complaint_id: str):
        if complaint_id not in self.reported_complaints:
            self.reported_complaints.append(complaint_id)
    
    def increment_reported_count(self):
        self.reported_by_others += 1
        # Auto-warn or suspend based on reports
        if self.reported_by_others >= 3 and self.status == UserStatus.ACTIVE:
            self.status = UserStatus.WARNED
        elif self.reported_by_others >= 5 and self.status == UserStatus.WARNED:
            self.status = UserStatus.TEMPORARILY_SUSPENDED
