"""Tests for the optimized synthetic data generation pipeline."""

import pytest
import json
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.pipeline import synthetic_data_generation_flow
from tests.conftest import temp_output_dir, sample_company_profile, mock_config, mock_config_no_azure


class TestPipelineBasic:
    """Test basic pipeline functionality."""
    
    @patch('src.pipeline.CompanyProfiler')
    @patch('src.pipeline.ManifestBuilder')
    @patch('src.pipeline._SCHEMA_VALIDATOR')
    def test_pipeline_basic_flow(
        self,
        mock_schema_validator,
        mock_manifest_builder_class,
        mock_profiler_class,
        temp_output_dir,
        sample_company_profile,
        mock_config_no_azure
    ):
        """Test basic pipeline flow without Azure dependencies."""
        # Setup mocks
        mock_profiler = Mock()
        mock_profiler.generate_profile.return_value = sample_company_profile
        mock_profiler_class.return_value = mock_profiler
        
        mock_manifest = Mock()
        mock_manifest.manifest_id = "test_manifest_123"
        mock_manifest.total_requirements = 5
        mock_manifest.total_components = 3
        mock_manifest.complexity_score = 0.65
        mock_manifest.dict.return_value = {"manifest_id": "test_manifest_123"}
        
        mock_manifest_builder = Mock()
        mock_manifest_builder.build_manifest.return_value = mock_manifest
        mock_manifest_builder_class.return_value = mock_manifest_builder
        
        mock_schema_result = Mock()
        mock_schema_result.passed = True
        mock_schema_result.dict.return_value = {"passed": True}
        mock_schema_validator.validate_system_manifest.return_value = mock_schema_result
        
        # Run pipeline
        result = synthetic_data_generation_flow(
            industry="Technology",
            output_dir=temp_output_dir,
            config=mock_config_no_azure
        )
        
        # Assertions
        assert result is not None
        assert "sample" in result
        assert "validation" in result
        assert result["sample"]["sample_id"] is not None
        assert result["company_profile_id"] == sample_company_profile.company_id
        assert result["manifest_id"] == "test_manifest_123"
        
        # Check output files exist
        json_path = Path(result["sample"]["json_path"])
        csv_path = Path(result["sample"]["csv_path"])
        assert json_path.exists()
        assert csv_path.exists()
    
    @patch('src.pipeline.CompanyProfiler')
    @patch('src.pipeline.ManifestBuilder')
    @patch('src.pipeline._SCHEMA_VALIDATOR')
    def test_pipeline_outputs_json(
        self,
        mock_schema_validator,
        mock_manifest_builder_class,
        mock_profiler_class,
        temp_output_dir,
        sample_company_profile,
        mock_config_no_azure
    ):
        """Test that pipeline generates valid JSON output."""
        # Setup mocks
        mock_profiler = Mock()
        mock_profiler.generate_profile.return_value = sample_company_profile
        mock_profiler_class.return_value = mock_profiler
        
        mock_manifest = Mock()
        mock_manifest.manifest_id = "test_manifest_123"
        mock_manifest.total_requirements = 5
        mock_manifest.total_components = 3
        mock_manifest.complexity_score = 0.65
        mock_manifest.dict.return_value = {"manifest_id": "test_manifest_123"}
        
        mock_manifest_builder = Mock()
        mock_manifest_builder.build_manifest.return_value = mock_manifest
        mock_manifest_builder_class.return_value = mock_manifest_builder
        
        mock_schema_result = Mock()
        mock_schema_result.passed = True
        mock_schema_result.dict.return_value = {"passed": True}
        mock_schema_validator.validate_system_manifest.return_value = mock_schema_result
        
        # Run pipeline
        result = synthetic_data_generation_flow(
            industry="Technology",
            output_dir=temp_output_dir,
            config=mock_config_no_azure
        )
        
        # Check JSON file
        json_path = Path(result["sample"]["json_path"])
        assert json_path.exists()
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert "sample_id" in data
        assert "company_profile" in data
        assert "system_manifest" in data
        assert "quality_scores" in data
        assert "created_at" in data
        assert data["quality_scores"]["schema_validation_passed"] is True
    
    @patch('src.pipeline.CompanyProfiler')
    @patch('src.pipeline.ManifestBuilder')
    @patch('src.pipeline._SCHEMA_VALIDATOR')
    def test_pipeline_outputs_csv(
        self,
        mock_schema_validator,
        mock_manifest_builder_class,
        mock_profiler_class,
        temp_output_dir,
        sample_company_profile,
        mock_config_no_azure
    ):
        """Test that pipeline generates valid CSV output."""
        # Setup mocks
        mock_profiler = Mock()
        mock_profiler.generate_profile.return_value = sample_company_profile
        mock_profiler_class.return_value = mock_profiler
        
        mock_manifest = Mock()
        mock_manifest.manifest_id = "test_manifest_123"
        mock_manifest.total_requirements = 5
        mock_manifest.total_components = 3
        mock_manifest.complexity_score = 0.65
        mock_manifest.dict.return_value = {"manifest_id": "test_manifest_123"}
        
        mock_manifest_builder = Mock()
        mock_manifest_builder.build_manifest.return_value = mock_manifest
        mock_manifest_builder_class.return_value = mock_manifest_builder
        
        mock_schema_result = Mock()
        mock_schema_result.passed = True
        mock_schema_result.dict.return_value = {"passed": True}
        mock_schema_validator.validate_system_manifest.return_value = mock_schema_result
        
        # Run pipeline
        result = synthetic_data_generation_flow(
            industry="Technology",
            output_dir=temp_output_dir,
            config=mock_config_no_azure
        )
        
        # Check CSV file
        csv_path = Path(result["sample"]["csv_path"])
        assert csv_path.exists()
        
        df = pd.read_csv(csv_path)
        assert len(df) == 1
        assert "sample_id" in df.columns
        assert "company_id" in df.columns
        assert "company_name" in df.columns
        assert "industry" in df.columns
        assert "requirements_count" in df.columns
        assert "complexity_score" in df.columns
        assert "realism_score" in df.columns
        
        # Check values
        assert df.iloc[0]["company_id"] == sample_company_profile.company_id
        assert df.iloc[0]["requirements_count"] == 5
        assert df.iloc[0]["complexity_score"] == 0.65
    
    @patch('src.pipeline.CompanyProfiler')
    @patch('src.pipeline.ManifestBuilder')
    @patch('src.pipeline._SCHEMA_VALIDATOR')
    def test_pipeline_schema_validation_integration(
        self,
        mock_schema_validator,
        mock_manifest_builder_class,
        mock_profiler_class,
        temp_output_dir,
        sample_company_profile,
        mock_config_no_azure
    ):
        """Test that schema validation is called correctly."""
        # Setup mocks
        mock_profiler = Mock()
        mock_profiler.generate_profile.return_value = sample_company_profile
        mock_profiler_class.return_value = mock_profiler
        
        mock_manifest = Mock()
        mock_manifest.manifest_id = "test_manifest_123"
        mock_manifest.total_requirements = 5
        mock_manifest.total_components = 3
        mock_manifest.complexity_score = 0.65
        mock_manifest.dict.return_value = {"manifest_id": "test_manifest_123"}
        
        mock_manifest_builder = Mock()
        mock_manifest_builder.build_manifest.return_value = mock_manifest
        mock_manifest_builder_class.return_value = mock_manifest_builder
        
        mock_schema_result = Mock()
        mock_schema_result.passed = True
        mock_schema_result.dict.return_value = {"passed": True}
        mock_schema_validator.validate_system_manifest.return_value = mock_schema_result
        
        # Run pipeline
        result = synthetic_data_generation_flow(
            industry="Technology",
            output_dir=temp_output_dir,
            config=mock_config_no_azure
        )
        
        # Verify schema validator was called
        mock_schema_validator.validate_system_manifest.assert_called_once()
        call_args = mock_schema_validator.validate_system_manifest.call_args[0][0]
        assert isinstance(call_args, dict)
        assert "manifest_id" in call_args
        
        # Check validation results
        assert "schema" in result["validation"]
        assert result["validation"]["schema"]["all_passed"] is True


