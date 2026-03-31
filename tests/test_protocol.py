"""Testes unitários do pacote TFTP (sem rede)."""

from __future__ import annotations

import struct

import pytest

from tftp_client.protocol import (
    BLOCK_SIZE,
    AckPacket,
    DataPacket,
    ErrorPacket,
    Opcode,
    build_ack,
    build_data,
    build_rrq,
    build_wrq,
    parse_packet,
)


def test_rrq_contains_opcode_and_octet() -> None:
    pkt = build_rrq("ficheiro.bin")
    assert struct.unpack("!H", pkt[:2])[0] == Opcode.RRQ
    assert b"ficheiro.bin\x00" in pkt
    assert pkt.endswith(b"octet\x00")


def test_wrq() -> None:
    pkt = build_wrq("out.txt")
    assert struct.unpack("!H", pkt[:2])[0] == Opcode.WRQ


def test_data_roundtrip() -> None:
    raw = build_data(7, b"abc")
    p = parse_packet(raw)
    assert isinstance(p, DataPacket)
    assert p.block == 7
    assert p.payload == b"abc"


def test_ack_roundtrip() -> None:
    raw = build_ack(0)
    p = parse_packet(raw)
    assert isinstance(p, AckPacket)
    assert p.block == 0


def test_error_roundtrip() -> None:
    err = struct.pack("!HH", Opcode.ERROR, 1) + b"not found\x00"
    p = parse_packet(err)
    assert isinstance(p, ErrorPacket)
    assert p.code == 1
    assert p.message == "not found"


def test_data_max_block_size() -> None:
    payload = b"x" * BLOCK_SIZE
    raw = build_data(1, payload)
    p = parse_packet(raw)
    assert isinstance(p, DataPacket)
    assert len(p.payload) == BLOCK_SIZE


def test_data_too_large() -> None:
    with pytest.raises(ValueError, match="carga"):
        build_data(1, b"x" * (BLOCK_SIZE + 1))
