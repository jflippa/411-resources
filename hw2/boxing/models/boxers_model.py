from dataclasses import dataclass
import logging
import sqlite3
from typing import Any, List

from boxing.utils.sql_utils import get_db_connection
from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)

"""A holder of values for the different data types. Simply assigns a type to each value"""
@dataclass
class Boxer:
    id: int
    name: str
    weight: int
    height: int
    reach: float
    age: int
    weight_class: str = None

    def __post_init__(self):
        self.weight_class = get_weight_class(self.weight)  # Automatically assign weight class


def create_boxer(name: str, weight: int, height: int, reach: float, age: int) -> None:
    """Adds a new boxer
    Args:
        name (string): the boxers name
        weight: the boxers weight (int)
        height: The height of the boxer (int)
        reach: A float for the reach of the boxer
        age: The int age of the boxer

    Raises:
        ValueError for invalide weight, height, reach, and age. Also if boxer with the name already exists
        """
    logger.info("Received request to add a boxer to the database")
    if weight < 125:
        logger.error("Invalid Value: weight must be at least 125")
        raise ValueError(f"Invalid weight: {weight}. Must be at least 125.")
    if height <= 0:
        logger.error("Invalid Value: height must be greater than 0")
        raise ValueError(f"Invalid height: {height}. Must be greater than 0.")
    if reach <= 0:
        logger.error("Invalid Value: reach must be greater than 0")
        raise ValueError(f"Invalid reach: {reach}. Must be greater than 0.")
    if not (18 <= age <= 40):
        logger.error("Invalid Value: age must be between 18 and 40")
        raise ValueError(f"Invalid age: {age}. Must be between 18 and 40.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the boxer already exists (name must be unique)
            cursor.execute("SELECT 1 FROM boxers WHERE name = ?", (name,))
            if cursor.fetchone():
                logger.error(f"Boxer with name '{name}' already exists")
                raise ValueError(f"Boxer with name '{name}' already exists")

            cursor.execute("""
                INSERT INTO boxers (name, weight, height, reach, age)
                VALUES (?, ?, ?, ?, ?)
            """, (name, weight, height, reach, age))

            conn.commit()
            logger.info(f"Successfully boxer song to database: {name} - {weight} - {height} - {reach} - {age}")
    except sqlite3.IntegrityError:
        raise ValueError(f"Boxer with name '{name}' already exists")

    except sqlite3.Error as e:
        raise e


def delete_boxer(boxer_id: int) -> None:
    """Removes boxer from database
    Args:
        boxer_id (int): The ID of the boxer to be removed 
        
    Raises: 
        ValueError: If the boxer does not exist or the ID is invalid
        """
    logger.info("Received request to remove boxer from database")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.error(f"Boxer with ID {boxer_id} not found")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            cursor.execute("DELETE FROM boxers WHERE id = ?", (boxer_id,))
            conn.commit()

    except sqlite3.Error as e:
        raise e
    logger.info("boxer successfully removed")

def get_leaderboard(sort_by: str = "wins") -> List[dict[str, Any]]:
    """Sorts boxers by either wins or win percentage
        Args: 
            sort_by (str): thing to sort boxers by
        
        Raises:
            ValueError: If sort_by is invalid

        Returns: leaderboard (list) which is the ranking of all the boxers.
    """
    logger.info("Recieved request for boxer leaderboard")
    query = """
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.error(f"Invalid sort_by parameter: {sort_by}")
        raise ValueError(f"Invalid sort_by parameter: {sort_by}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        leaderboard = []
        for row in rows:
            boxer = {
                'id': row[0],
                'name': row[1],
                'weight': row[2],
                'height': row[3],
                'reach': row[4],
                'age': row[5],
                'weight_class': get_weight_class(row[2]),  # Calculate weight class
                'fights': row[6],
                'wins': row[7],
                'win_pct': round(row[8] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(boxer)

        return leaderboard
      ##  
    except sqlite3.Error as e:
        raise e
    logger.info("successfully returned leaderboard")

def get_boxer_by_id(boxer_id: int) -> Boxer:
    """returns a boxer selected by using the boxer ID
        Args: 
            boxer_id (int): the boxers ID
        
        Raises:
            ValueError: If the boxer ID does not exist or is invalid

        Returns:
            boxer (Dict): the boxer with the ID given
            """
    logger.info("Successfully recieved get boxer by ID request")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE id = ?
            """, (boxer_id,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                return boxer
            else:
                logger.error(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

    except sqlite3.Error as e:
        raise e
    logger.info("Successfully returned boxer")

####
def get_boxer_by_name(boxer_name: str) -> Boxer:
    """Returns boxer selected by name

        Args: 
            boxer_name (str): name of the boxer
        
        Raises:
            ValueError: If boxer name is invalid or not in the database

        Returns:
            boxer (dict)
    """
    logger.info("Successfully recieved get boxer by name request")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE name = ?
            """, (boxer_name,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                return boxer
            else:
                logger.error(f"Boxer '{boxer_name}' not found.")
                raise ValueError(f"Boxer '{boxer_name}' not found.")

    except sqlite3.Error as e:
        raise e
    logger.info("Successfully returned boxer")

def get_weight_class(weight: int) -> str:
    """Gets the weight class for a boxer
        Args:
            weight (int): the weight of the boxer

        Raises:
            ValueError: If the weight is less than 125
        
        Returns: weight_class (str)
    """
    logger.info("Successfully recieved get weight class request")
    if weight >= 203:
        weight_class = 'HEAVYWEIGHT'
    elif weight >= 166:
        weight_class = 'MIDDLEWEIGHT'
    elif weight >= 133:
        weight_class = 'LIGHTWEIGHT'
    elif weight >= 125:
        weight_class = 'FEATHERWEIGHT'
    else:
        logger.error("fInvalid weight: {weight}. Weight must be at least 125.")
        raise ValueError(f"Invalid weight: {weight}. Weight must be at least 125.")
    logger.info("Successfully returned weight class")
    return weight_class


def update_boxer_stats(boxer_id: int, result: str) -> None:
    """Updates a boxer with the result of a match
        Args: 
            boxer_id (int): ID of the boxer
            result (str): result of the last game
        Raises: 
            ValueError: If invalid result (not win or loss)
            ValueError: If boxer ID is not in database or is invalid"""
    logger.info("Recieved boxer update request")
    if result not in {'win', 'loss'}:
        logger.error(f"Invalid result: {result}. Expected 'win' or 'loss'.")
        raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.error(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            if result == 'win':
                cursor.execute("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?", (boxer_id,))
            else:  # result == 'loss'
                cursor.execute("UPDATE boxers SET fights = fights + 1 WHERE id = ?", (boxer_id,))

            conn.commit()

    except sqlite3.Error as e:
        raise e
    logger.info("Successfully updated boxer")