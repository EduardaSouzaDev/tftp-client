from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum


class Opcode(IntEnum):
    """Códigos de operação TFTP."""

    RRQ = 1
    WRQ = 2
    DATA = 3
    ACK = 4
    ERROR = 5


OCTET_MODE = b"octet\x00"

BLOCK_SIZE = 512


@dataclass(frozen=True)
class DataPacket:
    """Bloco DATA"""

    block: int
    payload: bytes


@dataclass(frozen=True)
class AckPacket:
    """Confirmação ACK"""

    block: int


@dataclass(frozen=True)
class ErrorPacket:
    """Pacote ERROR"""

    code: int
    message: str


def build_rrq(filename: str) -> bytes:
    """Monta RRQ em modo octet."""
    name = filename.encode("utf-8") + b"\x00"
    return struct.pack("!H", Opcode.RRQ) + name + OCTET_MODE


def build_wrq(filename: str) -> bytes:
    """Monta WRQ em modo octet."""
    name = filename.encode("utf-8") + b"\x00"
    return struct.pack("!H", Opcode.WRQ) + name + OCTET_MODE


def build_data(block: int, payload: bytes) -> bytes:
    """Monta DATA com número de bloco e até 512 bytes de dados."""
    if not 0 <= block <= 0xFFFF:
        msg = f"número de bloco inválido: {block}"
        raise ValueError(msg)
    if len(payload) > BLOCK_SIZE:
        msg = f"carga excede {BLOCK_SIZE} bytes"
        raise ValueError(msg)
    return struct.pack("!HH", Opcode.DATA, block) + payload


def build_ack(block: int) -> bytes:
    """Monta ACK."""
    if not 0 <= block <= 0xFFFF:
        msg = f"número de bloco inválido: {block}"
        raise ValueError(msg)
    return struct.pack("!HH", Opcode.ACK, block)


def parse_packet(data: bytes) -> DataPacket | AckPacket | ErrorPacket:
    """Interpreta um datagrama UDP recebido do servidor."""
    if len(data) < 4:
        msg = "pacote muito curto"
        raise ValueError(msg)

    opcode = struct.unpack("!H", data[:2])[0]

    if opcode == Opcode.DATA:
        block = struct.unpack("!H", data[2:4])[0]
        return DataPacket(block=block, payload=data[4:])

    if opcode == Opcode.ACK:
        block = struct.unpack("!H", data[2:4])[0]
        return AckPacket(block=block)

    if opcode == Opcode.ERROR:
        if len(data) < 5:
            msg = "ERROR sem corpo"
            raise ValueError(msg)
        code = struct.unpack("!H", data[2:4])[0]
        rest = data[4:]
        if not rest.endswith(b"\x00"):
            msg = "terminador nulo ausente em ERROR"
            raise ValueError(msg)
        msg_text = rest[:-1].decode("utf-8", errors="replace")
        return ErrorPacket(code=code, message=msg_text)

    msg = f"opcode não suportado: {opcode}"
    raise ValueError(msg)