class TestPipelineRealismValidation:
    """Test realism validation functionality."""
    
    @patch('src.pipeline.RealismValidator')
    @patch('src.pipeline.CompanyProfiler')
    @patch('src.pipeline.ManifestBuilder')
    @patch('src.pipeline._SCHEMA_VALIDATOR')
    def test_pipeline_with_realism_validation(
        self,
        mock_schema_validator,
        mock_manifest_builder_class,
        mock_profiler_class,
        mock_realism_validator_class,
        temp_output_dir,
        sample_company_profile,
        mock_config
    ):
        """Test pipeline with realism validation enabled."""
        # Setup mocks
        mock_profiler = Mock()
        mock_profiler.generate_profile.return_value = sample_company_profile
        mock_profiler_class.return_value = mock_profiler
        
        mock_manifest = Mock()
        mock_manifest.manifest_id = "test_manifest_123"
        mock_manifest.total_requirements = 5
        mock_manifest.total_components = 3
        mock_manifest.complexity_score = 0.65
        mock_manifest.dict.return_value = {"manifest_id": "test_manifest_123"}
        
        mock_manifest_builder = Mock()
        mock_manifest_builder.build_manifest.return_value = mock_manifest
        mock_manifest_builder_class.return_value = mock_manifest_builder
        
        mock_schema_result = Mock()
        mock_schema_result.passed = True
        mock_schema_result.dict.return_value = {"passed": True}
        mock_schema_validator.validate_system_manifest.return_value = mock_schema_result
        
        mock_realism_score = Mock()
        mock_realism_score.overall_score = 0.85
        mock_realism_score.passed = True
        mock_realism_score.dict.return_value = {"overall_score": 0.85, "passed": True}
        
        mock_realism_validator = Mock()
        mock_realism_validator.validate_company_profile.return_value = mock_realism_score
        mock_realism_validator_class.return_value = mock_realism_validator
        
        # Run pipeline with realism validation enabled
        config = mock_config.copy()
        config["enable_realism_validation"] = True
        
        result = synthetic_data_generation_flow(
            industry="Technology",
            output_dir=temp_output_dir,
            config=config
        )
        
        # Verify realism validator was called
        mock_realism_validator.validate_company_profile.assert_called_once()
        
        # Check validation results
        assert "realism" in result["validation"]
        assert result["validation"]["realism"]["all_passed"] is True
        
        # Check JSON output has realism score
        json_path = Path(result["sample"]["json_path"])
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert data["quality_scores"]["realism_score"] == 0.85
    
    @patch('src.pipeline.CompanyProfiler')
    @patch('src.pipeline.ManifestBuilder')
    @patch('src.pipeline._SCHEMA_VALIDATOR')
    def test_pipeline_without_realism_validation(
        self,
        mock_schema_validator,
        mock_manifest_builder_class,
        mock_profiler_class,
        temp_output_dir,
        sample_company_profile,
        mock_config_no_azure
    ):
        """Test pipeline without realism validation (default behavior)."""
        # Setup mocks
        mock_profiler = Mock()
        mock_profiler.generate_profile.return_value = sample_company_profile
        mock_profiler_class.return_value = mock_profiler
        
        mock_manifest = Mock()
        mock_manifest.manifest_id = "test_manifest_123"
        mock_manifest.total_requirements = 5
        mock_manifest.total_components = 3
        mock_manifest.complexity_score = 0.65
        mock_manifest.dict.return_value = {"manifest_id": "test_manifest_123"}
        
        mock_manifest_builder = Mock()
        mock_manifest_builder.build_manifest.return_value = mock_manifest
        mock_manifest_builder_class.return_value = mock_manifest_builder
        
        mock_schema_result = Mock()
        mock_schema_result.passed = True
        mock_schema_result.dict.return_value = {"passed": True}
        mock_schema_validator.validate_system_manifest.return_value = mock_schema_result
        
        # Run pipeline without realism validation
        result = synthetic_data_generation_flow(
            industry="Technology",
            output_dir=temp_output_dir,
            config=mock_config_no_azure
        )
        
        # Check validation results
        assert "realism" not in result["validation"]
        
        # Check JSON output has default realism score
        json_path = Path(result["sample"]["json_path"])
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert data["quality_scores"]["realism_score"] == 0.8  # Default value


