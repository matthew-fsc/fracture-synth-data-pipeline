"""
Enhanced Dataset Registry with complete versioning, lineage tracking, and metadata management.

Provides:
- Complete dataset versioning
- Dataset lineage tracking
- Dataset metadata management
- Dataset search and discovery
- Dataset approval workflow
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
import shutil
import hashlib

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DatasetStatus(str, Enum):
    """Dataset status in approval workflow."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class DatasetVersion(BaseModel):
    """Dataset version information."""
    version: str  # Semantic version: major.minor.patch
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    status: DatasetStatus = DatasetStatus.DRAFT
    changelog: str = ""
    parent_version: Optional[str] = None  # For lineage tracking
    quality_scores: Dict = Field(default_factory=dict)
    validation_results: Dict = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)
    file_checksums: Dict[str, str] = Field(default_factory=dict)  # file -> checksum


class DatasetLineage(BaseModel):
    """Dataset lineage information."""
    dataset_id: str
    versions: List[str] = Field(default_factory=list)  # Version history
    parent_datasets: List[str] = Field(default_factory=list)  # Derived from
    child_datasets: List[str] = Field(default_factory=list)  # Used to create
    pipeline_runs: List[str] = Field(default_factory=list)  # Pipeline run IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EnhancedDatasetRegistry:
    """
    Enhanced dataset registry with versioning, lineage, and metadata management.
    """
    
    def __init__(self, registry_dir: Optional[Path] = None):
        """
        Initialize enhanced dataset registry.
        
        Args:
            registry_dir: Directory for registered datasets
        """
        if registry_dir is None:
            registry_dir = Path(__file__).parent.parent / "data" / "registry"
        
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.registry_dir / "registry_metadata.json"
        self.lineage_file = self.registry_dir / "lineage.json"
        self._load_metadata()
        self._load_lineage()
    
    def _load_metadata(self):
        """Load registry metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "datasets": {},
                "versions": {},
                "approval_workflow": {}
            }
    
    def _save_metadata(self):
        """Save registry metadata."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def _load_lineage(self):
        """Load lineage information."""
        if self.lineage_file.exists():
            with open(self.lineage_file, 'r') as f:
                lineage_data = json.load(f)
                self.lineage = {
                    dataset_id: DatasetLineage(**data)
                    for dataset_id, data in lineage_data.items()
                }
        else:
            self.lineage = {}
    
    def _save_lineage(self):
        """Save lineage information."""
        lineage_data = {
            dataset_id: lineage.dict()
            for dataset_id, lineage in self.lineage.items()
        }
        with open(self.lineage_file, 'w') as f:
            json.dump(lineage_data, f, indent=2, default=str)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _increment_version(self, current_version: Optional[str] = None, version_type: str = "patch") -> str:
        """
        Increment semantic version.
        
        Args:
            current_version: Current version (e.g., "1.2.3")
            version_type: Type of increment: "major", "minor", or "patch"
            
        Returns:
            New version string
        """
        if not current_version:
            return "1.0.0"
        
        parts = current_version.split(".")
        if len(parts) != 3:
            return "1.0.0"
        
        major, minor, patch = map(int, parts)
        
        if version_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif version_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def register_dataset(
        self,
        sample_id: str,
        json_path: str,
        csv_path: str,
        quality_scores: Dict,
        validation_results: Dict,
        metadata: Optional[Dict] = None,
        dataset_id: Optional[str] = None,
        version: Optional[str] = None,
        parent_version: Optional[str] = None,
        created_by: Optional[str] = None,
        quality_threshold: float = 0.7
    ) -> Optional[str]:
        """
        Register a dataset with versioning.
        
        Args:
            sample_id: Training sample ID
            json_path: Path to JSON file
            csv_path: Path to CSV file
            quality_scores: Quality scores dictionary
            validation_results: Validation results dictionary
            metadata: Additional metadata
            dataset_id: Optional dataset ID (defaults to dataset_{sample_id})
            version: Optional version (defaults to 1.0.0 or increments)
            parent_version: Optional parent version for lineage
            created_by: Creator identifier
            quality_threshold: Minimum quality score to pass
            
        Returns:
            Registered dataset version ID or None if failed quality gates
        """
        # Check quality gates
        realism_score = quality_scores.get("realism_score", 0.0)
        schema_passed = validation_results.get("schema", {}).get("all_passed", False)
        realism_passed = validation_results.get("realism", {}).get("all_passed", False)
        
        if realism_score < quality_threshold:
            logger.warning(f"Dataset {sample_id} failed quality gate: realism_score {realism_score} < {quality_threshold}")
            return None
        
        if not schema_passed:
            logger.warning(f"Dataset {sample_id} failed quality gate: schema validation failed")
            return None
        
        if not realism_passed:
            logger.warning(f"Dataset {sample_id} failed quality gate: realism validation failed")
            return None
        
        # Determine dataset ID and version
        if not dataset_id:
            dataset_id = f"dataset_{sample_id}"
        
        # Get or create version
        if dataset_id in self.metadata.get("datasets", {}):
            existing_versions = self.metadata["datasets"][dataset_id].get("versions", [])
            if not version:
                # Increment patch version
                latest_version = max(existing_versions, key=lambda v: v["version"]) if existing_versions else None
                current_version = latest_version["version"] if latest_version else None
                version = self._increment_version(current_version, "patch")
            else:
                # Check if version already exists
                if any(v["version"] == version for v in existing_versions):
                    logger.error(f"Version {version} already exists for dataset {dataset_id}")
                    return None
        else:
            version = version or "1.0.0"
        
        # Create versioned directory
        version_dir = self.registry_dir / dataset_id / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files to registry
        json_dest = version_dir / Path(json_path).name
        csv_dest = version_dir / Path(csv_path).name
        
        shutil.copy2(json_path, json_dest)
        shutil.copy2(csv_path, csv_dest)
        
        # Calculate checksums
        file_checksums = {
            "json": self._calculate_checksum(json_dest),
            "csv": self._calculate_checksum(csv_dest)
        }
        
        # Create version metadata
        dataset_version = DatasetVersion(
            version=version,
            created_by=created_by,
            status=DatasetStatus.DRAFT,
            parent_version=parent_version,
            quality_scores=quality_scores,
            validation_results=validation_results,
            metadata=metadata or {},
            file_checksums=file_checksums
        )
        
        # Update registry
        if dataset_id not in self.metadata["datasets"]:
            self.metadata["datasets"][dataset_id] = {
                "dataset_id": dataset_id,
                "created_at": datetime.utcnow().isoformat(),
                "versions": []
            }
        
        self.metadata["datasets"][dataset_id]["versions"].append(dataset_version.dict())
        self.metadata["versions"][f"{dataset_id}:{version}"] = {
            "dataset_id": dataset_id,
            "version": version,
            "status": dataset_version.status.value,
            "created_at": dataset_version.created_at.isoformat()
        }
        
        # Update lineage
        if dataset_id not in self.lineage:
            self.lineage[dataset_id] = DatasetLineage(dataset_id=dataset_id)
        
        self.lineage[dataset_id].versions.append(version)
        self.lineage[dataset_id].updated_at = datetime.utcnow()
        
        if parent_version:
            parent_dataset_id = parent_version.split(":")[0] if ":" in parent_version else dataset_id
            if parent_dataset_id != dataset_id and parent_dataset_id in self.lineage:
                if dataset_id not in self.lineage[parent_dataset_id].child_datasets:
                    self.lineage[parent_dataset_id].child_datasets.append(dataset_id)
                if parent_dataset_id not in self.lineage[dataset_id].parent_datasets:
                    self.lineage[dataset_id].parent_datasets.append(parent_dataset_id)
        
        self._save_metadata()
        self._save_lineage()
        
        version_id = f"{dataset_id}:{version}"
        logger.info(f"Registered dataset version: {version_id}")
        
        return version_id
    
    def approve_dataset(self, dataset_id: str, version: str, approved_by: str) -> bool:
        """
        Approve a dataset version.
        
        Args:
            dataset_id: Dataset ID
            version: Version to approve
            approved_by: Approver identifier
            
        Returns:
            True if approved successfully
        """
        if dataset_id not in self.metadata["datasets"]:
            logger.error(f"Dataset {dataset_id} not found")
            return False
        
        versions = self.metadata["datasets"][dataset_id]["versions"]
        version_data = next((v for v in versions if v["version"] == version), None)
        
        if not version_data:
            logger.error(f"Version {version} not found for dataset {dataset_id}")
            return False
        
        version_data["status"] = DatasetStatus.APPROVED.value
        version_data["approved_by"] = approved_by
        version_data["approved_at"] = datetime.utcnow().isoformat()
        
        self.metadata["versions"][f"{dataset_id}:{version}"]["status"] = DatasetStatus.APPROVED.value
        
        self._save_metadata()
        logger.info(f"Approved dataset {dataset_id} version {version}")
        
        return True
    
    def get_dataset(self, dataset_id: str, version: Optional[str] = None) -> Optional[Dict]:
        """
        Get dataset metadata.
        
        Args:
            dataset_id: Dataset ID
            version: Optional version (defaults to latest approved, or latest if none approved)
            
        Returns:
            Dataset metadata or None
        """
        if dataset_id not in self.metadata["datasets"]:
            return None
        
        versions = self.metadata["datasets"][dataset_id]["versions"]
        
        if version:
            version_data = next((v for v in versions if v["version"] == version), None)
            if version_data:
                return {
                    "dataset_id": dataset_id,
                    "version": version_data
                }
        else:
            # Get latest approved version, or latest version if none approved
            approved_versions = [v for v in versions if v.get("status") == DatasetStatus.APPROVED.value]
            if approved_versions:
                latest = max(approved_versions, key=lambda v: v["created_at"])
            else:
                latest = max(versions, key=lambda v: v["created_at"])
            
            return {
                "dataset_id": dataset_id,
                "version": latest
            }
        
        return None
    
    def get_lineage(self, dataset_id: str) -> Optional[Dict]:
        """
        Get lineage information for a dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Lineage information or None
        """
        if dataset_id not in self.lineage:
            return None
        
        lineage = self.lineage[dataset_id]
        return lineage.dict()
    
    def search_datasets(
        self,
        industry: Optional[str] = None,
        min_realism_score: Optional[float] = None,
        min_complexity: Optional[float] = None,
        status: Optional[DatasetStatus] = None,
        version: Optional[str] = None
    ) -> List[Dict]:
        """
        Search datasets by criteria.
        
        Args:
            industry: Filter by industry
            min_realism_score: Minimum realism score
            min_complexity: Minimum complexity score
            status: Filter by status
            version: Filter by version pattern
            
        Returns:
            List of matching datasets
        """
        results = []
        
        for dataset_id, dataset_data in self.metadata["datasets"].items():
            for version_data in dataset_data.get("versions", []):
                # Apply filters
                if status and version_data.get("status") != status.value:
                    continue
                
                if version and version not in version_data["version"]:
                    continue
                
                metadata = version_data.get("metadata", {})
                company_profile = metadata.get("company_profile", {})
                
                if industry and company_profile.get("industry") != industry:
                    continue
                
                quality_scores = version_data.get("quality_scores", {})
                realism_score = quality_scores.get("realism_score", 0.0)
                if min_realism_score and realism_score < min_realism_score:
                    continue
                
                results.append({
                    "dataset_id": dataset_id,
                    "version": version_data
                })
        
        return results
    
    def list_all_datasets(self) -> List[Dict]:
        """List all registered datasets."""
        return [
            {
                "dataset_id": dataset_id,
                "versions": dataset_data.get("versions", []),
                "created_at": dataset_data.get("created_at")
            }
            for dataset_id, dataset_data in self.metadata["datasets"].items()
        ]

