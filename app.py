from flask import Flask, render_template, request, Response
import mysql.connector
from datetime import datetime
import csv
import io

app = Flask(__name__)


# -----------------------------
# MySQL Connection
# -----------------------------
def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Samba@1397",
        database="ganesh_donation"
    )


# -----------------------------
# Home Page
# -----------------------------
@app.route("/")
def home():

    return render_template("index.html")


# -----------------------------
# Donation Submit
# -----------------------------
@app.route("/donate", methods=["POST"])
def donate():

    donor_name = request.form["donor_name"].strip()
    phone = request.form["phone"].strip()
    amount = request.form["amount"]
    payment_method = request.form["payment_method"]
    whatsapp = request.form["whatsapp"]

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO donations
        (donor_name, phone, amount, payment_method, whatsapp)
        VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        donor_name,
        phone,
        amount,
        payment_method,
        whatsapp
    )

    cursor.execute(query, values)

    connection.commit()

    donation_id = cursor.lastrowid

    receipt_no = f"GNY-{donation_id:05d}"

    update_query = """
        UPDATE donations
        SET receipt_no = %s
        WHERE id = %s
    """

    cursor.execute(
        update_query,
        (receipt_no, donation_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    current_date = datetime.now().strftime(
        "%d-%m-%Y | %I:%M %p"
    )

    return render_template(
        "receipt.html",

        receipt_no=receipt_no,

        donor_name=donor_name,

        phone=phone,

        amount=amount,

        payment_method=payment_method,

        date=current_date
    )


# -----------------------------
# Admin Dashboard
# -----------------------------
@app.route("/admin")
def admin():

    selected_date = request.args.get("date", "")

    connection = get_db_connection()
    cursor = connection.cursor()


    # -------------------------
    # Donations
    # -------------------------

    if selected_date:

        cursor.execute("""
            SELECT
                receipt_no,
                donor_name,
                phone,
                amount,
                payment_method,
                whatsapp,
                donation_date
            FROM donations
            WHERE DATE(donation_date) = %s
            ORDER BY id DESC
        """, (selected_date,))

    else:

        cursor.execute("""
            SELECT
                receipt_no,
                donor_name,
                phone,
                amount,
                payment_method,
                whatsapp,
                donation_date
            FROM donations
            ORDER BY id DESC
        """)

    donations = cursor.fetchall()


    # -------------------------
    # Total Donors
    # -------------------------

    if selected_date:

        cursor.execute("""
            SELECT COUNT(*)
            FROM donations
            WHERE DATE(donation_date) = %s
        """, (selected_date,))

    else:

        cursor.execute("""
            SELECT COUNT(*)
            FROM donations
        """)

    total_donors = cursor.fetchone()[0]


    # -------------------------
    # Total Amount
    # -------------------------

    if selected_date:

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM donations
            WHERE DATE(donation_date) = %s
        """, (selected_date,))

    else:

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM donations
        """)

    total_amount = cursor.fetchone()[0]


    # -------------------------
    # Cash
    # -------------------------

    if selected_date:

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM donations
            WHERE payment_method = 'Cash'
            AND DATE(donation_date) = %s
        """, (selected_date,))

    else:

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM donations
            WHERE payment_method = 'Cash'
        """)

    cash_amount = cursor.fetchone()[0]


    # -------------------------
    # UPI
    # -------------------------

    if selected_date:

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM donations
            WHERE payment_method = 'UPI'
            AND DATE(donation_date) = %s
        """, (selected_date,))

    else:

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM donations
            WHERE payment_method = 'UPI'
        """)

    upi_amount = cursor.fetchone()[0]


    # -------------------------
    # Bank Transfer
    # -------------------------

    if selected_date:

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM donations
            WHERE payment_method = 'Bank Transfer'
            AND DATE(donation_date) = %s
        """, (selected_date,))

    else:

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM donations
            WHERE payment_method = 'Bank Transfer'
        """)

    bank_amount = cursor.fetchone()[0]


    cursor.close()
    connection.close()


    return render_template(
        "admin.html",

        donations=donations,

        total_donors=total_donors,

        total_amount=total_amount,

        cash_amount=cash_amount,

        upi_amount=upi_amount,

        bank_amount=bank_amount,

        selected_date=selected_date
    )


# -----------------------------
# Export Donations CSV
# -----------------------------
@app.route("/admin/export")
def export_csv():

    selected_date = request.args.get("date", "")

    connection = get_db_connection()
    cursor = connection.cursor()


    if selected_date:

        cursor.execute("""
            SELECT
                receipt_no,
                donor_name,
                phone,
                amount,
                payment_method,
                whatsapp,
                donation_date
            FROM donations
            WHERE DATE(donation_date) = %s
            ORDER BY id DESC
        """, (selected_date,))

    else:

        cursor.execute("""
            SELECT
                receipt_no,
                donor_name,
                phone,
                amount,
                payment_method,
                whatsapp,
                donation_date
            FROM donations
            ORDER BY id DESC
        """)

    donations = cursor.fetchall()


    cursor.close()
    connection.close()


    # Create CSV in memory

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Receipt No",
        "Donor Name",
        "Phone",
        "Amount",
        "Payment Method",
        "WhatsApp",
        "Date & Time"
    ])


    for donation in donations:

        writer.writerow([
            donation[0],
            donation[1],
            donation[2],
            donation[3],
            donation[4],
            donation[5],
            donation[6]
        ])


    filename = "ganesh_donations"

    if selected_date:
        filename += "_" + selected_date

    filename += ".csv"


    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                f"attachment; filename={filename}"
        }
    )


# -----------------------------
# Run Application
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)