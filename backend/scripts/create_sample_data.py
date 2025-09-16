#!/usr/bin/env python3
"""
Script to create sample data for testing admin panel
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.database import DatabaseManager
from app.services.category_service import CategoryService
from app.services.prompt_service import PromptService
from app.models.prompt import PromptStatus


async def create_sample_data():
    """Create sample categories and prompts"""
    try:
        # Initialize database
        db_manager = DatabaseManager()
        await db_manager.connect()
        await db_manager.init_beanie()
        
        category_service = CategoryService()
        prompt_service = PromptService()
        
        print("🎯 Creating sample categories...")
        
        # Create simplified categories (essential fields only)
        categories_data = [
            {
                "name": "AI Art",
                "description": "Prompts for creating beautiful AI-generated artwork",
                "icon": "🎨",
                "order": 1,
                "is_active": True
            },
            {
                "name": "Photography", 
                "description": "Professional photography prompts",
                "icon": "📸",
                "order": 2,
                "is_active": True
            },
            {
                "name": "Creative Writing",
                "description": "Prompts for creative writing and storytelling",
                "icon": "✍️",
                "order": 3,
                "is_active": True
            },
            {
                "name": "Business",
                "description": "Business and marketing prompts",
                "icon": "💼",
                "order": 4,
                "is_active": True
            },
            {
                "name": "Tech",
                "description": "Technology and programming prompts",
                "icon": "💻",
                "order": 5,
                "is_active": True
            }
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category = await category_service.create(cat_data)
            created_categories.append(category)
            print(f"✅ Created category: {category.name}")
        
        print("🎨 Creating sample prompts...")
        
        # Create simplified prompts (12 total - essential fields only)
        prompts_data = [
            # AI Art Category
            {
                "title": "Cyberpunk City Portrait",
                "description": "Create a stunning cyberpunk cityscape with neon lights",
                "content": "Create a futuristic cyberpunk city at night, with towering skyscrapers covered in neon signs, holographic advertisements floating in the air, and flying cars moving between buildings.",
                "category_id": str(created_categories[0].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": True,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=400&fit=crop"
            },
            {
                "title": "Abstract Digital Art",
                "description": "Create stunning abstract digital artwork",
                "content": "Generate an abstract digital art piece with flowing, organic shapes and vibrant color gradients. Use geometric and fluid elements with dynamic composition.",
                "category_id": str(created_categories[0].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": False,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=400&h=400&fit=crop"
            },
            {
                "title": "Minimalist Logo Design",
                "description": "Design a clean and modern minimalist logo",
                "content": "Create a minimalist logo design with clean lines, simple shapes, and modern typography. Focus on negative space and geometric elements.",
                "category_id": str(created_categories[0].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": False,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1626785774573-4b799315345d?w=400&h=400&fit=crop"
            },
            
            # Photography Category
            {
                "title": "Portrait Photography Style",
                "description": "Professional portrait photography with studio lighting",
                "content": "Take a professional portrait photograph with soft, diffused studio lighting. Use an 85mm lens with shallow depth of field to create beautiful bokeh.",
                "category_id": str(created_categories[1].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": True,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop"
            },
            {
                "title": "Nature Landscape",
                "description": "Capture breathtaking natural landscapes",
                "content": "Photograph a stunning natural landscape during golden hour. Focus on composition, natural lighting, and capturing the essence of the environment.",
                "category_id": str(created_categories[1].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": False,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=400&fit=crop"
            },
            {
                "title": "Street Photography",
                "description": "Capture authentic moments in urban environments",
                "content": "Take candid street photography that tells a story. Focus on human interactions, urban architecture, and authentic moments in city life.",
                "category_id": str(created_categories[1].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": False,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&h=400&fit=crop"
            },
            
            # Creative Writing Category
            {
                "title": "Fantasy Story Starter",
                "description": "Begin an epic fantasy adventure story",
                "content": "Write the opening chapter of a fantasy novel about a young mage who discovers an ancient artifact that changes their life forever.",
                "category_id": str(created_categories[2].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": False,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=400&fit=crop"
            },
            {
                "title": "Sci-Fi Short Story",
                "description": "Create a compelling science fiction narrative",
                "content": "Write a short science fiction story set in the year 2150 where humans have colonized Mars and discovered something unexpected.",
                "category_id": str(created_categories[2].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": False,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400&h=400&fit=crop"
            },
            {
                "title": "Character Development",
                "description": "Create detailed and believable characters",
                "content": "Develop a complex character with a rich backstory, clear motivations, and realistic flaws that will drive your narrative forward.",
                "category_id": str(created_categories[2].id),
                "status": PromptStatus.DRAFT,
                "is_featured": False,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop"
            },
            
            # Business Category
            {
                "title": "Marketing Email Campaign",
                "description": "Create an engaging marketing email for product launch",
                "content": "Write a compelling marketing email for a product launch campaign with attention-grabbing subject line, clear value proposition, and strong call-to-action.",
                "category_id": str(created_categories[3].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": False,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=400&fit=crop"
            },
            {
                "title": "Social Media Strategy",
                "description": "Develop a comprehensive social media strategy",
                "content": "Create a 30-day social media strategy that includes content pillars, posting schedule, engagement tactics, and performance metrics.",
                "category_id": str(created_categories[3].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": False,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=400&h=400&fit=crop"
            },
            
            # Tech Category
            {
                "title": "API Documentation",
                "description": "Write clear and comprehensive API documentation",
                "content": "Create detailed API documentation that includes endpoint descriptions, request/response examples, authentication methods, and error handling.",
                "category_id": str(created_categories[4].id),
                "status": PromptStatus.PUBLISHED,
                "is_featured": True,
                "is_active": True,
                "image_url": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400&h=400&fit=crop"
            }
        ]
        
        for prompt_data in prompts_data:
            prompt = await prompt_service.create(prompt_data)
            print(f"✅ Created prompt: {prompt.title}")
        
        print(f"\n🎉 Sample data created successfully!")
        print(f"📊 Categories: {len(created_categories)}")
        print(f"📝 Prompts: {len(prompts_data)}")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(create_sample_data())

