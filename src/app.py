import atexit
import base64
import uuid
from calendar import monthrange
from datetime import datetime, timedelta
from os import environ
from random import randint
from re import sub

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_session import Session
from humanize import naturaldate

from database import client, add_one_to_visits, exclude_day_from_booking, populate_rooms_on_day, remove_database_booking, remove_database_bookings_before_day, schedule_booking
from utils import Room, send_email

load_dotenv()

FULL_URL = "https://falconbooking.onrender.com"
NUMBER_TO_MONTH = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December"
}
MONTH_TO_NUMBER = dict(zip(NUMBER_TO_MONTH.values(), NUMBER_TO_MONTH.keys()))

app = Flask(__name__)
base_rooms = [
    Room("SMCS Hub", 0, capacity=30),
    Room("Global Hub", 1, capacity=30),
    Room("Humanities Hub", 2, capacity=30),
    Room("ISP Hub (Nest)", 3, capacity=30),
    Room("SMCS Collab Rm.", 4, capacity=10),
    Room("Global Collab Rm.", 5, capacity=10),
    Room("Hum. Collab Rm.", 6, capacity=10),
    Room("ISP Collab Rm.", 7, capacity=10)
]
ongoing_bookings = {}

# Configure the Flask app
app.config["SECRET_KEY"] = environ.get("FLASK_HASH")
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "mongodb"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_NAME"] = "falconbooking"
app.config["SESSION_MONGODB"] = client
app.config["SESSION_MONGODB_DB"] = "falconbooking"
app.config["SESSION_MONGODB_COLLECTION"] = "sessions"

# Start the session to keep the user logged in
Session(app)

ongoing_logins = {}


def _prefix_of_day(day):
    """Helper function to determine the prefix of the day"""
    if day in {"11", "12", "13"}:
        return "th"
    elif day[-1] == "1":
        return "st"
    elif day[-1] == "2":
        return "nd"
    elif day[-1] == "3":
        return "rd"
    else:
        return "th"


def _truncate_date(year, month, day):
    """Helper function to truncate dates."""
    last_day_of_month = monthrange(year, month)[1]

    if day > last_day_of_month:
        day = last_day_of_month

    return datetime(year, month, day)


def _clear_database_bookings():
    """Clears database bookings for the previous day to keep the MongoDB queries quick."""
    date_today = datetime.today()
    remove_database_bookings_before_day(date_today)


def get_base_params():
    """Retrieves and updates the base parameters at the moment."""
    return {
        "name": session.get("name", "").title(),
        "email": session.get("email", ""),
        "isLoggedIn": session.get("logged_in", False),
        "color": "#efae04"
    }


@app.route("/")
def home():
    add_one_to_visits()

    if date_requested := request.args.get("date"):
        month, day, year = map(int, date_requested.split("/"))
        date_requested = _truncate_date(year, month, day)
        days_in_calendar = [date_requested + timedelta(days=day) for day in range(6)]
    else:
        days_in_calendar = [datetime.today() + timedelta(days=day) for day in range(6)]

    label_for_day = naturaldate(days_in_calendar[0])

    if not label_for_day.isalpha():  # Weirdly formatted date
        calendar_day = days_in_calendar[0].strftime('%d').lstrip('0')
        label_for_day = f"on {days_in_calendar[0].strftime('%B')} {calendar_day}{_prefix_of_day(calendar_day)}"

    rooms = populate_rooms_on_day(days_in_calendar[0], base_rooms)

    return render_template(
        "index.html",
        base=get_base_params(),
        date=request.args.get("date") or datetime.today().strftime("%m/%d/%Y"),
        days_in_calendar=[
            (
                " ".join(part.lstrip("0") for part in date.strftime("%B %d").split()),
                date.strftime("%m/%d/%Y")
            )
            for date in days_in_calendar
        ],
        label_for_day=label_for_day,
        availability_by_day=[randint(0, 100) for _ in range(6)],
        bookings=[
            {
                room.name: room for room in rooms[i:i+4]
            }
            for i in range(0, len(rooms), 4)
        ],
        number_to_month=NUMBER_TO_MONTH,
        month_to_number=MONTH_TO_NUMBER
    )


