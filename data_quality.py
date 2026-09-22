from sqlalchemy import text
from db_utils import get_engine


class DataQualityError(Exception):
    pass


def check_no_null_close():
    engine = get_engine()
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM staging_prices WHERE close IS NULL")
        ).scalar()
    if count > 0:
        raise DataQualityError(f"{count} rows in staging_prices have a NULL close price")
    print("check_no_null_close: passed")


def check_no_duplicate_rows():
    engine = get_engine()
    with engine.connect() as conn:
        count = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT ticker, trade_date, COUNT(*)
                FROM staging_prices
                GROUP BY ticker, trade_date
                HAVING COUNT(*) > 1
            ) dupes
        """)).scalar()
    if count > 0:
        raise DataQualityError(f"{count} duplicate (ticker, trade_date) pairs in staging_prices")
    print("check_no_duplicate_rows: passed")


def check_prices_positive():
    engine = get_engine()
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM staging_prices WHERE close <= 0")
        ).scalar()
    if count > 0:
        raise DataQualityError(f"{count} rows have a non-positive close price")
    print("check_prices_positive: passed")


def run():
    check_no_null_close()
    check_no_duplicate_rows()
    check_prices_positive()
    print("All data quality checks passed")


if __name__ == "__main__":
    run()