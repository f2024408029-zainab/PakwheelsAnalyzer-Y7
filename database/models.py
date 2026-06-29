
import csv
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, Session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pakwheels.db")
CSV_PATH = os.path.join(BASE_DIR, "sample_data.csv")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base = declarative_base()


class Car(Base):
    """Database model for a PakWheels car listing."""
    __tablename__ = "cars"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    title   = Column(String, nullable=False)
    price   = Column(String, nullable=False)
    year    = Column(String, nullable=False)
    mileage = Column(String, nullable=False)
    city    = Column(String, nullable=False)

    def __repr__(self):
        return f"<Car id={self.id} title={self.title!r} price={self.price!r}>"

def init_db():
    """Create database tables if they don't exist."""
    Base.metadata.create_all(engine)
    print("[INFO] Database initialized successfully.")


def load_csv_to_db(csv_path=CSV_PATH):
    """Read scraped CSV data and insert records into the database."""
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        return

    with Session(engine) as session:
       with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            records = []
            for row in reader:
                car = Car(
                    title   = row.get("title",   "N/A"),
                    price   = row.get("price",   "N/A"),
                    year    = row.get("year",    "N/A"),
                    mileage = row.get("mileage", "N/A"),
                    city    = row.get("city",    "N/A"),
                )
                records.append(car)

            session.add_all(records)
            session.commit()
            print(f"[INFO] {len(records)} car records inserted into database.")


def fetch_all_cars():
    """Retrieve and display all car records from the database."""
    with Session(engine) as session:
        cars = session.query(Car).all()
        print(f"\n[INFO] Total records in DB: {len(cars)}")
        for car in cars[:5]:
            print(f"  -> {car}")
    return cars

if __name__ == "__main__":
    init_db()
    load_csv_to_db()
    fetch_all_cars()