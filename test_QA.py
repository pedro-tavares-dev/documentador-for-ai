import os
import codecs
import hashlib
from pathlib import Path
import pytest

# Importa as funções e classes puras do motor de documentação
from documentador import (
    parse_rules,
    match_rule,
    decode_bytes,
    human_size,
    human_time,
    is_sensitive,
    AtomicWriter,
    ScanResult,
    Options,
    remount_parts
)


def test_parse_rules_and_matching():
    """Valida o parsing de regras de exclusão e o casamento com curingas e caminhos."""
    rules_raw = "# Comentário\nnode_modules/, *.log\nsub/deep/*.min.js\n.git/\n"
    rules = parse_rules(rules_raw)
    
    # Deve conter exatamente 4 regras válidas (ignorando comentários e linhas vazias)
    assert len(rules) == 4
    
    # Testa diretório restrito por barra final ('/')
    assert match_rule(rules, "node_modules", "src/node_modules", True) == "node_modules/"
    assert match_rule(rules, "node_modules", "node_modules", False) is None
    
    # Testa curinga no nome do arquivo
    assert match_rule(rules, "app.log", "logs/app.log", False) == "*.log"
    
    # Testa caminho relativo profundo
    assert match_rule(rules, "script.min.js", "sub/deep/script.min.js", False) == "sub/deep/*.min.js"
    
    # Sem regras, nada deve casar
    assert match_rule([], "qualquer.py", "qualquer.py", False) is None


def test_is_sensitive_detection():
    """Garante a identificação correta de arquivos potencialmente sensíveis."""
    assert is_sensitive(".env") is True
    assert is_sensitive(".env.production") is True
    assert is_sensitive("id_rsa") is True
    assert is_sensitive("credentials.json") is True
    assert is_sensitive("secrets.yml") is True
    assert is_sensitive("main.py") is False
    assert is_sensitive("README.md") is False


def test_decode_bytes_safely(tmp_path):
    """Valida a decodificação segura de diferentes encodings (UTF-8, BOM, CP1252) e binários."""
    # 1. UTF-8 Puro
    raw_utf8 = "print('olá mundo')\n".encode("utf-8")
    info_utf8 = decode_bytes(raw_utf8, "test.py")
    assert info_utf8["kind"] == "text"
    assert info_utf8["encoding"] == "utf-8"
    assert "olá mundo" in info_utf8["text"]
    assert info_utf8["verified"] is True

    # 2. UTF-8 com BOM
    raw_bom = codecs.BOM_UTF8 + "conteudo com bom\n".encode("utf-8")
    info_bom = decode_bytes(raw_bom, "bom.txt")
    assert info_bom["kind"] == "text"
    assert "com bom" in info_bom["text"]

    # 3. Windows-1252 (Heurística)
    raw_cp1252 = "ação e coração\n".encode("cp1252")
    info_cp = decode_bytes(raw_cp1252, "latin.txt")
    assert info_cp["kind"] == "text"
    assert "ação" in info_cp["text"]

    # 4. Arquivo Binário (detectado por bytes nulos ou assinatura forte PNG)
    raw_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    info_png = decode_bytes(raw_png, "image.png")
    assert info_png["kind"] == "binary"
    assert "PNG" in info_png["type"]


def test_human_formatters():
    """Valida formatação legível de tamanhos de bytes e tempos."""
    assert human_size(0) == "0 B"
    assert human_size(512) == "512 B"
    assert human_size(1024) == "1.0 KB"
    assert human_size(1048576) == "1.0 MB"
    
    assert human_time(0) == "00:00"
    assert human_time(65) == "01:05"
    assert human_time(3600) == "60:00"


def test_atomic_writer_success(tmp_path):
    """Garante que o AtomicWriter grava com sucesso e remove temporários em caso de sucesso."""
    target = tmp_path / "resultado.txt"
    
    with AtomicWriter(target) as f:
        f.write("dados protegidos por transação atômica")
        
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "dados protegidos por transação atômica"
    
    # Verifica que nenhum arquivo temporário resíduo (.gravando_tmp) sobrou na pasta
    tmp_files = list(tmp_path.glob("*.gravando_tmp"))
    assert len(tmp_files) == 0


def test_atomic_writer_rollback_on_exception(tmp_path):
    """Garante que se ocorrer exceção no bloco, o arquivo de destino não é corrompido e o temporário é limpo."""
    target = tmp_path / "existente.txt"
    target.write_text("conteúdo original seguro", encoding="utf-8")
    
    try:
        with AtomicWriter(target) as f:
            f.write("conteúdo corrompido parcial")
            raise RuntimeError("Falha simulada no meio da escrita")
    except RuntimeError:
        pass
        
    # O arquivo original deve permanecer intacto
    assert target.read_text(encoding="utf-8") == "conteúdo original seguro"
    assert len(list(tmp_path.glob("*.gravando_tmp"))) == 0


def test_options_initialization():
    """Valida a construção e encapsulamento correto do objeto Options."""
    opts = Options(rules=[("node_modules/", True, "node_modules/")], exclude_sensitive=True, max_bytes=1024)
    assert opts.exclude_sensitive is True
    assert opts.max_bytes == 1024
    assert len(opts.rules) == 1