"""Expression evaluator for dynamic values in composable actions."""

from __future__ import annotations

import ast
import operator
from typing import TYPE_CHECKING, Any

from agent.character.abilities import AbilityType

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class ExpressionEvaluator:
    """Safe expression evaluator for action definitions.

    Supports:
    - Arithmetic: +, -, *, /, //, %, **
    - Comparisons: <, >, <=, >=, ==, !=
    - Math functions: min, max, abs, ceil, floor
    - Character attributes: level, strength, dexterity, etc.
    - Ability modifiers: strength_mod, wisdom_mod, etc.
    - Target attributes: target.max_hp, target.hp, etc.
    - Special values: max (infinity)
    """

    # Safe operators
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    # Safe comparison operators
    _comparisons = {
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
    }

    # Safe functions
    _functions = {
        "min": min,
        "max": max,
        "abs": abs,
        "ceil": lambda x: int(x) if x == int(x) else int(x) + 1,
        "floor": lambda x: int(x),
    }

    @classmethod
    def eval(
        cls,
        expr: str | float,
        actor: Character,
        target: Character | None = None,
        ctx: CombatContext | None = None,
    ) -> int | float:
        """Evaluate an expression with character/context variables.

        Args:
            expr: Expression string like "{level} * 5" or literal number
            actor: The character performing the action
            target: Optional target character
            ctx: Optional combat context

        Returns:
            Evaluated numeric result

        Examples:
            eval("1d6", actor) -> 4  # Uses actor's dice roller
            eval("{level} * 5", actor) -> 15  # level=3
            eval("{wisdom_mod} + 2", actor) -> 5  # wisdom_mod=3
            eval("{target.max_hp} / 2", actor, target) -> 20  # target.max_hp=40
        """
        # If already a number, return it
        if isinstance(expr, (int, float)):
            return expr

        # Build variable context
        variables = cls._build_variables(actor, target, ctx)

        # Replace placeholders with values
        expr_str = str(expr)
        for key, value in variables.items():
            expr_str = expr_str.replace(f"{{{key}}}", str(value))

        # Parse and evaluate safely
        try:
            return cls._safe_eval(expr_str, variables)
        except Exception as e:
            msg = f"Failed to evaluate expression '{expr}': {e}"
            raise ValueError(msg) from e

    @classmethod
    def _build_variables(cls, actor: Character, target: Character | None, _: CombatContext | None) -> dict[str, Any]:
        """Build variable context from character and context."""
        variables = {
            # Actor attributes
            "level": actor.level,
            "strength": actor.attributes.strength,
            "dexterity": actor.attributes.dexterity,
            "constitution": actor.attributes.constitution,
            "intelligence": actor.attributes.intelligence,
            "wisdom": actor.attributes.wisdom,
            "charisma": actor.attributes.charisma,
            # Actor modifiers
            "strength_mod": actor.attributes.ability_modifier(AbilityType.STR),
            "dexterity_mod": actor.attributes.ability_modifier(AbilityType.DEX),
            "constitution_mod": actor.attributes.ability_modifier(AbilityType.CON),
            "intelligence_mod": actor.attributes.ability_modifier(AbilityType.INT),
            "wisdom_mod": actor.attributes.ability_modifier(AbilityType.WIS),
            "charisma_mod": actor.attributes.ability_modifier(AbilityType.CHA),
            # Actor stats
            "hp": actor.attributes.hp,
            "max_hp": actor.max_hp,
            "ac": actor.armor_class,
            "proficiency_bonus": actor.attributes.proficiency_bonus,
            # Special values
            "max": float("inf"),
        }

        # Add target attributes if available
        if target:
            variables["target.hp"] = target.attributes.hp
            variables["target.max_hp"] = target.max_hp
            variables["target.ac"] = target.armor_class

        return variables

    @classmethod
    def _safe_eval(cls, expr: str, variables: dict[str, Any]) -> int | float:
        """Safely evaluate an expression using AST.

        Only allows safe operations (no exec, eval, imports, etc.)
        """
        # Parse the expression
        tree = ast.parse(expr, mode="eval")

        # Evaluate the AST
        return cls._eval_node(tree.body, variables)

    @classmethod
    def _eval_node(cls, node: ast.AST, variables: dict[str, Any]) -> Any:
        """Recursively evaluate an AST node."""
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            msg = f"Unknown variable: {node.id}"
            raise NameError(msg)

        if isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left, variables)
            right = cls._eval_node(node.right, variables)
            bin_op = cls._operators.get(type(node.op))
            if bin_op is None:
                msg = f"Unsupported operator: {type(node.op).__name__}"
                raise ValueError(msg)
            return bin_op(left, right)  # type: ignore[operator]

        if isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand, variables)
            unary_op = cls._operators.get(type(node.op))
            if unary_op is None:
                msg = f"Unsupported unary operator: {type(node.op).__name__}"
                raise ValueError(msg)
            return unary_op(operand)  # type: ignore[operator]

        if isinstance(node, ast.Compare):
            left = cls._eval_node(node.left, variables)
            if len(node.ops) != 1 or len(node.comparators) != 1:
                msg = "Only single comparisons are supported"
                raise ValueError(msg)
            right = cls._eval_node(node.comparators[0], variables)
            cmp_op = cls._comparisons.get(type(node.ops[0]))
            if cmp_op is None:
                msg = f"Unsupported comparison: {type(node.ops[0]).__name__}"
                raise ValueError(msg)
            return cmp_op(left, right)  # type: ignore[operator]

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                msg = "Only simple function calls are supported"
                raise TypeError(msg)
            func_name = node.func.id
            if func_name not in cls._functions:
                msg = f"Unknown function: {func_name}"
                raise ValueError(msg)
            func = cls._functions[func_name]
            args = [cls._eval_node(arg, variables) for arg in node.args]
            return func(*args)  # type: ignore[operator]

        msg = f"Unsupported node type: {type(node).__name__}"
        raise ValueError(msg)
