"""
app/database/seed.py

Database seeding script for development and demo environments.

Creates all tables (idempotent — skips tables that already exist) then
inserts representative seed data for all five user roles, plus sample
disasters, resources, hospitals, shelters, and notifications.

Usage
-----
Run as a module from the project root (with .venv active):

    python -m app.database.seed

Run with --reset to drop and recreate tables before seeding:

    python -m app.database.seed --reset

Idempotency
-----------
Each seed section checks for the existence of a seed record before
inserting. Re-running the script against a populated database is safe
and will not create duplicate records.
"""

from __future__ import annotations

import argparse
import logging
import secrets
import string
import sys
import uuid
from datetime import datetime, timezone

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database.database import Base, engine
from app.database.session import SessionLocal
from app.models.assignment import Assignment
from app.models.disaster import Disaster
from app.models.emergency_report import EmergencyReport
from app.models.enums import (
    AssignmentStatus,
    DisasterSeverity,
    DisasterStatus,
    NotificationPriority,
    ResourceStatus,
    RoleEnum,
)
from app.models.hospital import Hospital
from app.models.notification import Notification
from app.models.prediction import Prediction
from app.models.resource import Resource
from app.models.shelter import Shelter
from app.models.user import User

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | seed | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("seed")

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash(plain: str) -> str:
    return _pwd_context.hash(plain)


def _generate_password() -> str:
    """Generate a random password satisfying the app's complexity policy
    (>=8 chars, upper, lower, digit, special)."""
    required = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    pool = string.ascii_letters + string.digits + "!@#$%^&*"
    required += [secrets.choice(pool) for _ in range(8)]
    secrets.SystemRandom().shuffle(required)
    return "".join(required)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _exists(db: Session, model: type, **filters: object) -> bool:
    """Return True if at least one matching record exists."""
    return db.query(model).filter_by(**filters).first() is not None


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------
def seed_users(db: Session) -> dict[str, User]:
    """Insert one demo user per role. Returns a {role_key: User} mapping."""
    log.info("Seeding users …")
    users: dict[str, User] = {}

    definitions = [
        {
            "key": "government",
            "full_name": "Arjun Krishnamurthy",
            "email": "gov.admin@tn.gov.in",
            "phone": "+919876543210",
            "role": RoleEnum.GOVERNMENT,
            "organization_name": "Tamil Nadu Disaster Management Authority",
            "district": "Chennai",
            "state": "Tamil Nadu",
        },
        {
            "key": "ngo",
            "full_name": "Priya Subramaniam",
            "email": "priya@redcross.in",
            "phone": "+919876543211",
            "role": RoleEnum.NGO,
            "organization_name": "Red Cross India — Tamil Nadu Chapter",
            "district": "Chennai",
            "state": "Tamil Nadu",
        },
        {
            "key": "volunteer",
            "full_name": "Vikram Natarajan",
            "email": "vikram.volunteer@gmail.com",
            "phone": "+919876543212",
            "role": RoleEnum.VOLUNTEER,
            "organization_name": None,
            "district": "Coimbatore",
            "state": "Tamil Nadu",
        },
        {
            "key": "hospital",
            "full_name": "Dr. Meera Anand",
            "email": "meera@apollochennai.in",
            "phone": "+919876543213",
            "role": RoleEnum.HOSPITAL,
            "organization_name": "Apollo Hospitals Chennai",
            "district": "Chennai",
            "state": "Tamil Nadu",
        },
        {
            "key": "citizen",
            "full_name": "Ramesh Kumar",
            "email": "ramesh.citizen@gmail.com",
            "phone": "+919876543214",
            "role": RoleEnum.CITIZEN,
            "organization_name": None,
            "district": "Madurai",
            "state": "Tamil Nadu",
        },
    ]

    # The government admin account keeps a fixed password: it's used by the
    # frontend's auto-login and documented in the README as the primary demo
    # login, so it must stay predictable. Every other seeded account gets a
    # random password printed to the console below.
    generated_passwords: dict[str, str] = {}

    for defn in definitions:
        key: str = defn.pop("key")  # type: ignore[assignment]
        if _exists(db, User, email=defn["email"]):
            log.info("  User %s already exists — skipping.", defn["email"])
            users[key] = db.query(User).filter_by(email=defn["email"]).one()
            continue

        if key == "government":
            plain_password = "ResQMesh@2024!"
        else:
            plain_password = _generate_password()
            generated_passwords[defn["email"]] = plain_password

        user = User(
            **defn,  # type: ignore[arg-type]
            password_hash=_hash(plain_password),
            country="India",
            is_active=True,
        )
        db.add(user)
        db.flush()
        users[key] = user
        log.info("  Created user: %s (%s)", user.full_name, user.role)

    db.commit()

    if generated_passwords:
        log.info("=" * 70)
        log.info("Generated demo account passwords (shown once, not stored anywhere):")
        for email, pw in generated_passwords.items():
            log.info("  %s : %s", email, pw)
        log.info("=" * 70)

    return users


