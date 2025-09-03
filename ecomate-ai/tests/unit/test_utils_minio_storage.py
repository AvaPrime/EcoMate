"""Unit tests for MinIO storage utility functions."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
import io
from minio.error import S3Error

from src.utils.minio_storage import (
    MinIOClient,
    StorageConfig,
    StorageResult,
    FileMetadata,
    upload_file,
    download_file,
    generate_presigned_url,
    copy_file,
    move_file,
    sync_directory,
    compress_and_upload
)
from src.utils.exceptions import StorageError as StorageException, ValidationError


class TestStorageConfig:
    """Test cases for StorageConfig class."""
    
    def test_storage_config_initialization(self):
        """Test StorageConfig initialization."""
        config = StorageConfig(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False,
            region="us-east-1"
        )
        
        assert config.endpoint == "localhost:9000"
        assert config.access_key == "minioadmin"
        assert config.secret_key == "minioadmin"
        assert config.secure is False
        assert config.region == "us-east-1"
    
    def test_storage_config_default_values(self):
        """Test StorageConfig with default values."""
        config = StorageConfig(
            endpoint="minio.example.com",
            access_key="access",
            secret_key="secret"
        )
        
        assert config.secure is True  # Default
        assert config.region == "us-east-1"  # Default
    
    def test_storage_config_validation(self):
        """Test StorageConfig validation."""
        # Test missing required fields
        with pytest.raises(ValidationError):
            StorageConfig(endpoint="", access_key="key", secret_key="secret")
        
        with pytest.raises(ValidationError):
            StorageConfig(endpoint="localhost:9000", access_key="", secret_key="secret")
        
        with pytest.raises(ValidationError):
            StorageConfig(endpoint="localhost:9000", access_key="key", secret_key="")


class TestMinIOClient:
    """Test cases for MinIOClient class."""
    
    @pytest.fixture
    def storage_config(self):
        """Create a storage configuration for testing."""
        return StorageConfig(
            endpoint="localhost:9000",
            access_key="testkey",
            secret_key="testsecret",
            secure=False
        )
    
    @pytest.fixture
    def minio_client(self, storage_config):
        """Create a MinIOClient instance for testing."""
        with patch('src.utils.minio_storage.Minio') as mock_minio:
            client = MinIOClient(storage_config)
            client._client = mock_minio.return_value
            return client
    
    def test_minio_client_initialization(self, storage_config):
        """Test MinIOClient initialization."""
        with patch('src.utils.minio_storage.Minio') as mock_minio:
            client = MinIOClient(storage_config)
            
            mock_minio.assert_called_once_with(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                secure=False,
                region="us-east-1"
            )
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, minio_client):
        """Test successful file upload."""
        mock_client = minio_client._client
        mock_client.put_object = Mock()
        
        file_content = b"Test file content"
        file_stream = io.BytesIO(file_content)
        
        result = await minio_client.upload_file(
            bucket_name="test-bucket",
            object_name="test-file.txt",
            file_data=file_stream,
            content_type="text/plain"
        )
        
        assert isinstance(result, StorageResult)
        assert result.success is True
        assert result.object_name == "test-file.txt"
        assert result.bucket_name == "test-bucket"
        
        mock_client.put_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_with_metadata(self, minio_client):
        """Test file upload with custom metadata."""
        mock_client = minio_client._client
        mock_client.put_object = Mock()
        
        file_content = b"Test content with metadata"
        file_stream = io.BytesIO(file_content)
        metadata = {"author": "test-user", "category": "documents"}
        
        result = await minio_client.upload_file(
            bucket_name="test-bucket",
            object_name="document.pdf",
            file_data=file_stream,
            metadata=metadata
        )
        
        assert result.success is True
        
        # Verify metadata was passed to put_object
        call_args = mock_client.put_object.call_args
        assert "metadata" in call_args.kwargs
    
    @pytest.mark.asyncio
    async def test_upload_file_error(self, minio_client):
        """Test file upload with error."""
        mock_client = minio_client._client
        mock_client.put_object = Mock(side_effect=S3Error(
            "NoSuchBucket", "The specified bucket does not exist", "test-bucket", "", "", "", ""
        ))
        
        file_content = b"Test content"
        file_stream = io.BytesIO(file_content)
        
        result = await minio_client.upload_file(
            bucket_name="nonexistent-bucket",
            object_name="test-file.txt",
            file_data=file_stream
        )
        
        assert result.success is False
        assert "NoSuchBucket" in result.error_message
    
    @pytest.mark.asyncio
    async def test_download_file_success(self, minio_client):
        """Test successful file download."""
        mock_client = minio_client._client
        
        # Mock the response object
        mock_response = Mock()
        mock_response.read = Mock(return_value=b"Downloaded file content")
        mock_response.close = Mock()
        mock_client.get_object = Mock(return_value=mock_response)
        
        result = await minio_client.download_file(
            bucket_name="test-bucket",
            object_name="test-file.txt"
        )
        
        assert isinstance(result, StorageResult)
        assert result.success is True
        assert result.data == b"Downloaded file content"
        
        mock_client.get_object.assert_called_once_with("test-bucket", "test-file.txt")
        mock_response.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_file_not_found(self, minio_client):
        """Test download of non-existent file."""
        mock_client = minio_client._client
        mock_client.get_object = Mock(side_effect=S3Error(
            "NoSuchKey", "The specified key does not exist", "test-bucket", "nonexistent.txt", "", "", ""
        ))
        
        result = await minio_client.download_file(
            bucket_name="test-bucket",
            object_name="nonexistent.txt"
        )
        
        assert result.success is False
        assert "NoSuchKey" in result.error_message
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self, minio_client):
        """Test successful file deletion."""
        mock_client = minio_client._client
        mock_client.remove_object = Mock()
        
        result = await minio_client.delete_file(
            bucket_name="test-bucket",
            object_name="file-to-delete.txt"
        )
        
        assert result.success is True
        mock_client.remove_object.assert_called_once_with("test-bucket", "file-to-delete.txt")
    
    @pytest.mark.asyncio
    async def test_list_files_success(self, minio_client):
        """Test successful file listing."""
        mock_client = minio_client._client
        
        # Mock MinIO objects
        mock_objects = [
            Mock(object_name="file1.txt", size=100, last_modified=datetime.now(timezone.utc)),
            Mock(object_name="file2.pdf", size=200, last_modified=datetime.now(timezone.utc)),
            Mock(object_name="folder/file3.jpg", size=300, last_modified=datetime.now(timezone.utc))
        ]
        
        mock_client.list_objects = Mock(return_value=mock_objects)
        
        result = await minio_client.list_files(
            bucket_name="test-bucket",
            prefix="",
            recursive=True
        )
        
        assert result.success is True
        assert len(result.files) == 3
        assert result.files[0].name == "file1.txt"
        assert result.files[0].size == 100
    
    @pytest.mark.asyncio
    async def test_list_files_with_prefix(self, minio_client):
        """Test file listing with prefix filter."""
        mock_client = minio_client._client
        
        mock_objects = [
            Mock(object_name="documents/doc1.pdf", size=100, last_modified=datetime.now(timezone.utc)),
            Mock(object_name="documents/doc2.pdf", size=200, last_modified=datetime.now(timezone.utc))
        ]
        
        mock_client.list_objects = Mock(return_value=mock_objects)
        
        result = await minio_client.list_files(
            bucket_name="test-bucket",
            prefix="documents/",
            recursive=True
        )
        
        assert result.success is True
        assert len(result.files) == 2
        assert all(f.name.startswith("documents/") for f in result.files)
        
        mock_client.list_objects.assert_called_once_with(
            "test-bucket", prefix="documents/", recursive=True
        )
    
    @pytest.mark.asyncio
    async def test_create_bucket_success(self, minio_client):
        """Test successful bucket creation."""
        mock_client = minio_client._client
        mock_client.bucket_exists = Mock(return_value=False)
        mock_client.make_bucket = Mock()
        
        result = await minio_client.create_bucket("new-bucket")
        
        assert result.success is True
        mock_client.bucket_exists.assert_called_once_with("new-bucket")
        mock_client.make_bucket.assert_called_once_with("new-bucket")
    
    @pytest.mark.asyncio
    async def test_create_bucket_already_exists(self, minio_client):
        """Test bucket creation when bucket already exists."""
        mock_client = minio_client._client
        mock_client.bucket_exists = Mock(return_value=True)
        
        result = await minio_client.create_bucket("existing-bucket")
        
        assert result.success is True  # Should succeed if bucket exists
        mock_client.bucket_exists.assert_called_once_with("existing-bucket")
        # make_bucket should not be called
        mock_client.make_bucket.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_bucket_success(self, minio_client):
        """Test successful bucket deletion."""
        mock_client = minio_client._client
        mock_client.bucket_exists = Mock(return_value=True)
        mock_client.list_objects = Mock(return_value=[])  # Empty bucket
        mock_client.remove_bucket = Mock()
        
        result = await minio_client.delete_bucket("bucket-to-delete")
        
        assert result.success is True
        mock_client.remove_bucket.assert_called_once_with("bucket-to-delete")
    
    @pytest.mark.asyncio
    async def test_delete_bucket_not_empty(self, minio_client):
        """Test bucket deletion when bucket is not empty."""
        mock_client = minio_client._client
        mock_client.bucket_exists = Mock(return_value=True)
        
        # Mock non-empty bucket
        mock_objects = [Mock(object_name="file1.txt")]
        mock_client.list_objects = Mock(return_value=mock_objects)
        
        result = await minio_client.delete_bucket("non-empty-bucket", force=False)
        
        assert result.success is False
        assert "not empty" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_delete_bucket_force(self, minio_client):
        """Test forced bucket deletion (removes all objects first)."""
        mock_client = minio_client._client
        mock_client.bucket_exists = Mock(return_value=True)
        
        # Mock objects in bucket
        mock_objects = [
            Mock(object_name="file1.txt"),
            Mock(object_name="file2.txt")
        ]
        mock_client.list_objects = Mock(return_value=mock_objects)
        mock_client.remove_object = Mock()
        mock_client.remove_bucket = Mock()
        
        result = await minio_client.delete_bucket("bucket-to-force-delete", force=True)
        
        assert result.success is True
        # Should remove all objects first
        assert mock_client.remove_object.call_count == 2
        mock_client.remove_bucket.assert_called_once()


class TestFileMetadata:
    """Test cases for FileMetadata class."""
    
    def test_file_metadata_creation(self):
        """Test FileMetadata creation."""
        now = datetime.now(timezone.utc)
        metadata = FileMetadata(
            name="test-file.txt",
            size=1024,
            last_modified=now,
            content_type="text/plain",
            etag="abc123",
            custom_metadata={"author": "test-user"}
        )
        
        assert metadata.name == "test-file.txt"
        assert metadata.size == 1024
        assert metadata.last_modified == now
        assert metadata.content_type == "text/plain"
        assert metadata.etag == "abc123"
        assert metadata.custom_metadata["author"] == "test-user"
    
    def test_file_metadata_size_formatting(self):
        """Test file size formatting."""
        metadata = FileMetadata(name="large-file.zip", size=1073741824)  # 1GB
        
        formatted_size = metadata.format_size()
        
        assert "1.0 GB" in formatted_size or "1024.0 MB" in formatted_size
    
    def test_file_metadata_age_calculation(self):
        """Test file age calculation."""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        metadata = FileMetadata(name="old-file.txt", size=100, last_modified=one_hour_ago)
        
        age = metadata.get_age()
        
        assert age.total_seconds() >= 3600  # At least 1 hour


class TestStorageResult:
    """Test cases for StorageResult class."""
    
    def test_storage_result_success(self):
        """Test successful StorageResult creation."""
        result = StorageResult(
            success=True,
            bucket_name="test-bucket",
            object_name="test-file.txt",
            operation="upload",
            size=1024
        )
        
        assert result.success is True
        assert result.bucket_name == "test-bucket"
        assert result.object_name == "test-file.txt"
        assert result.operation == "upload"
        assert result.size == 1024
        assert result.error_message is None
    
    def test_storage_result_error(self):
        """Test StorageResult with error."""
        result = StorageResult(
            success=False,
            operation="download",
            error_message="File not found",
            error_code="NoSuchKey"
        )
        
        assert result.success is False
        assert result.error_message == "File not found"
        assert result.error_code == "NoSuchKey"
        assert result.size is None


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    @pytest.mark.asyncio
    async def test_upload_file_function(self):
        """Test standalone upload_file function."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_result = StorageResult(
                success=True,
                bucket_name="test-bucket",
                object_name="test-file.txt",
                operation="upload"
            )
            mock_client.upload_file = AsyncMock(return_value=mock_result)
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            file_data = io.BytesIO(b"Test content")
            result = await upload_file(config, "test-bucket", "test-file.txt", file_data)
            
            assert result.success is True
            mock_client.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_file_function(self):
        """Test standalone download_file function."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_result = StorageResult(
                success=True,
                bucket_name="test-bucket",
                object_name="test-file.txt",
                operation="download",
                data=b"Downloaded content"
            )
            mock_client.download_file = AsyncMock(return_value=mock_result)
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            result = await download_file(config, "test-bucket", "test-file.txt")
            
            assert result.success is True
            assert result.data == b"Downloaded content"
    
    @pytest.mark.asyncio
    async def test_generate_presigned_url(self):
        """Test presigned URL generation."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_client._client = Mock()
            mock_client._client.presigned_get_object = Mock(
                return_value="https://localhost:9000/test-bucket/test-file.txt?X-Amz-Signature=..."
            )
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            url = await generate_presigned_url(
                config, "test-bucket", "test-file.txt", expires=timedelta(hours=1)
            )
            
            assert url.startswith("https://localhost:9000")
            assert "test-bucket" in url
            assert "test-file.txt" in url
    
    @pytest.mark.asyncio
    async def test_copy_file(self):
        """Test file copying between buckets/objects."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_client._client = Mock()
            mock_client._client.copy_object = Mock()
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            result = await copy_file(
                config,
                source_bucket="source-bucket",
                source_object="source-file.txt",
                dest_bucket="dest-bucket",
                dest_object="dest-file.txt"
            )
            
            assert result.success is True
            mock_client._client.copy_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_move_file(self):
        """Test file moving (copy + delete)."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_client._client = Mock()
            mock_client._client.copy_object = Mock()
            mock_client._client.remove_object = Mock()
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            result = await move_file(
                config,
                source_bucket="source-bucket",
                source_object="file-to-move.txt",
                dest_bucket="dest-bucket",
                dest_object="moved-file.txt"
            )
            
            assert result.success is True
            # Should copy then delete
            mock_client._client.copy_object.assert_called_once()
            mock_client._client.remove_object.assert_called_once()


