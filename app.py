from flask import Flask, request, jsonify
import datetime
import smtplib
from email.mime.text import MIMEText
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

database = {
    "patients": {},
    "appointments": [],
    "treatments": {
        "implant dentar": "Un implant dentar este o soluție permanentă pentru înlocuirea unui dinte lipsă. Procedura durează aproximativ 1-2 ore și implică inserarea unui șurub din titan în os. Post-tratament: ușoară inflamație și disconfort pentru 2-3 zile.",
        "detartraj": "Detartrajul elimină placa bacteriană și tartrul de pe dinți. Procedura durează 30-45 minute și este nedureroasă. Post-tratament: sensibilitate dentară ușoară timp de 1-2 zile."
    },
    "doctors": {},
    "pending_appointments": []
}

CLINIC_EMAIL = "clinica@example.com"
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "clinica@example.com"
SMTP_PASSWORD = "parola_secure"

@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    user_input = data.get("message", "").lower()
    phone_number = data.get("phone")
    name = data.get("name")

    if phone_number not in database["patients"]:
        database["patients"][phone_number] = {"name": name, "appointments": [], "procedures": []}

    response = "Nu am înțeles. Încercați din nou."

    if "programare" in user_input:
        response = triage_patient(phone_number, user_input)
    elif "istoric" in user_input:
        response = get_patient_history(phone_number)
    elif "tarife" in user_input:
        response = "Consultațiile costă între 100-300 lei, în funcție de procedură."
    elif "implant dentar" in user_input or "detartraj" in user_input:
        response = get_treatment_info(user_input)
    elif "mi-am pus implant dentar" in user_input or "după detartraj" in user_input:
        response = get_post_treatment_info(user_input)
elif "ma doare o masea" in user_input:
    response = "O durere de masea poate indica o carie sau o infectie. Va recomandam o consultatie. Puteti solicita o programare direct aici."

elif "detartraj" in user_input:
    response = "După detartraj este posibilă o sensibilitate temporară. Evitați alimentele foarte reci sau fierbinți timp de 24-48h."

elif "albire" in user_input:
    response = "Albirea dentară poate provoca sensibilitate ușoară. Nu consumați alimente sau băuturi colorate timp de 48h."

elif "nu am înțeles" in user_input or "ce fac" in user_input:
    response = "Puteți reformula întrebarea sau cere o programare pentru un control."

else:
    response = "Întrebarea dvs. nu a fost recunoscută. Reformulați sau contactați clinica telefonic."
    return jsonify({"response": response})

@app.route("/admin/add_doctor", methods=["POST"])
def add_doctor():
    data = request.json
    name = data.get("name")
    specialization = data.get("specialization")
    schedule = data.get("schedule")

    if name and specialization and schedule:
        database["doctors"][name] = {"specializare": specialization, "orar": schedule}
        return jsonify({"message": f"Medicul {name} a fost adăugat cu succes."})
    return jsonify({"error": "Date incomplete."}), 400

@app.route("/admin/get_doctors", methods=["GET"])
def get_doctors():
    return jsonify(database["doctors"])

@app.route("/admin/update_doctor", methods=["POST"])
def update_doctor():
    data = request.json
    name = data.get("name")
    specialization = data.get("specialization")
    schedule = data.get("schedule")

    if name in database["doctors"]:
        database["doctors"][name] = {"specializare": specialization, "orar": schedule}
        return jsonify({"message": f"Medicul {name} a fost actualizat cu succes."})
    return jsonify({"error": "Medicul nu există în baza de date."}), 404

@app.route("/admin/delete_doctor", methods=["POST"])
def delete_doctor():
    data = request.json
    name = data.get("name")

    if name in database["doctors"]:
        del database["doctors"][name]
        return jsonify({"message": f"Medicul {name} a fost șters cu succes."})
    return jsonify({"error": "Medicul nu există în baza de date."}), 404

def triage_patient(phone_number, issue):
    doctor = "Necunoscut"
    treatment = "Evaluare generală"

    for doc, details in database["doctors"].items():
        if "implant" in issue or "extracție" in issue and "implantologie" in details["specializare"]:
            doctor = doc
            treatment = "implantologie sau chirurgie"
        elif "plombă" in issue or "detartraj" in issue and "generale" in details["specializare"]:
            doctor = doc
            treatment = "tratamente dentare generale"

    appointment_request = {
        "patient": phone_number,
        "treatment": treatment,
        "doctor": doctor,
        "status": "pending"
    }
    database["pending_appointments"].append(appointment_request)
    send_email_notification(doctor, phone_number, treatment)
    return f"Programarea dvs. pentru {treatment} la {doctor} a fost trimisă pentru aprobare. Veți primi o confirmare în curând. Vă rugăm să rețineți că orarul poate suferi modificări."

def send_email_notification(doctor, phone_number, treatment):
    subject = "Cerere nouă de programare"
    message = f"Doctor {doctor}, a fost primită o cerere de programare pentru un pacient cu numărul {phone_number}, tratament: {treatment}."
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = CLINIC_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, CLINIC_EMAIL, msg.as_string())

def get_patient_history(phone_number):
    patient = database["patients"].get(phone_number)
    if patient:
        history = f"Programări anterioare: {patient['appointments']}, Proceduri: {patient['procedures']}"
        return history if history else "Nu aveți istoric de programări."
    return "Pacientul nu există în baza de date."

def get_treatment_info(treatment):
    for key in database["treatments"]:
        if key in treatment:
            return database["treatments"][key]
    return "Nu avem informații despre acest tratament."

def get_post_treatment_info(treatment):
    if "implant dentar" in treatment:
        return "După un implant dentar, este normal să aveți o ușoară inflamație și sensibilitate timp de câteva zile. Se recomandă evitarea alimentelor tari și a fumatului pentru o recuperare mai rapidă."
    elif "detartraj" in treatment:
        return "După detartraj, este posibil să simțiți o sensibilitate temporară a dinților. Se recomandă evitarea alimentelor acide și reci pentru 24 de ore."
    return "Nu am informații despre această situație. Contactați cabinetul pentru mai multe detalii."

import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
