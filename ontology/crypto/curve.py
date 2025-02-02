"""
Copyright (C) 2018 The ontology Authors
This file is part of The ontology library.

The ontology is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The ontology is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with The ontology.  If not, see <http://www.gnu.org/licenses/>.
"""

from enum import Enum, unique
from cryptography.hazmat.primitives.asymmetric import ec

from ontology.exception.error_code import ErrorCode
from ontology.exception.exception import SDKException


@unique
class Curve(Enum):
    P224 = ec.SECP224R1()
    P256 = ec.SECP256R1()
    P384 = ec.SECP384R1()
    P521 = ec.SECP521R1()

    @staticmethod
    def from_label(label: int):
        label = bytes([label])
        if Curve.P224.value == label:
            return Curve.P224.name
        elif Curve.P256.value == label:
            return Curve.P256.name
        elif Curve.P384.value == label:
            return Curve.P384.name
        elif Curve.P521.value == label:
            return Curve.P521.name
        else:
            raise SDKException(ErrorCode.unknown_asymmetric_key_type)

    @staticmethod
    def from_str_curve(str_curve: str):
        if not isinstance(str_curve, str):
            raise SDKException(ErrorCode.require_str_params)
        if str_curve == 'P224':
            return Curve.P224
        elif str_curve == 'P256':
            return Curve.P256
        elif str_curve == 'P384':
            return Curve.P384
        elif str_curve == 'P521':
            return Curve.P521
        else:
            raise SDKException(ErrorCode.unknown_asymmetric_key_type)
