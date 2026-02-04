from scraper import main  # noqa: I001
from notification import notify_error, notify_success

if __name__ == "__main__":
    try:
        main()
        notify_success("Job Mensal Das")
    except Exception:
        notify_error("Job Mensal Das")
        raise