class TestAdvancedOperations:
    """Test cases for advanced storage operations."""
    
    @pytest.mark.asyncio
    async def test_compress_and_upload(self):
        """Test compressing files before upload."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_result = StorageResult(
                success=True,
                bucket_name="test-bucket",
                object_name="compressed-file.zip",
                operation="upload"
            )
            mock_client.upload_file = AsyncMock(return_value=mock_result)
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            files_to_compress = {
                "file1.txt": b"Content of file 1",
                "file2.txt": b"Content of file 2"
            }
            
            result = await compress_and_upload(
                config, "test-bucket", "archive.zip", files_to_compress
            )
            
            assert result.success is True
            mock_client.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_and_extract(self):
        """Test downloading and extracting compressed files."""
        # This would test downloading a zip file and extracting its contents
        # Implementation depends on specific compression/extraction requirements
        pass
    
    @pytest.mark.asyncio
    async def test_sync_directory(self):
        """Test directory synchronization."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            
            # Mock existing files in bucket
            existing_files = [
                Mock(object_name="dir/file1.txt", size=100),
                Mock(object_name="dir/file2.txt", size=200)
            ]
            mock_client.list_files = AsyncMock(return_value=StorageResult(
                success=True, files=existing_files
            ))
            
            # Mock upload operations
            mock_client.upload_file = AsyncMock(return_value=StorageResult(success=True))
            mock_client.delete_file = AsyncMock(return_value=StorageResult(success=True))
            
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            local_files = {
                "file1.txt": b"Updated content 1",
                "file3.txt": b"New file content"
            }
            
            result = await sync_directory(
                config, "test-bucket", "dir/", local_files
            )
            
            assert result.success is True
            # Should upload new/changed files and delete removed files
            assert mock_client.upload_file.call_count >= 1
            assert mock_client.delete_file.call_count >= 1


