# Wyibe Engine 🚀

![Architecture](https://img.shields.io/badge/Architecture-Spec_Driven-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-005571?logo=fastapi)
![VanillaJS](https://img.shields.io/badge/Frontend-Vanilla_JS-F7DF1E?logo=javascript&logoColor=black)
![AI](https://img.shields.io/badge/AI-dlib%20Face%20Recognition-success)

**Wyibe** is an intelligent, high-performance Identity & Retrieval engine designed to automate the painful process of massive event photography mapping. Instead of manual tagging or relying on text-based usernames, Wyibe introduces a fully autonomous **"Selfie-as-a-Key"** biometric authorization system.

---

## 🏆 Hackathon Criteria Met (Checklist)

This project was built strictly according to the hackathon judging rubric. 

✅ **Discovery & Transformation Engine:** Wyibe features a recursive, idempotent ingestion crawler (`/ingest`). Point it at an enterprise raw file dump, and it automatically extracts faces, assigns system-generated UUIDs (`grab_id`), and binds geometric vectors to images.
✅ **AI Geometric Similarity Extraction:** Uses the `face_recognition` (dlib) library to extract 128-d spatial vectors. When a user authenticates, it runs highly-tuned Euclidean distance comparisons (Strict `0.55` Threshold) to prevent False Positives.
✅ **ID-Based Authorization:** No manual passwords or names. The user *is* the key. Presenting a biometric selfie instantly executes the mathematical cross-reference across the DB to fetch access to their matched file arrays.
✅ **Spec-Driven Architecture (5% Judging Weight):** Built natively on FastAPI. Strict HTTP type contracts and auto-generated Swagger UI (`/docs`).
✅ **Graceful Error Handling (15% Judging Weight):** Complete Pydantic schemas intercept corrupt encodings, bad uploads, or missing faces with beautifully nested `HTTP 404` and `HTTP 422` error handling.
✅ **Bonus Requirement (All Faces with Counts):** Includes a deeply integrated `/faces` API endpoint seamlessly visualized in the "Identity Database" dashboard tab.

---

## ✨ Features That Make Wyibe "Better"

We didn't just build an API; we engineered an enterprise-ready ecosystem with advanced computer vision resilience:

* **Live Webcam Injection:** Forget file-uploaders! Wyibe features a raw WebRTC JavaScript hook allowing live camera captures directly in the browser. 
* **CLAHE Backlighting Equalization:** Often webcams look terrible due to bad lighting or backlit shadows causing AI engines to fail. We injected a **Contrast-Limited Adaptive Histogram Equalization (CLAHE)** preprocessing layer. It artificially relights and recovers shadows *before* face extraction, ensuring flawless accuracy.
* **Portable OS Fallbacks:** If a judge clones this repo to their local machine, our backend intelligently falls back from absolute pathing to dynamic relative pathing, allowing the system to run seamlessly anywhere.
* **Idempotent Crawling:** If the ingest engine runs twice, it safely skips known files.

---

## 🏗️ Technical Architecture & Deployment Deploying

Wyibe is built as a Decoupled Microservice:

**🟢 Frontend (Vercel)**
The frontend is a strictly engineered, pure-CSS Dark Glassmorphism SPA (Single Page Application). It is ready for instant deployment to Vercel. Thanks to our zero-dependency framework, load times are near zero. 

**🔵 Backend (Render & Local)**
The backend leverages Python 3.11 + FastAPI + SQLite + OpenCV + Dlib. 
We enabled global `CORSMiddleware`, allowing the deployed Vercel frontend to seamlessly ping the securely hosted Python backend executing on **Render** (or tunneled via **Ngrok/Localhost**).

### Deployment Instructions for Judges

Because we pushed the entire `photos/` dataset *and* the pre-calculated `wyibe.db` SQLite database to GitHub, **you don't even need to wait for ingestion to run it.** 

1. **Clone the Repo:**
   ```bash
   git clone https://github.com/ahmedmalik07/vyrothon.git
   cd vyrothon
   ```

2. **Install AI Dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # (or venv\Scripts\activate on Windows)
   pip install -r requirements.txt
   ```

3. **Ignite the Server!**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
4. **View the Dashboard:** Open `http://localhost:8000/` in your browser.

---

## 📂 System Directory 

```text
wyibe/
├── database.py       <-- SQLite Connection Engine
├── main.py           <-- FastAPI App + CORS + Global Error Handler
├── models.py         <-- SQLAlchemy ORM Models
├── schemas.py        <-- Pydantic Response Validation
├── services/
│   ├── auth.py         <-- CLAHE Preprocessing & Biometric Auth
│   ├── face_engine.py  <-- 128-d Vector Generation & Thresholding
│   ├── ingest.py       <-- Idempotent Directory Crawler
├── frontend/
│   ├── index.html      <-- 3-Tab Glassmorphism UI
│   ├── style.css       <-- Custom Dark UI Library 
│   ├── app.js          <-- VanillaJS WebRTC Logic
```

Wyibe — Engineered for Speed, Privacy, and Scale.
