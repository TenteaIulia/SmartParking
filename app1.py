from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import cv2
import numpy as np
import easyocr
from datetime import datetime, timedelta
import os
import re
import logging
import requests

reader = easyocr.Reader(['en'], gpu=False)
app = Flask(__name__)
app.json.ensure_ascii = False
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

class IgnoreApiLogs(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()

        if "/api/led-events" in msg:
            return False

        if "/api/free-spots" in msg:
            return False

        return True

logging.getLogger("werkzeug").addFilter(IgnoreApiLogs())

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="parking_user",
        password="1234",
        database="smart_parking",
        auth_plugin="mysql_native_password"
    )

def extract_plate_from_image(image_bytes):
    print("### OCR RULEAZA ###")

    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        return None

    images_to_try = [
        image,
        cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE),
        cv2.rotate(image, cv2.ROTATE_180),
        cv2.flip(image, 1),
        cv2.flip(image, 0),
        cv2.flip(cv2.rotate(image, cv2.ROTATE_180), 1),
    ]

    patterns = [
        r'^[A-Z]{2}[0-9]{2}[A-Z]{3}$',
        r'^[A-Z]{2}[0-9]{3}[A-Z]{3}$',
        r'^B[0-9]{2}[A-Z]{3}$',
        r'^B[0-9]{3}[A-Z]{3}$'
    ]

    valid_counties = {
        "AB", "AR", "AG", "BC", "BH", "BN", "BT", "BV", "BR", "BZ",
        "CS", "CL", "CJ", "CT", "CV", "DB", "DJ", "GL", "GR", "GJ",
        "HR", "HD", "IL", "IS", "IF", "MM", "MH", "MS", "NT", "OT",
        "PH", "SM", "SJ", "SB", "SV", "TR", "TM", "TL", "VS", "VL",
        "VN", "B"
    }

    def normalize_plate(raw):
        cleaned = raw.upper()
        cleaned = ''.join(ch for ch in cleaned if ch.isalnum())

        if len(cleaned) < 6 or len(cleaned) > 8:
            return []

        candidates = [
            cleaned,
            cleaned[::-1]
        ]

        normalized_candidates = []

        for cand in candidates:
            chars = list(cand)

            if cand.startswith("B"):
                digit_positions = [1, 2, 3]
            else:
                digit_positions = [2, 3, 4]

            for i in range(len(chars)):
                if i in digit_positions:
                    chars[i] = (
                        chars[i]
                        .replace("O", "0")
                        .replace("I", "1")
                        .replace("L", "1")
                        .replace("S", "5")
                        .replace("B", "8")
                        .replace("Z", "2")
                    )
                else:
                    chars[i] = (
                        chars[i]
                        .replace("0", "O")
                        .replace("1", "I")
                        .replace("5", "S")
                        .replace("8", "B")
                        .replace("2", "Z")
                    )

            normalized_candidates.append(''.join(chars))

        return normalized_candidates
         

    for img in images_to_try:
        variants = [img]

        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)

            _, thresh = cv2.threshold(
                gray,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            variants.append(gray)
            variants.append(thresh)


        except Exception as err:
            print("Eroare preprocesare:", err)

        for variant in variants:
            results = reader.readtext(
                variant,
                allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
                decoder="beamsearch"
            )

            for result in results:
                text = result[1]
                confidence = result[2]

                normalized_list = normalize_plate(text)

                for cleaned in normalized_list:
                    county = "B" if cleaned.startswith("B") else cleaned[:2]

                    if county not in valid_counties:
                        print("IGNORAT JUDET:", cleaned)
                        continue

                    valid = any(re.match(p, cleaned) for p in patterns)

                    print(
                        "OCR CANDIDAT:",
                        cleaned,
                        "CONF:",
                        confidence,
                        "VALID:",
                        valid
                    )

                    if valid and confidence > 0.15:
                        print("PLACA GASITA:", cleaned)
                        return cleaned
                    

    print("PLACA DETECTATA: None")
    return None

def has_capacity_for_reservation(cursor, zone_id, start_dt, end_dt):
    cursor.execute("""
        SELECT total_spots
        FROM parking_zones
        WHERE id = %s AND status = 'active'
        LIMIT 1
    """, (zone_id,))
    zone = cursor.fetchone()

    if not zone:
        return False

    total_spots = int(zone["total_spots"])

    cursor.execute("""
        SELECT COUNT(*) AS overlapping_count
        FROM parking_reservations
        WHERE zone_id = %s
          AND status = 'active'
          AND (%s < reservation_end AND %s > reservation_start)
    """, (zone_id, start_dt, end_dt))

    overlapping_count = int(cursor.fetchone()["overlapping_count"])

    return overlapping_count < total_spots

def expire_unused_reservations():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        grace_minutes = 15
        cutoff_time = datetime.now() - timedelta(minutes=grace_minutes)

        cursor.execute("""
            SELECT 
                pr.id,
                pr.zone_id,
                pr.spot_id,
                pr.reservation_start,
                pr.reservation_end,
                pz.price_per_hour
            FROM parking_reservations pr
            JOIN parking_zones pz ON pr.zone_id = pz.id
            LEFT JOIN parking_sessions ps
                ON pr.id = ps.reservation_id
                AND ps.status = 'active'
            WHERE pr.status = 'active'
              AND pr.reservation_start <= %s
              AND ps.id IS NULL
        """, (cutoff_time,))

        expired_reservations = cursor.fetchall()

        for reservation in expired_reservations:
            duration_hours = (
                reservation["reservation_end"] - reservation["reservation_start"]
            ).total_seconds() / 3600

            if duration_hours < 0:
                duration_hours = 0

            penalty_fee = round(duration_hours * float(reservation["price_per_hour"]), 2)

            cursor.execute("""
                UPDATE parking_reservations
                SET status = 'expired',
                    penalty_fee = %s,
                    notes = %s
                WHERE id = %s
            """, (
                penalty_fee,
                "No-show: Rezervarea a expirat fără intrare în parcare.",
                reservation["id"]
            ))

            cursor.execute("""
                UPDATE parking_spots
                SET status = 'free',
                    license_plate = NULL,
                    session_id = NULL,
                    reservation_id = NULL
                WHERE status = 'reserved'
                  AND (
                        reservation_id = %s
                        OR id = %s
                  )
            """, (
                reservation["id"],
                reservation["spot_id"]
            ))

        conn.commit()

    except mysql.connector.Error as err:
        print(f"Eroare la expirarea rezervărilor: {err}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def process_barrier_entry(license_plate, selected_zone_id=None, user_id=None, access_type="session"):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        now = datetime.now()
        license_plate = (license_plate or "").strip().upper()
        selected_zone_id = str(selected_zone_id).strip() if selected_zone_id is not None else ""

        if not license_plate:
            return {
                "success": False,
                "message": "Introdu numărul de înmatriculare."
            }

        cursor.execute("""
            SELECT id
            FROM parking_sessions
            WHERE license_plate = %s
              AND status = 'active'
            LIMIT 1
        """, (license_plate,))
        existing_active_session = cursor.fetchone()

        if existing_active_session:
            return {
                "success": False,
                "message": "Există deja o sesiune activă pentru acest număr de înmatriculare."
            }

        # 1. Caută rezervare activă validă acum
        cursor.execute("""
            SELECT pr.*, pz.zone_name
            FROM parking_reservations pr
            JOIN parking_zones pz ON pr.zone_id = pz.id
            WHERE pr.license_plate = %s
              AND pr.status = 'active'
              AND %s BETWEEN DATE_SUB(pr.reservation_start, INTERVAL 15 MINUTE)
                          AND pr.reservation_end
            ORDER BY pr.reservation_start ASC
            LIMIT 1
        """, (license_plate, now))

        reservation = cursor.fetchone()

        if reservation:
            cursor.execute("""
                SELECT id, spot_number
                FROM parking_spots
                WHERE id = %s
                  AND status = 'reserved'
                LIMIT 1
            """, (reservation["spot_id"],))

            spot = cursor.fetchone()

            if not spot:
                cursor.execute("""
                    SELECT id, spot_number
                    FROM parking_spots
                    WHERE zone_id = %s
                      AND status = 'free'
                    ORDER BY RAND()  -- Randomizează pentru a evita alocarea aceluiași loc de fiecare dată
                    LIMIT 1
                """, (reservation["zone_id"],))

                spot = cursor.fetchone()

                if not spot:
                    conn.rollback()
                    return {
                        "success": False,
                        "message": f"Nu există loc fizic liber în {reservation['zone_name']}."
                    }

                cursor.execute("""
                    UPDATE parking_spots
                    SET status = 'reserved',
                        license_plate = %s,
                        reservation_id = %s
                    WHERE id = %s
                """, (
                    license_plate,
                    reservation["id"],
                    spot["id"]
                ))

            cursor.execute("""
                INSERT INTO parking_sessions
                (user_id, zone_id, reservation_id, license_plate, start_time, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                reservation["user_id"],
                reservation["zone_id"],
                reservation["id"],
                license_plate,
                now,
                "active"
            ))

            session_id = cursor.lastrowid

            cursor.execute("""
                UPDATE parking_spots
                SET status = 'occupied',
                    license_plate = %s,
                    session_id = %s
                WHERE id = %s
            """, (
                license_plate,
                session_id,
                spot["id"]
            ))

            cursor.execute("""
                INSERT INTO led_events (zone_id, spot_number, duration_seconds, status)
                VALUES (%s, %s, 15, 'pending')
            """, (
                reservation["zone_id"],
                spot["spot_number"]
            ))

            conn.commit()

            return {
                "success": True,
                "message": f"Acces permis pe baza rezervării. Bariera s-a deschis pentru {reservation['zone_name']}, locul {spot['spot_number']}.",
                "zone_id": reservation["zone_id"],
                "zone_name": reservation["zone_name"],
                "spot_id": spot["id"],
                "spot_number": spot["spot_number"],
                "reservation_id": reservation["id"]
            }

        # 2. Verific dacă există rezervare expirată
        cursor.execute("""
            SELECT pr.id, pr.status, pr.reservation_start, pr.reservation_end, pz.zone_name
            FROM parking_reservations pr
            JOIN parking_zones pz ON pr.zone_id = pz.id
            WHERE pr.license_plate = %s
            ORDER BY pr.created_at DESC
            LIMIT 1
        """, (license_plate,))
        latest_reservation = cursor.fetchone()

        warning_message = None
        if latest_reservation and latest_reservation["status"] == "expired":
            warning_message = (
                "Rezervarea pentru acest număr este expirată. "
                "Poți intra doar fără rezervare, dacă selectezi o zonă și există locuri."
            )
        if access_type == "reservation":
            return {
                "success": False,
                "message": "Nu există rezervare activă pentru acest număr."
                }


        # 3. Intrare fără rezervare
        if not selected_zone_id:
            return {
                "success": False,
                "message": "Nu există rezervare activă validă. Selectează o zonă pentru acces fără rezervare.",
                "warning": warning_message
            }

        cursor.execute("""
            SELECT id, zone_name, status
            FROM parking_zones
            WHERE id = %s AND status = 'active'
            LIMIT 1
        """, (selected_zone_id,))
        zone = cursor.fetchone()

        if not zone:
            return {
                "success": False,
                "message": "Zona selectată nu este validă."
            }

        cursor.execute("""
            SELECT id, spot_number
            FROM parking_spots
            WHERE zone_id = %s
              AND status = 'free'
            ORDER BY spot_number ASC
            LIMIT 1
        """, (zone["id"],))

        spot = cursor.fetchone()

        if not spot:
            conn.rollback()
            return {
                "success": False,
                "message": f"Nu există loc fizic liber în {zone['zone_name']}."
            }

        cursor.execute("""
            INSERT INTO parking_sessions
            (user_id, zone_id, reservation_id, license_plate, start_time, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            zone["id"],
            None,
            license_plate,
            now,
            "active"
        ))

        session_id = cursor.lastrowid

        cursor.execute("""
            UPDATE parking_spots
            SET status = 'occupied',
                license_plate = %s,
                session_id = %s
            WHERE id = %s
        """, (
            license_plate,
            session_id,
            spot["id"]
        ))

        cursor.execute("""
            INSERT INTO led_events (zone_id, spot_number, duration_seconds, status)
            VALUES (%s, %s, 15, 'pending')
        """, (
            zone["id"],
            spot["spot_number"]
        ))

        conn.commit()

        return {
            "success": True,
            "message": f"Acces permis fără rezervare. Bariera s-a deschis pentru {zone['zone_name']}, locul {spot['spot_number']}.",
            "zone_id": zone["id"],
            "zone_name": zone["zone_name"],
            "spot_id": spot["id"],
            "spot_number": spot["spot_number"],
            "warning": warning_message
        }

    except mysql.connector.Error as err:
        if conn is not None:
            conn.rollback()
        return {
            "success": False,
            "message": f"Eroare MySQL: {err}"
        }

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def process_barrier_exit(license_plate):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        now = datetime.now()
        license_plate = (license_plate or "").strip().upper()

        if not license_plate:
            return {
                "success": False,
                "message": "Introdu numărul de înmatriculare."
            }

        cursor.execute("""
            SELECT 
                ps.*,
                pz.price_per_hour,
                pz.zone_name,
                pr.reservation_end,
                pr.notes,
                pr.payment_status AS reservation_payment_status,
                pr.reservation_cost
            FROM parking_sessions ps
            JOIN parking_zones pz ON ps.zone_id = pz.id
            LEFT JOIN parking_reservations pr ON ps.reservation_id = pr.id
            WHERE ps.license_plate = %s
              AND ps.status = 'active'
            ORDER BY ps.start_time ASC
            LIMIT 1
        """, (license_plate,))

        session_data = cursor.fetchone()

        if not session_data:
            return {
                "success": False,
                "message": "Nu există nicio sesiune activă pentru acest număr."
            }

        start_time = session_data["start_time"]
        price_per_hour = float(session_data["price_per_hour"])
        reservation_note = None
        total_cost = 0.00
        is_reservation_session = session_data["reservation_id"] is not None

        if is_reservation_session and session_data["reservation_end"] is not None:
            reservation_end = session_data["reservation_end"]

            if now <= reservation_end:
                total_cost = 0.00
            else:
                extra_minutes = (now - reservation_end).total_seconds() / 60
                if extra_minutes < 1:
                    extra_minutes = 1

                extra_hours = extra_minutes / 60
                total_cost = round(extra_hours * (price_per_hour * 2), 2)

                if total_cost < 1:
                    total_cost = 1.00

                reservation_note = "Ieșire după expirarea rezervării - tarif extra aplicat."
        else:
            duration_minutes = (now - start_time).total_seconds() / 60

            if duration_minutes < 1:
                duration_minutes = 1

            duration_hours = duration_minutes / 60
            total_cost = round(duration_hours * price_per_hour, 2)

            if total_cost < 1:
                total_cost = 1.00

        if is_reservation_session:
            reservation_paid = session_data.get("reservation_payment_status") == "paid"

            if not reservation_paid:
                return {
                    "success": False,
                    "payment_required": True,
                    "message": "Rezervarea nu este plătită.",
                    "session_id": session_data["id"],
                    "zone_name": session_data["zone_name"],
                    "total_cost": total_cost,
                    "payment_url": url_for("session_payment", session_id=session_data["id"])
                }

            if total_cost == 0:
                cursor.execute("""
                    UPDATE parking_sessions
                    SET end_time = %s,
                        total_cost = %s,
                        payment_status = 'paid',
                        status = 'finished'
                    WHERE id = %s
                """, (
                    now,
                    total_cost,
                    session_data["id"]
                ))

                cursor.execute("""
                    UPDATE parking_reservations
                    SET status = 'completed'
                    WHERE id = %s
                """, (
                    session_data["reservation_id"],
                ))

                cursor.execute("""
                    UPDATE parking_spots
                    SET status = 'free',
                        license_plate = NULL,
                        reservation_id = NULL,
                        session_id = NULL
                    WHERE session_id = %s
                """, (
                    session_data["id"],
                ))

                conn.commit()

                return {
                    "success": True,
                    "message": f"Ieșire permisă pe baza rezervării plătite din {session_data['zone_name']}.",
                    "zone_name": session_data["zone_name"],
                    "total_cost": total_cost
                }

            if session_data.get("payment_status") != "paid":
                cursor.execute("""
                    UPDATE parking_sessions
                    SET total_cost = %s,
                        payment_status = 'unpaid'
                    WHERE id = %s
                """, (
                    total_cost,
                    session_data["id"]
                ))

                if reservation_note:
                    cursor.execute("""
                        UPDATE parking_reservations
                        SET notes = %s
                        WHERE id = %s
                    """, (
                        reservation_note,
                        session_data["reservation_id"]
                    ))

                conn.commit()

                return {
                    "success": False,
                    "payment_required": True,
                    "message": f"Plată suplimentară necesară pentru depășirea rezervării. Cost extra: {total_cost} lei.",
                    "session_id": session_data["id"],
                    "zone_name": session_data["zone_name"],
                    "total_cost": total_cost,
                    "payment_url": url_for("session_payment", session_id=session_data["id"])
                }

            cursor.execute("""
                UPDATE parking_sessions
                SET end_time = %s,
                    total_cost = %s,
                    status = 'finished'
                WHERE id = %s
            """, (
                now,
                total_cost,
                session_data["id"]
            ))

            cursor.execute("""
                UPDATE parking_reservations
                SET status = 'completed',
                    notes = %s
                WHERE id = %s
            """, (
                reservation_note,
                session_data["reservation_id"]
            ))

            cursor.execute("""
                UPDATE parking_spots
                SET status = 'free',
                    license_plate = NULL,
                    reservation_id = NULL,
                    session_id = NULL
                WHERE session_id = %s
            """, (
                session_data["id"],
            ))

            conn.commit()

            return {
                "success": True,
                "message": f"Ieșire permisă după plata costului suplimentar din {session_data['zone_name']}.",
                "zone_name": session_data["zone_name"],
                "total_cost": total_cost
            }

        if session_data.get("payment_status") != "paid":
            cursor.execute("""
                UPDATE parking_sessions
                SET total_cost = %s,
                    payment_status = 'unpaid'
                WHERE id = %s
            """, (
                total_cost,
                session_data["id"]
            ))

            conn.commit()

            return {
                "success": False,
                "payment_required": True,
                "message": f"Plată necesară pentru ieșirea din {session_data['zone_name']}. Cost total: {total_cost} lei.",
                "session_id": session_data["id"],
                "zone_name": session_data["zone_name"],
                "total_cost": total_cost,
                "payment_url": url_for("session_payment", session_id=session_data["id"])
            }

        cursor.execute("""
            UPDATE parking_sessions
            SET end_time = %s,
                total_cost = %s,
                status = 'finished'
            WHERE id = %s
        """, (
            now,
            total_cost,
            session_data["id"]
        ))

        cursor.execute("""
            UPDATE parking_spots
            SET status = 'free',
                license_plate = NULL,
                reservation_id = NULL,
                session_id = NULL
            WHERE session_id = %s
        """, (
            session_data["id"],
        ))

        conn.commit()

        return {
            "success": True,
            "message": f"Ieșire permisă din {session_data['zone_name']}. Cost total: {total_cost} lei.",
            "zone_name": session_data["zone_name"],
            "total_cost": total_cost
        }

    except mysql.connector.Error as err:
        if conn is not None:
            conn.rollback()

        return {
            "success": False,
            "message": f"Eroare MySQL: {err}"
        }

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()

@app.route("/reserve/<int:zone_id>", methods=["GET", "POST"])
def reserve(zone_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    expire_unused_reservations()

    conn = None
    cursor = None
    zone = None
    spots = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                pz.id,
                pz.zone_name,
                pz.location_description,
                pz.total_spots,
                COUNT(CASE WHEN ps.status = 'free' THEN 1 END) AS available_spots,
                pz.price_per_hour,
                pz.status
            FROM parking_zones pz
            LEFT JOIN parking_spots ps
                ON pz.id = ps.zone_id
            WHERE pz.id = %s
              AND pz.status = 'active'
            GROUP BY
                pz.id,
                pz.zone_name,
                pz.location_description,
                pz.total_spots,
                pz.price_per_hour,
                pz.status
        """, (zone_id,))

        zone = cursor.fetchone()

        if not zone:
            flash("Zona selectată nu este disponibilă.", "error")
            return redirect(url_for("home"))

        cursor.execute("""
            SELECT id, spot_number, status
            FROM parking_spots
            WHERE zone_id = %s
            ORDER BY spot_number ASC
        """, (zone_id,))

        spots = cursor.fetchall()

        if request.method == "POST":
            license_plate = request.form.get("license_plate", "").strip().upper()
            reservation_start = request.form.get("reservation_start", "").strip()
            reservation_end = request.form.get("reservation_end", "").strip()
            spot_id = request.form.get("spot_id", "").strip()

            if not license_plate or not reservation_start or not reservation_end or not spot_id:
                flash("Completează toate câmpurile și alege un loc de parcare.", "error")
                return redirect(url_for("reserve", zone_id=zone_id))

            try:
                start_dt = datetime.strptime(reservation_start, "%Y-%m-%dT%H:%M")
                end_dt = datetime.strptime(reservation_end, "%Y-%m-%dT%H:%M")
                now = datetime.now()

                if start_dt < now:
                    flash("Nu poți face o rezervare în trecut.", "error")
                    return redirect(url_for("reserve", zone_id=zone_id))

                if end_dt <= start_dt:
                    flash("Data de final trebuie să fie după data de început.", "error")
                    return redirect(url_for("reserve", zone_id=zone_id))

                cursor.execute("""
                    SELECT id
                    FROM parking_reservations
                    WHERE license_plate = %s
                      AND status = 'active'
                      AND (%s < reservation_end AND %s > reservation_start)
                    LIMIT 1
                """, (license_plate, start_dt, end_dt))

                overlapping_reservation = cursor.fetchone()

                if overlapping_reservation:
                    flash("Există deja o rezervare activă suprapusă pentru acest număr de înmatriculare.", "error")
                    return redirect(url_for("reserve", zone_id=zone_id))

                cursor.execute("""
                    SELECT id
                    FROM parking_sessions
                    WHERE license_plate = %s
                      AND status = 'active'
                    LIMIT 1
                """, (license_plate,))

                active_session = cursor.fetchone()

                if active_session:
                    flash("Există deja o sesiune activă pentru acest număr de înmatriculare.", "error")
                    return redirect(url_for("reserve", zone_id=zone_id))

                cursor.execute("""
                    SELECT id, spot_number
                    FROM parking_spots
                    WHERE id = %s
                      AND zone_id = %s
                      AND status = 'free'
                    LIMIT 1
                """, (spot_id, zone_id))

                selected_spot = cursor.fetchone()

                if not selected_spot:
                    flash("Locul selectat nu mai este disponibil.", "error")
                    return redirect(url_for("reserve", zone_id=zone_id))

                if not has_capacity_for_reservation(cursor, zone_id, start_dt, end_dt):
                    flash("Nu mai există capacitate disponibilă în intervalul selectat pentru această zonă.", "error")
                    return redirect(url_for("reserve", zone_id=zone_id))

                duration_hours = (end_dt - start_dt).total_seconds() / 3600
                reservation_cost = round(duration_hours * float(zone["price_per_hour"]), 2)

                session["pending_reservation"] = {
                    "user_id": session["user_id"],
                    "zone_id": zone_id,
                    "zone_name": zone["zone_name"],
                    "license_plate": license_plate,
                    "reservation_start": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "reservation_end": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "reservation_cost": reservation_cost,
                    "spot_id": spot_id,
                    "spot_number": selected_spot["spot_number"]
                }

                return redirect(url_for("reservation_payment"))

            except ValueError:
                flash("Formatul datei nu este valid.", "error")
                return redirect(url_for("reserve", zone_id=zone_id))

    except mysql.connector.Error as err:
        flash(f"Eroare MySQL: {err}", "error")
        return redirect(url_for("home"))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    return render_template("reserve.html", zone=zone, spots=spots)

@app.route("/session-payment/<int:session_id>", methods=["GET", "POST"])
def session_payment(session_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT ps.*, pz.zone_name
            FROM parking_sessions ps
            JOIN parking_zones pz ON ps.zone_id = pz.id
            WHERE ps.id = %s
              AND ps.status = 'active'
              AND ps.payment_status = 'unpaid'
            LIMIT 1
        """, (session_id,))

        session_data = cursor.fetchone()

        if not session_data:
            flash("Sesiunea nu există sau este deja plătită.", "error")
            return redirect(url_for("home"))

        if request.method == "POST":
            payment_method = request.form.get("payment_method", "card_test")
            now = datetime.now()

            cursor.execute("""
                UPDATE parking_sessions
                SET payment_status = 'paid',
                    payment_method = %s,
                    paid_at = %s
                WHERE id = %s
                  AND status = 'active'
            """, (
                payment_method,
                now,
                session_id
            ))

            conn.commit()

            flash("Plata a fost efectuată. Așteaptă verificarea camerei pentru deschiderea barierei.", "success")
            return redirect(url_for("home"))

        return render_template("session_payment.html", session_data=session_data)

    except mysql.connector.Error as err:
        flash(f"Eroare MySQL: {err}", "error")
        return redirect(url_for("home"))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.route("/my-active-payments", methods=["GET", "POST"])
def my_active_payments():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = None
    cursor = None
    unpaid_sessions = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == "POST":
            license_plate = request.form.get("license_plate", "").strip().upper()

            if not license_plate:
                flash("Introdu numărul de înmatriculare.", "error")
                return redirect(url_for("my_active_payments"))

            cursor.execute("""
                SELECT 
                    ps.id,
                    ps.license_plate,
                    ps.start_time,
                    ps.total_cost,
                    ps.payment_status,
                    pz.zone_name
                FROM parking_sessions ps
                JOIN parking_zones pz ON ps.zone_id = pz.id
                WHERE ps.status = 'active'
                  AND ps.payment_status = 'unpaid'
                  AND ps.license_plate = %s
                ORDER BY ps.start_time DESC
            """, (license_plate,))

        else:
            cursor.execute("""
                SELECT 
                    ps.id,
                    ps.license_plate,
                    ps.start_time,
                    ps.total_cost,
                    ps.payment_status,
                    pz.zone_name
                FROM parking_sessions ps
                JOIN parking_zones pz ON ps.zone_id = pz.id
                WHERE ps.status = 'active'
                  AND ps.payment_status = 'unpaid'
                  AND ps.user_id = %s
                ORDER BY ps.start_time DESC
            """, (session["user_id"],))

        unpaid_sessions = cursor.fetchall()

    except mysql.connector.Error as err:
        flash(f"Eroare MySQL: {err}", "error")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    return render_template(
        "my_active_payments.html",
        unpaid_sessions=unpaid_sessions
    )
   
@app.route("/manual-exit", methods=["GET", "POST"])
def manual_exit():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Nu ai acces la această secțiune.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        license_plate = request.form.get("license_plate", "").strip().upper()

        result = process_manual_exit(license_plate)

        if result.get("payment_required"):
            flash(result["message"], "warning")
            return redirect(result["payment_url"])

        if result.get("success"):
            try:
                requests.get("http://192.168.1.7/open-barrier", timeout=5)
                flash(result["message"] + " Bariera a fost deschisă.", "success")
            except requests.RequestException:
                flash(result["message"] + " Dar bariera nu a răspuns.", "warning")
        else:
            flash(result["message"], "error")

        return redirect(url_for("manual_exit"))

    return render_template("manual_exit.html")

def process_manual_exit(license_plate):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        now = datetime.now()
        license_plate = license_plate.strip().upper()

        cursor.execute("""
            SELECT *
            FROM parking_sessions
            WHERE license_plate = %s
              AND status = 'active'
            ORDER BY start_time ASC
            LIMIT 1
        """, (license_plate,))

        session_data = cursor.fetchone()

        if not session_data:
            return {
                "success": False,
                "message": "Nu există sesiune activă pentru acest număr."
            }

        if session_data["payment_status"] != "paid":
            return {
                "success": False,
                "payment_required": True,
                "message": "Plata este necesară înainte de ieșire.",
                "payment_url": url_for("session_payment", session_id=session_data["id"])
            }

        cursor.execute("""
            UPDATE parking_sessions
            SET end_time = %s,
                status = 'finished'
            WHERE id = %s
        """, (now, session_data["id"]))

        cursor.execute("""
            UPDATE parking_spots
            SET status = 'free',
                license_plate = NULL,
                reservation_id = NULL,
                session_id = NULL
            WHERE session_id = %s
        """, (session_data["id"],))

        conn.commit()

        return {
            "success": True,
            "message": "Ieșirea manuală a fost procesată cu succes."
        }

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return {
            "success": False,
            "message": f"Eroare MySQL: {err}"
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def process_camera_barrier(license_plate, selected_zone_id=None):
    license_plate = (license_plate or "").strip().upper()
    selected_zone_id = str(selected_zone_id).strip() if selected_zone_id is not None else ""

    if not license_plate:
        return {
            "success": False,
            "message": "Număr de înmatriculare lipsă."
        }

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id
            FROM parking_sessions
            WHERE license_plate = %s
              AND status = 'active'
            LIMIT 1
        """, (license_plate,))

        active_session = cursor.fetchone()

    except mysql.connector.Error as err:
        return {
            "success": False,
            "message": f"Eroare MySQL la verificarea sesiunii active: {err}"
        }

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    if active_session:
        print("CAMERA ACTION: EXIT")
        result = process_barrier_exit(license_plate)
        result["action"] = "exit"
        return result

    print("CAMERA ACTION: ENTRY")
    result = process_barrier_entry(license_plate, selected_zone_id)
    result["action"] = "entry"
    return result


@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    expire_unused_reservations()
    lock_upcoming_reservations()

    conn = None
    cursor = None
    parking_zones = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                pz.id,
                pz.zone_name,
                pz.location_description,
                pz.total_spots,
                COUNT(CASE WHEN ps.status = 'free' THEN 1 END) AS available_spots,
                pz.price_per_hour,
                pz.status
            FROM parking_zones pz
            LEFT JOIN parking_spots ps
                ON pz.id = ps.zone_id
            WHERE pz.status = 'active'
            GROUP BY
                pz.id,
                pz.zone_name,
                pz.location_description,
                pz.total_spots,
                pz.price_per_hour,
                pz.status
            ORDER BY pz.zone_name ASC
        """)

        parking_zones = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Eroare MySQL: {err}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    return render_template(
        "home.html",
        full_name=session.get("full_name"),
        role=session.get("role"),
        parking_zones=parking_zones
    )

@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("home"))

    expire_unused_reservations()

    conn = None
    cursor = None
    stats = {}
    reservations = []
    sessions = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        reservation_status = request.args.get("reservation_status", "all").strip().lower()
        session_status = request.args.get("session_status", "all").strip().lower()

        allowed_reservation_statuses = {"all", "active", "expired", "cancelled", "completed"}
        allowed_session_statuses = {"all", "active", "finished"}

        if reservation_status not in allowed_reservation_statuses:
            reservation_status = "all"

        if session_status not in allowed_session_statuses:
            session_status = "all"

        cursor.execute("SELECT COUNT(*) AS total FROM parking_reservations")
        stats["total_reservations"] = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM parking_reservations WHERE status = 'active'")
        stats["active_reservations"] = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM parking_reservations WHERE status = 'expired'")
        stats["expired_reservations"] = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM parking_reservations WHERE status = 'cancelled'")
        stats["cancelled_reservations"] = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM parking_reservations WHERE status = 'completed'")
        stats["completed_reservations"] = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM parking_sessions")
        stats["total_sessions"] = cursor.fetchone()["total"]

        cursor.execute("SELECT IFNULL(SUM(total_cost), 0) AS total FROM parking_sessions")
        stats["sessions_revenue"] = float(cursor.fetchone()["total"])

        cursor.execute("SELECT IFNULL(SUM(penalty_fee), 0) AS total FROM parking_reservations")
        stats["penalties_revenue"] = float(cursor.fetchone()["total"])

        stats["total_revenue"] = round(
            stats["sessions_revenue"] + stats["penalties_revenue"], 2
        )

        cursor.execute("""
            SELECT COUNT(*) AS occupied
            FROM parking_spots
            WHERE status = 'occupied'
        """)
        stats["occupied_spots"] = cursor.fetchone()["occupied"]
        
        reservations_query = """
            SELECT 
                pr.id,
                pr.license_plate,
                pr.reservation_start,
                pr.reservation_end,
                pr.status,
                pr.penalty_fee,
                pr.notes,
                pr.created_at,
                pz.zone_name
            FROM parking_reservations pr
            JOIN parking_zones pz ON pr.zone_id = pz.id
            WHERE 1=1
        """
        reservations_params = []

        if reservation_status != "all":
            reservations_query += " AND pr.status = %s"
            reservations_params.append(reservation_status)

        reservations_query += " ORDER BY pr.created_at DESC LIMIT 10"

        cursor.execute(reservations_query, tuple(reservations_params))
        reservations = cursor.fetchall()

        sessions_query = """
            SELECT 
                ps.id,
                ps.license_plate,
                ps.start_time,
                ps.end_time,
                ps.total_cost,
                ps.status,
                pz.zone_name
            FROM parking_sessions ps
            JOIN parking_zones pz ON ps.zone_id = pz.id
            WHERE 1=1
        """
        sessions_params = []

        if session_status != "all":
            sessions_query += " AND ps.status = %s"
            sessions_params.append(session_status)

        sessions_query += " ORDER BY ps.start_time DESC LIMIT 10"

        cursor.execute(sessions_query, tuple(sessions_params))
        sessions = cursor.fetchall()

    except mysql.connector.Error as err:
        flash(f"Eroare MySQL: {err}", "error")
        return redirect(url_for("home"))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        reservations=reservations,
        sessions=sessions,
        reservation_status=reservation_status,
        session_status=session_status
    )

