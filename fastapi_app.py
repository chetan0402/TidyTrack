import json
import random
import secrets
import subprocess
import time

import requests
from fastapi import FastAPI, Depends, Response, status, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import settings.config
import models
from database import get_db
from schema import *
from utils import *
from constants.ReportType import *
from constants.tags import parseTags


# TODO - implement validation rule
def isValidId(id: str) -> bool:
    return True


app = FastAPI()
app.mount("/img", StaticFiles(directory="img"), name="img")
app.mount("/assets", StaticFiles(directory="templates/assets"), name="assets")
template = Jinja2Templates(directory="templates")
config = settings.config.get_config()
if not config.loaded:
    raise Exception("Config not loaded")


# region Website serve
@app.get("/")
def homePage():
    return FileResponse("templates/index.html")


@app.get("/404")
def notFound404():
    return FileResponse("templates/404.html")


@app.get("/success")
def success():
    return FileResponse("templates/mail-success.html")


@app.get("/privacy")
def privacy():
    return FileResponse("templates/privacy.html")


@app.get("/terms")
def terms():
    return FileResponse("templates/terms.html")


# endregion


@app.post("/internet/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def internetReport(internet_report: WithImgReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=internet_report, report_type=ReportType.INTERNET)


@app.post("/food/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def foodReport(food_report_request: BaseReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=food_report_request, report_type=ReportType.FOOD)


@app.post("/washroom/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def washroomReport(washroom_report: WithImgReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=washroom_report, report_type=ReportType.WASHROOM)


@app.post("/water/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def waterReport(water_report_request: BaseReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=water_report_request, report_type=ReportType.WATER)


@app.post("/cleaning/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def cleaningReport(cleaning_report: WithImgReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=cleaning_report, report_type=ReportType.WASHROOM)


@app.post("/other/report", tags=["report"], response_model=Message, responses=ReportReturnDocs)
def otherReport(other_report: BaseReport, db: Session = Depends(get_db)):
    return addReport(db, report_element=other_report, report_type=ReportType.WASHROOM)


@app.post("/sweeper/report", tags=["sweeper"], response_model=Message)
def sweeperReport(sweeper_report: SweeperReport, db: Session = Depends(get_db)):
    validUUID(sweeper_report.uuid)
    user = getUserFromToken(db, sweeper_report.token)
    verifyGroup(user, 2)

    time_rn = int(time.time())
    local_path = f"{ReportType.SWEEPER.name.lower()}-{time_rn}-{user.id}.png"
    # TODO - add mark late logic
    sweeper_record = models.SweeperRecords(
        uuid=sweeper_report.uuid,
        location=sweeper_report.location,
        img_path=local_path,
        late=False,
        time=time_rn,
        sweeper=user.id
    )
    db.add(sweeper_record)
    saveIMG(sweeper_report.img, local_path)
    db.commit()
    db.refresh(sweeper_record)
    return Message(message=sweeper_record.uuid)


# region Webview
@app.get("/internet/get", tags=["webview"])
def internetGet(request: Request, location: Union[str, None], from_time: int, to_time: int, offset: int,
                db: Session = Depends(get_db), token: str = Depends(getUserInHeaderVerified([3, 4]))):
    return template.TemplateResponse(name="dashboard_entry_show.html", context={
        "request": request,
        "data": getReport(db, location, from_time, to_time, offset=offset,
                          report_type=ReportType.INTERNET),
        "convertTime": convertTime,
        "token": token,
        "report_type": ReportType.INTERNET,
        "parseTags": parseTags
    })


@app.get("/food/get", tags=["webview"])
def foodGet(request: Request, location: Union[str, None], from_time: int, to_time: int, offset: int,
            db: Session = Depends(get_db), token: str = Depends(getUserInHeaderVerified([3, 4]))):
    return template.TemplateResponse(name="dashboard_entry_show.html", context={
        "request": request,
        "data": getReport(db, location, from_time, to_time, offset=offset,
                          report_type=ReportType.FOOD),
        "convertTime": convertTime,
        "token": token,
        "report_type": ReportType.FOOD,
        "parseTags": parseTags
    })


@app.get("/washroom/get", tags=["webview"])
def washroomGet(request: Request, location: Union[str, None], from_time: int, to_time: int, offset: int,
                db: Session = Depends(get_db), token: str = Depends(getUserInHeaderVerified([3, 4]))):
    return template.TemplateResponse(name="dashboard_entry_show.html", context={
        "request": request,
        "data": getReport(db, location, from_time, to_time, offset=offset,
                          report_type=ReportType.WASHROOM),
        "convertTime": convertTime,
        "token": token,
        "report_type": ReportType.WASHROOM,
        "parseTags": parseTags
    })


@app.get("/water/get", tags=["webview"])
def waterGet(request: Request, location: Union[str, None], from_time: int, to_time: int, offset: int,
             db: Session = Depends(get_db), token: str = Depends(getUserInHeaderVerified([3, 4]))):
    return template.TemplateResponse(name="dashboard_entry_show.html", context={
        "request": request,
        "data": getReport(db, location, from_time, to_time, offset=offset,
                          report_type=ReportType.WATER),
        "convertTime": convertTime,
        "token": token,
        "report_type": ReportType.WATER,
        "parseTags": parseTags
    })


@app.get("/cleaning/get", tags=["webview"])
def cleaningGet(request: Request, location: Union[str, None], from_time: int, to_time: int, offset: int,
                db: Session = Depends(get_db), token: str = Depends(getUserInHeaderVerified([3, 4]))):
    return template.TemplateResponse(name="dashboard_entry_show.html", context={
        "request": request,
        "data": getReport(db, location, from_time, to_time, offset=offset,
                          report_type=ReportType.CLEANING),
        "convertTime": convertTime,
        "token": token,
        "report_type": ReportType.CLEANING,
        "parseTags": parseTags
    })


@app.get("/other/get", tags=["webview"])
def otherGet(request: Request, location: Union[str, None], from_time: int, to_time: int, offset: int,
             db: Session = Depends(get_db), token: str = Depends(getUserInHeaderVerified([3, 4]))):
    return template.TemplateResponse(name="dashboard_entry_show.html", context={
        "request": request,
        "data": getReport(db, location, from_time, to_time, offset=offset,
                          report_type=ReportType.OTHER),
        "convertTime": convertTime,
        "token": token,
        "report_type": ReportType.OTHER,
        "parseTags": parseTags
    })


@app.get("/sweeper/get", tags=["webview"])
def sweeperGet(request: Request, location: Union[str, None], from_time: int, to_time: int, offset: int,
               db: Session = Depends(get_db), token: str = Depends(getUserInHeaderVerified([3, 4]))):
    return template.TemplateResponse(name="dashboard_sweeper_show.html", context={
        "request": request,
        "data": getSweeperReport(db, location, from_time, to_time, offset=offset),
        "convertTime": convertTime
    })


# endregion


# region Graphs
@app.post("/internet/graph", tags=["graph"], response_model=GraphDataResponse)
def internetGraph(graph_request: GraphDataRequest, db: Session = Depends(get_db)):
    if getUserFromToken(db, graph_request.token).usergroup not in [3, 4]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"data": getReport(db, graph_request.location, graph_request.from_time, graph_request.to_time,
                              ReportType.INTERNET)}


@app.post("/food/graph", tags=["graph"], response_model=GraphDataResponse)
def foodGraph(graph_request: GraphDataRequest, db: Session = Depends(get_db)):
    if getUserFromToken(db, graph_request.token).usergroup not in [3, 4]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"data": getReport(db, graph_request.location, graph_request.from_time, graph_request.to_time,
                              ReportType.FOOD)}


@app.post("/washroom/graph", tags=["graph"], response_model=GraphDataResponse)
def washroomGraph(graph_request: GraphDataRequest, db: Session = Depends(get_db)):
    if getUserFromToken(db, graph_request.token).usergroup not in [3, 4]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"data": getReport(db, graph_request.location, graph_request.from_time, graph_request.to_time,
                              ReportType.WASHROOM)}


@app.post("/water/graph", tags=["graph"], response_model=GraphDataResponse)
def waterGraph(graph_request: GraphDataRequest, db: Session = Depends(get_db)):
    if getUserFromToken(db, graph_request.token).usergroup not in [3, 4]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"data": getReport(db, graph_request.location, graph_request.from_time, graph_request.to_time,
                              ReportType.WATER)}


@app.post("/cleaning/graph", tags=["graph"], response_model=GraphDataResponse)
def cleaningGraph(graph_request: GraphDataRequest, db: Session = Depends(get_db)):
    if getUserFromToken(db, graph_request.token).usergroup not in [3, 4]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"data": getReport(db, graph_request.location, graph_request.from_time, graph_request.to_time,
                              ReportType.CLEANING)}


