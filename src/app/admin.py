import streamlit as st
from datetime import datetime
from typing import List, Optional
from .db import db
from .models import (
    Complaint, Report, User,
    ComplaintStatus, ReportStatus, UserStatus,
    ReportReason, ComplaintCategory
)

def _get_complaint_details(complaint_id: str) -> Optional[Complaint]:
    """Helper function to get complaint details"""
    return db.get_complaint(complaint_id)

def _get_user_details(user_id: str) -> Optional[User]:
    """Helper function to get user details"""
    return db.get_user(user_id)

def _display_complaint(complaint: Complaint):
    """Display complaint details in a card"""
    with st.expander(f"Complaint #{complaint.id} - {complaint.title}"):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if complaint.images:
                st.image(complaint.images[0], use_column_width=True)
            st.write(f"**Status:** {complaint.status.value}")
            st.write(f"**Category:** {complaint.category.value}")
            st.write(f"**Posted by:** {complaint.created_by}")
            st.write(f"**Created at:** {complaint.created_at}")
            
            # Show report count
            report_count = len(complaint.reports)
            st.warning(f"⚠️ {report_count} report{'s' if report_count != 1 else ''}")
        
        with col2:
            st.subheader(complaint.title)
            st.write(complaint.description)
            
            # Display location if available
            if complaint.location:
                st.write("**Location:**")
                st.json(complaint.location)
            
            # Display all reports for this complaint
            if complaint.reports:
                st.subheader("Reports")
                for report_id in complaint.reports[:5]:  # Show first 5 reports
                    report = db.get_report(report_id)
                    if report:
                        with st.container():
                            st.markdown(f"**{report.reason.value}** - *by {report.reported_by}*")
                            st.caption(f"{report.description}")
                            st.write("---")