def seed_hospitals(db: Session) -> list[Hospital]:
    """Insert demo hospital records."""
    log.info("Seeding hospitals …")
    hospitals: list[Hospital] = []

    definitions = [
        {
            "hospital_name": "Apollo Hospitals Chennai",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "available_beds": 320,
            "icu_beds": 48,
            "ventilators": 20,
            "ambulances": 12,
            "blood_units": 150,
            "oxygen_units": 200,
            "contact_number": "+914428298898",
        },
        {
            "hospital_name": "Coimbatore Medical College Hospital",
            "latitude": 11.0168,
            "longitude": 76.9558,
            "available_beds": 480,
            "icu_beds": 60,
            "ventilators": 30,
            "ambulances": 8,
            "blood_units": 200,
            "oxygen_units": 300,
            "contact_number": "+914222301393",
        },
        {
            "hospital_name": "Government Rajaji Hospital Madurai",
            "latitude": 9.9252,
            "longitude": 78.1198,
            "available_beds": 600,
            "icu_beds": 80,
            "ventilators": 40,
            "ambulances": 10,
            "blood_units": 250,
            "oxygen_units": 350,
            "contact_number": "+914522532535",
        },
    ]

    for defn in definitions:
        if _exists(db, Hospital, hospital_name=defn["hospital_name"]):
            log.info("  Hospital '%s' already exists — skipping.", defn["hospital_name"])
            hospitals.append(
                db.query(Hospital).filter_by(hospital_name=defn["hospital_name"]).one()
            )
            continue
        hospital = Hospital(**defn)  # type: ignore[arg-type]
        db.add(hospital)
        db.flush()
        hospitals.append(hospital)
        log.info("  Created hospital: %s", hospital.hospital_name)

    db.commit()
    return hospitals


def seed_shelters(db: Session) -> list[Shelter]:
    """Insert demo shelter records."""
    log.info("Seeding shelters …")
    shelters: list[Shelter] = []

    definitions = [
        {
            "shelter_name": "Anna Centenary Library Evacuation Centre",
            "latitude": 13.0451,
            "longitude": 80.2483,
            "capacity": 2000,
            "current_occupancy": 450,
            "contact_number": "+914428521547",
        },
        {
            "shelter_name": "SBOA School Relief Camp — Coimbatore",
            "latitude": 11.0168,
            "longitude": 76.9558,
            "capacity": 800,
            "current_occupancy": 120,
            "contact_number": "+914222345678",
        },
        {
            "shelter_name": "Meenakshi College Disaster Relief Centre",
            "latitude": 9.9252,
            "longitude": 78.1198,
            "capacity": 1200,
            "current_occupancy": 0,
            "contact_number": "+914452456789",
        },
    ]

    for defn in definitions:
        if _exists(db, Shelter, shelter_name=defn["shelter_name"]):
            log.info("  Shelter '%s' already exists — skipping.", defn["shelter_name"])
            shelters.append(
                db.query(Shelter).filter_by(shelter_name=defn["shelter_name"]).one()
            )
            continue
        shelter = Shelter(**defn)  # type: ignore[arg-type]
        db.add(shelter)
        db.flush()
        shelters.append(shelter)
        log.info("  Created shelter: %s (%d/%d)", shelter.shelter_name, shelter.current_occupancy, shelter.capacity)

    db.commit()
    return shelters


