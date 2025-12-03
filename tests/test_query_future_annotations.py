from __future__ import annotations

import pytest

from arepy.ecs.components import Component
from arepy.ecs.entities import Entity
from arepy.ecs.query import Query, With, Without, get_signed_query_arguments
from arepy.ecs.registry import Registry


class Position(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y


class Velocity(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y


def test_query_with_future_annotations():
    """Test that queries work correctly with 'from __future__ import annotations'."""

    def test_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        pass

    arguments = get_signed_query_arguments(test_system)
    assert "query" in arguments
    assert isinstance(arguments["query"], Query)
    assert hasattr(arguments["query"], "get_entities")


def test_query_iteration_with_future_annotations():
    """Test that query iteration works with future annotations."""
    registry = Registry()

    def movement_system(query: Query[Entity, With[Position, Velocity]]) -> None:
        for entity in query.get_entities():
            pass

    arguments = get_signed_query_arguments(movement_system)
    query = arguments["query"]

    entity = registry.create_entity()
    registry.add_component(entity, Position, Position(1.0, 2.0))
    registry.add_component(entity, Velocity, Velocity(3.0, 4.0))

    query.add_entity(entity)

    entities = list(query.get_entities())
    assert len(entities) == 1
    assert entities[0] == entity


def test_multiple_queries_with_future_annotations():
    """Test multiple query parameters with future annotations."""

    def complex_system(
        moving: Query[Entity, With[Position, Velocity]],
        static: Query[Entity, Without[Velocity]],
    ) -> None:
        pass

    arguments = get_signed_query_arguments(complex_system)

    assert "moving" in arguments
    assert "static" in arguments
    assert isinstance(arguments["moving"], Query)
    assert isinstance(arguments["static"], Query)
