import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd
import structlog

from .main_graph import State

logger = structlog.get_logger(__name__)


class DatabaseExecutor:
    """
    Executes generated databases, populates them with data, and validates SQL queries.
    """

    def __init__(self, db_folder: str = "output/db"):
        """
        Initialize the database executor.

        Args:
            db_folder: Folder to store SQLite databases
        """
        self.db_folder = Path(db_folder)
        self.db_folder.mkdir(exist_ok=True)

    def _create_temp_python_file(self, code: str, suffix: str = ".py") -> str:
        """
        Create a temporary Python file with the given code.

        Args:
            code: Python code to write to file
            suffix: File suffix

        Returns:
            Path to the temporary file
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            f.write(code)
            return f.name

    def _execute_python_file(self, file_path: str, db_path: str, models_file_path: str = None) -> Tuple[bool, str]:
        """
        Execute a Python file in a separate process with the database path.

        Args:
            file_path: Path to Python file to execute
            db_path: Path to SQLite database
            models_file_path: Path to models file (for population scripts)

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Modify the code to use the specified database path
            with open(file_path, "r") as f:
                code = f.read()

            # Replace common SQLite database patterns - be more comprehensive
            import re
            
            # Ensure db_path is absolute
            abs_db_path = str(Path(db_path).resolve())
            
            # Replace sqlite:/// patterns with any .db file (more precise)
            code = re.sub(r"sqlite:///([^'\")\s]+\.db)", f"sqlite:///{abs_db_path}", code)

            # Write modified code back
            with open(file_path, "w") as f:
                f.write(code)

            # Execute the file
            import subprocess

            # Check if this is a population script that expects arguments
            if models_file_path and "argparse" in code and "--input" in code:
                # This is a population script that expects command line arguments
                result = subprocess.run(
                    ["python", file_path, "--input", models_file_path, "--output", db_path], 
                    capture_output=True, text=True, timeout=30
                )
            else:
                # Regular script execution
                result = subprocess.run(
                    ["python", file_path], capture_output=True, text=True, timeout=30
                )

            if result.returncode == 0:
                # Log successful execution output for debugging
                if result.stdout:
                    logger.debug("Script execution output", stdout=result.stdout)
                return True, ""
            else:
                # Log both stdout and stderr for better debugging
                error_msg = f"Script failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nSTDERR: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nSTDOUT: {result.stdout}"
                logger.error("Script execution failed", 
                           return_code=result.returncode,
                           stderr=result.stderr,
                           stdout=result.stdout)
                return False, error_msg

        except subprocess.TimeoutExpired:
            return False, "Script execution timed out"
        except Exception as e:
            return False, str(e)
        # NOTE: File cleanup is now handled by the caller to avoid premature deletion

    def _execute_sql_query(self, db_path: str, query: str) -> Tuple[bool, Any, str]:
        """
        Execute a SQL query against the database.

        Args:
            db_path: Path to SQLite database
            query: SQL query to execute

        Returns:
            Tuple of (success, result, error_message)
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Execute the query
            cursor.execute(query)

            # Fetch results if it's a SELECT query
            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
                conn.commit()

            conn.close()
            return True, result, ""

        except Exception as e:
            try:
                conn.close()
            except (sqlite3.Error, AttributeError):
                pass
            return False, None, str(e)

    def _validate_database_populated(self, db_path: str) -> Tuple[bool, str]:
        """
        Validate that the database actually contains data.
        
        Args:
            db_path: Path to SQLite database
            
        Returns:
            Tuple of (has_data, error_message)
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                conn.close()
                return False, "No tables found in database"
            
            total_rows = 0
            table_counts = {}
            
            for (table_name,) in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                table_counts[table_name] = count
                total_rows += count
            
            conn.close()
            
            if total_rows == 0:
                return False, f"Database has tables but no data: {table_counts}"
            else:
                logger.debug("Database validation successful", 
                           total_rows=total_rows,
                           table_counts=table_counts)
                return True, ""
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def create_and_populate_database(
        self, database_info: Dict[str, Any], db_index: int
    ) -> Tuple[str, bool, str]:
        """
        Create and populate a single database.

        Args:
            database_info: Dictionary containing database models and population script
            db_index: Index of the database for naming

        Returns:
            Tuple of (db_path, success, error_message)
        """
        db_path = self.db_folder / f"database_{db_index}.db"
        db_path = db_path.resolve()  # Ensure absolute path

        models_file = None
        populate_file = None
        
        try:
            # Remove existing database
            if db_path.exists():
                db_path.unlink()

            # Create database schema
            models_file = self._create_temp_python_file(
                database_info["database_models"]
            )
            success, error = self._execute_python_file(models_file, str(db_path))

            if not success:
                return str(db_path), False, f"Failed to create schema: {error}"

            # Populate database - models_file is still available here
            populate_file = self._create_temp_python_file(
                database_info["populate_database_script"]
            )
            success, error = self._execute_python_file(populate_file, str(db_path), models_file)

            if not success:
                return str(db_path), False, f"Failed to populate database: {error}"
            
            # Validate that data was actually inserted
            validation_success, validation_error = self._validate_database_populated(str(db_path))
            if not validation_success:
                logger.warning("Population script ran successfully but database appears empty",
                             db_path=str(db_path),
                             validation_error=validation_error)
                # Don't fail here, just log the warning - the script might have run but with empty results

            logger.info("Database created and persisted", 
                       db_path=str(db_path),
                       db_index=db_index)
            return str(db_path), True, ""

        except Exception as e:
            return str(db_path), False, f"Unexpected error: {str(e)}"
        finally:
            # Clean up temporary files in finally block to ensure cleanup even on exceptions
            if models_file:
                try:
                    os.unlink(models_file)
                except OSError:
                    pass
            if populate_file:
                try:
                    os.unlink(populate_file)
                except OSError:
                    pass

    def validate_queries(
        self, db_path: str, question_sql_pairs: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Validate SQL queries against a database.

        Args:
            db_path: Path to SQLite database
            question_sql_pairs: List of question/SQL pairs

        Returns:
            List of validated query results
        """
        results = []

        for pair in question_sql_pairs:
            question = pair.get("question", "")
            sql = pair.get("sql", "")

            success, answer, error = self._execute_sql_query(db_path, sql)

            results.append(
                {
                    "db_path": db_path,
                    "question": question,
                    "query": sql,
                    "answer": answer if success else None,
                    "is_valid": success,
                    "error": error if not success else None,
                }
            )

        return results

    def process_main_graph_output(self, state: State) -> List[Dict[str, Any]]:
        """
        Process the output from the main graph and create validated dataset.

        Args:
            state: State object from main graph containing databases

        Returns:
            List of validated database entries
        """
        all_results = []
        total_databases = len(state["databases"])
        
        logger.info("Starting database processing", total_databases=total_databases)

        for i, database_info in enumerate(state["databases"]):
            logger.info("Processing database", 
                       database_index=i + 1, 
                       total=total_databases)

            # Create and populate database
            db_path, success, error = self.create_and_populate_database(
                database_info, i
            )

            if not success:
                logger.error("Failed to create database", 
                           database_index=i, 
                           error=error)
                # Still add entries for this database but mark as invalid
                question_sql_pairs = database_info.get("question_sql_pairs", {}).get(
                    "questions", []
                )
                for pair in question_sql_pairs:
                    all_results.append(
                        {
                            "db_path": db_path,
                            "question": pair.get("question", ""),
                            "query": pair.get("sql", ""),
                            "answer": None,
                            "is_valid": False,
                            "error": f"Database creation failed: {error}",
                        }
                    )
                continue

            # Validate queries
            question_sql_pairs = database_info.get("question_sql_pairs", {}).get(
                "questions", []
            )
            query_results = self.validate_queries(db_path, question_sql_pairs)
            all_results.extend(query_results)

            logger.info("Database processed successfully", 
                       database_index=i, 
                       queries_validated=len(query_results))

        # Collect unique database paths for summary
        unique_db_paths = set(result["db_path"] for result in all_results if result.get("db_path"))
        
        logger.info("Database processing complete", 
                   total_results=len(all_results),
                   databases_created=len(unique_db_paths),
                   db_folder=str(self.db_folder.resolve()))
        
        logger.info("Databases persisted at paths", 
                   database_paths=sorted(list(unique_db_paths)))
        
        return all_results

    def save_dataset(
        self, results: List[Dict[str, Any]], output_file: str = "validated_dataset.parquet"
    ):
        """
        Save the validated dataset to a parquet file.

        Args:
            results: List of validated query results
            output_file: Output file path
        """
        output_path = Path(output_file)
        
        df = pd.DataFrame(results)
        
        # Convert complex data types in 'answer' column to JSON strings
        if 'answer' in df.columns:
            df['answer'] = df['answer'].apply(lambda x: json.dumps(x) if x is not None else None)
        
        df.to_parquet(output_path)

        total_queries = len(results)
        valid_queries = sum(1 for r in results if r["is_valid"])
        validity_rate = valid_queries / total_queries if total_queries > 0 else 0
        
        logger.info("Dataset saved", 
                   output_path=str(output_path),
                   total_queries=total_queries,
                   valid_queries=valid_queries,
                   validity_rate=validity_rate)