class TestErrorHandling:
    """Test cases for error handling in storage operations."""
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test handling of connection errors."""
        config = StorageConfig(
            endpoint="nonexistent-server:9000",
            access_key="key",
            secret_key="secret"
        )
        
        with patch('src.utils.minio_storage.Minio') as mock_minio:
            mock_minio.side_effect = Exception("Connection refused")
            
            with pytest.raises(StorageException):
                MinIOClient(config)
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self):
        """Test handling of authentication errors."""
        config = StorageConfig(
            endpoint="localhost:9000",
            access_key="invalid-key",
            secret_key="invalid-secret"
        )
        
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_client.upload_file = AsyncMock(side_effect=S3Error(
                "AccessDenied", "Access Denied", "test-bucket", "test-file.txt", "", "", ""
            ))
            mock_client_class.return_value = mock_client
            
            file_data = io.BytesIO(b"Test content")
            result = await upload_file(config, "test-bucket", "test-file.txt", file_data)
            
            assert result.success is False
            assert "AccessDenied" in result.error_message
    
    @pytest.mark.asyncio
    async def test_quota_exceeded_error(self):
        """Test handling of storage quota exceeded errors."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_client.upload_file = AsyncMock(side_effect=S3Error(
                "QuotaExceeded", "Storage quota exceeded", "test-bucket", "large-file.zip", "", "", ""
            ))
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            large_file_data = io.BytesIO(b"x" * (100 * 1024 * 1024))  # 100MB
            result = await upload_file(config, "test-bucket", "large-file.zip", large_file_data)
            
            assert result.success is False
            assert "QuotaExceeded" in result.error_message


