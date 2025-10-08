#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.
"""

def test_imports():
    """Test all major imports."""
    try:
        # Test main client import
        from governs_ai import GovernsAIClient, GovernsAIConfig
        print("Main client imports successful")
        
        # Test feature clients
        from governs_ai import PrecheckClient, ConfirmationClient, BudgetClient, ToolClient, AnalyticsClient
        print("Feature client imports successful")
        
        # Test data models
        from governs_ai import (
            PrecheckRequest, PrecheckResponse, Decision,
            BudgetContext, UsageRecord, ConfirmationRequest, ConfirmationResponse,
            HealthStatus
        )
        print("Data model imports successful")
        
        # Test exceptions
        from governs_ai import (
            GovernsAIError, PrecheckError, ConfirmationError,
            BudgetError, ToolError, AnalyticsError
        )
        print("Exception imports successful")
        
        # Test utilities
        from governs_ai.utils import with_retry, RetryConfig, HTTPClient, GovernsAILogger
        print("Utility imports successful")
        
        print("\nAll imports successful! The SDK is properly structured.")
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports()