import pytest

from arepy.ecs.components import Component, ComponentIndex, ComponentPool
from arepy.ecs.constants import MAX_COMPONENTS
from arepy.ecs.utils import Signature


class Position(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y


class Velocity(Component):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y


def test_component_creation():
    """Test component creation and ID assignment."""
    pos = Position(1.0, 2.0)
    assert pos.x == 1.0
    assert pos.y == 2.0
    assert isinstance(pos.get_id(), int)
    assert pos.get_id() > 0


def test_component_index_uniqueness():
    """Test that different component types get different IDs."""
    pos_id = ComponentIndex.get_id(Position.__name__)
    vel_id = ComponentIndex.get_id(Velocity.__name__)

    assert pos_id != vel_id
    assert isinstance(pos_id, int)
    assert isinstance(vel_id, int)


def test_component_index_consistency():
    """Test that same component type always gets same ID."""
    id1 = ComponentIndex.get_id(Position.__name__)
    id2 = ComponentIndex.get_id(Position.__name__)
    assert id1 == id2


def test_component_pool_creation():
    """Test component pool creation and basic operations."""
    pool = ComponentPool(Position)
    assert pool.is_empty()
    assert len(pool) == 0


def test_component_pool_operations():
    """Test component pool set/get operations."""
    pool = ComponentPool(Position)
    pos = Position(5.0, 10.0)

    # Extend pool to accommodate entity at index 0
    pool.extend([None])

    # Set component
    pool.set(0, pos)
    assert not pool.is_empty()
    assert len(pool) == 1

    # Get component
    retrieved = pool.get(0)
    assert retrieved, "Retrieved component should not be None"
    assert retrieved == pos
    assert retrieved.x == 5.0
    assert retrieved.y == 10.0


def test_component_pool_extend():
    """Test component pool extension."""
    pool = ComponentPool(Position)
    initial_size = len(pool)

    # Extend with None values
    pool.extend([None, None, None])
    assert len(pool) == initial_size + 3


def test_component_pool_resize_with():
    """Test component pool resize with fill function."""
    pool = ComponentPool(Position)

    # Resize with lambda that returns None
    pool.resize_with(5, lambda: None)
    assert len(pool) == 5

    # All elements should be None
    for i in range(len(pool)):
        assert pool.get(i) is None


def test_component_pool_iteration():
    """Test component pool iteration."""
    pool = ComponentPool(Position)
    components = [Position(i, i * 2) for i in range(3)]
    pool.extend(components)  # type: ignore

    # Test iteration
    iterated_components = list(pool)
    assert len(iterated_components) == 3
    for i, comp in enumerate(iterated_components):
        assert comp, "Component should not be None"
        assert comp.x == i, "X coordinate should match index"
        assert comp.y == i * 2, "Y coordinate should be double the index"


def test_component_pool_indexing():
    """Test component pool indexing operations."""
    pool = ComponentPool(Position)
    pos = Position(3.0, 4.0)

    pool.extend([pos])

    # Test getitem
    assert pool[0] == pos

    # Test setitem
    new_pos = Position(7.0, 8.0)
    pool[0] = new_pos
    assert pool[0] == new_pos
    assert pool.get(0) == new_pos


def test_component_pool_contains():
    """Test component pool contains operation."""
    pool = ComponentPool(Position)
    pos = Position(1.0, 1.0)

    pool.extend([pos])
    assert pos in pool

    other_pos = Position(2.0, 2.0)
    assert other_pos not in pool


def test_signature_creation():
    """Test signature creation."""
    sig = Signature(MAX_COMPONENTS)
    assert sig.get_bits() is not None
    assert len(sig.get_bits()) == MAX_COMPONENTS


def test_signature_set_test():
    """Test setting and testing bits in signature."""
    sig = Signature(MAX_COMPONENTS)

    # Initially all bits should be False
    assert not sig.test(0)
    assert not sig.test(5)

    # Set some bits
    sig.set(0, True)
    sig.set(5, True)

    # Test the bits
    assert sig.test(0)
    assert sig.test(5)
    assert not sig.test(1)


def test_signature_clear_bit():
    """Test clearing individual bits."""
    sig = Signature(MAX_COMPONENTS)

    # Set and then clear a bit
    sig.set(3, True)
    assert sig.test(3)

    sig.clear_bit(3)
    assert not sig.test(3)


def test_signature_matching():
    """Test signature matching logic."""
    sig1 = Signature(MAX_COMPONENTS)
    sig2 = Signature(MAX_COMPONENTS)

    # Set components in sig1 (requirement)
    sig1.set(1, True)
    sig1.set(3, True)

    # Set components in sig2 (entity has)
    sig2.set(1, True)
    sig2.set(2, True)
    sig2.set(3, True)

    # sig1 should match sig2 (sig2 has all required components)
    assert sig1.matches(sig2)

    # Create sig3 without component 3
    sig3 = Signature(MAX_COMPONENTS)
    sig3.set(1, True)
    sig3.set(2, True)

    # sig1 should not match sig3 (missing component 3)
    assert not sig1.matches(sig3)


def test_signature_copy():
    """Test signature copying."""
    original = Signature(MAX_COMPONENTS)
    original.set(1, True)
    original.set(5, True)

    copy = original.copy()

    # Copy should have same bits set
    assert copy.test(1)
    assert copy.test(5)
    assert not copy.test(2)

    # Modifying copy shouldn't affect original
    copy.set(2, True)
    assert copy.test(2)
    assert not original.test(2)


def test_signature_clear():
    """Test clearing entire signature."""
    sig = Signature(MAX_COMPONENTS)

    # Set some bits
    sig.set(1, True)
    sig.set(3, True)
    sig.set(7, True)

    # Clear all
    sig.clear()

    # All bits should be False
    assert not sig.test(1)
    assert not sig.test(3)
    assert not sig.test(7)


def test_signature_flip():
    """Test signature flipping."""
    sig = Signature(MAX_COMPONENTS)

    # Initially not flipped
    assert not sig.was_flipped

    # Flip signature
    sig.flip()
    assert sig.was_flipped

    # Flip again
    sig.flip()
    assert not sig.was_flipped
