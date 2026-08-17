# Templates Service

Responsibility: template storage, placeholder validation, rendering, and version history.

Planned clean-architecture layout:
- `domain`: template entities and placeholder rules
- `application`: preview/render/version use cases
- `infrastructure`: persistence and rendering adapters
- `interfaces`: API/UI integration boundaries
