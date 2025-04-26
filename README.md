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
`NA`

### Team Member:  
- Aanand Pandit ([GitHub](https://github.com/AanandPandit) / Developer / Solo Performer)

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

- [✅] **All members of the team completed the mandatory task - Followed at least 2 of our social channels and filled the form**  
- [✅] **Completed Bonus Task 1 - Sharing of Badges and filled the form (2 points)**  
- [✅] **Completed Bonus Task 2 - Signing up for Sprint.dev and filled the form (3 points)**  

---

## 🧪 How to Run the Project

### Requirements:
- Python 3.7+
- Fluvio CLI
- PyQt5, Flask, pytz
### Documentation Link: https://docs.google.com/document/d/13aQOE2tZ54SxaIsgggub240drTbfWEte/edit?usp=drive_link&ouid=118111382130845977162&rtpof=true&sd=true
### Local Setup:
```bash
1. Clone the Repository:
    ‘git clone https://github.com/AanandPandit/hackhazards25_green-house-agri-farming.git’
    cd hackhazards25_green-house-agri-farming

2. Install Fluvio Client:
    sudo curl -fsS https://hub.infinyon.cloud/install/install.sh | bash

    (After installing run this command to add path to system environment:)
    echo 'export PATH="${HOME}/.fvm/bin:${HOME}/.fluvio/bin:${PATH}"' >> ~/.zshrc

    (Reboot the system to take effect on changes of installation.)
    sudo reboot 

3. Login to InfinyOn Cloud:
    fluvio cloud login
    (Enter your InfinyOn Cloud email and password when prompted.)

4. Create and Setup the Cluster:
    # Create cluster
    fluvio cloud cluster create greenhouse-agri
       
    # Check available clusters
    fluvio profile list        
     
    # Set cluster for use                  
    fluvio profile switch greenhouse-agri 

    # Check the current cluster       
    fluvio profile                                    

5. Create Fluvio Topics:
    fluvio topic create dht-temp
    fluvio topic create dht-humid
    fluvio topic create co2
    fluvio topic create rain-sensor
    fluvio topic create soil-moisture-1
    fluvio topic create soil-moisture-2
    fluvio topic create water-level-sensor
    fluvio topic create fan-1
    fluvio topic create fan-2
    fluvio topic create fan-3
    fluvio topic create fan-4
    fluvio topic create fan-5
    fluvio topic create ac-1
    fluvio topic create ac-2
    fluvio topic create humidifier-1
    fluvio topic create humidifier-2
    fluvio topic create humidifier-3
    fluvio topic create light-1
    fluvio topic create light-2
    fluvio topic create light-3
    fluvio topic create light-4
    fluvio topic create light-5
    fluvio topic create water-pump

6. Install Python Dependencies:
    sudo pip3 install -r requirements.txt --break-system-packages

7. Run the Project:

    Terminal 1: Start the Greenhouse Simulator:
        cd greenhouse
        python3 greenHouseSimulation.py

    Terminal 2: Start the Dashboard:
        cd webpage_dashboard
        python3 app.py

8. View the Dashboad:
    Open Firefox or any browser
    Got to http://localhost:5000

(Interact with the dashboard and watch real-time changes in the simulator.)

NOTE:
More information at: 
'https://github.com/AanandPandit/hackhazards25_green-house-agri-farming'
```

---

## 🧬 Future Scope

While currently a simulation, this system is designed for real-world integration with:
- Hardware Integration – Connect real sensors and control devices via Raspberry Pi or Arduino.
- IoT Edge Deployment – Run the simulator on edge devices and stream data using Fluvio.
- Cloud & Alerts – Use cloud platforms for analytics, storage, and real-time alerts.
- Mobile Access – Build a mobile-friendly UI or app for remote monitoring and control.
- AI Automation – Train models for smart decisions like irrigation and climate control.

---

## 📎 Resources / Credits

- https://youtu.be/ubT7Vlt_fJ4
- https://www.flaticon.com/
- PyQt5 GUI Library
- InfinyOn Fluvio
- https://github.com/AanandPandit/hackhazards25_green-house-agri-farming/blob/main/readme.txt
- https://github.com/AanandPandit/hackhazards25_green-house-agri-farming/blob/main/Documentation/Greenhouse-agri-monitoring-presentation.pdf

---

## 🏁 Final Words

HackHazards’25 was an amazing journey! I learned a lot about real-time data streaming using Fluvio, UI design, and IoT system simulation while building the Smart Greenhouse Dashboard.

From syncing devices to handling offline modes, every challenge taught me something new. The best part? Watching everything work together in real time — sensors, controls, and the dashboard.

Huge thanks to the organizers and the open-source community for the inspiration. This is just the beginning — the future of smart farming is here! 🌱

---