class TestBucketOperations:
    """Test cases for bucket-level operations."""
    
    @pytest.mark.asyncio
    async def test_list_buckets(self):
        """Test listing all buckets."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_buckets = [
                Mock(name="bucket1", creation_date=datetime.now(timezone.utc)),
                Mock(name="bucket2", creation_date=datetime.now(timezone.utc))
            ]
            mock_client._client = Mock()
            mock_client._client.list_buckets = Mock(return_value=mock_buckets)
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            client = MinIOClient(config)
            buckets = await client.list_buckets()
            
            assert len(buckets) == 2
            assert buckets[0].name == "bucket1"
            assert buckets[1].name == "bucket2"
    
    @pytest.mark.asyncio
    async def test_get_bucket_info(self):
        """Test getting bucket information."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            
            # Mock bucket exists
            mock_client._client = Mock()
            mock_client._client.bucket_exists = Mock(return_value=True)
            
            # Mock bucket objects for size calculation
            mock_objects = [
                Mock(object_name="file1.txt", size=100),
                Mock(object_name="file2.txt", size=200)
            ]
            mock_client._client.list_objects = Mock(return_value=mock_objects)
            
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            client = MinIOClient(config)
            bucket_info = await client.get_bucket_info("test-bucket")
            
            assert bucket_info.name == "test-bucket"
            assert bucket_info.exists is True
            assert bucket_info.total_size == 300
            assert bucket_info.object_count == 2


