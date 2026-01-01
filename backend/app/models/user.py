"""
User model for authentication and role-based access control.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash
from app.utils.database import Base

class User(Base):
    """User model for authentication and RBAC."""
    
    __tablename__ = 'users'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # User identification
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Role-based access control
    role = Column(String(20), nullable=False, default='viewer')  # admin, analyst, viewer
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime)
    password_changed_at = Column(DateTime)
    
    # Additional fields
    login_count = Column(Integer, default=0)
    profile_picture = Column(String(255))  # URL or path to profile picture
    phone = Column(String(20))
    department = Column(String(50))
    notes = Column(Text)  # Admin notes about the user
    
    def __init__(self, name, email, password, role='viewer', **kwargs):
        """Initialize a new user."""
        self.name = name
        self.email = email.lower()  # Store email in lowercase
        self.password_hash = generate_password_hash(password)
        self.role = role
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary representation."""
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'login_count': self.login_count or 0,
            'phone': self.phone,
            'department': self.department,
            'profile_picture': self.profile_picture
        }
        
        if include_sensitive:
            data.update({
                'password_changed_at': self.password_changed_at.isoformat() if self.password_changed_at else None,
                'notes': self.notes
            })
        
        return data
    
    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'
    
    @property
    def is_analyst(self):
        """Check if user has analyst role or higher."""
        return self.role in ['admin', 'analyst']
    
    @property
    def is_viewer(self):
        """Check if user has at least viewer role."""
        return self.role in ['admin', 'analyst', 'viewer']
    
    def has_permission(self, required_role):
        """Check if user has required role permission."""
        role_hierarchy = {
            'viewer': 1,
            'analyst': 2,
            'admin': 3
        }
        
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def update_last_login(self):
        """Update last login timestamp and increment login count."""
        self.last_login_at = datetime.utcnow()
        self.login_count = (self.login_count or 0) + 1
    
    @classmethod
    def create_default_users(cls, db_session):
        """Create default users for demo/development."""
        default_users = [
            {
                'name': 'System Administrator',
                'email': 'admin@fraudnet.ai',
                'password': 'admin123',
                'role': 'admin',
                'is_verified': True,
                'department': 'IT Security'
            },
            {
                'name': 'Fraud Analyst',
                'email': 'analyst@fraudnet.ai',
                'password': 'analyst123',
                'role': 'analyst',
                'is_verified': True,
                'department': 'Risk Management'
            },
            {
                'name': 'Dashboard Viewer',
                'email': 'viewer@fraudnet.ai',
                'password': 'viewer123',
                'role': 'viewer',
                'is_verified': True,
                'department': 'Operations'
            },
            {
                'name': 'John Smith',
                'email': 'john.smith@fraudnet.ai',
                'password': 'demo123',
                'role': 'analyst',
                'is_verified': True,
                'department': 'Fraud Investigation',
                'phone': '+1-555-0123'
            },
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.johnson@fraudnet.ai',
                'password': 'demo123',
                'role': 'viewer',
                'is_verified': True,
                'department': 'Customer Service',
                'phone': '+1-555-0124'
            }
        ]
        
        created_users = []
        
        try:
            for user_data in default_users:
                # Check if user already exists
                existing_user = db_session.query(cls).filter_by(email=user_data['email']).first()
                
                if not existing_user:
                    user = cls(**user_data)
                    db_session.add(user)
                    created_users.append(user.email)
            
            db_session.commit()
            
            if created_users:
                print(f"Created default users: {', '.join(created_users)}")
            else:
                print("Default users already exist")
                
        except Exception as e:
            db_session.rollback()
            print(f"Error creating default users: {str(e)}")
            raise
    
    @classmethod
    def get_by_email(cls, db_session, email):
        """Get user by email address."""
        return db_session.query(cls).filter_by(email=email.lower()).first()
    
    @classmethod
    def get_active_users(cls, db_session):
        """Get all active users."""
        return db_session.query(cls).filter_by(is_active=True).all()
    
    @classmethod
    def get_by_role(cls, db_session, role):
        """Get users by role."""
        return db_session.query(cls).filter_by(role=role, is_active=True).all()

# Role constants for easy reference
class UserRole:
    ADMIN = 'admin'
    ANALYST = 'analyst'
    VIEWER = 'viewer'
    
    ALL_ROLES = [ADMIN, ANALYST, VIEWER]
    
    @classmethod
    def is_valid(cls, role):
        """Check if role is valid."""
        return role in cls.ALL_ROLES
    
    @classmethod
    def get_permissions(cls, role):
        """Get permissions for a role."""
        permissions = {
            cls.ADMIN: [
                'view_dashboard',
                'view_transactions', 
                'manage_transactions',
                'view_models',
                'manage_models',
                'view_users',
                'manage_users',
                'view_settings',
                'manage_settings',
                'view_audit_logs',
                'export_data'
            ],
            cls.ANALYST: [
                'view_dashboard',
                'view_transactions',
                'manage_transactions',
                'view_models',
                'manage_models',
                'export_data'
            ],
            cls.VIEWER: [
                'view_dashboard',
                'view_transactions'
            ]
        }
        
        return permissions.get(role, [])