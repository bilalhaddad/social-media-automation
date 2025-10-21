"""
CSV upload manager for Peace Map platform
"""

import csv
import io
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

from .base import BaseSupplyChainManager, Supplier, SupplierStatus

logger = logging.getLogger(__name__)


class CSVUploadManager(BaseSupplyChainManager):
    """Manages CSV file uploads and processing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("csv_upload_manager", config)
        self.max_file_size = config.get("max_file_size", 10 * 1024 * 1024)  # 10MB
        self.allowed_extensions = config.get("allowed_extensions", [".csv"])
        self.required_columns = config.get("required_columns", ["name", "country", "latitude", "longitude"])
        self.optional_columns = config.get("optional_columns", [
            "region", "city", "industry", "contact_email", "contact_phone", "status"
        ])
        self.column_mapping = config.get("column_mapping", {})
        self.auto_geocode = config.get("auto_geocode", True)
    
    async def initialize(self):
        """Initialize the CSV upload manager"""
        try:
            self.is_initialized = True
            logger.info("CSV upload manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize CSV upload manager: {str(e)}")
            raise
    
    async def process_suppliers(self, suppliers: List[Dict[str, Any]]) -> List[Supplier]:
        """Process supplier data from CSV"""
        processed_suppliers = []
        
        for supplier_data in suppliers:
            try:
                # Validate supplier data
                if not self._validate_supplier_data(supplier_data):
                    logger.warning(f"Invalid supplier data: {supplier_data}")
                    continue
                
                # Normalize data
                normalized_data = self._normalize_supplier_data(supplier_data)
                
                # Create supplier object
                supplier = self._create_supplier(normalized_data)
                processed_suppliers.append(supplier)
                
            except Exception as e:
                logger.error(f"Error processing supplier: {str(e)}")
                continue
        
        logger.info(f"Processed {len(processed_suppliers)} suppliers from CSV")
        return processed_suppliers
    
    async def process_csv_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process uploaded CSV file"""
        try:
            # Validate file
            validation_result = self._validate_csv_file(file_content, filename)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "suppliers": []
                }
            
            # Parse CSV content
            csv_data = self._parse_csv_content(file_content)
            if not csv_data["success"]:
                return {
                    "success": False,
                    "error": csv_data["error"],
                    "suppliers": []
                }
            
            # Process suppliers
            suppliers_data = csv_data["data"]
            processed_suppliers = await self.process_suppliers(suppliers_data)
            
            return {
                "success": True,
                "suppliers": processed_suppliers,
                "total_processed": len(processed_suppliers),
                "total_rows": len(suppliers_data),
                "processing_errors": csv_data.get("errors", [])
            }
            
        except Exception as e:
            logger.error(f"CSV processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "suppliers": []
            }
    
    def _validate_csv_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validate CSV file"""
        # Check file size
        if len(file_content) > self.max_file_size:
            return {
                "valid": False,
                "error": f"File size exceeds maximum allowed size of {self.max_file_size} bytes"
            }
        
        # Check file extension
        if not any(filename.lower().endswith(ext) for ext in self.allowed_extensions):
            return {
                "valid": False,
                "error": f"File type not allowed. Allowed extensions: {self.allowed_extensions}"
            }
        
        # Check if file is not empty
        if len(file_content) == 0:
            return {
                "valid": False,
                "error": "File is empty"
            }
        
        return {"valid": True}
    
    def _parse_csv_content(self, file_content: bytes) -> Dict[str, Any]:
        """Parse CSV content"""
        try:
            # Decode file content
            content = file_content.decode('utf-8')
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(content))
            rows = list(csv_reader)
            
            if not rows:
                return {
                    "success": False,
                    "error": "CSV file contains no data rows"
                }
            
            # Validate columns
            column_validation = self._validate_columns(rows[0].keys())
            if not column_validation["valid"]:
                return {
                    "success": False,
                    "error": column_validation["error"]
                }
            
            # Process rows
            processed_rows = []
            errors = []
            
            for i, row in enumerate(rows):
                try:
                    # Map columns if mapping is provided
                    mapped_row = self._map_columns(row)
                    
                    # Validate required fields
                    if self._validate_row_data(mapped_row):
                        processed_rows.append(mapped_row)
                    else:
                        errors.append(f"Row {i+1}: Missing required fields")
                        
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
                    continue
            
            return {
                "success": True,
                "data": processed_rows,
                "errors": errors
            }
            
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "File encoding not supported. Please use UTF-8 encoding."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"CSV parsing failed: {str(e)}"
            }
    
    def _validate_columns(self, columns: List[str]) -> Dict[str, Any]:
        """Validate CSV columns"""
        column_names = [col.lower().strip() for col in columns]
        
        # Check for required columns
        missing_columns = []
        for required_col in self.required_columns:
            if required_col.lower() not in column_names:
                missing_columns.append(required_col)
        
        if missing_columns:
            return {
                "valid": False,
                "error": f"Missing required columns: {', '.join(missing_columns)}"
            }
        
        return {"valid": True}
    
    def _map_columns(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Map CSV columns to standard field names"""
        if not self.column_mapping:
            return row
        
        mapped_row = {}
        for csv_col, standard_col in self.column_mapping.items():
            if csv_col in row:
                mapped_row[standard_col] = row[csv_col]
        
        # Add unmapped columns
        for col, value in row.items():
            if col not in self.column_mapping:
                mapped_row[col] = value
        
        return mapped_row
    
    def _validate_row_data(self, row: Dict[str, Any]) -> bool:
        """Validate individual row data"""
        # Check required fields
        for required_field in self.required_columns:
            if required_field not in row or not row[required_field]:
                return False
        
        # Validate coordinates if present
        if "latitude" in row and "longitude" in row:
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    return False
            except (ValueError, TypeError):
                return False
        
        return True
    
    def _create_supplier(self, data: Dict[str, Any]) -> Supplier:
        """Create a Supplier object from data"""
        # Generate ID if not provided
        supplier_id = data.get("id", str(uuid.uuid4()))
        
        # Parse dates
        created_at = datetime.utcnow()
        if "created_at" in data and data["created_at"]:
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                created_at = datetime.utcnow()
        
        # Create supplier
        supplier = Supplier(
            id=supplier_id,
            name=data["name"],
            country=data["country"],
            region=data.get("region", ""),
            city=data.get("city", ""),
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            industry=data.get("industry", ""),
            status=SupplierStatus(data.get("status", SupplierStatus.ACTIVE.value)),
            risk_score=data.get("risk_score", 0.0),
            risk_level=data.get("risk_level", "low"),
            contact_email=data.get("contact_email", ""),
            contact_phone=data.get("contact_phone", ""),
            created_at=created_at,
            updated_at=datetime.utcnow(),
            metadata=data.get("metadata", {})
        )
        
        return supplier
    
    def get_csv_template(self) -> str:
        """Get CSV template for supplier upload"""
        # Create template with required and optional columns
        template_columns = self.required_columns + [col for col in self.optional_columns if col not in self.required_columns]
        
        # Create sample data
        sample_data = {
            "name": "Sample Supplier",
            "country": "United States",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "region": "New York",
            "city": "New York City",
            "industry": "Manufacturing",
            "contact_email": "contact@supplier.com",
            "contact_phone": "+1-555-123-4567",
            "status": "active"
        }
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=template_columns)
        writer.writeheader()
        writer.writerow({col: sample_data.get(col, "") for col in template_columns})
        
        return output.getvalue()
    
    def get_upload_requirements(self) -> Dict[str, Any]:
        """Get upload requirements and specifications"""
        return {
            "max_file_size": self.max_file_size,
            "allowed_extensions": self.allowed_extensions,
            "required_columns": self.required_columns,
            "optional_columns": self.optional_columns,
            "column_mapping": self.column_mapping,
            "supported_encodings": ["utf-8"],
            "max_rows": 10000,  # Configurable limit
            "sample_template": self.get_csv_template()
        }
    
    def validate_supplier_batch(self, suppliers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of suppliers"""
        valid_suppliers = []
        invalid_suppliers = []
        
        for i, supplier_data in enumerate(suppliers):
            if self._validate_supplier_data(supplier_data):
                valid_suppliers.append(supplier_data)
            else:
                invalid_suppliers.append({
                    "index": i,
                    "data": supplier_data,
                    "errors": self._get_validation_errors(supplier_data)
                })
        
        return {
            "total_suppliers": len(suppliers),
            "valid_suppliers": len(valid_suppliers),
            "invalid_suppliers": len(invalid_suppliers),
            "valid_data": valid_suppliers,
            "invalid_data": invalid_suppliers
        }
    
    def _get_validation_errors(self, supplier_data: Dict[str, Any]) -> List[str]:
        """Get validation errors for supplier data"""
        errors = []
        
        # Check required fields
        for required_field in self.required_columns:
            if required_field not in supplier_data or not supplier_data[required_field]:
                errors.append(f"Missing required field: {required_field}")
        
        # Check coordinates
        if "latitude" in supplier_data and "longitude" in supplier_data:
            try:
                lat = float(supplier_data["latitude"])
                lon = float(supplier_data["longitude"])
                
                if not (-90 <= lat <= 90):
                    errors.append("Latitude must be between -90 and 90")
                if not (-180 <= lon <= 180):
                    errors.append("Longitude must be between -180 and 180")
            except (ValueError, TypeError):
                errors.append("Invalid coordinate format")
        
        return errors
