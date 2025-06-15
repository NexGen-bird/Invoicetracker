import os
import logging
from typing import Optional, Union
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from playwright.async_api import async_playwright
import tempfile
from datetime import datetime
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Receipt Downloader", description="Validate and download receipts")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")
def format_date(value, fmt="%d %b %Y"):
    try:
        if "T" in value:
            dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        else:
            dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime(fmt)
    except Exception:
        return value  # fallback if parsing fails
       
templates.env.filters["format_date"] = format_date

# Initialize Supabase client
# SUPABASE_URL = os.getenv("SUPABASE_URL", "")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_URL = "https://dvobjzoqovdrsuzhjnkf.supabase.co"  # From the Supabase Dashboard
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR2b2Jqem9xb3ZkcnN1emhqbmtmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzIzNzY5MjUsImV4cCI6MjA0Nzk1MjkyNX0.YiMofxYQxrp4YjO3zdSB2pThHXY62KJRppmZLxaFGBo"  # From the API Settings

try:
    from supabase import create_client
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    else:
        supabase = None
        logger.warning("Supabase credentials not found")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None
def login_user(email: str, password: str):
    """Authenticate a user with Supabase."""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        return {"error": str(e)}
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
        test = login_user("abhijit.shinde@test.com","india@123")
        print("This is Login -->",(test))
        # Query Supabase for receipt with matching ID and phone number
        response = supabase.table("receipts").select("*").eq("receiptid", receipt_id).execute()
        print("data -----> ",response)
        if not response.data:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Receipt not found. Please check the receipt ID.",
                "receipt_id": receipt_id
            })
        
        receipt_data = response.data[0]
        
        # Verify phone number matches
        stored_phone = ''.join(filter(str.isdigit, receipt_data.get('customer_phone', "")))
        print("stored_phone --- > ",stored_phone)
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

# @app.post("/receipt/{receipt_id}/download")
# async def download_receipt_pdf(
#     receipt_id: str,
#     phone_number: str = Form(..., description="Customer phone number")
# ):
#     """Generate and download PDF receipt"""
    
#     if not supabase:
#         raise HTTPException(status_code=500, detail="Database connection not available")
    
#     try:
#         # Clean phone number
#         cleaned_phone = ''.join(filter(str.isdigit, phone_number))
#         login_user("abhijit.shinde@test.com","india@123")
#         # Verify receipt and phone number again
#         response = supabase.table("receipts").select("*").eq("receiptid", receipt_id).execute()
        
#         if not response.data:
#             raise HTTPException(status_code=404, detail="Receipt not found")
        
#         receipt_data = response.data[0]
#         stored_phone = ''.join(filter(str.isdigit, receipt_data.get("customer_phone", "")))
        
#         if cleaned_phone != stored_phone:
#             raise HTTPException(status_code=403, detail="Phone number does not match")
        
#         # Generate HTML content for PDF
#         html_content = f"""
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <meta charset="UTF-8">
#             <title>Receipt {receipt_id}</title>
#             <style>
#                 body {{
#                     font-family: Arial, sans-serif;
#                     margin: 40px;
#                     color: #333;
#                 }}
#                 .header {{
#                     text-align: center;
#                     border-bottom: 2px solid #333;
#                     padding-bottom: 20px;
#                     margin-bottom: 30px;
#                 }}
#                 .receipt-info {{
#                     margin-bottom: 30px;
#                 }}
#                 .receipt-info h2 {{
#                     color: #555;
#                     border-bottom: 1px solid #ccc;
#                     padding-bottom: 10px;
#                 }}
#                 .info-row {{
#                     display: flex;
#                     justify-content: space-between;
#                     margin: 10px 0;
#                     padding: 5px 0;
#                 }}
#                 .info-label {{
#                     font-weight: bold;
#                     width: 150px;
#                 }}
#                 .items-table {{
#                     width: 100%;
#                     border-collapse: collapse;
#                     margin: 20px 0;
#                 }}
#                 .items-table th,
#                 .items-table td {{
#                     border: 1px solid #ddd;
#                     padding: 12px;
#                     text-align: left;
#                 }}
#                 .items-table th {{
#                     background-color: #f5f5f5;
#                     font-weight: bold;
#                 }}
#                 .total-section {{
#                     margin-top: 30px;
#                     text-align: right;
#                 }}
#                 .total-amount {{
#                     font-size: 18px;
#                     font-weight: bold;
#                     color: #333;
#                 }}
#                 .footer {{
#                     margin-top: 40px;
#                     text-align: center;
#                     font-size: 12px;
#                     color: #666;
#                     border-top: 1px solid #ccc;
#                     padding-top: 20px;
#                 }}
#             </style>
#         </head>
#         <body>
#             <div class="header">
#                 <h1>RECEIPT</h1>
#                 <h2>Receipt #{receipt_data.get('receipt_id', 'N/A')}</h2>
#             </div>
            
