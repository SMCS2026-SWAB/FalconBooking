from datetime import datetime
from os import environ
from dotenv import load_dotenv
from pymongo import MongoClient

from utils import Booking, Room

load_dotenv()

client = MongoClient(environ["MONGODB_URI"])
db = client["falconbooking"]


def schedule_booking(date: str, block: str, room: str, name: str, **kwargs) -> None:
    """Schedules a booking for the assigned date and block for a designated room assigned to a name."""
    bookings = db["bookings"]

    if bookings.find_one({"date": date, "block": block, "room": room}):
        return  # Make sure to not override bookings

    bookings.insert_one(
        {
            "date": date,
            "block": block,
            "room": room,
            "name": name
        }
    )


def remove_database_booking(query: dict) -> None:
    """Removes a booking from the MongoDB database."""
    bookings = db["bookings"]
    bookings.remove(query)


def serialize_booking_for_room(date: datetime, room: str) -> Booking:
    """Serializes the bookings from the database for a specific room into their respective class."""
    bookings = db["bookings"]
    room_bookings = list(bookings.find({"date": date.strftime('%m/%d/%Y'), "room": room}))
    return Booking(
        [booking["block"] for booking in room_bookings],
        {booking["block"]: booking["name"] for booking in room_bookings}
    )


def populate_rooms_on_day(date: datetime, rooms: list[Room]) -> list[Room]:
    """Populates a list of rooms for the bookings on that day."""
    return [room.with_bookings(serialize_booking_for_room(date, room.name)) for room in rooms]
