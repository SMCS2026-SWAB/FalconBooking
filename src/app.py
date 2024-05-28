from datetime import datetime, timedelta
from random import randint, sample

from flask import Flask, render_template, request
from humanize import naturaldate
from utils import Booking, Room

app = Flask(__name__)


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


def get_base_params():
    """Retrieves and updates the base parameters at the moment."""
    return {"name": "Shayaan Wadkar", "email": "shayaanwadkar@gmail.com", "isLoggedIn": True, "color": "#efae04"}


@app.route("/")
def home():
    if date_requested := request.args.get("date"):
        date_requested = datetime.strptime(date_requested, "%Y-%m-%d")
        days_in_calendar = [date_requested + timedelta(days=day) for day in range(6)]
    else:
        days_in_calendar = [datetime.today() + timedelta(days=day) for day in range(6)]

    label_for_day = naturaldate(days_in_calendar[0])

    if not label_for_day.isalpha():  # Weirdly formatted date
        calendar_day = days_in_calendar[0].strftime('%d').lstrip('0')
        label_for_day = f"on {days_in_calendar[0].strftime('%B')} {calendar_day}{_prefix_of_day(calendar_day)}"

    return render_template(
        "index.html",
        base={"name": "Shayaan Wadkar", "isLoggedIn": False, "color": "#efae04"},
        days_in_calendar=[
            (
                " ".join(part.lstrip("0") for part in date.strftime("%B %d").split()),
                date.strftime("%Y-%m-%d")
            )
            for date in days_in_calendar
        ],
        label_for_day=label_for_day,
        availability_by_day=[randint(0, 100) for _ in range(6)],
        bookings=[
            {
                "SMCS Hub": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=1)), 0),
                "Global Hub": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=3)), 1),
                "Humanities Hub": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=8)), 2),
                "ISP Hub": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=5)), 3),
            },
            {
                "Room 2709": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=4)), 4),
                "Room 2800": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=2)), 5),
                "Room 2801": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=7)), 6),
                "Room 2901": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=5)), 7)
            }
        ]
    )


@app.route("/availability")
def availability():
    room_id = int(request.args.get("id", 0))
    bookings = {
        "SMCS Hub": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=1)), 0),
        "Global Hub": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=3)), 1),
        "Humanities Hub": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=8)), 2),
        "ISP Hub": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=5)), 3),
        "Room 2709": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=4)), 4),
        "Room 2800": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=2)), 5),
        "Room 2801": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=7)), 6),
        "Room 2901": Room(Booking(sample(Booking.AVAILABLE_PERIODS, k=5)), 7)
    }
    return render_template(
        "availability.html",
        base=get_base_params(),
        room_id=room_id,
        room_selected=next(room for room in bookings.values() if room.id_ == room_id),
        bookings=bookings
    )


if __name__ == "__main__":
    app.run(debug=True, port=3000)