@app.post("/other/graph", tags=["graph"], response_model=GraphDataResponse)
def otherGraph(graph_request: GraphDataRequest, db: Session = Depends(get_db)):
    if getUserFromToken(db, graph_request.token).usergroup not in [3, 4]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"data": getReport(db, graph_request.location, graph_request.from_time, graph_request.to_time,
                              ReportType.OTHER)}


@app.post("/sweeper/graph", tags=["graph"], response_model=SweeperGraphResponse)
def sweeperGraph(graph_request: GraphDataRequest, db: Session = Depends(get_db)):
    if getUserFromToken(db, graph_request.token).usergroup not in [3, 4]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"data": getSweeperReport(db, graph_request.location, graph_request.from_time, graph_request.to_time)}


# endregion


@app.post("/report/edit")
def reportEdit(report_edit_request: ReportEditRequest, db: Session = Depends(get_db)):
    if getUserFromToken(db, report_edit_request.token).usergroup not in [3, 4]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    result = db.query(models.Report).filter(models.Report.ticket_id == report_edit_request.ticket_id).first()
    result.status = report_edit_request.status
    db.commit()


@app.post("/generateReport")
def generateReport(generate_report_request: GenerateReportRequest, db: Session = Depends(get_db)):
    if getUserFromToken(db, generate_report_request.token).usergroup not in [3, 4]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return entryReport(db, generate_report_request)


