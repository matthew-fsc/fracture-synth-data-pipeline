"""
Schema validation using JSON Schema and Pydantic.

Validates that synthetic data conforms to expected schemas.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import jsonschema
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class SchemaValidationResult(BaseModel):
    """Schema validation result."""
    passed: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SchemaValidator:
    """Validates data against JSON schemas."""
    
    def __init__(self, schemas_dir: Optional[Path] = None):
        """
        Initialize schema validator.
        
        Args:
            schemas_dir: Directory containing JSON schema files
        """
        if schemas_dir is None:
            schemas_dir = Path(__file__).parent.parent.parent / "schemas"
        
        self.schemas_dir = Path(schemas_dir)
        self.schemas = {}
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all JSON schemas from schemas directory."""
        schema_files = {
            "company_profile": "company_profile.json",
            "system_manifest": "system_manifest.json",
            "training_sample": "training_sample.json"
        }
        
        for schema_name, filename in schema_files.items():
            schema_path = self.schemas_dir / filename
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    self.schemas[schema_name] = json.load(f)
            else:
                logger.warning(f"Schema file not found: {schema_path}")
    
    def validate_company_profile(
        self,
        data: Dict[str, Any]
    ) -> SchemaValidationResult:
        """
        Validate company profile against schema.
        
        Args:
            data: Company profile data
            
        Returns:
            Validation result
        """
        return self._validate_against_schema(data, "company_profile")
    
    def validate_system_manifest(
        self,
        data: Dict[str, Any]
    ) -> SchemaValidationResult:
        """
        Validate system manifest against schema.
        
        Args:
            data: System manifest data
            
        Returns:
            Validation result
        """
        return self._validate_against_schema(data, "system_manifest")
    
    def validate_training_sample(
        self,
        data: Dict[str, Any]
    ) -> SchemaValidationResult:
        """
        Validate training sample against schema.
        
        Args:
            data: Training sample data
            
        Returns:
            Validation result
        """
        return self._validate_against_schema(data, "training_sample")
    
    def _validate_against_schema(
        self,
        data: Dict[str, Any],
        schema_name: str
    ) -> SchemaValidationResult:
        """Validate data against a named schema."""
        if schema_name not in self.schemas:
            return SchemaValidationResult(
                passed=False,
                errors=[f"Schema '{schema_name}' not found"]
            )
        
        schema = self.schemas[schema_name]
        errors = []
        
        try:
            jsonschema.validate(instance=data, schema=schema)
            return SchemaValidationResult(passed=True)
        except jsonschema.ValidationError as e:
            errors.append(f"Validation error: {e.message} at {'.'.join(str(p) for p in e.path)}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
        
        return SchemaValidationResult(passed=False, errors=errors)
    
    def validate_pydantic_model(
        self,
        model_class: type[BaseModel],
        data: Dict[str, Any]
    ) -> SchemaValidationResult:
        """
        Validate data using a Pydantic model.
        
        Args:
            model_class: Pydantic model class
            data: Data to validate
            
        Returns:
            Validation result
        """
        errors = []
        
        try:
            model_class(**data)
            return SchemaValidationResult(passed=True)
        except ValidationError as e:
            for error in e.errors():
                field = '.'.join(str(p) for p in error['loc'])
                msg = error['msg']
                errors.append(f"{field}: {msg}")
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
        
        return SchemaValidationResult(passed=False, errors=errors)

