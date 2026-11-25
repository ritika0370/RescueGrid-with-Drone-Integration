"""
Seed Demo Data Script.
Initializes test users (Admin, Officer, Pilot, Citizens), departments,
drone stations, and available drones.
"""
import asyncio
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.core.security import hash_password
from app.models.department import Department
from app.models.drone import Drone, DroneStation
from app.models.user import User


async def seed():
    print("[*] Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # 1. Seed Departments
        print("[*] Seeding Emergency Departments...")
        existing_dept = await db.execute(select(Department).where(Department.name == "Metro Fire & Rescue"))
        if not existing_dept.scalar_one_or_none():
            fire_dept = Department(
                name="Metro Fire & Rescue",
                department_type="FIRE",
                service_area={"type": "Polygon", "description": "Metro downtown and northern district"},
                latitude=37.7749,
                longitude=-122.4194,
                contact_information={"phone": "555-0100", "radio": "Channel 4-Alpha", "email": "dispatch@metrofire.gov"},
                status="ACTIVE",
                supported_categories=["Fire", "Building collapse", "Industrial or chemical incident", "Road accident"],
            )
            disaster_dept = Department(
                name="Regional Disaster & Flood Response Agency",
                department_type="DISASTER_RESPONSE",
                service_area={"type": "Polygon", "description": "Full river basin and low-lying sectors"},
                latitude=37.7800,
                longitude=-122.4100,
                contact_information={"phone": "555-0200", "radio": "Channel 9-Echo", "email": "command@disaster.gov"},
                status="ACTIVE",
                supported_categories=["Flood", "Earthquake", "Missing or trapped person", "Other emergency"],
            )
            medical_dept = Department(
                name="Metro Emergency Medical Services",
                department_type="MEDICAL",
                service_area={"type": "Polygon", "description": "Citywide medical triage response"},
                latitude=37.7700,
                longitude=-122.4300,
                contact_information={"phone": "555-0300", "radio": "Channel 1-Med", "email": "ems@metromedical.gov"},
                status="ACTIVE",
                supported_categories=["Medical emergency", "Road accident"],
            )
            db.add_all([fire_dept, disaster_dept, medical_dept])
            await db.commit()
            await db.refresh(fire_dept)
            await db.refresh(disaster_dept)
            print("    [+] Departments created.")
        else:
            res = await db.execute(select(Department).where(Department.name == "Regional Disaster & Flood Response Agency"))
            disaster_dept = res.scalar_one()

        # 2. Seed Users
        print("[*] Seeding Authorized Users...")
        existing_user = await db.execute(select(User).where(User.email == "officer.john@disaster.org"))
        if not existing_user.scalar_one_or_none():
            users = [
                User(
                    name="Admin Commander",
                    email="admin@disaster.org",
                    phone="+15550009999",
                    password_hash=hash_password("Password123!"),
                    role="admin",
                    is_active=True,
                ),
                User(
                    name="Officer John Commander",
                    email="officer.john@disaster.org",
                    phone="+15550001001",
                    password_hash=hash_password("Password123!"),
                    role="officer",
                    department_id=disaster_dept.id,
                    is_active=True,
                ),
                User(
                    name="Pilot Sarah Sky",
                    email="pilot.sarah@rescue.org",
                    phone="+15550002002",
                    password_hash=hash_password("Password123!"),
                    role="pilot",
                    department_id=disaster_dept.id,
                    is_active=True,
                ),
                User(
                    name="Citizen Alice",
                    email="alice@citizen.org",
                    phone="+15550003001",
                    password_hash=hash_password("Password123!"),
                    role="citizen",
                    is_active=True,
                ),
                User(
                    name="Citizen Bob",
                    email="bob@citizen.org",
                    phone="+15550003002",
                    password_hash=hash_password("Password123!"),
                    role="citizen",
                    is_active=True,
                ),
            ]
            db.add_all(users)
            await db.commit()
            print("    [+] Users created (Admin, Officer, Pilot, Citizens).")

        # 3. Seed Drone Station and Drones
        print("[*] Seeding Drone Stations & Telemetry Fleet...")
        existing_station = await db.execute(select(DroneStation).where(DroneStation.name == "North Sector Station Alpha"))
        if not existing_station.scalar_one_or_none():
            station = DroneStation(
                name="North Sector Station Alpha",
                department_id=disaster_dept.id,
                latitude=37.7810,
                longitude=-122.4110,
                status="OPERATIONAL",
            )
            db.add(station)
            await db.commit()
            await db.refresh(station)

            drones = [
                Drone(
                    model="DJI Matrice 300 RTK (Disaster Survey Spec)",
                    station_id=station.id,
                    latitude=37.7812,
                    longitude=-122.4112,
                    battery_percentage=96.0,
                    availability_status="AVAILABLE",
                    max_range_km=15.0,
                    max_flight_time_min=45,
                    is_simulated=True,
                ),
                Drone(
                    model="Autel EVO II Dual 640T (Thermal Scout)",
                    station_id=station.id,
                    latitude=37.7815,
                    longitude=-122.4115,
                    battery_percentage=88.0,
                    availability_status="AVAILABLE",
                    max_range_km=12.0,
                    max_flight_time_min=38,
                    is_simulated=True,
                ),
            ]
            db.add_all(drones)
            await db.commit()
            print("    [+] Drone station and fleet registered.")

    print("\n[SUCCESS] Seed demo database populated successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