@app.get("/printReport/{report_id}")
def printReport(request: Request, report_id: str, db: Session = Depends(get_db)):
    all_data,location,all_flag = getGenReport(db, report_id)
    if len(all_data) == 0:
        return Message(message="Empty Report")
    if isinstance(all_data[0], models.SweeperRecords):
        report_type = ReportType.SWEEPER
    else:
        report_type = ReportType(all_data[0].type)
    return template.TemplateResponse(name="generate_report.html", context={
        "data": all_data,
        "convertTime": convertTime,
        "time_rn": int(time.time()),
        "request": request,
        "location": location,
        "report_type": report_type,
        "parseTags": parseTags,
        "sweeper": isinstance(all_data[0], models.SweeperRecords),
        "all": all_flag
    })


# region Supervisor-Sweeper
@app.post("/sweeper/create")
def sweeperCreate(sweeper_create: SweeperCreate, db: Session = Depends(get_db)):
    verifyGroups(getUserFromToken(db, sweeper_create.token), [3, 4])
    sweeper = models.Userbase(
        name=sweeper_create.sweeper,
        id=sweeper_create.sweeper,
        phone=sweeper_create.phone,
        usergroup=2
    )
    db.add(sweeper)


@app.post("/sweeper/assign")
def sweeperAssign(sweeper_assign: SweeperAssign, db: Session = Depends(get_db)):
    verifyGroups(getUserFromToken(db, sweeper_assign.token), [3, 4])
    task = models.SweeperAssign(
        sweeper=sweeper_assign.sweeper,
        location=sweeper_assign.location
    )
    db.add(task)
    db.commit()


