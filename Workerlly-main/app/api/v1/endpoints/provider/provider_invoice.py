import base64
from datetime import datetime
from io import BytesIO

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader
from num2words import num2words
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import motor_db
from app.utils.roles import role_required

router = APIRouter()
env = Environment(loader=FileSystemLoader("app/templates/invoices"))


def get_logo_base64():
    try:
        with open("app/templates/invoices/workerlly.png", "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    except:
        return ""


def number_to_words(number):
    try:
        words = num2words(number, lang="en_IN")
        return words.title()
    except:
        return ""


def generate_provider_invoice_pdf(template_data):
    font_config = FontConfiguration()
    css = CSS(
        string="""
        @page {
            size: A4;
            margin: 1.5cm;
        }
        @font-face {
            font-family: 'Inter';
            src: url('app/static/fonts/Inter-Regular.ttf');
        }
    """
    )

    html = HTML(string=render_invoice_template(template_data), base_url=".")
    return html.write_pdf(font_config=font_config, stylesheets=[css])


def render_invoice_template(template_data):
    template_data["logo_base64"] = get_logo_base64()
    template = env.get_template("provider_invoice.html")
    return template.render(**template_data)


@router.get("/invoice/{job_id}")
async def get_provider_invoice(
        job_id: str,
        current_user: dict = Depends(get_current_user),
        role: str = Depends(role_required("provider")),
):
    try:
        # Fetch job and validate provider
        job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job or str(job["user_id"]) != str(current_user["user_id"]):
            raise HTTPException(status_code=403, detail="Access denied")

        # Fetch category name
        category = await motor_db.categories.find_one(
            {"_id": ObjectId(job["category_id"])}
        )
        category_name = category.get("name", "Service") if category else "Service"

        # Get provider details
        provider_stats = await motor_db.user_stats.find_one(
            {"user_id": ObjectId(current_user["user_id"])}
        )
        provider_info = (
            provider_stats.get("personal_info", {}) if provider_stats else {}
        )

        # Get seeker details
        seeker_stats = await motor_db.user_stats.find_one(
            {"user_id": ObjectId(job["assigned_to"])}
        )
        seeker_info = seeker_stats.get("personal_info", {}) if seeker_stats else {}

        # Check if provider invoice exists
        existing_invoice = await motor_db.provider_invoices.find_one(
            {"job_id": ObjectId(job_id)}
        )

        if not existing_invoice:
            invoice_number = f"WRKRLYP{int(datetime.now().timestamp())}"
            invoice_data = {
                "invoice_number": invoice_number,
                "job_id": job["_id"],
                "provider_id": current_user["user_id"],
                "seeker_id": job["assigned_to"],
                "invoice_date": datetime.now(),
                "created_at": datetime.now(),
            }
            await motor_db.provider_invoices.insert_one(invoice_data)
        else:
            invoice_data = existing_invoice

        template_data = {
            "invoice_number": invoice_data["invoice_number"],
            "invoice_date": invoice_data["invoice_date"].strftime("%d %b. %Y"),
            "customer_name": seeker_info.get("name", ""),
            "city_name": seeker_info.get("city_name", ""),
            "provider_name": provider_info.get("name", ""),
            "address": job.get("address_snapshot", {}),
            "total_amount": job.get("total_amount", 0),
            "amount_in_words": number_to_words(job.get("total_amount", 0)),
            "category_name": category_name,  # Added category name
        }

        # Generate PDF
        pdf_content = generate_provider_invoice_pdf(template_data)

        return StreamingResponse(
            BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={invoice_data['invoice_number']}.pdf"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