class TestPipelineScenarios:
    """Test scenario generation functionality."""
    
    @patch('src.pipeline.ScenarioGenerator')
    @patch('src.pipeline.CompanyProfiler')
    @patch('src.pipeline.ManifestBuilder')
    @patch('src.pipeline._SCHEMA_VALIDATOR')
    def test_pipeline_with_transcript(
        self,
        mock_schema_validator,
        mock_manifest_builder_class,
        mock_profiler_class,
        mock_scenario_generator_class,
        temp_output_dir,
        sample_company_profile,
        mock_config_no_azure
    ):
        """Test pipeline with transcript input."""
        # Create temporary transcript file
        transcript_file = temp_output_dir / "test_transcript.txt"
        transcript_file.write_text("Test transcript content")
        
        # Setup mocks
        mock_profiler = Mock()
        mock_profiler.generate_profile.return_value = sample_company_profile
        mock_profiler_class.return_value = mock_profiler
        
        mock_scenario = Mock()
        mock_scenario.scenario_id = "scenario_1"
        
        mock_scenario_generator = Mock()
        mock_scenario_generator.extract_scenarios.return_value = [mock_scenario]
        mock_scenario_generator_class.return_value = mock_scenario_generator
        
        mock_manifest = Mock()
        mock_manifest.manifest_id = "test_manifest_123"
        mock_manifest.total_requirements = 5
        mock_manifest.total_components = 3
        mock_manifest.complexity_score = 0.65
        mock_manifest.dict.return_value = {"manifest_id": "test_manifest_123"}
        
        mock_manifest_builder = Mock()
        mock_manifest_builder.build_manifest.return_value = mock_manifest
        mock_manifest_builder_class.return_value = mock_manifest_builder
        
        mock_schema_result = Mock()
        mock_schema_result.passed = True
        mock_schema_result.dict.return_value = {"passed": True}
        mock_schema_validator.validate_system_manifest.return_value = mock_schema_result
        
        # Run pipeline with transcript
        result = synthetic_data_generation_flow(
            transcript_path=transcript_file,
            industry="Technology",
            output_dir=temp_output_dir,
            config=mock_config_no_azure
        )
        
        # Verify scenario generator was called
        mock_scenario_generator.extract_scenarios.assert_called_once()
        
        # Verify manifest builder was called with scenarios
        mock_manifest_builder.build_manifest.assert_called_once()
        call_args = mock_manifest_builder.build_manifest.call_args
        assert len(call_args[0]) >= 2  # company_profile and scenarios