@app.post("/sweeper/unassign")
def sweeperUnassign(sweeper_unassign: SweeperAssign, db: Session = Depends(get_db)):
    verifyGroups(getUserFromToken(db, sweeper_unassign.token), [3, 4])
    db.query(models.SweeperAssign).filter(and_(
        models.SweeperAssign.sweeper == sweeper_unassign.sweeper,
        models.SweeperAssign.location == sweeper_unassign.location
    )).delete()
    db.commit()


@app.post("/sweeper/remove")
def sweeperRemove(sweeper_remove: SweeperRemove, db: Session = Depends(get_db)):
    verifyGroups(getUserFromToken(db, sweeper_remove.token), [3, 4])
    db.query(models.SweeperAssign).filter(
        models.SweeperAssign.sweeper == sweeper_remove.sweeper
    ).delete()
    db.query(models.Userbase).filter(
        models.Userbase.id == sweeper_remove.sweeper
    ).delete()
    db.commit()


@app.post("/sweeper/list")
def sweeperList(sweeper_list: SweeperList, db: Session = Depends(get_db)):
    verifyGroups(getUserFromToken(db, sweeper_list.token), [3, 4])
    return db.query(models.Userbase).filter(
        models.Userbase.usergroup == 2
    ).all()


# endregion


# region Authentication Code
@app.post("/otp/send", tags=["account"], response_model=Message, responses={
    400: {
        "model": Message
    },
    429: {
        "model": Message
    }
})
def otpSend(otp_request: OTPRequest, response: Response, db: Session = Depends(get_db)):
    # Commenting everything cuz this workflow is hard to understand.
    clean_otp(db)
    # If there is no id in the request, it means that the request must be a login request
    if otp_request.id is None:
        # Login workflow
        # Verify if the user exists
        user = getUserFromPhone(db, otp_request.phone)
        if user is None:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Signup First")

        # Verify the role
        if user.usergroup != otp_request.role:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Invalid Role")

        otp_request.id = user.id
    else:
        # Signup Workflow
        # verify if the ID is allowed to register
        if not isValidId(otp_request.id):
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Invalid ID")

        # Check if the user already exists in the userbase and reject if it does
        user = getUserFromID(db, otp_request.id)
        if user is not None:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Account already exists. Please login instead")

    otp_element = db.query(models.OTP).filter(models.OTP.id == otp_request.id).first()
    if otp_element is None:
        otp_element = models.OTP(
            id=otp_request.id,
            role=otp_request.role,
            tries=1,
            otp=random.randint(100000, 999999),
            firstTime=int(time.time()),
            deleteTime=int(time.time()) + (60 * 60),
            nextSendTime=int(time.time()) + (2 * 60)
        )
        db.add(otp_element)
    else:
        if int(time.time()) < otp_element.nextSendTime:
            response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return Message(message="Wait for a few seconds. Try again later")
        otp_element.tries += 1
        otp_element.nextSendTime = int(time.time()) + (2 * 60)
        if otp_element.tries == 4:
            response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return Message(message="Too many requests. Please try again in an hour")
    db.commit()
    db.refresh(otp_element)

    url = "https://bulksms.bsnl.in:5010/api/Send_SMS"

    response_bsnl = requests.post(url, headers={
        "Authorization": f"Bearer {config.BSNL_AUTH}",
        "Content-Type": "application/json;charset=utf-8"
    }, data=json.dumps({
        "Header": "NITBPL",
        "Target": otp_request.phone,
        "Is_Unicode": "0",
        "Is_Flash": "0",
        "Message_Type": "SI",
        "Entity_Id": config.ENTITY_ID,
        "Content_Template_Id": config.TEMPLATE_ID,
        "Template_Keys_and_Values": [{
            "Key": "var",
            "Value": otp_element.otp
        }]
    }))

    response.status_code = response_bsnl.status_code
    return Message(message=str(otp_request.phone))