@pytest.mark.parametrize("file_size,expected_unit", [
    (1024, "KB"),
    (1024 * 1024, "MB"),
    (1024 * 1024 * 1024, "GB"),
    (1024 * 1024 * 1024 * 1024, "TB"),
])
def test_file_size_formatting(file_size, expected_unit):
    """Parametrized test for file size formatting."""
    metadata = FileMetadata(name="test-file", size=file_size)
    formatted = metadata.format_size()
    
    assert expected_unit in formatted


@pytest.mark.parametrize("bucket_name,is_valid", [
    ("valid-bucket-name", True),
    ("valid.bucket.name", True),
    ("123-valid-bucket", True),
    ("Invalid_Bucket_Name", False),  # Underscores not allowed
    ("INVALID-BUCKET", False),  # Uppercase not allowed
    ("invalid..bucket", False),  # Consecutive dots not allowed
    ("invalid-", False),  # Cannot end with hyphen
    ("-invalid", False),  # Cannot start with hyphen
    ("a" * 64, False),  # Too long (max 63 characters)
    ("ab", False),  # Too short (min 3 characters)
])
def test_bucket_name_validation(bucket_name, is_valid):
    """Parametrized test for bucket name validation."""
    from src.utils.minio_storage import validate_bucket_name
    
    assert validate_bucket_name(bucket_name) == is_valid


