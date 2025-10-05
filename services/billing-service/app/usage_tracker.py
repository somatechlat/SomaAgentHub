"""
Usage tracking for billing integration.

Tracks compute resources, API calls, and storage for accurate billing.
Integrates with Stripe for payment processing.
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from decimal import Decimal
from clickhouse_driver import Client
import stripe

logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@dataclass
class UsageRecord:
    """Usage record for billing."""
    
    user_id: str
    resource_type: str  # compute, storage, api_calls, capsule_execution
    quantity: Decimal
    unit: str  # hours, gb_hours, requests, executions
    unit_price: Decimal
    total_cost: Decimal
    metadata: Optional[Dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class UsageTracker:
    """Tracks resource usage for billing."""
    
    def __init__(
        self,
        clickhouse_host: str = "clickhouse",
        clickhouse_port: int = 9000,
        database: str = "somaagent"
    ):
        """
        Initialize usage tracker.
        
        Args:
            clickhouse_host: ClickHouse server hostname
            clickhouse_port: ClickHouse native protocol port
            database: Database name
        """
        self.client = Client(
            host=clickhouse_host,
            port=clickhouse_port,
            database=database
        )
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """Ensure usage_records table exists."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS usage_records (
            timestamp DateTime64(3),
            user_id String,
            resource_type String,
            quantity Decimal(18, 6),
            unit String,
            unit_price Decimal(10, 6),
            total_cost Decimal(10, 6),
            metadata String,
            billing_period Date
        ) ENGINE = MergeTree()
        ORDER BY (user_id, billing_period, timestamp)
        PARTITION BY toYYYYMM(billing_period)
        TTL timestamp + INTERVAL 3 YEAR
        """
        
        try:
            self.client.execute(create_table_sql)
            logger.info("Usage records table ready")
        except Exception as e:
            logger.error(f"Failed to create usage table: {e}")
    
    def track_compute(
        self,
        user_id: str,
        cpu_hours: Decimal,
        memory_gb_hours: Decimal,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Track compute resource usage.
        
        Args:
            user_id: User identifier
            cpu_hours: CPU hours consumed
            memory_gb_hours: Memory GB-hours consumed
            metadata: Additional metadata
        """
        # Pricing (example)
        CPU_PRICE_PER_HOUR = Decimal("0.05")  # $0.05 per CPU hour
        MEMORY_PRICE_PER_GB_HOUR = Decimal("0.01")  # $0.01 per GB-hour
        
        # Track CPU
        cpu_record = UsageRecord(
            user_id=user_id,
            resource_type="compute_cpu",
            quantity=cpu_hours,
            unit="cpu_hours",
            unit_price=CPU_PRICE_PER_HOUR,
            total_cost=cpu_hours * CPU_PRICE_PER_HOUR,
            metadata=metadata
        )
        self._write_record(cpu_record)
        
        # Track memory
        memory_record = UsageRecord(
            user_id=user_id,
            resource_type="compute_memory",
            quantity=memory_gb_hours,
            unit="gb_hours",
            unit_price=MEMORY_PRICE_PER_GB_HOUR,
            total_cost=memory_gb_hours * MEMORY_PRICE_PER_GB_HOUR,
            metadata=metadata
        )
        self._write_record(memory_record)
    
    def track_capsule_execution(
        self,
        user_id: str,
        capsule_id: str,
        execution_time_ms: int,
        memory_used_mb: int,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Track capsule execution for billing.
        
        Args:
            user_id: User identifier
            capsule_id: Capsule identifier
            execution_time_ms: Execution time in milliseconds
            memory_used_mb: Memory used in MB
            metadata: Additional metadata
        """
        # Convert to billable units
        cpu_hours = Decimal(execution_time_ms) / Decimal(3600000)  # ms to hours
        memory_gb_hours = (Decimal(memory_used_mb) / 1024) * cpu_hours
        
        execution_metadata = metadata or {}
        execution_metadata['capsule_id'] = capsule_id
        
        self.track_compute(user_id, cpu_hours, memory_gb_hours, execution_metadata)
    
    def track_api_calls(
        self,
        user_id: str,
        endpoint: str,
        count: int = 1,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Track API calls for billing.
        
        Args:
            user_id: User identifier
            endpoint: API endpoint called
            count: Number of calls
            metadata: Additional metadata
        """
        API_PRICE_PER_1000 = Decimal("0.10")  # $0.10 per 1000 calls
        
        record = UsageRecord(
            user_id=user_id,
            resource_type="api_calls",
            quantity=Decimal(count),
            unit="requests",
            unit_price=API_PRICE_PER_1000 / 1000,
            total_cost=(Decimal(count) * API_PRICE_PER_1000) / 1000,
            metadata={**(metadata or {}), 'endpoint': endpoint}
        )
        self._write_record(record)
    
    def track_storage(
        self,
        user_id: str,
        storage_gb: Decimal,
        duration_hours: Decimal = Decimal(1),
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Track storage usage for billing.
        
        Args:
            user_id: User identifier
            storage_gb: Storage in GB
            duration_hours: Duration in hours
            metadata: Additional metadata
        """
        STORAGE_PRICE_PER_GB_MONTH = Decimal("0.023")  # $0.023 per GB per month
        HOURS_PER_MONTH = Decimal(730)  # Average hours in a month
        
        gb_hours = storage_gb * duration_hours
        
        record = UsageRecord(
            user_id=user_id,
            resource_type="storage",
            quantity=gb_hours,
            unit="gb_hours",
            unit_price=STORAGE_PRICE_PER_GB_MONTH / HOURS_PER_MONTH,
            total_cost=(gb_hours * STORAGE_PRICE_PER_GB_MONTH) / HOURS_PER_MONTH,
            metadata=metadata
        )
        self._write_record(record)
    
    def _write_record(self, record: UsageRecord) -> None:
        """
        Write usage record to ClickHouse.
        
        Args:
            record: UsageRecord to write
        """
        try:
            import json
            
            billing_period = record.timestamp.date()
            
            self.client.execute(
                """
                INSERT INTO usage_records (
                    timestamp, user_id, resource_type,
                    quantity, unit, unit_price, total_cost,
                    metadata, billing_period
                ) VALUES
                """,
                [(
                    record.timestamp,
                    record.user_id,
                    record.resource_type,
                    float(record.quantity),
                    record.unit,
                    float(record.unit_price),
                    float(record.total_cost),
                    json.dumps(record.metadata or {}),
                    billing_period
                )]
            )
            
            logger.debug(f"Tracked usage: {record.resource_type} for {record.user_id}")
        except Exception as e:
            logger.error(f"Failed to write usage record: {e}")
    
    def get_usage_summary(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Get usage summary for a user and date range.
        
        Args:
            user_id: User identifier
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Usage summary with costs by resource type
        """
        query = """
        SELECT
            resource_type,
            sum(quantity) as total_quantity,
            unit,
            sum(total_cost) as total_cost
        FROM usage_records
        WHERE user_id = %(user_id)s
          AND timestamp BETWEEN %(start_date)s AND %(end_date)s
        GROUP BY resource_type, unit
        ORDER BY total_cost DESC
        """
        
        result = self.client.execute(
            query,
            {
                'user_id': user_id,
                'start_date': start_date,
                'end_date': end_date
            }
        )
        
        summary = {
            'user_id': user_id,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'usage_by_type': [],
            'total_cost': Decimal(0)
        }
        
        for row in result:
            resource_type, quantity, unit, cost = row
            summary['usage_by_type'].append({
                'resource_type': resource_type,
                'quantity': float(quantity),
                'unit': unit,
                'cost': float(cost)
            })
            summary['total_cost'] += Decimal(str(cost))
        
        summary['total_cost'] = float(summary['total_cost'])
        return summary
    
    def create_invoice(
        self,
        user_id: str,
        billing_period_start: datetime,
        billing_period_end: datetime
    ) -> Optional[str]:
        """
        Create Stripe invoice for a billing period.
        
        Args:
            user_id: User identifier
            billing_period_start: Start of billing period
            billing_period_end: End of billing period
            
        Returns:
            Stripe invoice ID
        """
        try:
            # Get usage summary
            summary = self.get_usage_summary(
                user_id,
                billing_period_start,
                billing_period_end
            )
            
            if summary['total_cost'] == 0:
                logger.info(f"No usage to bill for {user_id}")
                return None
            
            # Get or create Stripe customer
            # In production, retrieve customer_id from user database
            customer_id = self._get_stripe_customer(user_id)
            
            # Create invoice
            invoice = stripe.Invoice.create(
                customer=customer_id,
                auto_advance=True,
                collection_method='charge_automatically',
                description=f"SomaAgent usage for {billing_period_start.date()}"
            )
            
            # Add line items
            for usage in summary['usage_by_type']:
                stripe.InvoiceItem.create(
                    customer=customer_id,
                    invoice=invoice.id,
                    amount=int(usage['cost'] * 100),  # cents
                    currency='usd',
                    description=f"{usage['resource_type']}: {usage['quantity']} {usage['unit']}"
                )
            
            # Finalize and send
            stripe.Invoice.finalize_invoice(invoice.id)
            
            logger.info(f"Created invoice {invoice.id} for {user_id}: ${summary['total_cost']:.2f}")
            return invoice.id
            
        except Exception as e:
            logger.error(f"Failed to create invoice for {user_id}: {e}")
            return None
    
    def _get_stripe_customer(self, user_id: str) -> str:
        """
        Get or create Stripe customer for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Stripe customer ID
        """
        # In production, this would query user database
        # For now, create a test customer
        try:
            customers = stripe.Customer.list(email=f"{user_id}@example.com", limit=1)
            if customers.data:
                return customers.data[0].id
            
            customer = stripe.Customer.create(
                email=f"{user_id}@example.com",
                metadata={'user_id': user_id}
            )
            return customer.id
        except Exception as e:
            logger.error(f"Failed to get/create Stripe customer: {e}")
            raise


# Global usage tracker instance
_usage_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Get or create global usage tracker."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker


def track_usage(
    user_id: str,
    resource_type: str,
    **kwargs
) -> None:
    """
    Convenience function to track usage.
    
    Args:
        user_id: User identifier
        resource_type: Type of resource (compute, api_calls, storage, capsule)
        **kwargs: Resource-specific parameters
    """
    tracker = get_usage_tracker()
    
    if resource_type == "compute":
        tracker.track_compute(
            user_id,
            kwargs.get('cpu_hours', Decimal(0)),
            kwargs.get('memory_gb_hours', Decimal(0)),
            kwargs.get('metadata')
        )
    elif resource_type == "capsule":
        tracker.track_capsule_execution(
            user_id,
            kwargs['capsule_id'],
            kwargs['execution_time_ms'],
            kwargs['memory_used_mb'],
            kwargs.get('metadata')
        )
    elif resource_type == "api_calls":
        tracker.track_api_calls(
            user_id,
            kwargs['endpoint'],
            kwargs.get('count', 1),
            kwargs.get('metadata')
        )
    elif resource_type == "storage":
        tracker.track_storage(
            user_id,
            kwargs['storage_gb'],
            kwargs.get('duration_hours', Decimal(1)),
            kwargs.get('metadata')
        )
