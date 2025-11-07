"""Condition checker for notifications."""
import json
from typing import Dict, Any, Optional


class ConditionChecker:
    """Check if event data matches subscription conditions."""

    @staticmethod
    def check(event_data: Dict[str, Any], conditions: Optional[str]) -> bool:
        """
        Check if event data satisfies conditions.

        Args:
            event_data: Event data dictionary
            conditions: JSON string with conditions or None

        Returns:
            True if conditions are satisfied or no conditions set

        Condition format examples:
        {
            "operator": "and",  # or "or"
            "rules": [
                {"field": "price", "operator": ">=", "value": 100},
                {"field": "status", "operator": "==", "value": "active"},
                {"field": "category", "operator": "in", "value": ["electronics", "gadgets"]}
            ]
        }
        """
        if not conditions:
            return True

        try:
            condition_dict = json.loads(conditions) if isinstance(conditions, str) else conditions
        except (json.JSONDecodeError, TypeError):
            return True

        return ConditionChecker._evaluate_condition(event_data, condition_dict)

    @staticmethod
    def _evaluate_condition(data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Recursively evaluate condition."""
        operator = condition.get("operator", "and")
        rules = condition.get("rules", [])

        if not rules:
            return True

        results = []
        for rule in rules:
            # Nested condition
            if "rules" in rule:
                results.append(ConditionChecker._evaluate_condition(data, rule))
            # Simple rule
            else:
                results.append(ConditionChecker._evaluate_rule(data, rule))

        # Combine results based on operator
        if operator == "and":
            return all(results)
        elif operator == "or":
            return any(results)
        else:
            return True

    @staticmethod
    def _evaluate_rule(data: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Evaluate single rule."""
        field = rule.get("field")
        operator = rule.get("operator")
        expected = rule.get("value")

        if not field or not operator:
            return True

        # Get actual value from data (support nested fields with dot notation)
        actual = ConditionChecker._get_nested_value(data, field)

        # Handle None values
        if actual is None:
            return operator in ["!=", "not_in"] if expected is not None else True

        # Evaluate based on operator
        try:
            if operator == "==":
                return actual == expected
            elif operator == "!=":
                return actual != expected
            elif operator == ">":
                return float(actual) > float(expected)
            elif operator == ">=":
                return float(actual) >= float(expected)
            elif operator == "<":
                return float(actual) < float(expected)
            elif operator == "<=":
                return float(actual) <= float(expected)
            elif operator == "in":
                return actual in expected
            elif operator == "not_in":
                return actual not in expected
            elif operator == "contains":
                return expected in str(actual)
            elif operator == "starts_with":
                return str(actual).startswith(str(expected))
            elif operator == "ends_with":
                return str(actual).endswith(str(expected))
            else:
                return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _get_nested_value(data: Dict[str, Any], field: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = field.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value


# Example usage and tests
if __name__ == "__main__":
    # Test data
    event_data = {
        "price": 150,
        "status": "active",
        "category": "electronics",
        "user": {
            "age": 25,
            "country": "US"
        }
    }

    # Test conditions
    conditions = {
        "operator": "and",
        "rules": [
            {"field": "price", "operator": ">=", "value": 100},
            {"field": "status", "operator": "==", "value": "active"},
            {"field": "category", "operator": "in", "value": ["electronics", "gadgets"]}
        ]
    }

    checker = ConditionChecker()
    result = checker.check(event_data, json.dumps(conditions))
    print(f"Condition check result: {result}")  # Should be True

    # Test nested field
    conditions2 = {
        "operator": "and",
        "rules": [
            {"field": "user.age", "operator": ">=", "value": 18},
            {"field": "user.country", "operator": "==", "value": "US"}
        ]
    }
    result2 = checker.check(event_data, json.dumps(conditions2))
    print(f"Nested condition check result: {result2}")  # Should be True
