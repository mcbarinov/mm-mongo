# Architecture Decision Records

Key design decisions for this project. Read this before suggesting changes.

## ADR-001: Factory Pattern for Collection Initialization

### Context
`MongoCollection` and `AsyncMongoCollection` need to perform setup operations during initialization:
- Create indexes from model's `__indexes__`
- Apply schema validation from model's `__schema__`
- Create collection if it doesn't exist

For `AsyncMongoCollection`, these operations are asynchronous (e.g., `await collection.create_indexes(...)`).

### Problem
Python does not support `async def __init__`. There's no way to use `await` inside a constructor.

### Decision
Use factory classmethod pattern:
- Override `__new__` to raise `TypeError`, blocking direct instantiation
- Provide `init()` classmethod as the only way to create instances
- `AsyncMongoCollection.init()` is async, allowing `await` for setup operations
- `MongoCollection.init()` mirrors the same API for consistency

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| `__await__` (awaitable class) | Confusing API, doesn't work for sync version |
| Separate `await col.setup()` | Allows using uninitialized objects — bug-prone |
| Factory function | Loses class association, worse for inheritance |

### Consequences
- Consistent API between sync and async versions
- IDE autocomplete works via classmethod
- Users must use `MongoCollection.init()` instead of `MongoCollection()`
