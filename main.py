from fastapi import FastAPI, Request, Form, Depends, BackgroundTasks, Cookie, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import database
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os
import shutil
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIRECTORY = "static/uploads/profile_images"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

password_reset_tokens = {}

class UserProfileUpdate(BaseModel):
    full_name: str
    email: str
    phone_number: str
    gender: str

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class UserPreferences(BaseModel):
    email_notifications: bool
    dark_mode: bool
    language: str

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def send_reset_email(email, reset_token, reset_url):
    smtp_server = os.getenv("MAILTRAP_SMTP_SERVER", "sandbox.smtp.mailtrap.io")
    smtp_port = int(os.getenv("MAILTRAP_SMTP_PORT", "2525"))
    smtp_username = os.getenv("MAILTRAP_USERNAME")
    smtp_password = os.getenv("MAILTRAP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL", "noreply@yourapplication.com")
    
    print(f"Mailtrap config: Server={smtp_server}, Port={smtp_port}, Username={smtp_username}")
    
    if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
        print("Missing Mailtrap configuration. Check your .env file")
        print(f"Would send reset email to {email} with token {reset_token}")
        print(f"Reset URL: {reset_url}")
        return True
    
    subject = "Password Reset Request"
    body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>You requested to reset your password. Please click the link below to reset your password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <p>This link will expire in 30 minutes.</p>
    </body>
    </html>
    """
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = email

    try:
        print(f"Attempting to connect to Mailtrap: {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)
        print(f"Logging in with username: {smtp_username}")
        server.login(smtp_username, smtp_password)
        print(f"Sending email from {sender_email} to {email}")
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        print("Email sent successfully through Mailtrap")
        return True
    except Exception as e:
        print(f"Error sending email through Mailtrap: {e}")
        return False

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse("/home", status_code=302)

@app.get("/login-page", response_class=HTMLResponse)
async def read_login_register(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def process_login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(database.User).filter(database.User.username == username).first()
    if user and user.hashed_password == password:
        response = RedirectResponse("/home", status_code=302)
        response.set_cookie(key="user_logged_in", value="true", httponly=True)
        response.set_cookie(key="username", value=username, httponly=True)
        response.set_cookie(key="user_id", value=str(user.id), httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error_message": "Invalid username or password"})

@app.post("/register", response_class=HTMLResponse)
async def process_register(request: Request, full_name: str = Form(...), username: str = Form(...), email: str = Form(...), phone_number: str = Form(...), gender: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(get_db)):
    try:
        if password != confirm_password:
            return templates.TemplateResponse("register.html", {
                "request": request, 
                "error_message": "Passwords do not match"
            })
        
        db_user = database.User(full_name=full_name, username=username, phone_number=phone_number, gender=gender, email=email, hashed_password=password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return templates.TemplateResponse("reg_succes.html", {"request": request})
    except Exception as e:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error_message": f"An error occurred: {str(e)}"
        })

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_form(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/forgot-password", response_class=HTMLResponse)
async def process_forgot_password(request: Request, background_tasks: BackgroundTasks, email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(database.User).filter(database.User.email == email).first()
    if not user:
        return templates.TemplateResponse("password_reset_sent.html", {"request": request})
    
    reset_token = secrets.token_urlsafe(32)
    expiration_time = datetime.now() + timedelta(minutes=30)
    password_reset_tokens[reset_token] = {
        "user_id": user.id,
        "expiration": expiration_time
    }

    base_url = str(request.base_url)
    reset_url = f"{base_url}reset-password?token={reset_token}"
    
    print(f"Generated reset URL: {reset_url}")

    background_tasks.add_task(send_reset_email, email, reset_token, reset_url)

    return templates.TemplateResponse("password_reset_sent.html", {"request": request})

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_form(request: Request, token: str = None):
    if not token or token not in password_reset_tokens:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Invalid or expired password reset link."
        })
    
    token_data = password_reset_tokens[token]
    if datetime.now() > token_data["expiration"]:
        del password_reset_tokens[token]
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Password reset link has expired. Please request a new one"
        })
    
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@app.post("/reset-password", response_class=HTMLResponse)
async def process_reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if token not in password_reset_tokens:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Invalid or expired password reset link."
        })
    if new_password != confirm_password:
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "token": token,
            "error_message": "Passwords do not match."
        })
    user_id = password_reset_tokens[token]["user_id"]
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "User not found."
        })
    user.hashed_password = new_password
    db.commit()
    del password_reset_tokens[token]
    return templates.TemplateResponse("password_reset_success.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request):
    user_logged_in = request.cookies.get("user_logged_in") == "true"
    username = request.cookies.get("username")

    return templates.TemplateResponse("home.html", {
        "request": request,
        "user_logged_in": user_logged_in,
        "username": username
    })

@app.get("/profile", response_class=HTMLResponse)
async def read_profile(request: Request, db: Session = Depends(get_db)):
    user_logged_in = request.cookies.get("user_logged_in") == "true"
    if not user_logged_in:
        return RedirectResponse("/login-page", status_code=302)
    
    username = request.cookies.get("username")
    user_id = request.cookies.get("user_id")

    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        return RedirectResponse("/logout", status_code=302)

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "username": username,
        "user": user
    })

@app.get("/api/user-profile", response_class=JSONResponse)
async def get_user_profile(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    preferences = db.query(database.UserPreferences).filter(database.UserPreferences.user_id == user_id).first()
    
    user_data = {
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "gender": user.gender,
        "profile_image": user.profile_image or "/static/images/avatar-placeholder.jpg",
        "preferences": {
            "email_notifications": preferences.email_notifications if preferences else True,
            "dark_mode": preferences.dark_mode if preferences else False,
            "language": preferences.language if preferences else "en"
        }
    }
    
    return user_data

@app.post("/api/update-profile")
async def update_profile(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    gender: str = Form(...),
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.full_name = full_name
    user.email = email
    user.phone_number = phone_number
    user.gender = gender
    
    db.commit()
    
    return {"message": "Profile updated successfully"}

@app.post("/api/update-password")
async def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.hashed_password != current_password:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    
    user.hashed_password = new_password
    db.commit()
    
    return {"message": "Password updated successfully"}

@app.post("/api/update-preferences")
async def update_preferences(
    request: Request,
    email_notifications: bool = Form(False),
    dark_mode: bool = Form(False),
    language: str = Form("en"),
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    preferences = db.query(database.UserPreferences).filter(database.UserPreferences.user_id == user_id).first()
    
    if preferences:
        preferences.email_notifications = email_notifications
        preferences.dark_mode = dark_mode
        preferences.language = language
    else:
        preferences = database.UserPreferences(
            user_id=user_id,
            email_notifications=email_notifications,
            dark_mode=dark_mode,
            language=language
        )
        db.add(preferences)
    
    db.commit()
    
    return {"message": "Preferences saved successfully"}

@app.post("/api/upload-profile-image")
async def upload_profile_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"profile_{user_id}_{secrets.token_hex(8)}{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    relative_path = f"/static/uploads/profile_images/{unique_filename}"
    
    if user.profile_image and os.path.exists(user.profile_image.replace("/static/", "", 1)):
        try:
            old_image_path = user.profile_image.replace("/static/", "static/", 1)
            if os.path.isfile(old_image_path):
                os.remove(old_image_path)
        except Exception as e:
            print(f"Could not delete old profile image: {e}")
    
    user.profile_image = relative_path
    db.commit()
    
    return {"message": "Profile image updated successfully", "image_url": relative_path}

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = RedirectResponse("/home", status_code=302)
    response.delete_cookie("user_logged_in")
    response.delete_cookie("username")
    response.delete_cookie("user_id")
    return response

@app.get("/register", response_class=HTMLResponse)
async def read_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def read_contact(request: Request):
    user_logged_in = request.cookies.get("user_logged_in") == "true"
    username = request.cookies.get("username")
    return templates.TemplateResponse("contact.html", {
        "request": request,
        "user_logged_in": user_logged_in,
        "username": username
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)