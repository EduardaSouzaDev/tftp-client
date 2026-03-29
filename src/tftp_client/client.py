from __future__ import annotations

import socket
from pathlib import Path

from tftp_client.protocol import (
    BLOCK_SIZE,
    AckPacket,
    DataPacket,
    ErrorPacket,
    build_ack,
    build_data,
    build_rrq,
    build_wrq,
    parse_packet,
)


class TftpError(Exception):
    """Erro reportado pelo servidor TFTP ou falha de protocolo."""


def _open_socket(timeout: float, local_port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    sock.bind(("", local_port))
    return sock


class TftpClient:
    """Cliente TFTP (download e upload em modo octet)."""

    def __init__(
        self,
        host: str,
        port: int = 69,
        *,
        timeout: float = 5.0,
        local_port: int = 0,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._local_port = local_port

    def download(self, remote_name: str, local_path: str | Path) -> None:
        """Recebe um ficheiro do servidor (RRQ)."""
        path = Path(local_path)
        sock = _open_socket(self._timeout, self._local_port)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as out:
                server_tid: tuple[str, int] | None = None
                expected_block = 1
                last_ack = build_ack(0)

                sock.sendto(build_rrq(remote_name), (self._host, self._port))

                while True:
                    try:
                        packet, addr = sock.recvfrom(65536)
                    except TimeoutError:
                        if server_tid is None:
                            sock.sendto(build_rrq(remote_name), (self._host, self._port))
                        else:
                            sock.sendto(last_ack, server_tid)
                        continue

                    if server_tid is None:
                        server_tid = addr
                    elif addr != server_tid:
                        continue

                    try:
                        parsed = parse_packet(packet)
                    except ValueError:
                        continue

                    if isinstance(parsed, ErrorPacket):
                        raise TftpError(f"TFTP {parsed.code}: {parsed.message}")
                    if not isinstance(parsed, DataPacket):
                        continue
                    if parsed.block != expected_block:
                        continue

                    out.write(parsed.payload)
                    last_ack = build_ack(parsed.block)
                    sock.sendto(last_ack, server_tid)

                    if len(parsed.payload) < BLOCK_SIZE:
                        break
                    expected_block += 1
        finally:
            sock.close()

    def upload(self, local_path: str | Path, remote_name: str) -> None:
        """Envia um ficheiro para o servidor (WRQ).

        Se o tamanho for múltiplo de 512, envia um DATA final vazio (RFC 1350).
        """
        path = Path(local_path)
        if not path.is_file():
            raise TftpError(f"ficheiro local inexistente: {path}")

        data = path.read_bytes()
        sock = _open_socket(self._timeout, self._local_port)
        try:
            server_tid: tuple[str, int] | None = None
            pending_ack = 0
            offset = 0
            last_sent = build_wrq(remote_name)
            last_packet_was_final = False
            sock.sendto(last_sent, (self._host, self._port))

            while True:
                try:
                    packet, addr = sock.recvfrom(65536)
                except TimeoutError:
                    if server_tid is None:
                        sock.sendto(last_sent, (self._host, self._port))
                    else:
                        sock.sendto(last_sent, server_tid)
                    continue

                if server_tid is None:
                    server_tid = addr
                elif addr != server_tid:
                    continue

                try:
                    parsed = parse_packet(packet)
                except ValueError:
                    continue

                if isinstance(parsed, ErrorPacket):
                    raise TftpError(f"TFTP {parsed.code}: {parsed.message}")
                if not isinstance(parsed, AckPacket):
                    continue
                if parsed.block != pending_ack:
                    continue

                if last_packet_was_final:
                    break

                chunk = data[offset : offset + BLOCK_SIZE]
                block_num = pending_ack + 1
                last_sent = build_data(block_num, chunk)
                sock.sendto(last_sent, server_tid)
                offset += len(chunk)
                pending_ack = block_num
                last_packet_was_final = len(chunk) < BLOCK_SIZE
        finally:
            sock.close()