@app.route("/reservation-payment", methods=["GET", "POST"])
def reservation_payment():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if "pending_reservation" not in session:
        flash("Nu există nicio rezervare de plătit.", "error")
        return redirect(url_for("home"))

    reservation = session["pending_reservation"]

    if request.method == "POST":
        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            now = datetime.now()

            cursor.execute("""
                SELECT id, spot_number
                FROM parking_spots
                WHERE id = %s
                  AND zone_id = %s
                LIMIT 1
            """, (reservation["spot_id"], reservation["zone_id"]))

            spot = cursor.fetchone()

            if not spot:
                conn.rollback()
                flash("Locul selectat nu mai există.", "error")
                return redirect(url_for("home"))

            cursor.execute("""
                INSERT INTO parking_reservations
                (user_id, zone_id, spot_id, license_plate, reservation_start, reservation_end,
                 status, reservation_cost, payment_status, payment_method, paid_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                reservation["user_id"],
                reservation["zone_id"],
                reservation["spot_id"],
                reservation["license_plate"],
                reservation["reservation_start"],
                reservation["reservation_end"],
                "active",
                reservation["reservation_cost"],
                "paid",
                request.form.get("payment_method"),
                now
            ))

            conn.commit()
            session.pop("pending_reservation", None)

            flash("Plata a fost efectuată. Rezervarea a fost creată cu succes.", "success")
            return redirect(url_for("my_reservations"))

        except mysql.connector.Error as err:
            if conn is not None:
                conn.rollback()
            flash(f"Eroare MySQL: {err}", "error")
            return redirect(url_for("home"))

        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    return render_template("reservation_payment.html", reservation=reservation)

def lock_upcoming_reservations():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        now = datetime.now()
        lock_until = now + timedelta(minutes=15)

        cursor.execute("""
            SELECT id, spot_id, license_plate
            FROM parking_reservations
            WHERE status = 'active'
              AND spot_id IS NOT NULL
              AND reservation_start BETWEEN %s AND %s
        """, (now, lock_until))

        reservations = cursor.fetchall()

        for reservation in reservations:
            cursor.execute("""
                UPDATE parking_spots
                SET status = 'reserved',
                    license_plate = %s,
                    reservation_id = %s
                WHERE id = %s
                  AND status = 'free'
            """, (
                reservation["license_plate"],
                reservation["id"],
                reservation["spot_id"]
            ))

        conn.commit()

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/my-reservations")
def my_reservations():
    if "user_id" not in session:
        return redirect(url_for("login"))

    expire_unused_reservations()
    lock_upcoming_reservations()
    conn = None
    cursor = None
    reservations = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        selected_status = request.args.get("status", "all")
        print("STATUS DIN URL:", selected_status)

        query = """
            SELECT 
                pr.id,
                pz.zone_name,
                pr.license_plate,
                pr.reservation_start,
                pr.reservation_end,
                pr.status,
                pr.penalty_fee,
                pr.notes,
                pr.created_at,
                ps.total_cost
            FROM parking_reservations pr
            JOIN parking_zones pz ON pr.zone_id = pz.id
            LEFT JOIN parking_sessions ps ON pr.id = ps.reservation_id
            WHERE pr.user_id = %s
        """

        params = [session["user_id"]]

        if selected_status != "all":
            query += " AND pr.status = %s"
            params.append(selected_status)

        query += " ORDER BY pr.created_at DESC"

        print("QUERY FINAL:", query)
        print("PARAMS:", params)

        cursor.execute(query, tuple(params))
        reservations = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Eroare MySQL: {err}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    return render_template(
        "my_reservations.html",
        reservations=reservations,
        selected_status=selected_status
    )

@app.route("/cancel-reservation/<int:reservation_id>", methods=["POST"])
def cancel_reservation(reservation_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    expire_unused_reservations()

    conn = None
    cursor = None
    cancelled = False

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT pr.*, pz.price_per_hour
            FROM parking_reservations pr
            JOIN parking_zones pz ON pr.zone_id = pz.id
            WHERE pr.id = %s AND pr.user_id = %s
        """, (reservation_id, session["user_id"]))
        reservation = cursor.fetchone()

        if not reservation:
            flash("Rezervarea nu a fost găsită.", "error")
            return redirect(url_for("my_reservations"))

        if reservation["status"] != "active":
            flash("Doar rezervările active pot fi anulate.", "warning")
            return redirect(url_for("my_reservations"))

        cursor.execute("""
            SELECT id
            FROM parking_sessions
            WHERE reservation_id = %s
              AND status = 'active'
            LIMIT 1
        """, (reservation_id,))
        active_session = cursor.fetchone()

        if active_session:
            flash("Rezervarea nu mai poate fi anulată deoarece există deja o sesiune activă.", "error")
            return redirect(url_for("my_reservations"))

        now = datetime.now()
        penalty_fee = 0.00
        notes = "Rezervare anulată la timp."

        duration_hours = (
            reservation["reservation_end"] - reservation["reservation_start"]
        ).total_seconds() / 3600

        if duration_hours < 0:
            duration_hours = 0

        full_reservation_cost = duration_hours * float(reservation["price_per_hour"])

        if now >= reservation["reservation_start"]:
            penalty_fee = round(full_reservation_cost * 0.5, 2)
            notes = "Late cancellation: anulare după începerea intervalului rezervat."

        cursor.execute("""
            UPDATE parking_reservations
            SET status = 'cancelled',
                penalty_fee = %s,
                notes = %s
            WHERE id = %s
        """, (penalty_fee, notes, reservation_id))

        cursor.execute("""
            UPDATE parking_spots
            SET status = 'free',
                license_plate = NULL,
                reservation_id = NULL,
                session_id = NULL
            WHERE reservation_id = %s
                AND status = 'reserved'
        """, (reservation_id,
        ))

        conn.commit()
        cancelled = True

    except mysql.connector.Error as err:
        flash(f"Eroare MySQL: {err}", "error")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    if cancelled:
        flash("Rezervarea a fost anulată cu succes.", "success")

    return redirect(url_for("my_reservations"))

