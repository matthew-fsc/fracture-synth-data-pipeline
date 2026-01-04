"""
Dataset registry for versioned, quality-gated training samples.

Manages the /data/registry/ directory with automated quality gates.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import shutil

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DatasetMetadata(BaseModel):
    """Metadata for a registered dataset."""
    dataset_id: str
    version: str
    sample_id: str
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    quality_scores: Dict = Field(default_factory=dict)
    validation_results: Dict = Field(default_factory=dict)
    file_paths: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)


class DatasetRegistry:
    """Manages versioned dataset registry with quality gates."""
    
    def __init__(self, registry_dir: Optional[Path] = None):
        """
        Initialize dataset registry.
        
        Args:
            registry_dir: Directory for registered datasets
        """
        if registry_dir is None:
            registry_dir = Path(__file__).parent.parent / "data" / "registry"
        
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.registry_dir / "registry_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load registry metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {"datasets": [], "versions": {}}
    
    def _save_metadata(self):
        """Save registry metadata."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def register_dataset(
        self,
        sample_id: str,
        json_path: str,
        csv_path: str,
        quality_scores: Dict,
        validation_results: Dict,
        metadata: Optional[Dict] = None,
        quality_threshold: float = 0.7
    ) -> bool:
        """
        Register a dataset if it passes quality gates.
        
        Args:
            sample_id: Training sample ID
            json_path: Path to JSON file
            csv_path: Path to CSV file
            quality_scores: Quality scores dictionary
            validation_results: Validation results dictionary
            metadata: Additional metadata
            quality_threshold: Minimum quality score to pass
            
        Returns:
            True if registered, False if failed quality gates
        """
        # Check quality gates
        realism_score = quality_scores.get("realism_score", 0.0)
        schema_passed = validation_results.get("schema", {}).get("all_passed", False)
        realism_passed = validation_results.get("realism", {}).get("all_passed", False)
        
        if realism_score < quality_threshold:
            logger.warning(f"Dataset {sample_id} failed quality gate: realism_score {realism_score} < {quality_threshold}")
            return False
        
        if not schema_passed:
            logger.warning(f"Dataset {sample_id} failed quality gate: schema validation failed")
            return False
        
        if not realism_passed:
            logger.warning(f"Dataset {sample_id} failed quality gate: realism validation failed")
            return False
        
        # Generate dataset ID and version
        dataset_id = f"dataset_{sample_id}"
        version = "1.0.0"
        
        # Create versioned directory
        version_dir = self.registry_dir / dataset_id / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files to registry
        json_dest = version_dir / Path(json_path).name
        csv_dest = version_dir / Path(csv_path).name
        
        shutil.copy2(json_path, json_dest)
        shutil.copy2(csv_path, csv_dest)
        
        # Create metadata
        dataset_metadata = DatasetMetadata(
            dataset_id=dataset_id,
            version=version,
            sample_id=sample_id,
            quality_scores=quality_scores,
            validation_results=validation_results,
            file_paths={
                "json": str(json_dest),
                "csv": str(csv_dest)
            },
            metadata=metadata or {}
        )
        
        # Update registry
        self.metadata["datasets"].append(dataset_metadata.dict())
        self.metadata["versions"][dataset_id] = version
        
        self._save_metadata()
        
        logger.info(f"Registered dataset {dataset_id} v{version}")
        return True
    
    def list_datasets(self) -> List[Dict]:
        """List all registered datasets."""
        return self.metadata.get("datasets", [])
    
    def get_dataset(self, dataset_id: str, version: Optional[str] = None) -> Optional[Dict]:
        """
        Get dataset metadata.
        
        Args:
            dataset_id: Dataset ID
            version: Optional version (defaults to latest)
            
        Returns:
            Dataset metadata or None
        """
        datasets = [d for d in self.metadata.get("datasets", []) if d["dataset_id"] == dataset_id]
        
        if not datasets:
            return None
        
        if version:
            datasets = [d for d in datasets if d["version"] == version]
        
        if not datasets:
            return None
        
        # Return latest if no version specified
        return max(datasets, key=lambda x: x["registered_at"])
    
    def search_datasets(
        self,
        industry: Optional[str] = None,
        min_realism_score: Optional[float] = None,
        min_complexity: Optional[float] = None
    ) -> List[Dict]:
        """
        Search datasets by criteria.
        
        Args:
            industry: Filter by industry
            min_realism_score: Minimum realism score
            min_complexity: Minimum complexity score
            
        Returns:
            List of matching datasets
        """
        datasets = self.metadata.get("datasets", [])
        
        results = []
        for dataset in datasets:
            # Get full sample data to check criteria
            sample_metadata = dataset.get("metadata", {})
            company_profile = sample_metadata.get("company_profile", {})
            
            if industry and company_profile.get("industry") != industry:
                continue
            
            realism_score = dataset.get("quality_scores", {}).get("realism_score", 0.0)
            if min_realism_score and realism_score < min_realism_score:
                continue
            
            # Complexity would be in manifest
            # For now, skip complexity check or add it to metadata
            
            results.append(dataset)
        
        return results

