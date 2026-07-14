"""Low-level ECS signature helpers without application-wide side effects."""

try:
    from bitarray import bitarray
except ImportError:
    class bitarray(list):
        """Small compatibility fallback for WebAssembly runtimes."""

        def __init__(self, size: int):
            super().__init__([False] * size)

        def setall(self, value: bool) -> None:
            for index in range(len(self)):
                self[index] = value

        def __invert__(self):
            inverted = bitarray(len(self))
            for index, value in enumerate(self):
                inverted[index] = not value
            return inverted

        def copy(self):
            duplicate = bitarray(len(self))
            duplicate[:] = self
            return duplicate

class Signature:
    __slots__ = ["__bits", "__flipped", "__mask", "__size", "__size_mask"]

    def __init__(self, size: int):
        # Matching is performed with the integer mask.  Most entity signatures
        # never expose their bitarray, so materialize that compatibility view
        # only when get_bits() is explicitly requested.
        self.__bits = None
        self.__flipped = False
        self.__mask = 0
        self.__size = size
        self.__size_mask = (1 << size) - 1

    def __materialize_bits(self):
        bits = self.__bits
        if bits is not None:
            return bits

        bits = bitarray(self.__size)
        bits.setall(False)
        remaining = self.__mask
        while remaining:
            lowest_bit = remaining & -remaining
            bits[lowest_bit.bit_length() - 1] = True
            remaining ^= lowest_bit
        self.__bits = bits
        return bits

    def set(self, index, value: bool):
        if not 0 <= index < self.__size:
            raise IndexError("signature index out of range")
        if self.__bits is not None:
            self.__bits[index] = value
        bit = 1 << index
        if value:
            self.__mask |= bit
        else:
            self.__mask &= ~bit

    def flip(self):
        self.__flipped = not self.__flipped
        if self.__bits is not None:
            self.__bits = ~self.__bits
        self.__mask ^= self.__size_mask

    def clear_bit(self, index: int):
        if not 0 <= index < self.__size:
            raise IndexError("signature index out of range")
        if self.__bits is not None:
            self.__bits[index] = False
        self.__mask &= ~(1 << index)

    def test(self, index: int):
        return bool(self.__mask & (1 << index))

    def get_bits(self):
        return self.__materialize_bits()

    def matches(self, other_signature: "Signature"):
        return (other_signature.__mask & self.__mask) == self.__mask

    def intersects(self, other_signature: "Signature") -> bool:
        return bool(self.__mask & other_signature.__mask)

    def clear(self):
        if self.__bits is not None:
            self.__bits.setall(False)
        self.__mask = 0

    def copy(self) -> "Signature":
        signature = Signature(self.__size)
        if self.__bits is not None:
            signature.__bits = self.__bits.copy()
        signature.__flipped = self.__flipped
        signature.__mask = self.__mask
        return signature

    @property
    def was_flipped(self):
        return self.__flipped
