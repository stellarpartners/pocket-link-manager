# Tests Directory

Test scripts for validating database functionality and data integrity.

## Test Scripts

### test_database.py

Comprehensive test suite for database functionality.

**Test Coverage:**

1. **Database Initialization** - Tests database creation and setup
2. **Database Models** - Tests model creation and relationships
3. **Query Functions** - Tests query classes and methods
4. **Small CSV Import** - Tests importing a sample CSV

**Usage:**

```bash
python tests/test_database.py
```

**Output:**

- Detailed test results for each component
- Summary of passed/failed tests
- Error messages for failures

**Requirements:**

- Database must be initialized
- Test CSV will be created temporarily (first 10 rows)

### verify_database.py

Verify database contents and display statistics.

**Usage:**

```bash
python tests/verify_database.py
```

**Output:**

- Total link count
- Pocket status breakdown
- HTTP status code distribution
- Quality score distribution
- Sample links with details
- Top domains statistics

Useful for:
- Verifying imports completed successfully
- Understanding your data distribution
- Debugging data issues

### test_output.md

Test output documentation (if available).

## Running Tests

Run all tests:

```bash
# Run database tests
python tests/test_database.py

# Verify database contents
python tests/verify_database.py
```

Make sure the database is initialized before running tests:

```bash
python -c "from database.init_db import init_database; init_database()"
```
