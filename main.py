from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import database

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = database.get_db()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_login_register(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def process_login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.username == username).first()
    if user and user.hashed_password == password:
        return RedirectResponse("/home", status_code=302)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error_message": "Invalid username or password"})

@app.post("/register", response_class=HTMLResponse)
async def process_register(request: Request,full_name: str = Form(...), username: str = Form(...), email: str = Form(...),phone_number: str = Form(...), gender: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(database.get_db)):
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

@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    return RedirectResponse("/", status_code=302)

@app.get("/register", response_class=HTMLResponse)
async def read_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)