@app.route("/availability")
def availability():
    room_id = int(request.args.get("id", 0))
    date = request.args.get("date", datetime.today().strftime("%m/%d/%Y"))
    rooms = populate_rooms_on_day(datetime.strptime(date, "%m/%d/%Y"), base_rooms)
    bookings = {room.name: room for room in rooms}

    return render_template(
        "availability.html",
        base=get_base_params(),
        date=date,
        room_id=room_id,
        room_selected=next(room for room in bookings.values() if room.id_ == room_id),
        bookings=bookings
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        
        if any(char.isalpha() for char in email.split("@")[0]) and "mcpsmd.net" == email.split("@")[-1]:
            session['email'] = email
            hash_generated = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("utf-8").replace("=", "")

            name_splitted = email.split("@")[0].split(".")
            full_name = sub(r"[0-9]", "", name_splitted[0].capitalize()) + "_" + sub(r"[0-9]", "", name_splitted[-1].capitalize())

            ongoing_logins[(hash_generated, full_name)] = {
                "name": full_name.replace("_", " "),
                "email": email
            }

            # Send email to confirm log in.
            send_email(
                email, "", "", "", "",
                subject=f"Finish logging in, {full_name.replace('_', ' ')}",
                full_text=(
                    f"Follow the link provided to finish logging into FalconBooking (do not share this link with anyone!):"
                    f" {FULL_URL}/confirmation?hash={hash_generated}&name={full_name}"
                )
            )

            return redirect(url_for("check_email", email=email.split("@")[0]))
        else:
            flash('Invalid email', 'danger')
    
    return render_template('login.html', base=get_base_params())


@app.route("/logout")
def logout():
    session["name"] = ""
    session["logged_in"] = False
    session["email"] = ""

    return redirect(url_for("home"))


@app.route('/confirmation')
def confirmation():
    hash_requested = request.args["hash"]
    name = request.args["name"]
    if (login_info := ongoing_logins.get((hash_requested, name))) is None:
        return render_template(
            "404.html",
            error_message="The login you're trying to confirm doesn't exist.",
            secondary_error_message="Try logging in again."
        )
    else:
        session["name"] = login_info["name"]
        session["email"] = login_info["email"]
        session["logged_in"] = True

        return redirect(url_for("home"))


@app.route("/confirm_booking")
def confirm_booking():
    confirmation_id = int(request.args["id"])

    if (booking_info := ongoing_bookings.get(confirmation_id)) is None:
        return render_template(
            "404.html",
            base=get_base_params(),
            error_message="This confirmation ID doesn't exist.",
            secondary_error_message="Are you sure this booking exists? Check your email again."
        )
    else:
        parsed_date = datetime.strptime(booking_info["date"], "%m/%d/%Y")
        return render_template(
            "confirm_booking.html",
            base=get_base_params(),
            id=confirmation_id,
            block=booking_info["block"],
            raw_date=booking_info["date"],
            formatted_date=f"{parsed_date.strftime('%B')} {parsed_date.day}{_prefix_of_day(str(parsed_date.day))}, {parsed_date.year}",
            name=booking_info["name"],
            room=booking_info["room"],
            repeat_time=request.args.get("repeat", "Never").capitalize(),
            end_date=request.args.get("date", datetime.today().strftime('%m/%d/%Y'))
        )


@app.route("/cancel_booking")
def cancel_booking():
    return render_template(
        "cancel_booking.html",
        base=get_base_params(),
        block=request.args.get("block"),
        room=request.args.get("room"),
        date=request.args.get("date"),
        name=request.args.get("name"),
        id=request.args.get("id")
    )


@app.route("/create_booking", methods=["POST"])
def create_booking():
    data = request.get_json()
    schedule_booking(**data)
    return {"link": f"/availability?id={next(room for room in base_rooms if room.name == data['room']).id_}&date={data['date']}"}


@app.route("/remove_booking", methods=["POST"])
def remove_booking():
    data = request.get_json()

    if data.get("purge_all_bookings", False):
        remove_database_booking(data["id"])
    else:
        exclude_day_from_booking(data["id"], data["date"])

    return {"link": f"/availability?id={next(room for room in base_rooms if room.name == data['room']).id_}&date={data['date']}"}


@app.route("/process_booking", methods=["POST"])
def process_booking():
    confirmation_id = int(list(ongoing_bookings.keys())[-1]) + 1 if len(ongoing_bookings.keys()) > 0 else 0
    ongoing_bookings[confirmation_id] = request.get_json()
    return {"id": confirmation_id}


@app.route("/check_email")
def check_email():
    return render_template("check_email.html", email=request.args.get("email"), base=get_base_params())


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=_clear_database_bookings, trigger="interval", seconds=60 * 60 * 24)
    scheduler.start()

    app.run(debug=True, port=3000)

    atexit.register(lambda: scheduler.shutdown())
