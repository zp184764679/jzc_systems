from app import db
from datetime import datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

class Employee(db.Model):
    __tablename__ = 'employees'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    empNo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, comment='Employee Number')
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='Employee Name')
    gender: Mapped[Optional[str]] = mapped_column(String(10), comment='Gender (Male/Female/Other)')
    birth_date: Mapped[Optional[datetime]] = mapped_column(Date, comment='Date of Birth')
    id_card: Mapped[Optional[str]] = mapped_column(String(50), comment='ID Card Number')
    phone: Mapped[Optional[str]] = mapped_column(String(20), comment='Phone Number')
    email: Mapped[Optional[str]] = mapped_column(String(100), comment='Email Address')

    # Additional Personal Information (from Dongguan factory data)
    nationality: Mapped[Optional[str]] = mapped_column(String(50), comment='Nationality/Ethnicity (民族)')
    education: Mapped[Optional[str]] = mapped_column(String(50), comment='Education Level (学历)')
    native_place: Mapped[Optional[str]] = mapped_column(String(100), comment='Native Place/Hometown (籍贯)')
    bank_card: Mapped[Optional[str]] = mapped_column(String(50), comment='Bank Card Number (银行卡)')
    has_card: Mapped[Optional[str]] = mapped_column(String(10), comment='Has Employee Card (制卡: 是/否)')
    salary_type: Mapped[Optional[str]] = mapped_column(String(20), comment='Salary Type (薪资制: 计时/计件)')
    accommodation: Mapped[Optional[str]] = mapped_column(String(20), comment='Accommodation (住宿: 内宿/外宿)')

    # Work Information - Foreign Keys (new standardized fields)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('departments.id'), comment='Department ID')
    position_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('positions.id'), comment='Position ID')
    team_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('teams.id'), comment='Team ID')
    factory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('factories.id'), comment='Factory ID')

    # Work Information - Text fields (kept for backward compatibility)
    department: Mapped[Optional[str]] = mapped_column(String(100), comment='Department (legacy)')
    title: Mapped[Optional[str]] = mapped_column(String(100), comment='Job Title (legacy)')
    team: Mapped[Optional[str]] = mapped_column(String(100), comment='Team/Section (legacy)')
    hire_date: Mapped[Optional[datetime]] = mapped_column(Date, comment='Hire Date')
    employment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default='Active',
        comment='Employment Status (Active/Resigned/Terminated/On Leave)'
    )
    resignation_date: Mapped[Optional[datetime]] = mapped_column(Date, comment='Resignation Date')

    # Contract Information
    contract_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment='Contract Type (Full-time/Part-time/Contract/Intern)'
    )
    contract_start_date: Mapped[Optional[datetime]] = mapped_column(Date, comment='Contract Start Date')
    contract_end_date: Mapped[Optional[datetime]] = mapped_column(Date, comment='Contract End Date')

    # Salary Information
    base_salary: Mapped[Optional[float]] = mapped_column(Float, comment='Base Salary')
    performance_salary: Mapped[Optional[float]] = mapped_column(Float, comment='Performance/Bonus Salary')
    total_salary: Mapped[Optional[float]] = mapped_column(Float, comment='Total Salary')

    # Address and Emergency Contact
    home_address: Mapped[Optional[str]] = mapped_column(Text, comment='Home Address')
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(100), comment='Emergency Contact Name')
    emergency_phone: Mapped[Optional[str]] = mapped_column(String(20), comment='Emergency Contact Phone')

    # Other Information
    remark: Mapped[Optional[str]] = mapped_column(Text, comment='Additional Remarks/Notes')

    # Blacklist Information
    is_blacklisted: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment='Is in Blacklist (是否在黑名单)'
    )
    blacklist_reason: Mapped[Optional[str]] = mapped_column(Text, comment='Blacklist Reason (黑名单原因)')
    blacklist_date: Mapped[Optional[datetime]] = mapped_column(Date, comment='Blacklist Date (加入黑名单日期)')

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='Record Creation Time'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment='Record Last Update Time'
    )
    # Soft delete support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        comment='Soft delete timestamp'
    )
    deleted_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment='User ID who deleted this record'
    )

    # Relationships
    department_ref = relationship('Department', backref='employees', foreign_keys=[department_id])
    position_ref = relationship('Position', backref='employees', foreign_keys=[position_id])
    team_ref = relationship('Team', backref='members', foreign_keys=[team_id])
    factory_ref = relationship('Factory', backref='employees', foreign_keys=[factory_id])

    def to_dict(self):
        """Convert employee object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            # Basic Information
            'empNo': self.empNo,
            'name': self.name,
            'gender': self.gender,
            'birth_date': self.birth_date.strftime('%Y-%m-%d') if self.birth_date else None,
            'id_card': self.id_card,
            'phone': self.phone,
            'email': self.email,
            # Additional Personal Information
            'nationality': self.nationality,
            'education': self.education,
            'native_place': self.native_place,
            'bank_card': self.bank_card,
            'has_card': self.has_card,
            'salary_type': self.salary_type,
            'accommodation': self.accommodation,
            # Work Information - IDs
            'department_id': self.department_id,
            'position_id': self.position_id,
            'team_id': self.team_id,
            'factory_id': self.factory_id,
            # Work Information - Names (from relations or legacy fields)
            'department': self.department_ref.name if self.department_ref else self.department,
            'title': self.position_ref.name if self.position_ref else self.title,
            'team': self.team_ref.name if self.team_ref else self.team,
            'factory': self.factory_ref.name if self.factory_ref else None,
            'factory_city': self.factory_ref.city if self.factory_ref else None,
            'hire_date': self.hire_date.strftime('%Y-%m-%d') if self.hire_date else None,
            'employment_status': self.employment_status,
            'resignation_date': self.resignation_date.strftime('%Y-%m-%d') if self.resignation_date else None,
            # Contract Information
            'contract_type': self.contract_type,
            'contract_start_date': self.contract_start_date.strftime('%Y-%m-%d') if self.contract_start_date else None,
            'contract_end_date': self.contract_end_date.strftime('%Y-%m-%d') if self.contract_end_date else None,
            # Salary Information
            'base_salary': self.base_salary,
            'performance_salary': self.performance_salary,
            'total_salary': self.total_salary,
            # Address and Emergency Contact
            'home_address': self.home_address,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            # Other Information
            'remark': self.remark,
            # Blacklist Information
            'is_blacklisted': self.is_blacklisted,
            'blacklist_reason': self.blacklist_reason,
            'blacklist_date': self.blacklist_date.strftime('%Y-%m-%d') if self.blacklist_date else None,
            # Timestamps
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            # Soft delete
            'deleted_at': self.deleted_at.strftime('%Y-%m-%d %H:%M:%S') if self.deleted_at else None,
            'deleted_by': self.deleted_by
        }

    def __repr__(self):
        return f'<Employee {self.empNo} - {self.name}>'