def _display_user(user: User):
    """Display user details in a card"""
    with st.expander(f"User: {user.username} ({user.status.value})"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Email:** {user.email}")
            st.write(f"**Status:** {user.status.value}")
            st.write(f"**Warnings:** {user.warnings}")
            st.write(f"**Member since:** {user.created_at}")
            
            if user.status == UserStatus.BANNED and hasattr(user, 'banned_at'):
                st.error(f"Banned on: {user.banned_at}")
                if hasattr(user, 'ban_reason'):
                    st.error(f"Reason: {user.ban_reason}")
        
        with col2:
            # User statistics
            st.metric("Complaints", len(db.get_user_complaints(user.id)))
            st.metric("Reports Submitted", len(db.get_user_reports(user.id)))
            
            # User actions
            if user.status != UserStatus.BANNED:
                if st.button(f"Warn User", key=f"warn_{user.id}"):
                    db.warn_user(user.id, "Administrative action")
                    st.experimental_rerun()
                
                if st.button(f"Ban User", key=f"ban_{user.id}"):
                    db.ban_user(user.id, "Administrative action")
                    st.experimental_rerun()
            else:
                if st.button(f"Unban User", key=f"unban_{user.id}"):
                    db.update_user(user.id, status=UserStatus.ACTIVE, warnings=0)
                    st.experimental_rerun()

def show_admin_panel():
    st.title("Admin Dashboard")
    
    # Authentication (in a real app, use proper auth)
    admin_password = st.sidebar.text_input("Admin Password", type="password", key="admin_pass")
    if admin_password != "admin123":  # Replace with secure auth in production
        st.warning("Please enter the admin password")
        return
    
    # Admin navigation
    tab1, tab2, tab3 = st.tabs(["Complaints", "Reports", "Users"])
    
    with tab1:  # Complaints Tab
        st.header("Complaint Management")
        
        # Filter complaints
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All"] + [status.value for status in ComplaintStatus],
                key="complaint_status_filter"
            )
        with col2:
            category_filter = st.selectbox(
                "Category",
                ["All"] + [cat.value for cat in ComplaintCategory],
                key="complaint_category_filter"
            )
        with col3:
            sort_by = st.selectbox(
                "Sort by",
                ["Newest First", "Most Reported", "Oldest First"],
                key="complaint_sort"
            )
        
        # Get and display complaints
        complaints = db.get_complaints()
        
        # Apply filters
        if status_filter != "All":
            complaints = [c for c in complaints if c.status.value == status_filter]
        if category_filter != "All":
            complaints = [c for c in complaints if c.category.value == category_filter]
        
        # Apply sorting
        if sort_by == "Newest First":
            complaints.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == "Oldest First":
            complaints.sort(key=lambda x: x.created_at)
        elif sort_by == "Most Reported":
            complaints.sort(key=lambda x: len(x.reports), reverse=True)
        
        if not complaints:
            st.info("No complaints found matching the filters")
            return
            
        for complaint in complaints:
            _display_complaint(complaint)
    
    with tab2:  # Reports Tab
        st.header("Report Management")
        
        # Filter reports
        report_status = st.selectbox(
            "Filter by status",
            ["All"] + [status.value for status in ReportStatus],
            key="report_status_filter"
        )
        
        # Get and display reports
        reports = db.get_reports()
        
        if report_status != "All":
            reports = [r for r in reports if r.status.value == report_status]
        
        if not reports:
            st.info("No reports found")
            return
            
        for report in reports:
            complaint = _get_complaint_details(report.complaint_id)
            reporter = _get_user_details(report.reported_by)
            
            with st.expander(f"Report #{report.id} - {report.reason.value}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Complaint ID:** {report.complaint_id}")
                    if complaint:
                        st.write(f"**Complaint Title:** {complaint.title}")
                    st.write(f"**Reason:** {report.reason.value}")
                    st.write(f"**Status:** {report.status.value}")
                    st.write(f"**Reported By:** {reporter.username if reporter else 'Unknown'}")
                    st.write(f"**Reported At:** {report.reported_at}")
                
                with col2:
                    st.write("**Description:**")
                    st.write(report.description)
                    
                    if report.admin_notes:
                        st.write("**Admin Notes:**")
                        st.write(report.admin_notes)
                
                # Admin actions
                st.subheader("Actions")
                with st.form(f"action_form_{report.id}"):
                    notes = st.text_area("Notes", key=f"notes_{report.id}", value=report.admin_notes or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        action = st.selectbox(
                            "Action",
                            ["No Action", "Dismiss Report", "Warn User", "Suspend User", "Ban User"],
                            key=f"action_{report.id}"
                        )
                    
                    with col2:
                        st.write("")
                        st.write("")
                        if st.form_submit_button("Submit Action"):
                            if action != "No Action":
                                # Update report status based on action
                                status_updates = {
                                    "Dismiss Report": ReportStatus.DISMISSED,
                                    "Warn User": ReportStatus.RESOLVED,
                                    "Suspend User": ReportStatus.RESOLVED,
                                    "Ban User": ReportStatus.RESOLVED
                                }
                                
                                updates = {
                                    "admin_notes": notes,
                                    "resolved_at": datetime.now(),
                                    "status": status_updates.get(action, report.status)
                                }
                                
                                # Update report
                                db.update_report(report.id, **updates)
                                
                                # Take user action if needed
                                if complaint:
                                    if action == "Warn User":
                                        db.warn_user(complaint.created_by, f"Report #{report.id}")
                                        st.success(f"User {complaint.created_by} has been warned.")
                                    elif action == "Suspend User":
                                        db.warn_user(complaint.created_by, f"Temporary suspension from report #{report.id}")
                                        st.success(f"User {complaint.created_by} has been temporarily suspended.")
                                    elif action == "Ban User":
                                        db.ban_user(complaint.created_by, f"Banned due to report #{report.id}")
                                        st.success(f"User {complaint.created_by} has been banned.")
                                
                                st.success(f"Report {report.id} has been {updates['status'].value}")
                                st.experimental_rerun()
    
    with tab3:  # Users Tab
        st.header("User Management")
        
        # Search users
        search_term = st.text_input("Search users by username or email")
        
        # Get and display users
        users = []
        if search_term:
            # In a real app, implement proper search
            all_users = db._read_file(db.users_file, User)
            users = [u for u in all_users 
                    if search_term.lower() in u.username.lower() 
                    or search_term.lower() in u.email.lower()]
        else:
            # Show users with reports first
            all_users = db._read_file(db.users_file, User)
            users_with_reports = [u for u in all_users if u.reported_by_others > 0]
            other_users = [u for u in all_users if u.reported_by_others == 0]
            users = users_with_reports + other_users
        
        if not users:
            st.info("No users found")
            return
            
        for user in users:
            _display_user(user)

def report_complaint(complaint_id: str, report_type: str, description: str, user_id: str):
    """Function to create a new report"""
    report = Report(
        id=f"rep_{int(datetime.now().timestamp())}",
        complaint_id=complaint_id,
        report_type=report_type,
        description=description,
        reported_by=user_id,
        reported_at=datetime.now(),
        status=ReportStatus.PENDING
    )
    return db.create_report(report)
