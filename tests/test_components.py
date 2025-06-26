import unittest

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


class ComponentTest(unittest.TestCase):
    def test_component_creation(self):
        """Test component creation and ID assignment."""
        pos = Position(1.0, 2.0)
        self.assertEqual(pos.x, 1.0)
        self.assertEqual(pos.y, 2.0)
        self.assertIsInstance(pos.get_id(), int)
        self.assertTrue(pos.get_id() > 0)

    def test_component_index_uniqueness(self):
        """Test that different component types get different IDs."""
        pos_id = ComponentIndex.get_id(Position.__name__)
        vel_id = ComponentIndex.get_id(Velocity.__name__)

        self.assertNotEqual(pos_id, vel_id)
        self.assertIsInstance(pos_id, int)
        self.assertIsInstance(vel_id, int)

    def test_component_index_consistency(self):
        """Test that same component type always gets same ID."""
        id1 = ComponentIndex.get_id(Position.__name__)
        id2 = ComponentIndex.get_id(Position.__name__)
        self.assertEqual(id1, id2)

    def test_component_pool_creation(self):
        """Test component pool creation and basic operations."""
        pool = ComponentPool(Position)
        self.assertTrue(pool.is_empty())
        self.assertEqual(len(pool), 0)

    def test_component_pool_operations(self):
        """Test component pool set/get operations."""
        pool = ComponentPool(Position)
        pos = Position(5.0, 10.0)

        # Extend pool to accommodate entity at index 0
        pool.extend([None])

        # Set component
        pool.set(0, pos)
        self.assertFalse(pool.is_empty())
        self.assertEqual(len(pool), 1)

        # Get component
        retrieved = pool.get(0)
        assert retrieved is not None, "Retrieved component should not be None"
        self.assertEqual(retrieved, pos)
        self.assertEqual(retrieved.x, 5.0)
        self.assertEqual(retrieved.y, 10.0)

    def test_component_pool_extend(self):
        """Test component pool extension."""
        pool = ComponentPool(Position)
        initial_size = len(pool)

        # Extend with None values
        pool.extend([None, None, None])
        self.assertEqual(len(pool), initial_size + 3)

    def test_component_pool_resize_with(self):
        """Test component pool resize with fill function."""
        pool = ComponentPool(Position)

        # Resize with lambda that returns None
        pool.resize_with(5, lambda: None)
        self.assertEqual(len(pool), 5)

        # All elements should be None
        for i in range(len(pool)):
            self.assertIsNone(pool.get(i))

    def test_component_pool_iteration(self):
        """Test component pool iteration."""
        pool = ComponentPool(Position)
        components = [Position(i, i * 2) for i in range(3)]

        pool.extend(components)  # type: ignore

        # Test iteration
        iterated_components = list(pool)
        self.assertEqual(len(iterated_components), 3)
        for i, comp in enumerate(iterated_components):
            assert comp is not None, "Component should not be None"
            self.assertEqual(comp.x, i)
            self.assertEqual(comp.y, i * 2)

    def test_component_pool_indexing(self):
        """Test component pool indexing operations."""
        pool = ComponentPool(Position)
        pos = Position(3.0, 4.0)

        pool.extend([pos])

        # Test getitem
        self.assertEqual(pool[0], pos)

        # Test setitem
        new_pos = Position(7.0, 8.0)
        pool[0] = new_pos
        self.assertEqual(pool[0], new_pos)
        self.assertEqual(pool.get(0), new_pos)

    def test_component_pool_contains(self):
        """Test component pool contains operation."""
        pool = ComponentPool(Position)
        pos = Position(1.0, 1.0)

        pool.extend([pos])
        self.assertTrue(pos in pool)

        other_pos = Position(2.0, 2.0)
        self.assertFalse(other_pos in pool)


class SignatureTest(unittest.TestCase):
    def test_signature_creation(self):
        """Test signature creation."""
        sig = Signature(MAX_COMPONENTS)
        self.assertIsNotNone(sig.get_bits())
        self.assertEqual(len(sig.get_bits()), MAX_COMPONENTS)

    def test_signature_set_test(self):
        """Test setting and testing bits in signature."""
        sig = Signature(MAX_COMPONENTS)

        # Initially all bits should be False
        self.assertFalse(sig.test(0))
        self.assertFalse(sig.test(5))

        # Set some bits
        sig.set(0, True)
        sig.set(5, True)

        # Test the bits
        self.assertTrue(sig.test(0))
        self.assertTrue(sig.test(5))
        self.assertFalse(sig.test(1))

    def test_signature_clear_bit(self):
        """Test clearing individual bits."""
        sig = Signature(MAX_COMPONENTS)

        # Set and then clear a bit
        sig.set(3, True)
        self.assertTrue(sig.test(3))

        sig.clear_bit(3)
        self.assertFalse(sig.test(3))

    def test_signature_matching(self):
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
        self.assertTrue(sig1.matches(sig2))

        # Create sig3 without component 3
        sig3 = Signature(MAX_COMPONENTS)
        sig3.set(1, True)
        sig3.set(2, True)

        # sig1 should not match sig3 (missing component 3)
        self.assertFalse(sig1.matches(sig3))

    def test_signature_copy(self):
        """Test signature copying."""
        original = Signature(MAX_COMPONENTS)
        original.set(1, True)
        original.set(5, True)

        copy = original.copy()

        # Copy should have same bits set
        self.assertTrue(copy.test(1))
        self.assertTrue(copy.test(5))
        self.assertFalse(copy.test(2))

        # Modifying copy shouldn't affect original
        copy.set(2, True)
        self.assertTrue(copy.test(2))
        self.assertFalse(original.test(2))

    def test_signature_clear(self):
        """Test clearing entire signature."""
        sig = Signature(MAX_COMPONENTS)

        # Set some bits
        sig.set(1, True)
        sig.set(3, True)
        sig.set(7, True)

        # Clear all
        sig.clear()

        # All bits should be False
        self.assertFalse(sig.test(1))
        self.assertFalse(sig.test(3))
        self.assertFalse(sig.test(7))

    def test_signature_flip(self):
        """Test signature flipping."""
        sig = Signature(MAX_COMPONENTS)

        # Initially not flipped
        self.assertFalse(sig.was_flipped)

        # Flip signature
        sig.flip()
        self.assertTrue(sig.was_flipped)

        # Flip again
        sig.flip()
        self.assertFalse(sig.was_flipped)


if __name__ == "__main__":
    unittest.main()
