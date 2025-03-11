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
async def process_login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.email == email).first()
    if user and user.hashed_password == password:
        return RedirectResponse("/home", status_code=302)
    else:
        return HTMLResponse("<h1>Login Failed</h1>")

@app.post("/register", response_class=HTMLResponse)
async def process_register(request: Request, email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(database.get_db)):
    if password != confirm_password:
        return HTMLResponse("<h1>Passwords do not match</h1>")
    
    db_user = database.User(email=email, hashed_password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return HTMLResponse("<h1>Registration Successful</h1>")

@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    return RedirectResponse("/", status_code=302)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)