def seed_disasters(db: Session, users: dict[str, User]) -> list[Disaster]:
    """Insert demo disaster records."""
    log.info("Seeding disasters …")
    disasters: list[Disaster] = []

    definitions = [
        {
            "title": "Chennai Coastal Flooding — 2024 Northeast Monsoon",
            "description": (
                "Severe flooding across coastal areas of Chennai following prolonged northeast "
                "monsoon rains. Velachery, Adyar, and Mylapore zones critically affected. "
                "Road networks and power infrastructure disrupted."
            ),
            "disaster_type": "flood",
            "severity": DisasterSeverity.CRITICAL,
            "status": DisasterStatus.RESCUE_ONGOING,
            "latitude": 13.0827,
            "longitude": 80.2707,
            "district": "Chennai",
            "state": "Tamil Nadu",
        },
        {
            "title": "Coimbatore District Earthquake — M4.8",
            "description": (
                "Magnitude 4.8 earthquake centred 15 km northeast of Coimbatore city. "
                "Structural damage reported in Singanallur and Saravanampatti. "
                "No fatalities confirmed; 23 injuries reported."
            ),
            "disaster_type": "earthquake",
            "severity": DisasterSeverity.HIGH,
            "status": DisasterStatus.VERIFIED,
            "latitude": 11.0168,
            "longitude": 76.9558,
            "district": "Coimbatore",
            "state": "Tamil Nadu",
        },
        {
            "title": "Madurai Chemical Plant Incident",
            "description": (
                "Minor chemical leak at an industrial plant in Madurai. "
                "Evacuation zone of 500m radius established. Air quality monitoring active."
            ),
            "disaster_type": "industrial_accident",
            "severity": DisasterSeverity.MEDIUM,
            "status": DisasterStatus.RESOURCE_ALLOCATED,
            "latitude": 9.9252,
            "longitude": 78.1198,
            "district": "Madurai",
            "state": "Tamil Nadu",
        },
    ]

    for defn in definitions:
        if _exists(db, Disaster, title=defn["title"]):
            log.info("  Disaster '%s' already exists — skipping.", defn["title"])
            disasters.append(db.query(Disaster).filter_by(title=defn["title"]).one())
            continue
        disaster = Disaster(
            **defn,  # type: ignore[arg-type]
            reported_by=users["government"].id,
            country="India",
        )
        db.add(disaster)
        db.flush()
        disasters.append(disaster)
        log.info("  Created disaster: %s [%s]", disaster.title, disaster.severity)

    db.commit()
    return disasters


