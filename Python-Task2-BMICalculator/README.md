# BMI Tracker

### Advanced BMI Calculator | Oasis Infobyte Python Programming Internship

A modern BMI tracking application built with Python, Tkinter, SQLite, and Matplotlib.

BMI Tracker allows users to calculate their BMI, understand their BMI category, manage multiple users, save measurements, view historical records, and visualize BMI changes over time.

---

## 🌐 Live Web Demo

A browser-based version of BMI Tracker is available through GitHub Pages.

The web demo provides:

- 🧮 BMI calculation
- 👤 User name support
- 💾 Browser-based data persistence
- 📋 BMI history
- 📈 BMI trend visualization
- 🎨 Colour-coded BMI categories
- ⚠️ Input validation
- 📱 Responsive interface

> **Note:** The GitHub Pages version is a web demonstration of the project.
> The official Advanced internship implementation is the Python desktop application using Tkinter, SQLite, and Matplotlib.

**Live Demo:** Add the GitHub Pages link here after deployment.

---

## ✨ Project Preview

BMI Tracker provides a clean and professional interface designed to make BMI calculation and tracking simple and easy to understand.

### Main Features

- 🧮 Accurate BMI calculation
- 👤 Multiple named users
- 💾 Persistent SQLite database
- 📊 BMI history
- 📈 BMI trend visualization
- 🎨 Colour-coded BMI categories
- ⚠️ Input validation and error handling
- 🖥️ Modern Tkinter graphical interface
- 🌐 Browser-based web demo

---

## 🎯 BMI Categories

| BMI | Category |
|---|---|
| Below 18.5 | Underweight |
| 18.5 – 24.9 | Normal |
| 25 – 29.9 | Overweight |
| 30 and above | Obese |

BMI is calculated using:

**BMI = Weight (kg) / Height² (m)**

Results are rounded to **2 decimal places**.

---

## 🚀 Advanced Features

### 👤 Multi-User Support

Create and select different users from the desktop application.

Each user has an independent BMI history stored in SQLite.

### 💾 Persistent Data Storage

BMI measurements are stored using SQLite, allowing records to remain available after the application is closed and reopened.

### 📋 BMI History

Users can view previously saved BMI measurements, including:

- Date and time
- Weight
- Height
- BMI
- BMI category

### 📈 BMI Trend

Historical BMI measurements can be visualized through a Matplotlib line chart.

This makes it possible to see how a user's BMI changes over time.

### 🎨 Colour-Coded Results

BMI results provide category-based visual feedback for:

- Underweight
- Normal
- Overweight
- Obese

### ⚠️ Validation & Error Handling

The application handles:

- Non-numeric values
- Empty values
- Zero values
- Negative values
- Invalid measurements
- Database read/write failures

Helpful error messages are displayed directly in the GUI.

---

## 🌐 Web Demo

The GitHub Pages version is implemented as a browser-based demonstration.

Unlike the desktop application, the web version runs entirely in the browser and uses **localStorage** for saving demo records.

It does not run Python, Tkinter, SQLite, or Matplotlib on GitHub Pages.

---

## 🖥️ User Interface

The desktop application contains:

- BMI Calculator panel
- User selection
- Weight input
- Height input
- Calculate BMI button
- BMI result card
- Category feedback
- Save BMI Record button
- History viewer
- BMI Trend viewer

The interface is designed with a clean dark theme for a modern desktop-app experience.

---

## 🛠️ Technology Stack

### Desktop Application

| Technology | Purpose |
|---|---|
| Python | Core application |
| Tkinter | Graphical User Interface |
| SQLite3 | Persistent data storage |
| Matplotlib | BMI trend visualization |

### Web Demo

| Technology | Purpose |
|---|---|
| HTML | Web structure |
| CSS | Styling and responsive UI |
| JavaScript | BMI calculation and interaction |
| LocalStorage | Browser-based demo persistence |
| Canvas | BMI trend visualization |

---

## 📁 Project Structure

```text
Python-Task2-BMICalculator/
│
├── app.py
├── database.py
├── README.md
├── requirements.txt
│
├── docs/
│   └── index.html
│
└── web/
    └── index.html
```

### `app.py`

Main Python desktop application containing the graphical interface, BMI calculation, validation, user interaction, history display, and trend visualization.

### `database.py`

Handles SQLite database operations including user management, BMI record storage, history retrieval, and trend data retrieval.

### `requirements.txt`

Contains the Python packages required by the desktop application.

### `docs/index.html`

GitHub Pages version of the BMI Tracker web demonstration.

### `web/index.html`

Browser-based BMI Tracker development and local demo version.

---

## ▶️ Running the Desktop Application

This project includes an official Python desktop GUI application.

To run it locally:

```bash
python app.py
```

The BMI Tracker graphical application will open automatically.

---

## 🌐 Running the Web Demo Locally

Open the `web` folder and run:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

---

## 🧪 Tested Functionality

### Desktop Application

The application has been tested for:

- BMI calculation
- BMI rounding
- Underweight classification
- Normal classification
- Overweight classification
- Obese classification
- BMI category boundaries
- Invalid text input
- Zero values
- Negative values
- Multiple users
- Saving BMI records
- Viewing history
- SQLite persistence
- BMI trend visualization
- Database operations
- Error handling

### Web Demo

The web demo has been tested for:

- BMI calculation
- Saving records
- History display
- Input validation
- BMI trend visualization
- Responsive interface
- Browser-based data persistence

---

## 📸 Screenshots

Screenshots can be added here to demonstrate the project interface and functionality.

### BMI Calculator

_Add application screenshot here._

### BMI History

_Add history screenshot here._

### BMI Trend

_Add trend graph screenshot here._

### Web Demo

_Add GitHub Pages screenshot here._

---

## 📌 Internship Task

**Organization:** Oasis Infobyte

**Program:** Python Programming Internship

**Task:** Task 2 — BMI Calculator

**Level:** Advanced

**Track:** Python Programming

---

## 👩‍💻 Author

**Taqwa Asif**

AI Agents • Chatbots • Generative AI • Machine Learning • Frontend Development

---

## ⚠️ Disclaimer

This project is an educational BMI calculation and tracking application created for the Oasis Infobyte internship.

BMI is a general numerical screening measure and does not by itself provide a medical diagnosis.
