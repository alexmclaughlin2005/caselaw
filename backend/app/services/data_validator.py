"""
Data Validator Service

Validates data integrity after import.
"""
import logging
from datetime import datetime
from typing import Dict, List
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from app.core.database import engine

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Service for validating data integrity after import.
    """
    
    def __init__(self):
        """Initialize data validator."""
        pass
    
    def validate_foreign_keys(self, db_session: Session) -> Dict[str, bool]:
        """
        Validate all foreign key constraints.
        
        Args:
            db_session: Database session
            
        Returns:
            Dictionary mapping constraint names to validation results
        """
        results = {}
        
        try:
            # Get all foreign key constraints
            inspector = inspect(engine)
            
            # Check each table for foreign key violations
            for table_name in inspector.get_table_names():
                fks = inspector.get_foreign_keys(table_name)
                
                for fk in fks:
                    constraint_name = fk['name']
                    constrained_columns = fk['constrained_columns']
                    referred_table = fk['referred_table']
                    referred_columns = fk['referred_columns']
                    
                    # Check for orphaned records
                    check_sql = f"""
                        SELECT COUNT(*)
                        FROM {table_name} t
                        WHERE NOT EXISTS (
                            SELECT 1
                            FROM {referred_table} r
                            WHERE {' AND '.join(f"t.{col} = r.{ref_col}" 
                                               for col, ref_col in zip(constrained_columns, referred_columns))}
                        )
                    """
                    
                    result = db_session.execute(text(check_sql))
                    orphaned_count = result.scalar()
                    
                    results[constraint_name] = orphaned_count == 0
                    
                    if orphaned_count > 0:
                        logger.warning(
                            f"Found {orphaned_count} orphaned records in {table_name} "
                            f"for constraint {constraint_name}"
                        )
        
        except Exception as e:
            logger.error(f"Error validating foreign keys: {str(e)}")
            raise
        
        return results
    
    def validate_record_counts(
        self,
        expected_counts: Dict[str, int],
        db_session: Session
    ) -> Dict[str, Dict]:
        """
        Validate record counts match expected values.
        
        Args:
            expected_counts: Dictionary mapping table names to expected counts
            db_session: Database session
            
        Returns:
            Dictionary with validation results for each table
        """
        results = {}
        
        for table_name, expected_count in expected_counts.items():
            try:
                result = db_session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                actual_count = result.scalar()
                
                results[table_name] = {
                    'expected': expected_count,
                    'actual': actual_count,
                    'matches': actual_count == expected_count,
                    'difference': actual_count - expected_count
                }
                
                if actual_count != expected_count:
                    logger.warning(
                        f"Table {table_name}: expected {expected_count}, "
                        f"got {actual_count} (difference: {actual_count - expected_count})"
                    )
            
            except Exception as e:
                logger.error(f"Error validating record count for {table_name}: {str(e)}")
                results[table_name] = {
                    'expected': expected_count,
                    'actual': None,
                    'matches': False,
                    'error': str(e)
                }
        
        return results
    
    def validate_data_quality(self, db_session: Session) -> Dict[str, List[str]]:
        """
        Run basic data quality checks.
        
        Args:
            db_session: Database session
            
        Returns:
            Dictionary with warnings and errors
        """
        warnings = []
        errors = []
        
        try:
            # Check for people without names
            result = db_session.execute(text("""
                SELECT COUNT(*) FROM people_db_person
                WHERE (name_first IS NULL OR name_first = '')
                  AND (name_last IS NULL OR name_last = '')
            """))
            no_name_count = result.scalar()
            if no_name_count > 0:
                warnings.append(f"Found {no_name_count} people without first or last name")
            
            # Check for positions without dates
            result = db_session.execute(text("""
                SELECT COUNT(*) FROM people_db_position
                WHERE date_start IS NULL AND date_termination IS NULL
            """))
            no_dates_count = result.scalar()
            if no_dates_count > 0:
                warnings.append(f"Found {no_dates_count} positions without start or termination dates")
            
            # Check for positions with invalid date ranges
            result = db_session.execute(text("""
                SELECT COUNT(*) FROM people_db_position
                WHERE date_start IS NOT NULL
                  AND date_termination IS NOT NULL
                  AND date_termination < date_start
            """))
            invalid_dates_count = result.scalar()
            if invalid_dates_count > 0:
                errors.append(f"Found {invalid_dates_count} positions with termination date before start date")
            
            # Check for educations without schools
            result = db_session.execute(text("""
                SELECT COUNT(*) FROM people_db_education
                WHERE school_id IS NULL
            """))
            no_school_count = result.scalar()
            if no_school_count > 0:
                warnings.append(f"Found {no_school_count} education records without school")
        
        except Exception as e:
            logger.error(f"Error validating data quality: {str(e)}")
            errors.append(f"Validation error: {str(e)}")
        
        return {
            'warnings': warnings,
            'errors': errors
        }
    
    def run_full_validation(self, db_session: Session) -> Dict:
        """
        Run all validation checks.
        
        Args:
            db_session: Database session
            
        Returns:
            Dictionary with all validation results
        """
        logger.info("Running full data validation")
        
        results = {
            'foreign_keys': {},
            'data_quality': {},
            'timestamp': None
        }
        
        try:
            # Validate foreign keys
            results['foreign_keys'] = self.validate_foreign_keys(db_session)
            
            # Validate data quality
            results['data_quality'] = self.validate_data_quality(db_session)
            
            results['timestamp'] = datetime.now().isoformat()
            
            # Determine overall status
            fk_passed = all(results['foreign_keys'].values())
            no_errors = len(results['data_quality'].get('errors', [])) == 0
            
            results['passed'] = fk_passed and no_errors
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            results['error'] = str(e)
            results['passed'] = False
        
        return results