def seed_resources(db: Session, disasters: list[Disaster]) -> list[Resource]:
    """Insert demo resource records."""
    log.info("Seeding resources …")
    resources: list[Resource] = []
    chennai_disaster = disasters[0]

    definitions = [
        {
            "resource_type": "food_packet",
            "quantity": 5000,
            "available_quantity": 2500,
            "location": "Chennai Central Depot — Koyambedu",
            "status": ResourceStatus.ALLOCATED,
            "assigned_disaster": chennai_disaster.id,
        },
        {
            "resource_type": "drinking_water",
            "quantity": 10000,
            "available_quantity": 6000,
            "location": "Chennai Central Depot — Koyambedu",
            "status": ResourceStatus.ALLOCATED,
            "assigned_disaster": chennai_disaster.id,
        },
        {
            "resource_type": "medical_kit",
            "quantity": 500,
            "available_quantity": 500,
            "location": "Apollo Hospitals Chennai — Warehouse",
            "status": ResourceStatus.AVAILABLE,
            "assigned_disaster": None,
        },
        {
            "resource_type": "rescue_boat",
            "quantity": 20,
            "available_quantity": 8,
            "location": "Chennai Marina Coast Guard Station",
            "status": ResourceStatus.IN_TRANSIT,
            "assigned_disaster": chennai_disaster.id,
        },
        {
            "resource_type": "generator",
            "quantity": 30,
            "available_quantity": 30,
            "location": "TNEB Regional Office — Coimbatore",
            "status": ResourceStatus.AVAILABLE,
            "assigned_disaster": None,
        },
    ]

    for defn in definitions:
        if _exists(db, Resource, resource_type=defn["resource_type"], location=defn["location"]):
            log.info(
                "  Resource '%s' at '%s' already exists — skipping.",
                defn["resource_type"],
                defn["location"],
            )
            resources.append(
                db.query(Resource)
                .filter_by(resource_type=defn["resource_type"], location=defn["location"])
                .one()
            )
            continue
        resource = Resource(**defn)  # type: ignore[arg-type]
        db.add(resource)
        db.flush()
        resources.append(resource)
        log.info(
            "  Created resource: %s (%d/%d) [%s]",
            resource.resource_type,
            resource.available_quantity,
            resource.quantity,
            resource.status,
        )

    db.commit()
    return resources


def seed_emergency_reports(
    db: Session, users: dict[str, User], disasters: list[Disaster]
) -> list[EmergencyReport]:
    """Insert demo emergency reports."""
    log.info("Seeding emergency reports …")
    reports: list[EmergencyReport] = []

    definitions = [
        {
            "reporter_name": "Ramesh Kumar",
            "phone": "+919876543214",
            "description": (
                "Water level has risen above 3 feet in Velachery Main Road. "
                "Approximately 200 families stranded. Immediate boat rescue required."
            ),
            "latitude": 12.9778,
            "longitude": 80.2209,
            "image_url": None,
            "reported_at": _now(),
            "reported_by_user_id": users["citizen"].id,
            "linked_disaster_id": disasters[0].id,
        },
        {
            "reporter_name": "Anonymous Citizen",
            "phone": "+919876500001",
            "description": (
                "Crack observed in wall of residential building in Singanallur after earthquake. "
                "Residents evacuated to street. Need structural assessment team."
            ),
            "latitude": 11.0168,
            "longitude": 76.9558,
            "image_url": None,
            "reported_at": _now(),
            "reported_by_user_id": None,  # Anonymous report
            "linked_disaster_id": disasters[1].id,
        },
    ]

    for defn in definitions:
        if _exists(
            db,
            EmergencyReport,
            reporter_name=defn["reporter_name"],
            linked_disaster_id=defn["linked_disaster_id"],
        ):
            log.info(
                "  Report from '%s' already exists — skipping.", defn["reporter_name"]
            )
            continue
        report = EmergencyReport(**defn)  # type: ignore[arg-type]
        db.add(report)
        db.flush()
        reports.append(report)
        log.info("  Created report from: %s", report.reporter_name)

    db.commit()
    return reports


