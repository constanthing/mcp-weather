from google.protobuf.struct_pb2 import Struct
from collections.abc import Mapping, Sequence

def _make_serializable(value):
    """
    Recursively converts non-serializable Protobuf and other special
    types into native Python types that can be JSON serialized.
    """
    if isinstance(value, Struct):
        return {k: _make_serializable(v) for k, v in value.items()}
    if hasattr(value, 'DESCRIPTOR') and hasattr(value, 'fields'):
        # This is a robust way to handle generic Protobuf messages
        return {field.name: _make_serializable(getattr(value, field.name)) for field in value.DESCRIPTOR.fields}
    # Check for dict-like behavior
    if isinstance(value, Mapping):
        return {k: _make_serializable(v) for k, v in value.items()}
    # Check for list-like behavior (and not a string)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [_make_serializable(v) for v in value]
    return value