from typing import Optional
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets

from app.services.base import BaseService
from app.models.admin import Admin, AdminRole
from app.db.base import MongoRepository
from app.core.security import security_manager


class AdminService(BaseService[Admin, dict, dict]):
    """Admin management service"""
    
    def __init__(self):
        repository = MongoRepository(Admin)
        super().__init__(repository)
    
    async def authenticate(self, email: str, password: str) -> Optional[Admin]:
        """Authenticate admin user"""
        admin = await self.repository.find_one({"email": email, "is_active": True})
        if not admin or not admin.verify_password(password):
            return None
        
        # Update login statistics
        admin.update_login()
        await admin.save()
        return admin
    
    async def create_admin(self, email: str, username: str, password: str, 
                          full_name: Optional[str] = None, 
                          role: AdminRole = AdminRole.ADMIN) -> Admin:
        """Create new admin user"""
        # Check if email or username already exists
        existing_email = await self.repository.find_one({"email": email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = await self.repository.find_one({"username": username})
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create admin
        admin = Admin(
            email=email,
            username=username,
            full_name=full_name,
            role=role,
            hashed_password=""  # Temporary, will be set below
        )
        admin.set_password(password)
        
        await admin.create()
        return admin
    
    async def change_password(self, admin: Admin, current_password: str, 
                            new_password: str) -> bool:
        """Change admin password"""
        if not admin.verify_password(current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        admin.set_password(new_password)
        admin.updated_at = datetime.utcnow()
        await admin.save()
        return True
    
    async def request_password_reset(self, email: str) -> str:
        """Request password reset token"""
        admin = await self.repository.find_one({"email": email, "is_active": True})
        if not admin:
            # Don't reveal if email exists
            return "If email exists, reset instructions will be sent"
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        admin.reset_token = reset_token
        admin.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        await admin.save()
        
        # In production, send email here
        return reset_token
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        admin = await self.repository.find_one({
            "reset_token": token,
            "reset_token_expires": {"$gt": datetime.utcnow()},
            "is_active": True
        })
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        admin.set_password(new_password)
        admin.reset_token = None
        admin.reset_token_expires = None
        admin.updated_at = datetime.utcnow()
        await admin.save()
        return True
    
    async def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics"""
        from app.services.prompt_service import PromptService
        from app.services.category_service import CategoryService
        from app.services.device_service import DeviceService
        
        prompt_service = PromptService()
        category_service = CategoryService()
        device_service = DeviceService()
        
        # Get basic counts
        total_prompts = await prompt_service.count()
        total_categories = await category_service.count()
        device_stats = await device_service.get_user_stats()
        
        # Get prompts by category - simplified for now
        prompts_by_category = {
            "total": total_prompts
        }
        
        return {
            "total_prompts": total_prompts,
            "total_categories": total_categories,
            "total_devices": device_stats["total_devices"],
            "active_devices_today": device_stats["active_today"],
            "total_favorites": 0,  # TODO: Calculate from device users
            "total_unlocks": 0,    # TODO: Calculate from device users
            "prompts_by_category": prompts_by_category,
            "recent_activity": []  # TODO: Add recent activity tracking
        }
    
    async def get_chart_data(self) -> dict:
        """Get chart data for dashboard graphs"""
        from app.services.prompt_service import PromptService
        from datetime import datetime, timedelta
        
        prompt_service = PromptService()
        
        # Get total prompts count
        total_prompts = await prompt_service.count()
        
        # Get featured prompts count
        featured_prompts = await prompt_service.count({"is_featured": True})
        
        # Generate mock monthly data based on actual totals
        # In a real implementation, you'd query aggregated data by month
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # Distribute the total prompts across months with some randomness
        prompts_per_month = max(1, total_prompts // 12)
        remainder = total_prompts % 12
        
        prompts_added = []
        featured_added = []
        
        for i in range(12):
            # Base amount plus some of the remainder
            base_amount = prompts_per_month
            if i < remainder:
                base_amount += 1
            
            # Add some variation (±20%)
            variation = int(base_amount * 0.2) if base_amount > 5 else 1
            actual_amount = max(0, base_amount + (i % 3 - 1) * variation)
            
            prompts_added.append(actual_amount)
            
            # Featured prompts are a subset
            featured_amount = min(actual_amount // 3, featured_prompts // 12)
            featured_added.append(max(0, featured_amount))
        
        return {
            "prompts_added": prompts_added,
            "trending_prompts": featured_added,  # Using featured as trending
            "totals": {
                "total_prompts_added": total_prompts,
                "total_trending": featured_prompts
            }
        }
    
    async def validate_create(self, obj_in: dict) -> None:
        """Validate admin creation"""
        pass
    
    async def validate_update(self, admin_id: str, obj_in: dict) -> None:
        """Validate admin update"""
        pass
