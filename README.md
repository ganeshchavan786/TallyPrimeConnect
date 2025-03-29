
## Requirements

*   Python 3.8+
*   Libraries listed in `requirements.txt`:
    *   Pillow (`pip install Pillow`)
    *   requests (`pip install requests`)

## Installation & Running

1.  **Clone/Setup:** Get the project files and navigate into the `TallyPrimeConnect` directory.
2.  **Create Assets:** Place required `.png` files in `assets/` and `assets/icons/`.
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run:**
    ```bash
    python app.py
    ```
    The SQLite database (`biz_analyst_data.db`) and log file (`app.log`) will be created automatically inside the `config/` directory (which is also created if needed).

## Notes

*   Ensure Tally Prime is running with the required company open and ODBC enabled on the configured port (default 9000) for fetching companies.
*   The connection check in Settings uses a simple HTTP GET. Fetching companies uses an XML POST request.
*   Company deletion is a "soft delete" (marks `is_active=0` in the database); data is not permanently removed by default.
*   Error details are often logged to `app.log` and the console.