class TestPerformanceAndLimits:
    """Test cases for performance and resource limits."""
    
    @pytest.mark.asyncio
    async def test_large_file_upload_performance(self):
        """Test performance with large file uploads."""
        # This would test upload performance with large files
        # Implementation depends on specific performance requirements
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent storage operations."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            mock_client.upload_file = AsyncMock(return_value=StorageResult(success=True))
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            # Create multiple concurrent upload tasks
            tasks = []
            for i in range(10):
                file_data = io.BytesIO(f"Content {i}".encode())
                task = upload_file(config, "test-bucket", f"file{i}.txt", file_data)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            assert all(result.success for result in results)
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_large_files(self):
        """Test memory usage patterns with large files."""
        # This would test memory usage during large file operations
        # Implementation depends on specific memory monitoring requirements
        pass


class TestRetryMechanism:
    """Test cases for retry mechanisms in storage operations."""
    
    @pytest.mark.asyncio
    async def test_upload_with_retries(self):
        """Test upload operation with retry on transient failures."""
        with patch('src.utils.minio_storage.MinIOClient') as mock_client_class:
            mock_client = Mock()
            
            # First two calls fail, third succeeds
            side_effects = [
                S3Error("ServiceUnavailable", "Service temporarily unavailable", "", "", "", "", ""),
                S3Error("SlowDown", "Please reduce your request rate", "", "", "", "", ""),
                StorageResult(success=True, operation="upload")
            ]
            
            mock_client.upload_file = AsyncMock(side_effect=side_effects)
            mock_client_class.return_value = mock_client
            
            config = StorageConfig(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            
            file_data = io.BytesIO(b"Test content")
            result = await upload_file(
                config, "test-bucket", "test-file.txt", file_data, max_retries=3
            )
            
            assert result.success is True
            assert mock_client.upload_file.call_count == 3
    
    @pytest.mark.asyncio
    async def test_download_with_retries(self):
        """Test download operation with retry on transient failures."""
        # Similar to upload test but for download operations
        pass