#             <div class="receipt-info">
#                 <h2>Customer Information</h2>
#                 <div class="info-row">
#                     <span class="info-label">Customer Name:</span>
#                     <span>{receipt_data.get('customer_name', 'N/A')}</span>
#                 </div>
#                 <div class="info-row">
#                     <span class="info-label">Phone Number:</span>
#                     <span>{receipt_data.get('customer_phone', 'N/A')}</span>
#                 </div>
#                 <div class="info-row">
#                     <span class="info-label">Email:</span>
#                     <span>{receipt_data.get('customer_email', 'N/A')}</span>
#                 </div>
#                 <div class="info-row">
#                     <span class="info-label">Date:</span>
#                     <span>{receipt_data.get('created_at', 'N/A')}</span>
#                 </div>
#             </div>
            
#             <div class="receipt-info">
#                 <h2>Transaction Details</h2>
#                 <div class="info-row">
#                     <span class="info-label">Description:</span>
#                     <span>{receipt_data.get('description', 'N/A')}</span>
#                 </div>
#                 <div class="info-row">
#                     <span class="info-label">Amount:</span>
#                     <span>${receipt_data.get('amount', '0.00')}</span>
#                 </div>
#                 <div class="info-row">
#                     <span class="info-label">Payment Method:</span>
#                     <span>{receipt_data.get('payment_method', 'N/A')}</span>
#                 </div>
#                 <div class="info-row">
#                     <span class="info-label">Status:</span>
#                     <span>{receipt_data.get('status', 'N/A')}</span>
#                 </div>
#             </div>
            
#             <div class="total-section">
#                 <div class="total-amount">
#                     Total: ${receipt_data.get('amount', '0.00')}
#                 </div>
#             </div>
            
#             <div class="footer">
#                 <p>Thank you for your business!</p>
#                 <p>This is an official receipt for your records.</p>
#             </div>
#         </body>
#         </html>
#         """
        
#         # Generate PDF using WeasyPrint
#         try:
#             html_doc = weasyprint.HTML(string=html_content)
#             pdf_bytes = html_doc.write_pdf()
            
#             # Create a temporary file to store the PDF
#             with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
#                 tmp_file.write(pdf_bytes)
#                 tmp_file_path = tmp_file.name
#         except Exception as pdf_error:
#             logger.error(f"PDF generation error: {pdf_error}")
#             raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
#         # Return the PDF as a file download
#         return FileResponse(
#             tmp_file_path,
#             media_type='application/pdf',
#             filename=f'receipt_{receipt_id}.pdf'
#         )
        
#     except Exception as e:
#         logger.error(f"Error generating PDF for receipt {receipt_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail="Error generating PDF")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Receipt Downloader"}


@app.post("/receipt/{receipt_id}/download")
async def download_receipt_pdf(
    receipt_id: str,
    phone_number: str = Form(..., description="Customer phone number")
    # phone_number: str = Query(..., description="Customer phone number")
):
    print("Inside Download function")
    print("Method Values --> ",receipt_id,phone_number)
    # Validate DB connection
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")

    try:
        cleaned_phone = ''.join(filter(str.isdigit, phone_number))
        login_user("abhijit.shinde@test.com", "india@123")
        print("Login complete..")
        response = supabase.table("receipts").select("*").eq("receiptid", receipt_id).execute()
        print("Got Response..")
        if not response.data:
            raise HTTPException(status_code=404, detail="Receipt not found")

        receipt_data1 = response.data[0]
        stored_phone = ''.join(filter(str.isdigit, receipt_data1.get("customer_phone", "")))
        print("stored_phonem --> ",stored_phone)
        print("stored_receipt data --> ",receipt_data1)
        receipt_data = response.data[0]

        if cleaned_phone != stored_phone:
            raise HTTPException(status_code=403, detail="Phone number does not match")

        # Build HTML string
        template = templates.env.get_template("receipt_display2.html")  # <-- your Jinja file
        html_content = template.render(receipt=receipt_data)

        # Generate PDF using Playwright
        tmp_file_path = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.set_content(html_content, wait_until='networkidle')
                # tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                # await page.pdf(path=tmp.name, format="A4", print_background=True)
                # tmp_file_path = tmp.name
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    await page.pdf(path=tmp_file.name, format="A4", print_background=True)
                    tmp_file_path = tmp_file.name
                await browser.close()
                print("playwright closed..")
        except Exception as pdf_error:
            logger.error(f"PDF generation error: {pdf_error}")
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        print(f"receipt_{receipt_id}.pdf")
        return FileResponse(
            tmp_file_path,
            media_type="application/pdf",
            filename=f"receipt_{receipt_id}.pdf"
        )

    except Exception as e:
        import traceback
        logger.error(f"Error generating PDF for receipt {receipt_id}: {str(e)}")
        print("[Error generating PDF]")
        # raise HTTPException(status_code=500, detail="Error generating PDF")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error generating PDF")

