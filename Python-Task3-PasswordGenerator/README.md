# Advanced Password Generator

A secure and modern password generator built as part of the **Oasis Infobyte Python Internship (Task 3)**.

---

## Live Demo

**Web Version:** [https://passwordcreater22.netlify.app/](https://passwordcreater22.netlify.app/)

---

## Features

- Generate strong, random passwords
- Customizable password length (8–64 characters)
- Select character types: Uppercase, Lowercase, Numbers, Symbols
- Option to exclude ambiguous characters (`0`, `O`, `l`, `1`, `I`)
- Guarantees at least one character from each selected type
- Real-time password strength indicator (Weak / Medium / Strong)
- One-click copy to clipboard
- Generation history (last 5 passwords – session only)
- Modern glassmorphism UI with smooth gradients
- Fully responsive design

---

## Tech Stack

- HTML5
- CSS3 (Glassmorphism + Gradients)
- JavaScript (Vanilla)
- Web Crypto API (for cryptographically secure randomness)

---

## How to Use

1. Set the desired **password length** using the slider.
2. Select at least **two character types**.
3. (Optional) Enable **Exclude Ambiguous** characters.
4. Click **Generate Password**.
5. Password is automatically copied to clipboard.
6. View the last 5 generated passwords in the history section.

---

Python-Task3-PasswordGenerator/
├── index.html          # Main Web Application
├── app.py              # Optional Desktop GUI (Tkinter)
├── requirements.txt    # Python dependencies (for desktop version)
└── README.md           # Project documentation

---

## Optional: Desktop Version (Tkinter)

If you want to run the desktop GUI version:

```bash
cd Python-Task3-PasswordGenerator
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py

Security Notes

Uses Web Crypto API (crypto.getRandomValues) for secure random generation.
History is session-only and never saved to disk (following security best practices).


Author
Taqwa Asif

Oasis Infobyte Python Internship – Task 3

License
This project is created for educational purposes under the Oasis Infobyte Internship Program.


---

### Update + Push karne ke commands:

```powershell
cd C:\Users\Asif\Desktop\OIBSIP

# README update karo (VS Code se paste karke save kar lena pehle)
git add Python-Task3-PasswordGenerator/README.md
git commit -m "Update README with Netlify live demo link"
git push origin main

## Project Structure