def seed_predictions(db: Session, disasters: list[Disaster]) -> list[Prediction]:
    """Insert demo AI prediction records."""
    log.info("Seeding predictions …")
    predictions: list[Prediction] = []

    definitions = [
        {
            "prediction": (
                "Flood waters expected to recede within 48–72 hours pending cessation of rainfall. "
                "Critical resource demand: 8,000 food packets, 15,000 water units over 72 hours. "
                "Recommend pre-positioning rescue boats at Marina and Adyar river mouth."
            ),
            "confidence_score": 0.87,
            "input_features": {
                "rainfall_mm_24h": 180.5,
                "river_level_m": 4.2,
                "affected_area_km2": 28.3,
                "population_density": 26903,
                "historical_flood_count": 7,
            },
            "predicted_at": _now(),
            "disaster_id": disasters[0].id,
        },
        {
            "prediction": (
                "Aftershock probability of M3.0+ within 72 hours estimated at 62%. "
                "Recommend structural inspection of all buildings within 2 km radius. "
                "Hospital surge capacity activation advised."
            ),
            "confidence_score": 0.74,
            "input_features": {
                "magnitude": 4.8,
                "depth_km": 12.5,
                "epicentre_population_density": 8200,
                "soil_type": "alluvial",
                "aftershock_probability_72h": 0.62,
            },
            "predicted_at": _now(),
            "disaster_id": disasters[1].id,
        },
    ]

    for defn in definitions:
        if _exists(db, Prediction, disaster_id=defn["disaster_id"]):
            log.info(
                "  Prediction for disaster %s already exists — skipping.", defn["disaster_id"]
            )
            continue
        prediction = Prediction(**defn)  # type: ignore[arg-type]
        db.add(prediction)
        db.flush()
        predictions.append(prediction)
        log.info(
            "  Created prediction for disaster %s (confidence=%.2f)",
            prediction.disaster_id,
            prediction.confidence_score,
        )

    db.commit()
    return predictions


def seed_assignments(
    db: Session,
    users: dict[str, User],
    disasters: list[Disaster],
    resources: list[Resource],
    hospitals: list[Hospital],
) -> list[Assignment]:
    """Insert demo assignment records."""
    log.info("Seeding assignments …")
    assignments: list[Assignment] = []

    definitions = [
        {
            "volunteer_id": users["volunteer"].id,
            "disaster_id": disasters[0].id,
            "status": AssignmentStatus.IN_PROGRESS,
            "resource_id": None,
            "ngo_id": None,
            "hospital_id": None,
        },
        {
            "ngo_id": users["ngo"].id,
            "disaster_id": disasters[0].id,
            "status": AssignmentStatus.IN_PROGRESS,
            "resource_id": None,
            "volunteer_id": None,
            "hospital_id": None,
        },
        {
            "hospital_id": hospitals[0].id,
            "disaster_id": disasters[0].id,
            "status": AssignmentStatus.PENDING,
            "resource_id": None,
            "volunteer_id": None,
            "ngo_id": None,
        },
        {
            "resource_id": resources[0].id,
            "disaster_id": disasters[0].id,
            "status": AssignmentStatus.IN_PROGRESS,
            "volunteer_id": None,
            "ngo_id": None,
            "hospital_id": None,
        },
    ]

    for defn in definitions:
        assignment = Assignment(
            **defn,  # type: ignore[arg-type]
            assigned_at=_now(),
        )
        db.add(assignment)
        db.flush()
        assignments.append(assignment)
        log.info("  Created assignment: %s [%s]", assignment.id, assignment.status)

    db.commit()
    return assignments