@app.get("/receipt/{receipt_id}/test-pdf")
async def generate_pdf():
    # html = "<html><body><h1>Hello Playwright PDF</h1></body></html>"
    html = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Receipt</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f3f3f3;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .receipt-container {{
                    width: 700px;
                    background-color: white;
                    border: 1px solid #ccc;
                    padding: 30px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                }}
                .header img {{
                    width: 200px; /* Increased logo size */
                    margin-bottom: 1px;
                }}
                .receipt-tagline {{
                    text-align: center;
                    font-weight: bold;
                    font-size: 14px;
                    /* margin: 20px 0; */
                    color: #ff7c00;
                    /* text-transform: uppercase; */
                }}
                .grad {{
                    font-size: 14px;
                    background: -webkit-linear-gradient(#ffb447, #ff7c00);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-weight: bold;
                }}
                .header p {{
                    margin: 5px 0;
                    font-size: 12px;
                }}
                .receipt-title {{
                    text-align: center;
                    font-weight: bold;
                    font-size: 18px;
                    margin: 20px 0;
                    color: #8b1e1d;
                    text-transform: uppercase;
                }}
                .row {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin: 15px 0;
                }}
                .input-line {{
                    border-bottom: 1px solid #000;
                    flex: 1;
                    margin-left: 10px;
                    padding: 5px;
                }}
                .checkbox-group {{
                    display: flex;
                    gap: 10px;
                    font-size: 14px;
                }}
                .checkbox-group label {{
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }}
                .signature-section {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 30px;
                }}
                .signature-line {{
                    border-top: 1px solid #000;
                    width: 200px;
                    margin-left: 10px;
                }}
                .amount-box {{
                    border: 1px solid #8b1e1d;
                    width: 180px;
                    height: 50px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 20px;
                    font-weight: bold;
                    color: #8b1e1d;
                }}
                .date-input {{
                    border: none;
                    border-bottom: 1px solid #000;
                    text-align: left;
                    padding: 5px;
                    width: 100px;
                    font-size: 16px;
                }}
                .bottom-input {{
                    border: none;
                    border-bottom: 1px solid #000;
                    text-align: left;
                    padding: 5px;
                    width: 200px;
                    font-size: 16px;
                }}
            </style>
        </head>
        <body>

        <div class="receipt-container">
            <div class="header" style="background-color: #f4f9fc;">
                <!-- Logo Section with Increased Size -->
                <img src="assets/img/receipt/logo.png" alt="Logo">
                <p class="receipt-tagline">Where Productivity meets Comfort</p>
                
                <!-- Updated Address and Contact Information -->
                <p>Sonata Commercial Co. Op. Society C-201, 2nd Floor, Above RK Bazar, MIDC, Dombivli (E) 421203</p>
                <p>Phone: 9930253216 | 8108236131                             Email: nexgenstudycenter@gmail.com</p>
                <p class="input-line"></p>
            </div>

            <div class="receipt-title">Receipt</div>

            <div class="row">
                <div>No.: <input type="text" class="date-input" id="" ></div>
                <div>Date: <input type="text" class="date-input" id="date"></div>
            </div>

            <div class="row">
                <div>Name : <input type="text" style="border: none;font-size: 16px;width: 580px;border-bottom: 1px solid #000;"></div>
                <!-- <span>Name :</span>
                <div class="input-line"></div> -->
            </div>

            <div class="row">
                <div>Plan Type : <input type="text" class="bottom-input" id=""></div>
                <div>Shift : <input type="text" class="bottom-input" id="" ></div>
                <!-- <span>Plan Type :</span> -->
                <!-- <div class="input-line"></div> -->
            </div>

            
            <div class="row checkbox-group">
                <span>Payment Mode :</span>
                <label><input type="checkbox"> UPI</label>
                <label><input type="checkbox"> Cash</label>
                <label><input type="checkbox"> Online</label>
            </div>
            <div class="row">
                <div>Joining Date : <input type="text" class="bottom-input" id="" ></div>
                <div>Expired On : <input type="text" class="bottom-input" id="" ></div>
            </div>

            <div class="row">
                
                <div class="amount-box">₹ <input type="number" id="" style="border: none;font-size: 20px;font-weight: bold;color: #8b1e1d;width: 90px;height: 30px;">/-</div>
                <div><img src="assets/img/receipt/AbhijitSign.png" class="bottom-input" alt="Logo" style="width: 100px;"></div>
                
            </div>

            <div class="row">
                <span></span>
                <span></span>
                <div><span>Abhijit Shinde</span></div>
            </div>
        </div>

        <script>
            // Set today's date automatically in the date field
            document.getElementById('date').value = new Date().toLocaleDateString();
        </script>

        </body>
        </html>

''' # Keep your HTML template as-is

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until='networkidle')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            await page.pdf(path=tmp_file.name, format="A4", print_background=True)
            file_path = tmp_file.name
        
        await browser.close()

    return FileResponse(path=file_path, filename="test_receipt.pdf", media_type="application/pdf")