@app.route("/barrier-access", methods=["GET", "POST"])
def barrier_access():
    if "user_id" not in session:
        return redirect(url_for("login"))

    expire_unused_reservations()
    lock_upcoming_reservations()

    conn = None
    cursor = None
    parking_zones = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, zone_name, available_spots, status
            FROM parking_zones
            WHERE status = 'active'
            ORDER BY zone_name ASC
        """)
        parking_zones = cursor.fetchall()

    except mysql.connector.Error as err:
        flash(f"Eroare MySQL: {err}", "error")
        return redirect(url_for("home"))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    if request.method == "POST":
        license_plate = request.form.get("license_plate", "")
        selected_zone_id = request.form.get("zone_id", "")

        result = process_barrier_entry(license_plate, selected_zone_id, session["user_id"])

        if result.get("warning"):
            flash(result["warning"], "warning")

        flash(result["message"], "success" if result["success"] else "error")
        return redirect(url_for("barrier_access"))

    return render_template("barrier_access.html", parking_zones=parking_zones)
 
@app.route("/barrier-exit", methods=["GET", "POST"])
def barrier_exit():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        license_plate = request.form.get("license_plate", "")
        result = process_barrier_exit(license_plate)

        flash(result["message"], "success" if result["success"] else "error")
        return redirect(url_for("barrier_exit"))

    return render_template("barrier_exit.html")

@app.route("/api/camera/barrier", methods=["POST"])
def api_camera_barrier():
    expire_unused_reservations()
    lock_upcoming_reservations()

    print("=== REQUEST DE LA ESP ===")
    print("zone_id:", request.form.get("zone_id"))
    print("direction:", request.form.get("direction"))
    print("access_type:", request.form.get("access_type"))
    print("files:", request.files.keys())

    zone_id = request.form.get("zone_id", "")
    direction = request.form.get("direction", "")
    access_type = request.form.get("access_type", "session")

    direction = direction.strip().lower()
    access_type = access_type.strip().lower()

    if "image" not in request.files:
        return jsonify({
            "success": False,
            "message": "Nu a fost primită nicio imagine."
        }), 400

    image_file = request.files["image"]
    image_bytes = image_file.read()

    with open("last_capture.jpg", "wb") as f:
        f.write(image_bytes)

    license_plate = extract_plate_from_image(image_bytes)
    print("PLACA DETECTATA:", license_plate)

    if not license_plate:
        return jsonify({
            "success": False,
            "message": "Nu s-a putut citi numărul de înmatriculare.",
            "detected_plate": "UNKNOWN",
            "direction": direction if direction else None,
            "access_type": access_type
        }), 400

    if direction == "entry":
        print("CAMERA ACTION: ENTRY")
        result = process_barrier_entry(
            license_plate,
            selected_zone_id=zone_id,
            access_type=access_type
        )

    elif direction == "exit":
        print("CAMERA ACTION: EXIT")
        result = process_barrier_exit(license_plate)

    else:
        print("CAMERA ACTION: AUTO")
        result = process_camera_barrier(license_plate, zone_id)

    result["detected_plate"] = license_plate
    result["direction"] = direction if direction else "auto"
    result["access_type"] = access_type

    print("RESULT CAMERA:", result)
    print("SUCCESS:", result.get("success"))

    if result.get("payment_required"):
        return jsonify(result), 402

    if result.get("success"):
        return jsonify(result), 200

    return jsonify(result), 400
              

@app.route("/api/parking-spots")
def parking_spots_status():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            zone_id,
            spot_number,
            status
        FROM parking_spots
        ORDER BY zone_id, spot_number
    """)

    spots = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(spots)

