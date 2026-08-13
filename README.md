# 🌐 Distributed Real-Time Chat Application

A college-friendly Distributed Systems term project demonstrating real-time client-server communication with Python, Flask, Flask-SocketIO, SQLite, HTML, CSS and JavaScript.

## ✨ Features

- Secure registration and login with password hashing
- Real-time global broadcast chat
- Private one-to-one messaging
- Live online-user presence
- Persistent chat history using SQLite
- Multiple simultaneous browser clients
- Client disconnect handling
- Responsive frontend
- Clean separation of HTML, CSS and JavaScript

## 📁 Project Structure

```text
distributed_chat_app/
├── app.py
├── requirements.txt
├── README.md
├── REPORT_OUTLINE.md
├── render.yaml
├── start_windows.bat
├── start_linux.sh
├── .gitignore
├── templates/
│   ├── login.html
│   └── chat.html
└── static/
    ├── style.css
    └── script.js
```

## ▶️ Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

Or double-click `start_windows.bat`.

## 📡 Same Wi-Fi Demo

1. Start the server on one laptop.
2. Run `ipconfig` on that laptop.
3. Find its Wi-Fi IPv4 address, for example `192.168.1.105`.
4. Allow Python through Windows Firewall on a Private network.
5. Other laptops open `http://192.168.1.105:5000`.

## ☁️ Deployment

`render.yaml` is included as a starting point for Render deployment. SQLite is appropriate for a student prototype; production multi-instance deployments should use a server database such as PostgreSQL and a shared message broker such as Redis.

## 🎓 Distributed Systems Concepts

- Concurrency: multiple clients communicate simultaneously.
- Communication: network-based Socket.IO events.
- Shared state: online user/session mapping.
- Message routing: global broadcast vs private user rooms.
- Persistence: SQLite chat history.
- Fault handling: disconnected clients are removed from presence state.
