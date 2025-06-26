import pytest

from arepy.ecs.constants import MAX_COMPONENTS
from arepy.ecs.utils import Signature


class TestSignature:
    def test_signature_creation(self):
        """Test signature creation and initialization."""
        sig = Signature(MAX_COMPONENTS)
        assert sig.get_bits() is not None
        assert len(sig.get_bits()) == MAX_COMPONENTS
        assert not sig.was_flipped

    def test_signature_custom_size(self):
        """Test signature creation with custom size."""
        custom_size = 64
        sig = Signature(custom_size)
        assert len(sig.get_bits()) == custom_size

    def test_signature_set_and_test(self):
        """Test setting and testing individual bits."""
        sig = Signature(MAX_COMPONENTS)

        # Initially all bits should be False
        for i in range(10):
            assert not sig.test(i)

        # Set some bits
        sig.set(0, True)
        sig.set(5, True)
        sig.set(15, True)

        # Test the bits
        assert sig.test(0)
        assert sig.test(5)
        assert sig.test(15)
        assert not sig.test(1)
        assert not sig.test(10)

    def test_signature_set_false(self):
        """Test setting bits to False."""
        sig = Signature(MAX_COMPONENTS)

        # Set bit to True then False
        sig.set(3, True)
        assert sig.test(3)

        sig.set(3, False)
        assert not sig.test(3)

    def test_signature_clear_bit(self):
        """Test clearing individual bits."""
        sig = Signature(MAX_COMPONENTS)

        # Set and then clear a bit
        sig.set(7, True)
        assert sig.test(7)

        sig.clear_bit(7)
        assert not sig.test(7)

    def test_signature_clear_all(self):
        """Test clearing entire signature."""
        sig = Signature(MAX_COMPONENTS)

        # Set multiple bits
        bits_to_set = [1, 3, 7, 15, 31]
        for bit in bits_to_set:
            sig.set(bit, True)

        # Verify bits are set
        for bit in bits_to_set:
            assert sig.test(bit)

        # Clear all
        sig.clear()

        # All bits should be False
        for bit in bits_to_set:
            assert not sig.test(bit)

        # was_flipped should also be reset
        assert not sig.was_flipped

    def test_signature_flip(self):
        """Test signature flipping functionality."""
        sig = Signature(MAX_COMPONENTS)

        # Initially not flipped
        assert not sig.was_flipped

        # Flip signature
        sig.flip()
        assert sig.was_flipped

        # Flip again
        sig.flip()
        assert not sig.was_flipped

    def test_signature_matching_basic(self):
        """Test basic signature matching logic."""
        sig1 = Signature(MAX_COMPONENTS)
        sig2 = Signature(MAX_COMPONENTS)

        # Empty signatures should match
        assert sig1.matches(sig2)
        assert sig2.matches(sig1)

        # Set components in sig1 (requirement)
        sig1.set(1, True)
        sig1.set(3, True)

        # sig1 should not match empty sig2
        assert not sig1.matches(sig2)
        # But empty sig1 should match sig2 with components
        sig2.set(1, True)
        sig2.set(2, True)
        sig2.set(3, True)
        assert sig1.matches(sig2)

    def test_signature_matching_subset(self):
        """Test signature matching with subsets."""
        sig1 = Signature(MAX_COMPONENTS)  # Requirements
        sig2 = Signature(MAX_COMPONENTS)  # Entity components

        # Set requirements
        sig1.set(1, True)
        sig1.set(5, True)

        # Set entity components (superset)
        sig2.set(1, True)
        sig2.set(3, True)
        sig2.set(5, True)
        sig2.set(7, True)

        # sig1 should match sig2 (sig2 has all required components)
        assert sig1.matches(sig2)

        # But sig2 should not match sig1 (sig1 doesn't have all components of sig2)
        assert not sig2.matches(sig1)

    def test_signature_matching_missing_components(self):
        """Test signature matching when components are missing."""
        sig1 = Signature(MAX_COMPONENTS)  # Requirements
        sig2 = Signature(MAX_COMPONENTS)  # Entity components

        # Set requirements
        sig1.set(1, True)
        sig1.set(5, True)
        sig1.set(10, True)

        # Set entity components (missing component 10)
        sig2.set(1, True)
        sig2.set(5, True)
        sig2.set(7, True)

        # sig1 should not match sig2 (missing component 10)
        assert not sig1.matches(sig2)

    def test_signature_copy(self):
        """Test signature copying functionality."""
        original = Signature(MAX_COMPONENTS)

        # Set some bits in original
        original.set(1, True)
        original.set(5, True)
        original.set(10, True)

        # Create copy before flipping
        copy = original.copy()

        # Copy should have same bits set
        assert copy.test(1)
        assert copy.test(5)
        assert copy.test(10)
        assert not copy.test(2)
        assert copy.was_flipped == original.was_flipped

        # Modifying copy shouldn't affect original
        copy.set(2, True)
        copy.clear_bit(5)

        assert copy.test(2)
        assert not copy.test(5)

        # Original should be unchanged
        assert not original.test(2)
        assert original.test(5)

        # Test flipped state copying
        original.flip()
        flipped_copy = original.copy()
        assert flipped_copy.was_flipped == original.was_flipped

    def test_signature_edge_cases(self):
        """Test signature edge cases."""
        sig = Signature(MAX_COMPONENTS)

        # Test boundary conditions
        sig.set(0, True)  # First bit
        sig.set(MAX_COMPONENTS - 1, True)  # Last bit

        assert sig.test(0)
        assert sig.test(MAX_COMPONENTS - 1)

        # Clear boundary bits
        sig.clear_bit(0)
        sig.clear_bit(MAX_COMPONENTS - 1)

        assert not sig.test(0)
        assert not sig.test(MAX_COMPONENTS - 1)

    def test_signature_large_numbers(self):
        """Test signature with larger bit indices."""
        sig = Signature(MAX_COMPONENTS)

        # Test with larger numbers within bounds
        large_indices = [MAX_COMPONENTS - 5, MAX_COMPONENTS - 3, MAX_COMPONENTS - 1]

        for idx in large_indices:
            if idx >= 0 and idx < MAX_COMPONENTS:
                sig.set(idx, True)
                assert sig.test(idx)

                sig.clear_bit(idx)
                assert not sig.test(idx)

    def test_signature_matching_identical(self):
        """Test matching of identical signatures."""
        sig1 = Signature(MAX_COMPONENTS)
        sig2 = Signature(MAX_COMPONENTS)

        # Set same bits in both (within MAX_COMPONENTS range)
        bits = [1, 5, 10, 15, 20]  # All within MAX_COMPONENTS (32)
        for bit in bits:
            sig1.set(bit, True)
            sig2.set(bit, True)

        # They should match each other
        assert sig1.matches(sig2)
        assert sig2.matches(sig1)

    def test_signature_performance_with_many_bits(self):
        """Test signature performance with many bits set."""
        sig1 = Signature(MAX_COMPONENTS)
        sig2 = Signature(MAX_COMPONENTS)

        # Set many bits (within range)
        max_bits = min(
            16, MAX_COMPONENTS
        )  # Use 16 or MAX_COMPONENTS, whichever is smaller
        for i in range(0, max_bits, 2):
            sig1.set(i, True)
            sig2.set(i, True)

        # Add extra bits to sig2
        for i in range(1, max_bits, 2):
            sig2.set(i, True)

        # sig1 should match sig2 (sig2 has all bits of sig1 plus more)
        assert sig1.matches(sig2)
        assert not sig2.matches(sig1)
