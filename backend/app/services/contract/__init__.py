"""
Contract Service

Business logic for contract management, templates, and deliverables.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contract import Contract, ContractTemplate, ContractDeliverable


class ContractService:
    """Service for contract lifecycle management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- Contracts ----

    async def create(
        self,
        user_id: uuid.UUID,
        title: str,
        brand_name: str,
        value_cents: int = 0,
        terms_text: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        template_id: Optional[uuid.UUID] = None,
        variables: Optional[dict] = None,
    ) -> Contract:
        """Create a new contract."""
        contract = Contract(
            user_id=user_id,
            title=title,
            brand_name=brand_name,
            value_cents=value_cents,
            terms_text=terms_text,
            expires_at=expires_at,
            template_id=template_id,
            variables=variables or {},
        )
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def from_template(
        self,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        title: str,
        brand_name: str,
        variables: dict,
        value_cents: int = 0,
    ) -> Contract:
        """Create a contract from a template."""
        template = await self.get_template(template_id)
        if not template:
            raise ValueError("Template not found")

        # Render template with variables
        terms_text = template.content_template
        for key, value in variables.items():
            terms_text = terms_text.replace(f"{{{{{key}}}}}", str(value))

        # Increment usage count
        template.usage_count += 1

        contract = await self.create(
            user_id=user_id,
            title=title,
            brand_name=brand_name,
            value_cents=value_cents,
            terms_text=terms_text,
            template_id=template_id,
            variables=variables,
        )
        return contract

    async def list_contracts(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Contract]:
        """List contracts for a user."""
        query = (
            select(Contract)
            .where(Contract.user_id == user_id)
            .options(selectinload(Contract.deliverables))
            .order_by(Contract.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            query = query.where(Contract.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, contract_id: uuid.UUID) -> Optional[Contract]:
        """Get a contract by ID."""
        query = (
            select(Contract)
            .where(Contract.id == contract_id)
            .options(selectinload(Contract.deliverables))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(self, contract_id: uuid.UUID, **kwargs) -> Optional[Contract]:
        """Update a contract."""
        contract = await self.get(contract_id)
        if not contract:
            return None
        for key, value in kwargs.items():
            if hasattr(contract, key) and value is not None:
                setattr(contract, key, value)
        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def sign(self, contract_id: uuid.UUID) -> Optional[Contract]:
        """Mark a contract as signed."""
        return await self.update(
            contract_id, status="active", signed_at=datetime.utcnow()
        )

    async def delete(self, contract_id: uuid.UUID) -> bool:
        """Delete a contract."""
        contract = await self.get(contract_id)
        if not contract:
            return False
        await self.db.delete(contract)
        await self.db.commit()
        return True

    # ---- Deliverables ----

    async def add_deliverable(
        self,
        contract_id: uuid.UUID,
        description: str,
        due_date: Optional[datetime] = None,
    ) -> ContractDeliverable:
        """Add a deliverable to a contract."""
        deliverable = ContractDeliverable(
            contract_id=contract_id,
            description=description,
            due_date=due_date,
        )
        self.db.add(deliverable)
        await self.db.commit()
        await self.db.refresh(deliverable)
        return deliverable

    async def update_deliverable(
        self, deliverable_id: uuid.UUID, status: str
    ) -> Optional[ContractDeliverable]:
        """Update deliverable status."""
        query = select(ContractDeliverable).where(
            ContractDeliverable.id == deliverable_id
        )
        result = await self.db.execute(query)
        deliverable = result.scalar_one_or_none()
        if not deliverable:
            return None
        deliverable.status = status
        if status == "completed":
            deliverable.completed_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(deliverable)
        return deliverable

    # ---- Templates ----

    async def list_templates(
        self, category: Optional[str] = None
    ) -> list[ContractTemplate]:
        """List available contract templates."""
        query = select(ContractTemplate).where(ContractTemplate.is_public == True)
        if category:
            query = query.where(ContractTemplate.category == category)
        query = query.order_by(ContractTemplate.usage_count.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_template(
        self, template_id: uuid.UUID
    ) -> Optional[ContractTemplate]:
        """Get a template by ID."""
        query = select(ContractTemplate).where(ContractTemplate.id == template_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_template(
        self,
        name: str,
        content_template: str,
        category: str = "general",
        description: Optional[str] = None,
        variables_schema: Optional[dict] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> ContractTemplate:
        """Create a new contract template."""
        template = ContractTemplate(
            name=name,
            content_template=content_template,
            category=category,
            description=description,
            variables_schema=variables_schema or {},
            created_by=created_by,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