@app.post("/login/verify", tags=["account"], response_model=Message, responses={
    400: {
        "model": Message
    },
    401: {
        "description": "Wrong OTP",
        "model": Message
    }
})
def verifyLogin(login_verify_request: LoginVerifyRequest, response: Response, db: Session = Depends(get_db)):
    userbase = getUserFromPhone(db, login_verify_request.phone)
    if userbase is None:
        # 400
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Message(message="Account does not exist")
    else:
        if userbase.usergroup != login_verify_request.role:
            # 400
            response.status_code = status.HTTP_400_BAD_REQUEST
            return Message(message="Selected Role - Registered Role mismatch")

    otp_element: models.OTP = db.query(models.OTP).filter(models.OTP.id == userbase.id).first()
    if login_verify_request.otp == otp_element.otp:
        token = secrets.token_hex(32)
        user: models.Tokens = db.query(models.Tokens).filter(models.Tokens.user == userbase.id).first()
        if user is None:
            user = models.Tokens(
                idtokens=token,
                time=int(time.time()) + 31556926,
                user=userbase.id
            )
            db.add(user)
        else:
            user.idtokens = token
            user.time = int(time.time()) + 31556926

        db.query(models.OTP).filter(models.OTP.id == userbase.id).delete()
        db.commit()
        db.refresh(user)
        # 200
        return Message(message=token)
    else:
        # 401
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return Message(message="Wrong OTP")


@app.post("/signup/verify", tags=["account"], response_model=Message,
          responses={
              401: {
                  "model": Message
              }
          })
def signup(signup_request: SignupRequest, response: Response, db: Session = Depends(get_db)):
    otp_element: models.OTP = db.query(models.OTP).filter(models.OTP.id == signup_request.id).first()
    if signup_request.otp == otp_element.otp:
        userbase_element = models.Userbase(
            id=signup_request.id,
            name=signup_request.name,
            phone=signup_request.phone,
            usergroup=0
        )
        db.add(userbase_element)
        db.commit()
        db.refresh(userbase_element)
        token = secrets.token_hex(32)
        user: models.Tokens = db.query(models.Tokens).filter(models.Tokens.user == signup_request.id).first()
        if user is None:
            user = models.Tokens(
                idtokens=token,
                time=int(time.time()) + 31556926,
                user=signup_request.id
            )
            db.add(user)
        else:
            user.idtokens = token
        db.commit()
        db.refresh(user)
        return Message(message=token)
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return Message(message="Wrong OTP")


# endregion


@app.post("/profile", tags=["account"], response_model=UserbaseModel, responses={
    401: ExceptionReturnDocs,
    422: ExceptionReturnDocs
})
def profile(profile_request: ProfileRequest, db: Session = Depends(get_db)):
    user = getUserFromToken(db, profile_request.token)
    if user.usergroup in [3, 4]:
        user.subgroup = getSubGroup(db, user.id)
    return user


@app.post("/reports", tags=["account"], response_model=MyReportsResponse)
def myReports(my_reports: MyReportsRequest, db: Session = Depends(get_db)):
    return {"reports": getReportFromUser(db, my_reports.token, offset=my_reports.offset)}


# region Static File Serve
@app.get("/get/locations")
def getLocation():
    return FileResponse("locations.json")


@app.get("/locations/mess")
def messLocation():
    return FileResponse(Path.home().joinpath("constants").joinpath("location_mess.json"))


@app.get("/locations/room")
def roomLocations():
    return FileResponse(Path.home().joinpath("constants").joinpath("location_room.json"))


@app.get("/download")
def download():
    return FileResponse(config.LATEST_APP_PATH, filename="TidyTrack.apk",
                        media_type="application/vnd.android.package-archive")


@app.get("/version")
def version():
    return FileResponse(config.VERSION_FILE)


# endregion


@app.post("/update/code", include_in_schema=False)
async def reloadCode():
    global config
    try:
        config = settings.config.get_config()
    except Exception as e:
        print(e)
    subprocess.run(["git", "pull"])
    return Message(message="Updated!")
