from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base dos DTOs HTTP: JSON em camelCase para o chat, atributos em snake_case no Python."""

    model_config = ConfigDict(
        frozen=True, alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True
    )
