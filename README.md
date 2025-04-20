![github-submission-banner](https://github.com/user-attachments/assets/a1493b84-e4e2-456e-a791-ce35ee2bcf2f)

# 🚀 Project Title

> GreenHouse Agri-Farming Monitoring

---

## 📌 Problem Statement

**Problem Statement 3 – Real-Time Data Experiences with Fluvio**

---

## 🎯 Objective

Modern agriculture faces challenges in maintaining optimal environmental conditions for crops, especially in controlled environments like greenhouses. This project solves that problem by simulating a smart greenhouse that:

- Monitors real-time sensor data like temperature, humidity, CO2, and more.
- Controls key devices such as fans, lights, humidifiers, and water pumps.
- Provides a visually rich dashboard for interaction.

It enables farmers and greenhouse managers to remotely monitor and control their greenhouse, ensuring healthier plants and better yields.

---

## 🧠 Team & Approach

### Team Name:  
`SoloBloom`

### Team Member:  
- Aanand Pandit ([GitHub](https://github.com/aanandpandit) / Developer / Solo Performer)

### My Approach:  
- Chose this problem for its real-world impact in agriculture automation.
- Built a simulation to model a greenhouse using PyQt5 and Flask.
- Integrated Fluvio for real-time, low-latency communication between UI and backend.
- Focused on simplicity, extensibility, and live visual feedback for a robust experience.

---

## 🛠️ Tech Stack

### Core Technologies Used:
- **Frontend:** HTML, JavaScript, Chart.js
- **Backend:** Flask (Python)
- **Database:** None (Fluvio handles streaming state)
- **APIs:** Fluvio CLI & Python SDK
- **Hosting:** Localhost (Flask & PyQt5)

### Sponsor Technologies Used:
- [ ] **Groq:**  
- [ ] **Monad:**  
- [✅] **Fluvio:** _Real-time stream processing and control messaging_
- [ ] **Base:**  
- [ ] **Screenpipe:**  
- [ ] **Stellar:**  

---

## ✨ Key Features

- ✅ Real-time monitoring of environmental sensor data
- ✅ Interactive simulator using PyQt5
- ✅ Device control (Fan, AC, Lights, Humidifier, Pump)
- ✅ Web dashboard with charts and insights
- ✅ Fluvio-powered data streaming between simulation and control layer

---

## 📽️ Demo & Deliverables

- **Demo Video Link:** [Paste YouTube or Loom link here]  
- **Pitch Deck / PPT Link:** [Paste Google Slides or PDF link here]  

---

## ✅ Tasks & Bonus Checklist

- [ ] **All members of the team completed the mandatory task - Followed at least 2 of our social channels and filled the form**  
- [ ] **Completed Bonus Task 1 - Sharing of Badges and filled the form (2 points)**  
- [ ] **Completed Bonus Task 2 - Signing up for Sprint.dev and filled the form (3 points)**  

---

## 🧪 How to Run the Project

### Requirements:
- Python 3.7+
- Fluvio CLI
- PyQt5, Flask, pytz

### Local Setup:
```bash
# Clone the repo
git clone https://github.com/your-username/greenhouse-fluvio-hackathon

# Go into project directory
cd hackhazards25_green-house-agri-farming

# Install dependencies
pip install -r requirements.txt

# Start Fluvio cluster
fluvio cluster start

# Run simulator (in one terminal)
cd greenhouse
python3 greenHouseSimulation.py

# Run dashboard (in second terminal)
cd webpage_dashboard
python3 app.py
