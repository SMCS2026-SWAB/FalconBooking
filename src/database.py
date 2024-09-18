from datetime import datetime, timedelta
from os import environ

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

from utils import Booking, Room

load_dotenv()

client = MongoClient(environ["MONGODB_URI"])
db = client["falconbooking"]


def schedule_booking(date: str, block: str, room: str, name: str, repeat: str, end_date: str, **kwargs) -> None:
    """Schedules a booking for the assigned date and block for a designated room assigned to a name."""
    bookings = db["bookings"]

    if bookings.find_one({"date": date, "block": block, "room": room}):
        return  # Make sure to not override bookings

    bookings.insert_one(
        {
            "date": date,
            "block": block,
            "room": room,
            "name": name,
            "repeat": repeat,
            "end_date": end_date,
            "exclude": []
        }
    )


def add_one_to_visits() -> None:
    visits = db["visits"]
    document_id = "66eabb5e906ced1769247f71"

    visit_count = visits.find_one({"_id": ObjectId(document_id)})["visits"] + 1
    visits.update_one({"_id": ObjectId(document_id)}, {"$set": {"visits": visit_count}})


def exclude_day_from_booking(entry_id: str, date: str) -> None:
    bookings = db["bookings"]
    booking_in_db = bookings.find_one({"_id": ObjectId(entry_id)})
    booking_in_db["exclude"].append(date)

    bookings.update_one({"_id": ObjectId(entry_id)}, {"$set": booking_in_db})


def remove_database_booking(entry_id: str) -> None:
    """Removes a booking from the MongoDB database."""
    bookings = db["bookings"]
    bookings.delete_one({"_id": ObjectId(entry_id)})


def remove_database_bookings_before_day(day: datetime) -> None:
    """Removes all bookings before a certain day in the MongoDB database."""
    bookings = db["bookings"]
    bookings.delete_many({"date": (day - timedelta(days=1)).strftime("%m/%d/%Y"), "repeat": "Never"})


def serialize_booking_for_room(date: datetime, room: str) -> Booking:
    """Serializes the bookings from the database for a specific room into their respective class."""
    bookings = db["bookings"]
    formatted_date = date.strftime("%m/%d/%Y")
    all_bookings = bookings.find()

    room_bookings = []

    # Serialize bookings for normal bookings, daily repeats and weekly repeats
    for booking in all_bookings:
        calendar_year_to_stop = datetime.today().year + 1 if 8 <= datetime.today().month <= 12 else datetime.today().year
        default_end_date = datetime(year=calendar_year_to_stop, month=7, day=1)

        # Temporary solution until every booking has an end date.
        end_date = datetime.strptime(booking.get("end_date", default_end_date.strftime('%m/%d/%Y')), "%m/%d/%Y")

        if booking["date"] == formatted_date and booking["room"] == room and formatted_date not in booking["exclude"]:
            room_bookings.append(booking)
        elif (
            booking["repeat"] == "Daily"
            and booking["room"] == room
            and formatted_date not in booking["exclude"]
            and booking not in room_bookings
            and date <= end_date
        ):
            room_bookings.append(booking)
        elif (
            booking["repeat"] == "Weekly"
            and booking["room"] == room
            and (date - datetime.strptime(booking["date"], "%m/%d/%Y")).days % 7 == 0
            and formatted_date not in booking["exclude"]
            and booking not in room_bookings
            and date <= end_date
        ):
            room_bookings.append(booking)

    return Booking(
        [booking["block"] for booking in room_bookings],
        {booking["block"]: booking["name"] for booking in room_bookings},
        {booking["block"]: booking["repeat"] for booking in room_bookings},
        {booking["block"]: booking["_id"] for booking in room_bookings}
    )


def populate_rooms_on_day(date: datetime, rooms: list[Room]) -> list[Room]:
    """Populates a list of rooms for the bookings on that day."""
    return [room.with_bookings(serialize_booking_for_room(date, room.name)) for room in rooms]
