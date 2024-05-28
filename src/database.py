from datetime import datetime
from os import environ
from dotenv import load_dotenv
from pymongo import MongoClient

from utils import Booking

load_dotenv()

client = MongoClient(environ["MONGODB_URI"])
db = client["falconbooking"]


def schedule_booking(date: datetime, block: str, room: str, name: str) -> None:
    """Schedules a booking for the assigned date and block for a designated room assigned to a name."""
    bookings = db["bookings"]

    if bookings.find_one({"date": date.strftime("%m/%d/%Y"), "block": block, "room": room}):
        return  # Make sure to not override bookings

    bookings.insert_one(
        {
            "date": date.strftime('%m/%d/%Y'),
            "block": block,
            "room": room,
            "name": name
        }
    )


def serialize_booking_for_room(date: datetime, room: str) -> Booking:
    """Serializes the bookings from the database for a specific room into their respective class."""
    bookings = db["bookings"]
    room_bookings = bookings.find({"date": date.strftime('%m/%d/%Y'), "room": room})
    return Booking(
        [booking["block"] for booking in room_bookings]
    )
