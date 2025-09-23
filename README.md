# 📚 My Quotes - Quote Management System

**My Quotes** is a web-based application designed to manage, organize, and visualize Kindle Highlights efficiently.

---

## 🖼️ Application Previews

### Quotes Table
![Quotes Table](static/images/Screenshot_383.png)

### Characters Page
![Characters Page](static/images/Screenshot_385.png)

### Book Gallery
![Book Gallery](static/images/Screenshot_384.png)

### Detailed Book View
![Detailed Book View](static/images/Screenshot_386.png)

---

## 🚀 Key Features

- **Random Quotes:** Display random quotes from your collection.
- **All Quotes:** Browse your complete library of saved quotes.
- **Books View:** Explore quotes grouped by book covers in a visual gallery.
- **Search Functionality:** Quickly search quotes, books, or authors.
- **Type Filters:** Filter quotes by categories (e.g., green, red, blue, yellow, cyan).
- **Notes Management:** Add, edit, or delete personal notes for each quote.
- **Interactive Table View:** View and manage quotes in an organized table format.
- **Dynamic Grid View:** Visualize book covers in a clean and modern grid layout.

## 🛠️ Technology Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Libraries:** Pandas (for data processing), SQLAlchemy (ORM)

## 📥 Data Import

- Import Kindle highlights from a .txt file (My Clippings.txt).
- Automatically processes and categorizes quotes.
- Prevents duplicate entries in the database.
- Generates an .xlsx file before importing into the database.

## 💾 Data Organization

- **Books Table:** Stores book titles, authors, and cover URLs.
- **Quotes Table:** Stores quotes, page numbers, types, and notes.
- **Relationships:** Quotes are linked to their respective books.

## ⚙️ How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/marciomizuhara/MyQuotes.git
   cd MyQuotes
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

4. Run the application:
   ```bash
   flask run
   ```

5. Access the app at: [http://127.0.0.1:5001](http://127.0.0.1:5001)

## 📂 Project Structure
```
MyQuotes/
├── app.py             # Main Flask application
├── models.py          # Database models
├── import_excel.py    # Kindle highlights importer
├── templates/         # HTML templates
├── static/            # CSS, JavaScript, and assets
├── data/
│   ├── input/         # My Clippings.txt goes here
│   └── output/        # quotes.xlsx is generated here
├── instance/          # SQLite database (ignored by Git)
├── requirements.txt   # Dependencies
├── .env.example       # Example environment configuration
└── README.md          # Project documentation
```


## 🌟 Future Improvements

- User authentication and profiles.
- Export quotes to PDF or Word.
- Enhanced analytics and reporting.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.
Please fork the repository and open a pull request.

## 📄 License

This project is licensed under the **MIT License**.

---