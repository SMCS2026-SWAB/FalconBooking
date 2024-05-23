from datetime import datetime, timedelta
from random import randint

from flask import Flask, render_template, request
from humanize import naturaldate
from utils.booking import Booking

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
                "SMCS Hub": Booking([]),
                "Global Hub": Booking(range(9)),
                "Humanities Hub": Booking([]),
                "ISP Hub": Booking(range(9))
            },
            {
                "Room 2709": Booking(["a", "b", "c", "d", "e"]),
                "Room 2800": Booking(range(9)),
                "Room 2801": Booking(range(9)),
                "Room 2901": Booking(["a", "b", "c", "d", "e"])
            }
        ]
    )


if __name__ == "__main__":
    app.run(debug=True, port=3000)