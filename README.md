# 🥗 NutriBite

### Fresh Food, Better Living

NutriBite is a Django-based meal planning web application that helps users explore meals, view nutritional information, choose their dietary preferences, and manage a weekly meal subscription.

The project focuses on making meal selection and subscription management simple through a clean, responsive interface.

---

## ✨ Features

- **Explore meals:** Browse meals by categories such as Breakfast, Lunch, Evening Snacks, Shakes & Beverages, and Dinner.
- **Meal details:** View meal descriptions and nutritional information, including calories, protein, carbohydrates, fats, fiber, and sugar where available.
- **Weekly menu:** Explore the weekly menu and filter meals by diet type.
- **User authentication:** Register, log in, and log out securely using Django's authentication system.
- **Meal subscription:** Create a subscription by selecting a diet preference, preferred days, and meals from the available menu.
- **Subscription management:** View and edit an active subscription, change diet preferences, and review subscription history.
- **Pause and resume:** Temporarily pause or resume a subscription.
- **Skip a meal:** Skip an eligible upcoming meal.
- **Admin management:** Manage meals, weekly menus, subscriptions, and orders through the Django admin panel.
- **Theme support:** Switch between light and dark themes.
- **Responsive interface:** Built with Bootstrap and custom CSS for different screen sizes.

## 🛠️ Tech Stack

| Area | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, JavaScript |
| UI Framework | Bootstrap 5 |
| Database | SQLite (development setup) |
| Image Handling | Pillow |
| Version Control | Git & GitHub |

## 📁 Project Structure

```text
NutriBite/
│
├── config/                 # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── custom_meal_web/        # Main Django application
│   ├── migrations/
│   ├── templates/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── media/                  # Meal images and uploaded media
├── manage.py
└── requirements.txt
```

## 🚀 Getting Started

Follow these steps to run NutriBite locally.

### 1. Clone the repository

```bash
git clone https://github.com/arpitatandon-ds/NutriBite.git
cd NutriBite
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create an admin account (optional)

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open the application at:

```text
http://127.0.0.1:8000/
```

The Django admin panel is available at:

```text
http://127.0.0.1:8000/admin/
```

## 🧭 Main Application Pages

- **Home:** Introduction to NutriBite and featured meals.
- **Our Menu:** Browse the weekly menu and filter by diet type.
- **Meal Categories:** Explore meals by category.
- **Meal Details:** View meal descriptions and nutrition information.
- **Subscribe:** Create a meal subscription based on available menu options.
- **My Subscription:** View and manage the current subscription.
- **Subscription History:** Review previous subscriptions.

## 🔐 Notes

- This repository contains a development setup using SQLite.
- The subscription features demonstrate meal-plan and order management; the application does **not** currently process real payments or provide food delivery.
- For production deployment, configure a secure Django secret key, production `DEBUG` and `ALLOWED_HOSTS` values, static/media file hosting, and a production-ready database.
- Do not commit passwords, secret keys, environment files, or private user data.

## 👩‍💻 Author

**Arpita Tandon**

- GitHub: [@arpitatandon-ds](https://github.com/arpitatandon-ds)
- Project Repository: [NutriBite](https://github.com/arpitatandon-ds/NutriBite)

---

<p align="center">
  Made with ❤️ using Django
</p>