def seed_notifications(
    db: Session, users: dict[str, User], disasters: list[Disaster]
) -> list[Notification]:
    """Insert demo notification records."""
    log.info("Seeding notifications …")
    notifications: list[Notification] = []

    definitions = [
        {
            "title": "CRITICAL ALERT: Chennai Coastal Flooding — Emergency Response Activated",
            "message": (
                "All government response teams are immediately activated. "
                "Report to Chennai DDMA control room. "
                "Rescue operations underway in Velachery, Adyar, and Mylapore zones."
            ),
            "priority": NotificationPriority.CRITICAL,
            "recipient_role": RoleEnum.GOVERNMENT,
            "recipient_id": None,
            "is_read": False,
        },
        {
            "title": "Resource Deployment Request — NGO Coordination Required",
            "message": (
                "Red Cross and all registered NGOs are requested to deploy relief teams "
                "to Chennai Velachery distribution point by 18:00 IST today. "
                "Contact: TNSDMA Control Room +914428521547."
            ),
            "priority": NotificationPriority.HIGH,
            "recipient_role": RoleEnum.NGO,
            "recipient_id": None,
            "is_read": False,
        },
        {
            "title": "Volunteer Deployment — Immediate Reporting Required",
            "message": (
                "All registered volunteers in Chennai district are required to report to "
                "the Anna Centenary Library Evacuation Centre immediately for assignment."
            ),
            "priority": NotificationPriority.HIGH,
            "recipient_role": RoleEnum.VOLUNTEER,
            "recipient_id": None,
            "is_read": False,
        },
        {
            "title": "Hospital Surge Protocol — Activate Disaster Beds",
            "message": (
                "All registered hospitals in Chennai are required to activate disaster surge "
                "protocols. Please update bed availability on the ResQMesh portal immediately."
            ),
            "priority": NotificationPriority.HIGH,
            "recipient_role": RoleEnum.HOSPITAL,
            "recipient_id": None,
            "is_read": False,
        },
        {
            "title": "Safety Advisory: Flood Zones — Citizen Guidance",
            "message": (
                "Citizens in Velachery, Adyar, and Mylapore are advised to evacuate to "
                "designated shelters immediately. Do not attempt to cross flooded roads. "
                "Helpline: 1077."
            ),
            "priority": NotificationPriority.CRITICAL,
            "recipient_role": RoleEnum.CITIZEN,
            "recipient_id": None,
            "is_read": False,
        },
        {
            "title": "Your Emergency Report Has Been Received",
            "message": (
                "Your emergency report regarding flooding in Velachery has been received "
                "and linked to the Chennai Coastal Flooding response operation. "
                "A rescue team has been dispatched to your area."
            ),
            "priority": NotificationPriority.MEDIUM,
            "recipient_role": None,
            "recipient_id": users["citizen"].id,
            "is_read": False,
        },
    ]

    for defn in definitions:
        notification = Notification(**defn)  # type: ignore[arg-type]
        db.add(notification)
        db.flush()
        notifications.append(notification)
        log.info(
            "  Created notification: '%s' [%s → %s]",
            notification.title[:50],
            notification.priority,
            notification.recipient_role or f"user:{notification.recipient_id}",
        )

    db.commit()
    return notifications


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def create_tables(reset: bool = False) -> None:
    """Create (or recreate) all database tables."""
    if reset:
        log.warning("--reset flag active: dropping all existing tables …")
        Base.metadata.drop_all(bind=engine)
        log.info("All tables dropped.")

    log.info("Creating tables (if not exists) …")
    Base.metadata.create_all(bind=engine)
    log.info("Table creation complete.")


def run_seed() -> None:
    """Execute the full seed sequence within a managed session."""
    db: Session = SessionLocal()
    try:
        users = seed_users(db)
        hospitals = seed_hospitals(db)
        shelters = seed_shelters(db)
        disasters = seed_disasters(db, users)
        resources = seed_resources(db, disasters)
        seed_emergency_reports(db, users, disasters)
        seed_predictions(db, disasters)
        assignments = seed_assignments(db, users, disasters, resources, hospitals)
        seed_notifications(db, users, disasters)

        log.info(
            "Seed complete. Summary: %d users, %d hospitals, %d shelters, "
            "%d disasters, %d resources, %d assignments.",
            len(users),
            len(hospitals),
            len(shelters),
            len(disasters),
            len(resources),
            len(assignments),
        )
    except Exception:
        db.rollback()
        log.exception("Seed failed — transaction rolled back.")
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the ResQMesh database with demo data."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables before seeding (destructive).",
    )
    args = parser.parse_args()

    create_tables(reset=args.reset)
    run_seed()


if __name__ == "__main__":
    main()
