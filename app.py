import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from supabase import create_client, Client
import weasyprint
from io import BytesIO
import tempfile

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Receipt Downloader", description="Validate and download receipts")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("Supabase credentials not found in environment variables")
    supabase: Optional[Client] = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with instructions"""
    return templates.TemplateResponse("receipt_form.html", {
        "request": request,
        "title": "Receipt Downloader",
        "message": "Enter a receipt ID in the URL: /receipt/{receipt_id}"
    })

@app.get("/receipt/{receipt_id}", response_class=HTMLResponse)
async def get_receipt_form(request: Request, receipt_id: str):
    """Display phone number verification form for a specific receipt ID"""
    return templates.TemplateResponse("receipt_form.html", {
        "request": request,
        "receipt_id": receipt_id,
        "title": f"Verify Receipt {receipt_id}"
    })

@app.post("/receipt/{receipt_id}/verify", response_class=HTMLResponse)
async def verify_receipt(
    request: Request,
    receipt_id: str,
    phone_number: str = Form(..., description="Customer phone number")
):
    """Verify phone number against receipt ID and display receipt data"""
    
    if not supabase:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Database connection not available. Please check configuration.",
            "receipt_id": receipt_id
        })
    
    try:
        # Clean phone number (remove spaces, dashes, etc.)
        cleaned_phone = ''.join(filter(str.isdigit, phone_number))
        
        # Query Supabase for receipt with matching ID and phone number
        response = supabase.table("receipts").select("*").eq("receiptid", receipt_id).execute()
        
        if not response.data:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Receipt not found. Please check the receipt ID.",
                "receipt_id": receipt_id
            })
        
        receipt_data = response.data[0]
        
        # Verify phone number matches
        stored_phone = ''.join(filter(str.isdigit, receipt_data.get("customer_phone", "")))
        
        if cleaned_phone != stored_phone:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Phone number does not match our records. Please check and try again.",
                "receipt_id": receipt_id
            })
        
        # Phone number verified, display receipt
        return templates.TemplateResponse("receipt_display.html", {
            "request": request,
            "receipt": receipt_data,
            "receipt_id": receipt_id
        })
        
    except Exception as e:
        logger.error(f"Error verifying receipt {receipt_id}: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "An error occurred while verifying your receipt. Please try again later.",
            "receipt_id": receipt_id
        })

@app.post("/receipt/{receipt_id}/download")
async def download_receipt_pdf(
    receipt_id: str,
    phone_number: str = Form(..., description="Customer phone number")
):
    """Generate and download PDF receipt"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Clean phone number
        cleaned_phone = ''.join(filter(str.isdigit, phone_number))
        
        # Verify receipt and phone number again
        response = supabase.table("receipts").select("*").eq("receiptid", receipt_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        receipt_data = response.data[0]
        stored_phone = ''.join(filter(str.isdigit, receipt_data.get("customer_phone", "")))
        
        if cleaned_phone != stored_phone:
            raise HTTPException(status_code=403, detail="Phone number does not match")
        
        # Generate HTML content for PDF
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Receipt {receipt_id}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #333;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .receipt-info {{
                    margin-bottom: 30px;
                }}
                .receipt-info h2 {{
                    color: #555;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 10px;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 5px 0;
                }}
                .info-label {{
                    font-weight: bold;
                    width: 150px;
                }}
                .items-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .items-table th,
                .items-table td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                .items-table th {{
                    background-color: #f5f5f5;
                    font-weight: bold;
                }}
                .total-section {{
                    margin-top: 30px;
                    text-align: right;
                }}
                .total-amount {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                }}
                .footer {{
                    margin-top: 40px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                    border-top: 1px solid #ccc;
                    padding-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>RECEIPT</h1>
                <h2>Receipt #{receipt_data.get('receipt_id', 'N/A')}</h2>
            </div>
            
            <div class="receipt-info">
                <h2>Customer Information</h2>
                <div class="info-row">
                    <span class="info-label">Customer Name:</span>
                    <span>{receipt_data.get('customer_name', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Phone Number:</span>
                    <span>{receipt_data.get('customer_phone', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Email:</span>
                    <span>{receipt_data.get('customer_email', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Date:</span>
                    <span>{receipt_data.get('created_at', 'N/A')}</span>
                </div>
            </div>
            
            <div class="receipt-info">
                <h2>Transaction Details</h2>
                <div class="info-row">
                    <span class="info-label">Description:</span>
                    <span>{receipt_data.get('description', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Amount:</span>
                    <span>${receipt_data.get('amount', '0.00')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Payment Method:</span>
                    <span>{receipt_data.get('payment_method', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Status:</span>
                    <span>{receipt_data.get('status', 'N/A')}</span>
                </div>
            </div>
            
            <div class="total-section">
                <div class="total-amount">
                    Total: ${receipt_data.get('amount', '0.00')}
                </div>
            </div>
            
            <div class="footer">
                <p>Thank you for your business!</p>
                <p>This is an official receipt for your records.</p>
            </div>
        </body>
        </html>
        """
        
        # Generate PDF using WeasyPrint
        pdf_file = weasyprint.HTML(string=html_content).write_pdf()
        
        # Create a temporary file to store the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file)
            tmp_file_path = tmp_file.name
        
        # Return the PDF as a file download
        return FileResponse(
            tmp_file_path,
            media_type='application/pdf',
            filename=f'receipt_{receipt_id}.pdf'
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF for receipt {receipt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating PDF")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Receipt Downloader"}
