from decimal import Decimal
from typing import no_type_check

from bson import Decimal128
from bson.codec_options import TypeCodec


class DecimalCodec(TypeCodec):
    python_type = Decimal
    bson_type = Decimal128

    @no_type_check
    def transform_python(self, value):  # noqa: ANN001, ANN201
        return Decimal128(value)

    @no_type_check
    def transform_bson(self, value):  # noqa: ANN001, ANN201
        return value.to_decimal()
