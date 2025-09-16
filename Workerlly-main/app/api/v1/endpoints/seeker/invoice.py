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
    # Read the logo file and convert to base64
    try:
        with open("app/templates/invoices/workerlly.png", "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    except:
        return ""  # Return empty if file not found


def generate_invoice_pdf(template_data):
    font_config = FontConfiguration()

    # Custom CSS for PDF
    css = CSS(
        string="""
        @page {
            size: A4;
            margin: 1.5cm;
        }
        body {
            font-family: Inter, sans-serif;
            font-size: 12px;
        }
        .container {
            max-width: 100%;
        }
    """
    )

    html = HTML(string=render_invoice_template(template_data), base_url=".")
    return html.write_pdf(font_config=font_config, stylesheets=[css])


def number_to_words(number):
    try:
        words = num2words(number, lang="en_IN")
        return words.title()
    except:
        return ""


def render_invoice_template(template_data):
    template_data["logo_base64"] = get_logo_base64()
    template = env.get_template("invoice.html")
    return template.render(**template_data)


@router.get("/invoice/{job_id}")
async def get_invoice(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    role: str = Depends(role_required("seeker")),
):
    try:
        # Validate job and seeker
        job = await motor_db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job or str(job["assigned_to"]) != str(current_user["user_id"]):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get or create invoice
        existing_invoice = await motor_db.invoices.find_one(
            {"job_id": ObjectId(job_id)}
        )

        if not existing_invoice:
            transaction = await motor_db.transactions.find_one(
                {
                    "job_id": ObjectId(job_id),
                    "user_id": ObjectId(current_user["user_id"]),
                    "transaction_type": "debit",
                    "description": "For Job Lead",
                }
            )
            if not transaction:
                raise HTTPException(status_code=404, detail="Transaction not found")

            invoice_number = f"WRKRLY{int(datetime.now().timestamp())}"
            invoice_data = {
                "invoice_number": invoice_number,
                "job_id": job["_id"],
                "transaction_id": transaction["_id"],
                "user_id": current_user["user_id"],
                "invoice_date": datetime.now(),
                "created_at": datetime.now(),
            }
            await motor_db.invoices.insert_one(invoice_data)
        else:
            invoice_data = existing_invoice
            transaction = await motor_db.transactions.find_one(
                {"_id": existing_invoice["transaction_id"]}
            )

        # Get user details
        user_stats = await motor_db.user_stats.find_one(
            {"user_id": ObjectId(current_user["user_id"])}
        )
        personal_info = user_stats.get("personal_info", {}) if user_stats else {}

        # Calculate amounts
        base_fee = transaction["fee_breakdown"]["base_fee"]
        total_fee = transaction["fee_breakdown"]["total_fee"]
        discount = 0
        gst_amount = transaction["fee_breakdown"]["gst_amount"]

        template_data = {
            "customer_name": personal_info.get("name", ""),
            "invoice_number": invoice_data["invoice_number"],
            "invoice_date": invoice_data["invoice_date"].strftime("%d %b. %Y"),
            "address": job["address_snapshot"],
            "transaction": {
                "base_fee": base_fee,
                "gst_amount": gst_amount,
                "total_fee": total_fee,
                "discount": discount,
            },
            "amount_in_words": number_to_words(total_fee),
        }

        # Generate PDF
        pdf_content = generate_invoice_pdf(template_data)

        return StreamingResponse(
            BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice_{invoice_data['invoice_number']}.pdf"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
