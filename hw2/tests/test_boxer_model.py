from contextlib import contextmanager
import re
import sqlite3

import pytest
#######
from boxing.models.boxers_model import (
    Boxer,
    create_boxer,
    delete_boxer,
    get_leaderboard,
    get_boxer_by_id,
    get_boxer_by_name,
    update_boxer_stats
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("boxing.models.boxer_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test


######################################################
#
#    Add and delete
#
######################################################


def test_create_boxer(mock_cursor):
    """Test creating a new boxer in the database.

    """
    create_boxer(name = "Boxer Name", weight = 150 , height = 70, reach = 20.5, age = 25)

    expected_query = normalize_whitespace("""
        INSERT INTO boxers (name, weight, height, reach, age)
        VALUES (?, ?, ?, ?, ?)
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Boxer Name", 150, 70, 20.5, 25)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_create_boxer_duplicate(mock_cursor):
    """Test creating a boxer with a duplicate name, should raise error.

    """
    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: boxer.name")

    with pytest.raises(ValueError, match="Boxer with name 'Boxer Name' already exists."):
        create_boxer(boxer="Boxer Name", weight = 150 , height = 70, reach = 20.5, age = 25)


def test_create_boxer_invalid_weight():
    """Test error when trying to create a boxer with an invalid weight (e.g., less than 125)

    """
    with pytest.raises(ValueError, match=r"Invalid weight: 110 \(Must be at least 125\)."):
        create_boxer(name = "Boxer Name", weight = 110 , height = 70, reach = 20.5, age = 25)

    with pytest.raises(ValueError, match=r"Invalid weight: invalid \(must be an integer above 125\)."):
        create_boxer(name = "Boxer Name", weight = "invalid" , height = 70, reach = 20.5, age = 25)

def test_create_boxer_invalid_height():
    """Test error when trying to create a boxer with an invalid height (e.g., negative height)

    """
    with pytest.raises(ValueError, match=r"Invalid height: -80 \(height must be greater than 0\)."):
        create_boxer(name = "Boxer Name", weight = 150 , height = -80, reach = 20.5, age = 25)

    with pytest.raises(ValueError, match=r"Invalid height: invalid \(height must be greater than 0\)."):
        create_boxer(name = "Boxer Name", weight = 150 , height = "invalid", reach = 20.5, age = 25)

def test_create_boxer_invalid_reach():
    """Test error when trying to create a boxer with an invalid reach (e.g., negative reach)

    """
    with pytest.raises(ValueError, match=r"Invalid reach: -20 \(reach must be greater than 0\)."):
        create_boxer(name = "Boxer Name", weight = 150 , height = 70, reach = -20, age = 25)

    with pytest.raises(ValueError, match=r"Invalid reach: invalid \(reach must be greater than 0\)."):
        create_boxer(name = "Boxer Name", weight = 150 , height = 70, reach = "invalid", age = 25)


def test_create_boxer_invalid_age():
    """Test error when trying to create a boxer with an invalid age (e.g., not in between 18 and 40 or invalid).

    """
    with pytest.raises(ValueError, match=r"Invalid age: 17 \( Must be between 18 and 40\)."):
        create_boxer(name = "Boxer Name", weight = 150 , height = 70, reach = 20.5, age = 17)

    with pytest.raises(ValueError, match=r"Invalid age: 41 \( Must be between 18 and 40\)."):
        create_boxer(name = "Boxer Name", weight = 150 , height = 70, reach = 20.5, age = 41)

    with pytest.raises(ValueError, match=r"Invalid year: invalid \( Must be between 18 and 40\)."):
        create_boxer(name = "Boxer Name", weight = 150 , height = 70, reach = 20.5, age = "invalid")


def test_delete_boxer(mock_cursor):
    """Test deleting a boxer from the database by boxer ID.

    """
    # Simulate the existence of a boxer w/ id=1
    # We can use any value other than None
    mock_cursor.fetchone.return_value = (True)

    delete_boxer(1)

    expected_select_sql = normalize_whitespace("SELECT id FROM boxers WHERE id = ?")
    expected_delete_sql = normalize_whitespace("DELETE FROM boxers WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_delete_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_delete_sql == expected_delete_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_delete_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_delete_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_delete_args == expected_delete_args, f"The UPDATE query arguments did not match. Expected {expected_delete_args}, got {actual_delete_args}."


def test_delete_boxer_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent boxer.

    """
    # Simulate that no boxer exists with the given ID
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Boxer with ID 999 not found"):
        delete_boxer(999)


######################################################
#
#    Get Boxer
#
######################################################


def test_get_boxer_by_id(mock_cursor):
    """Test getting a boxer by id.

    """
    mock_cursor.fetchone.return_value = (1, "Boxer Name", 150 , 70, 20.5, 25, False)

    result = get_boxer_by_id(1)

    expected_result = Boxer(1, "Boxer Name", 150 , 70, 20.5, 25)

    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, name, weight, reach, age FROM boxers WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = (1,)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_get_boxer_by_id_bad_id(mock_cursor):
    """Test error when getting a non-existent boxer.

    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Boxer with ID 999 not found"):
        get_boxer_by_id(999)


def test_get_boxer_by_name(mock_cursor):
    """Test getting a boxer by name.

    """
    mock_cursor.fetchone.return_value = (1, "Boxer Name", 150 , 70, 20.5, 25, False)

    result = get_boxer_by_name("Boxer Name")

    expected_result = Boxer(1, "Boxer Name", 150 , 70, 20.5, 25)

    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, name, weight, height, age, FROM boxer WHERE name = ? AND weight = ? AND height = ? AND weight = ? AND age = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Boxer Name")

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_get_boxer_by_name_bad_name(mock_cursor):
    """Test error when getting a non-existent boxer.

    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Boxer with name 'Boxer Name' not found"):
        get_boxer_by_name("Boxer Name")


def test_get_leaderboard(mock_cursor):
    """Test retrieving boxer leaderboard.

    """
    mock_cursor.fetchall.return_value = [
        (1, "Boxer A", 150, 70, 20.5, 19, 10, False),
        (2, "Boxer B", 170, 72, 24, 22, 20, False),
        (3, "Boxer C", 160, 68, 18, 34, 5, False)
    ]

    boxers = get_leaderboard()

    expected_result = [
        {"id": 1, "name": "Boxer A", "weight": 150, "height": 70, "reach": 20.5, "age": 19, "wins": 10},
        {"id": 2, "name": "Boxer B", "weight": 170, "height": 72, "reach": 24, "age": 22, "wins": 20},
        {"id": 3, "name": "Boxer C", "weight": 160, "height": 68, "reach": 18, "age": 34, "wins": 5}
    ]

    assert boxers == expected_result, f"Expected {expected_result}, but got {boxers}"

    expected_query = normalize_whitespace("""
        SELECT id, name, weight, height, reach, age, wins
        FROM boxers
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."
    


def test_get_leaderboard_empty_leaderboard(mock_cursor, caplog):
    """Test that retrieving leaderboard returns an empty list when the leaderboard is empty and logs a warning.

    """
    mock_cursor.fetchall.return_value = []

    result = get_leaderboard()

    assert result == [], f"Expected empty list, but got {result}"

    assert "The leaderboard is empty." in caplog.text, "Expected warning about empty leaderboard not found in logs."

    expected_query = normalize_whitespace("SELECT id, name, height, weight, reach, age, wins FROM leaderboard")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."


######################################################
#
#    Play count
#
######################################################


def test_update_boxer_stats(mock_cursor):
    """Test updating the wins of a boxer.

    """
    mock_cursor.fetchone.return_value = True

    boxer_id = 1
    update_boxer_stats(boxer_id)

    expected_query = normalize_whitespace("""
        UPDATE boxers SET wins = wins + 1 WHERE id = ?
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]
    expected_arguments = (boxer_id,)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


