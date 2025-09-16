import asyncio
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Unified endpoints
from app.api.v1.endpoints import (
    users,
    cities,
    rates,
    categories,
    faqs,
    reviews,
    bids,
    edit_profile,
    redis_test,
    test_fee,
    notifications
)
from app.api.v1.endpoints.admin import (
    user_manager,
    review_manager,
    company_data,
    job_manager,
    category_manager,
    city_manager,
    rate_manager,
    faq_manager,
    auth,
    admin_manager,
    roles_manager,
    permissions,
    seeker_manager,
    states_manager,
    provider_manager,
    job_schedular,
    dashboard_stats
)
# supabase Admin endpoints
# from app.api.v1.endpoints.admin.supabase import auth1
# Provider endpoints
from app.api.v1.endpoints.provider import (
    profile as provider_profile,
    addresses,
    jobs as provider_job,
    city_check,
    seekerProfiles,
    provider_job_details,
    provider_job_history,
    provider_dashboard,
    track_seeker_live,
    provider_cancel_job,
    delayed_cancel,
    provider_invoice,
)
# Seeker endpoints
from app.api.v1.endpoints.seeker import (
    jobs,
    salary,
    status,
    wallet,
    location,
    profile as seeker_profile,
    verify_otp,
    job_payment,
    view_provider_profile,
    seeker_job_history,
    test_seeker_job_details,
    seeker_dashboard,
    reached_on_location,
    update_live_location,
    cancel_job,
    invoice,
)
# Import the unified WebSocket endpoint
from app.api.v1.endpoints.unified_socket import router as websocket_router
from app.utils.exception_handler import create_validation_exception_handler
from app.utils.redis_subscriber import start_redis_subscriber
from app.utils.timezone import TimezoneMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Logs to console
        logging.FileHandler("app.log"),  # Logs to a file
    ],
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(TimezoneMiddleware)

# Register the custom validation exception handler
validation_handler = create_validation_exception_handler()
app.add_exception_handler(RequestValidationError, validation_handler)
# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict the origins as per your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# admin panel endpoints

app.include_router(auth.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(seeker_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(provider_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(user_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(review_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(company_data.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(job_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(category_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(city_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(states_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(rate_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(faq_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(roles_manager.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(permissions.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(job_schedular.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(dashboard_stats.router, prefix="/api/v1/admin", tags=["admin"])
# app.include_router(auth1.router, prefix="/api/v1/admin/supabase", tags=["admin"])

# Unified endpoints
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(cities.router, prefix="/api/v1", tags=["cities"])
app.include_router(rates.router, prefix="/api/v1", tags=["rates"])
app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
app.include_router(faqs.router, prefix="/api/v1", tags=["FAQ"])
app.include_router(reviews.router, prefix="/api/v1", tags=["review_ratings"])
app.include_router(bids.router, prefix="/api/v1", tags=["bid management"])
app.include_router(edit_profile.router, prefix="/api/v1", tags=["Edit Profile"])
app.include_router(redis_test.router, prefix="/api/v1", tags=["Redis Test"])
app.include_router(test_fee.router, prefix="/api/v1", tags=["Fee Testing"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notification"])

# Seeker endpoints
app.include_router(
    seeker_profile.router, prefix="/api/v1/seeker", tags=["seeker_profile"]
)
app.include_router(status.router, prefix="/api/v1/seeker", tags=["seeker_status"])
app.include_router(salary.router, prefix="/api/v1/seeker", tags=["seeker_salary"])
app.include_router(jobs.router, prefix="/api/v1/seeker", tags=["seeker_jobs"])
app.include_router(wallet.router, prefix="/api/v1/seeker", tags=["seeker_wallet"])
app.include_router(location.router, prefix="/api/v1/seeker", tags=["seeker_location"])
app.include_router(
    verify_otp.router, prefix="/api/v1/seeker", tags=["OTP Verification for jobs"]
)
app.include_router(
    job_payment.router, prefix="/api/v1/seeker", tags=["job payment status and method"]
)
app.include_router(
    test_seeker_job_details.router, prefix="/api/v1/seeker", tags=["seeker job details"]
)
app.include_router(
    view_provider_profile.router,
    prefix="/api/v1/seeker",
    tags=["view provider profile"],
)
app.include_router(
    seeker_job_history.router, prefix="/api/v1/seeker", tags=["seeker job history"]
)

app.include_router(
    seeker_dashboard.router,
    prefix="/api/v1/seeker",
    tags=["seeker dashboard with filter"],
)

app.include_router(
    reached_on_location.router,
    prefix="/api/v1/seeker",
    tags=["Reached on location"],
)

app.include_router(
    update_live_location.router,
    prefix="/api/v1/seeker",
    tags=["update live location for tracking"],
)

app.include_router(
    cancel_job.router,
    prefix="/api/v1/seeker",
    tags=["Cancel Job by Seeker"],
)

app.include_router(
    invoice.router,
    prefix="/api/v1/seeker",
    tags=["Cancel Job by Seeker"],
)

# Provider endpoints
app.include_router(
    provider_profile.router,
    prefix="/api/v1/provider",
    tags=["Complete provider profile"],
)
app.include_router(
    addresses.router, prefix="/api/v1/provider", tags=["provider_address"]
)
app.include_router(
    provider_job.router, prefix="/api/v1/provider", tags=["provider_jobs"]
)
app.include_router(
    city_check.router, prefix="/api/v1/provider", tags=["provider_city_check"]
)
app.include_router(
    seekerProfiles.router, prefix="/api/v1/provider", tags=["view_seeker_profile"]
)
app.include_router(
    provider_job_details.router,
    prefix="/api/v1/provider",
    tags=["provider job details"],
)

app.include_router(
    provider_job_history.router,
    prefix="/api/v1/provider",
    tags=["provider job history"],
)

app.include_router(
    provider_dashboard.router,
    prefix="/api/v1/provider",
    tags=["provider dashboard with filter"],
)

app.include_router(
    track_seeker_live.router,
    prefix="/api/v1/provider",
    tags=["seeker live tracking"],
)
app.include_router(
    provider_cancel_job.router,
    prefix="/api/v1/provider",
    tags=["cancel job by provider"],
)
app.include_router(
    delayed_cancel.router,
    prefix="/api/v1/provider",
    tags=["delayed cancel by provider"],
)

app.include_router(
    provider_invoice.router,
    prefix="/api/v1/provider",
    tags=["Download Provider PDF invoice"],
)
# Include the unified WebSocket router
app.include_router(websocket_router)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_redis_subscriber())
    # Place any startup event logic here if needed
    pass


@app.on_event("shutdown")
async def shutdown_event():
    # Place any shutdown event logic here if needed
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
