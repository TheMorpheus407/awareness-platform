"""Row Level Security utilities for multi-tenant database access."""

from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID

from sqlalchemy import and_, event, or_, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import Select

from core.logging import logger


class RLSPolicy:
    """Base class for Row Level Security policies."""
    
    def __init__(self, user_id: Optional[UUID] = None, company_id: Optional[UUID] = None):
        """
        Initialize RLS policy.
        
        Args:
            user_id: Current user ID
            company_id: Current company ID
        """
        self.user_id = user_id
        self.company_id = company_id
    
    def apply_to_query(self, query: Query, model: Type[Any]) -> Query:
        """
        Apply RLS policy to a query.
        
        Args:
            query: SQLAlchemy query
            model: Model class being queried
            
        Returns:
            Modified query with RLS filters
        """
        raise NotImplementedError
    
    def can_create(self, model: Type[Any], data: Dict[str, Any]) -> bool:
        """
        Check if user can create a record.
        
        Args:
            model: Model class
            data: Data to create
            
        Returns:
            True if allowed, False otherwise
        """
        raise NotImplementedError
    
    def can_update(self, instance: Any, data: Dict[str, Any]) -> bool:
        """
        Check if user can update a record.
        
        Args:
            instance: Model instance
            data: Update data
            
        Returns:
            True if allowed, False otherwise
        """
        raise NotImplementedError
    
    def can_delete(self, instance: Any) -> bool:
        """
        Check if user can delete a record.
        
        Args:
            instance: Model instance
            
        Returns:
            True if allowed, False otherwise
        """
        raise NotImplementedError


class CompanyRLSPolicy(RLSPolicy):
    """RLS policy for company-scoped resources."""
    
    def apply_to_query(self, query: Query, model: Type[Any]) -> Query:
        """Apply company-based filtering to queries."""
        if not self.company_id:
            # No company context, return empty result
            return query.filter(text("1=0"))
        
        # Check if model has company_id field
        if hasattr(model, "company_id"):
            return query.filter(model.company_id == self.company_id)
        
        return query
    
    def can_create(self, model: Type[Any], data: Dict[str, Any]) -> bool:
        """Check if user can create company-scoped resource."""
        if not self.company_id:
            return False
        
        # Ensure company_id matches if provided
        if "company_id" in data:
            return str(data["company_id"]) == str(self.company_id)
        
        return True
    
    def can_update(self, instance: Any, data: Dict[str, Any]) -> bool:
        """Check if user can update company-scoped resource."""
        if not self.company_id:
            return False
        
        # Check if instance belongs to user's company
        if hasattr(instance, "company_id"):
            if str(instance.company_id) != str(self.company_id):
                return False
        
        # Prevent changing company_id
        if "company_id" in data and str(data["company_id"]) != str(self.company_id):
            return False
        
        return True
    
    def can_delete(self, instance: Any) -> bool:
        """Check if user can delete company-scoped resource."""
        if not self.company_id:
            return False
        
        # Check if instance belongs to user's company
        if hasattr(instance, "company_id"):
            return str(instance.company_id) == str(self.company_id)
        
        return True


class UserRLSPolicy(RLSPolicy):
    """RLS policy for user-scoped resources."""
    
    def apply_to_query(self, query: Query, model: Type[Any]) -> Query:
        """Apply user-based filtering to queries."""
        if not self.user_id:
            # No user context, return empty result
            return query.filter(text("1=0"))
        
        # Check if model has user_id field
        if hasattr(model, "user_id"):
            return query.filter(model.user_id == self.user_id)
        
        # Check if model has created_by field
        if hasattr(model, "created_by"):
            return query.filter(model.created_by == self.user_id)
        
        return query
    
    def can_create(self, model: Type[Any], data: Dict[str, Any]) -> bool:
        """Check if user can create user-scoped resource."""
        if not self.user_id:
            return False
        
        # Ensure user_id matches if provided
        if "user_id" in data:
            return str(data["user_id"]) == str(self.user_id)
        
        return True
    
    def can_update(self, instance: Any, data: Dict[str, Any]) -> bool:
        """Check if user can update user-scoped resource."""
        if not self.user_id:
            return False
        
        # Check if instance belongs to user
        if hasattr(instance, "user_id"):
            if str(instance.user_id) != str(self.user_id):
                return False
        elif hasattr(instance, "created_by"):
            if str(instance.created_by) != str(self.user_id):
                return False
        
        # Prevent changing user_id
        if "user_id" in data and str(data["user_id"]) != str(self.user_id):
            return False
        
        return True
    
    def can_delete(self, instance: Any) -> bool:
        """Check if user can delete user-scoped resource."""
        if not self.user_id:
            return False
        
        # Check if instance belongs to user
        if hasattr(instance, "user_id"):
            return str(instance.user_id) == str(self.user_id)
        elif hasattr(instance, "created_by"):
            return str(instance.created_by) == str(self.user_id)
        
        return False