class TestPipelineOptimizations:
    """Test pipeline optimizations (shared validator, dict reuse, etc.)."""
    
    @patch('src.pipeline.CompanyProfiler')
    @patch('src.pipeline.ManifestBuilder')
    @patch('src.pipeline._SCHEMA_VALIDATOR')
    def test_shared_schema_validator_reuse(
        self,
        mock_schema_validator,
        mock_manifest_builder_class,
        mock_profiler_class,
        temp_output_dir,
        sample_company_profile,
        mock_config_no_azure
    ):
        """Test that shared schema validator instance is reused."""
        # Setup mocks
        mock_profiler = Mock()
        mock_profiler.generate_profile.return_value = sample_company_profile
        mock_profiler_class.return_value = mock_profiler
        
        mock_manifest = Mock()
        mock_manifest.manifest_id = "test_manifest_123"
        mock_manifest.total_requirements = 5
        mock_manifest.total_components = 3
        mock_manifest.complexity_score = 0.65
        mock_manifest.dict.return_value = {"manifest_id": "test_manifest_123"}
        
        mock_manifest_builder = Mock()
        mock_manifest_builder.build_manifest.return_value = mock_manifest
        mock_manifest_builder_class.return_value = mock_manifest_builder
        
        mock_schema_result = Mock()
        mock_schema_result.passed = True
        mock_schema_result.dict.return_value = {"passed": True}
        mock_schema_validator.validate_system_manifest.return_value = mock_schema_result
        
        # Run pipeline multiple times
        for _ in range(3):
            result = synthetic_data_generation_flow(
                industry="Technology",
                output_dir=temp_output_dir,
                config=mock_config_no_azure
            )
            assert result is not None
        
        # Verify validator was called multiple times (reusing same instance)
        assert mock_schema_validator.validate_system_manifest.call_count == 3
    
    @patch('src.pipeline.CompanyProfiler')
    @patch('src.pipeline.ManifestBuilder')
    @patch('src.pipeline._SCHEMA_VALIDATOR')
    def test_timestamp_consistency(
        self,
        mock_schema_validator,
        mock_manifest_builder_class,
        mock_profiler_class,
        temp_output_dir,
        sample_company_profile,
        mock_config_no_azure
    ):
        """Test that timestamps are consistent across JSON and CSV outputs."""
        # Setup mocks
        mock_profiler = Mock()
        mock_profiler.generate_profile.return_value = sample_company_profile
        mock_profiler_class.return_value = mock_profiler
        
        mock_manifest = Mock()
        mock_manifest.manifest_id = "test_manifest_123"
        mock_manifest.total_requirements = 5
        mock_manifest.total_components = 3
        mock_manifest.complexity_score = 0.65
        mock_manifest.dict.return_value = {"manifest_id": "test_manifest_123"}
        
        mock_manifest_builder = Mock()
        mock_manifest_builder.build_manifest.return_value = mock_manifest
        mock_manifest_builder_class.return_value = mock_manifest_builder
        
        mock_schema_result = Mock()
        mock_schema_result.passed = True
        mock_schema_result.dict.return_value = {"passed": True}
        mock_schema_validator.validate_system_manifest.return_value = mock_schema_result
        
        # Run pipeline
        result = synthetic_data_generation_flow(
            industry="Technology",
            output_dir=temp_output_dir,
            config=mock_config_no_azure
        )
        
        # Check timestamp consistency
        json_path = Path(result["sample"]["json_path"])
        csv_path = Path(result["sample"]["csv_path"])
        
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        df = pd.read_csv(csv_path)
        
        # Timestamps should match
        assert json_data["created_at"] == df.iloc[0]["created_at"]
        assert json_data["metadata"]["validation_timestamp"] == json_data["created_at"]

