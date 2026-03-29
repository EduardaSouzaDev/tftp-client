# ftpt-client

Cliente **TFTP** (RFC 1350) em Python, em modo **octet** (binário), com interface de linha de comandos. Usa **UDP** e suporta descarregar (`get`) e enviar (`put`) ficheiros para um servidor TFTP.

## Requisitos

- Python 3.10 ou superior

## Instalação

Na raiz do repositório:

```bash
python -m pip install -e .
```

Isto instala o pacote em modo editável e o comando `tftp-client` no ambiente atual.

## Utilização

É necessário um **servidor TFTP** acessível na rede (por exemplo outro PC ou um serviço local na porta 69).

### Descarregar um ficheiro (`get`)

```bash
tftp-client get SERVIDOR caminho/remoto/ficheiro.bin
```

O ficheiro local terá o mesmo nome que o último segmento do caminho remoto (ex.: `ficheiro.bin`). Para escolher o destino:

```bash
tftp-client get SERVIDOR caminho/remoto/ficheiro.bin ./destino/local.bin
```

### Enviar um ficheiro (`put`)

```bash
tftp-client put SERVIDOR ./meu_ficheiro.txt
```

O nome no servidor será, por predefinição, o nome do ficheiro local. Para definir o nome remoto:

```bash
tftp-client put SERVIDOR ./meu_ficheiro.txt nome_no_servidor.txt
```

### Opções globais

| Opção | Descrição |
|--------|------------|
| `-p`, `--port` | Porta UDP do servidor (predefinição: 69) |
| `-t`, `--timeout` | Tempo limite em segundos por operação de rede (predefinição: 5) |
| `-v`, `--verbose` | Mostra no stderr o resumo da operação |
| `--version` | Mostra a versão do programa |

Exemplo com porta e modo verboso:

```bash
tftp-client -p 1069 -v get 192.168.1.10 firmware.bin
```

### Executar como módulo

Sem depender do script no `PATH` (com o projeto instalável ou `PYTHONPATH` a apontar para `src`):

```bash
python -m tftp_client get SERVIDOR ficheiro_remoto
```

## Desenvolvimento

### Testes

```bash
python -m pip install pytest
python -m pytest tests
```

## Estrutura do projeto

- `src/tftp_client/protocol.py` — construção e análise de pacotes TFTP
- `src/tftp_client/client.py` — lógica de rede (download e upload)
- `src/tftp_client/cli.py` — argumentos da linha de comandos
- `tests/` — testes unitários (principalmente protocolo)