class AdminRLSPolicy(RLSPolicy):
    """RLS policy for admin users (no restrictions)."""
    
    def apply_to_query(self, query: Query, model: Type[Any]) -> Query:
        """Admin can see everything."""
        return query
    
    def can_create(self, model: Type[Any], data: Dict[str, Any]) -> bool:
        """Admin can create anything."""
        return True
    
    def can_update(self, instance: Any, data: Dict[str, Any]) -> bool:
        """Admin can update anything."""
        return True
    
    def can_delete(self, instance: Any) -> bool:
        """Admin can delete anything."""
        return True


class RLSManager:
    """Manager for applying Row Level Security policies."""
    
    def __init__(self):
        """Initialize RLS manager."""
        self.policies: Dict[str, Type[RLSPolicy]] = {
            "company": CompanyRLSPolicy,
            "user": UserRLSPolicy,
            "admin": AdminRLSPolicy,
        }
    
    def get_policy(
        self,
        policy_type: str,
        user_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None
    ) -> RLSPolicy:
        """
        Get RLS policy instance.
        
        Args:
            policy_type: Type of policy (company, user, admin)
            user_id: Current user ID
            company_id: Current company ID
            
        Returns:
            RLS policy instance
            
        Raises:
            ValueError: If policy type is invalid
        """
        if policy_type not in self.policies:
            raise ValueError(f"Invalid policy type: {policy_type}")
        
        policy_class = self.policies[policy_type]
        return policy_class(user_id=user_id, company_id=company_id)
    
    def apply_policy_to_query(
        self,
        query: Query,
        model: Type[Any],
        policy: RLSPolicy
    ) -> Query:
        """
        Apply RLS policy to a query.
        
        Args:
            query: SQLAlchemy query
            model: Model class being queried
            policy: RLS policy to apply
            
        Returns:
            Modified query with RLS filters
        """
        return policy.apply_to_query(query, model)
    
    def setup_session_rls(
        self,
        session: Session,
        user_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> None:
        """
        Set up RLS for a database session.
        
        Args:
            session: Database session
            user_id: Current user ID
            company_id: Current company ID
            is_admin: Whether user is admin
        """
        # Store RLS context in session info
        session.info["rls_user_id"] = user_id
        session.info["rls_company_id"] = company_id
        session.info["rls_is_admin"] = is_admin
        
        # Determine policy type
        if is_admin:
            policy_type = "admin"
        elif company_id:
            policy_type = "company"
        elif user_id:
            policy_type = "user"
        else:
            policy_type = None
        
        session.info["rls_policy_type"] = policy_type
        
        logger.debug(
            f"RLS configured for session: user_id={user_id}, "
            f"company_id={company_id}, policy={policy_type}"
        )


# Global RLS manager instance
rls_manager = RLSManager()


def get_current_rls_context(session: Session) -> Dict[str, Any]:
    """
    Get current RLS context from session.
    
    Args:
        session: Database session
        
    Returns:
        Dictionary with RLS context
    """
    return {
        "user_id": session.info.get("rls_user_id"),
        "company_id": session.info.get("rls_company_id"),
        "is_admin": session.info.get("rls_is_admin", False),
        "policy_type": session.info.get("rls_policy_type"),
    }


def apply_rls_to_query(query: Query, model: Type[Any], session: Session) -> Query:
    """
    Apply RLS to a query based on session context.
    
    Args:
        query: SQLAlchemy query
        model: Model class being queried
        session: Database session
        
    Returns:
        Modified query with RLS filters
    """
    context = get_current_rls_context(session)
    policy_type = context.get("policy_type")
    
    if not policy_type:
        # No RLS context, deny all access
        logger.warning("No RLS context found, denying query access")
        return query.filter(text("1=0"))
    
    policy = rls_manager.get_policy(
        policy_type,
        user_id=context.get("user_id"),
        company_id=context.get("company_id")
    )
    
    return rls_manager.apply_policy_to_query(query, model, policy)