@app.route("/api/free-spots")
def api_free_spots():

    lock_upcoming_reservations()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM parking_spots
        WHERE status = 'free'
    """)

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "free_spots": row["total"]
    })

@app.route("/register", methods=["GET", "POST"])
def register():
    conn = None
    cursor = None

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not full_name or not email or not password:
            flash("Completează toate câmpurile.", "error")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Există deja un cont cu acest email.", "error")
                return redirect(url_for("register"))
            else:
                sql = """
                    INSERT INTO users (full_name, email, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                """
                values = (full_name, email, password_hash, "user")
                cursor.execute(sql, values)
                conn.commit()

                flash("Cont creat cu succes. Te poți autentifica acum.", "success")
                return redirect(url_for("login"))

        except mysql.connector.Error as err:
            flash(f"Eroare MySQL: {err}", "error")
            return redirect(url_for("register"))

        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    conn = None
    cursor = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Completează emailul și parola.", "error")
            return redirect(url_for("login"))

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            sql = "SELECT * FROM users WHERE email = %s"
            cursor.execute(sql, (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["full_name"] = user["full_name"]
                session["email"] = user["email"]
                session["role"] = user["role"]

                flash("Te-ai autentificat cu succes.", "success")
                return redirect(url_for("home"))
            else:
                flash("Email sau parolă greșită.", "error")
                return redirect(url_for("login"))

        except mysql.connector.Error as err:
            flash(f"Eroare MySQL: {err}", "error")
            return redirect(url_for("login"))

        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Te-ai delogat cu succes.", "success")
    return redirect(url_for("login"))


@app.route("/test-camera")
def test_camera():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("home"))

    return render_template("test_camera.html")

@app.route("/api/led-events")
def api_led_events():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, zone_id, spot_number, duration_seconds
            FROM led_events
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT 1
        """)

        event = cursor.fetchone()

        if not event:
            return jsonify({
                "has_event": False
            })

        cursor.execute("""
            UPDATE led_events
            SET status = 'done'
            WHERE id = %s
        """, (
            event["id"],
        ))

        conn.commit()

        return jsonify({
            "has_event": True,
            "id": event["id"],
            "zone_id": event["zone_id"],
            "spot_number": event["spot_number"],
            "duration_seconds": event["duration_seconds"]
        })

    except mysql.connector.Error as err:
        return jsonify({
            "has_event": False,
            "error": str(err)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    print(app.url_map)
    app.run(host="0.0.0.0", port=5000, debug=True)

 

